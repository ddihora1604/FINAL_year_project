import os
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
from pathlib import Path
import pickle
import json
from datetime import datetime

# External libraries
try:
    from openai import OpenAI
    OPENAI_V1 = True
except ImportError:
    try:
        import openai
        OPENAI_V1 = False
    except ImportError:
        raise ImportError("OpenAI library not found. Please install with: pip install openai")

from sentence_transformers import SentenceTransformer
import faiss
from dotenv import load_dotenv
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import re

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RAGConfig:
    """Configuration for RAG pipeline"""
    model_name: str = "meta-llama/llama-3-8b-instruct"
    embedding_model: str = "all-MiniLM-L6-v2"
    max_tokens: int = 1024
    temperature: float = 0.7
    top_k_results: int = 5
    chunk_size: int = 512
    chunk_overlap: int = 50

class DocumentProcessor:
    """Handles document preprocessing and chunking"""
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.stop_words = set(stopwords.words('english'))
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if pd.isna(text):
            return ""
        
        # Remove HTML tags, special characters, and normalize whitespace
        text = re.sub(r'<[^>]+>', '', str(text))
        text = re.sub(r'[^\w\s\.\,\!\?\-\:\;]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """Split text into overlapping chunks"""
        if not text or len(text) < 50:
            return []
        
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = ""
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append({
                    'text': current_chunk.strip(),
                    'metadata': metadata or {},
                    'length': current_length
                })
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                current_chunk = overlap_text + " " + sentence
                current_length = len(current_chunk)
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                current_length = len(current_chunk)
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'metadata': metadata or {},
                'length': current_length
            })
        
        return chunks

class VectorStore:
    """FAISS-based vector store for similarity search"""
    
    def __init__(self, embedding_model_name: str = "all-MiniLM-L6-v2"):
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.index = None
        self.documents = []
        self.embeddings = []
        
    def add_documents(self, documents: List[Dict]):
        """Add documents to vector store"""
        logger.info(f"Adding {len(documents)} documents to vector store")
        
        # Extract text for embedding
        texts = [doc['text'] for doc in documents]
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        
        # Store documents and embeddings
        self.documents.extend(documents)
        self.embeddings.extend(embeddings)
        
        # Build/update FAISS index
        if self.index is None:
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
        # Normalize embeddings for cosine similarity
        embeddings_normalized = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        self.index.add(embeddings_normalized.astype('float32'))
        
        logger.info(f"Vector store now contains {len(self.documents)} documents")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for similar documents"""
        if self.index is None or len(self.documents) == 0:
            return []
        
        # Encode query
        query_embedding = self.embedding_model.encode([query])
        query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        
        # Search
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        # Return results with scores
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents):
                result = self.documents[idx].copy()
                result['similarity_score'] = float(score)
                results.append(result)
        
        return results
    
    def save(self, filepath: str):
        """Save vector store to disk"""
        data = {
            'documents': self.documents,
            'embeddings': self.embeddings
        }
        
        # Save FAISS index
        if self.index is not None:
            faiss.write_index(self.index, f"{filepath}.faiss")
        
        # Save documents and embeddings
        with open(f"{filepath}.pkl", 'wb') as f:
            pickle.dump(data, f)
        
        logger.info(f"Vector store saved to {filepath}")
    
    def load(self, filepath: str):
        """Load vector store from disk"""
        # Load FAISS index
        if os.path.exists(f"{filepath}.faiss"):
            self.index = faiss.read_index(f"{filepath}.faiss")
        
        # Load documents and embeddings
        if os.path.exists(f"{filepath}.pkl"):
            with open(f"{filepath}.pkl", 'rb') as f:
                data = pickle.load(f)
                self.documents = data['documents']
                self.embeddings = data['embeddings']
        
        logger.info(f"Vector store loaded from {filepath}")

class RAGPipeline:
    """Main RAG Pipeline class"""
    
    def __init__(self, config: RAGConfig = None):
        self.config = config or RAGConfig()
        
        # Load environment variables
        load_dotenv()
        
        # Initialize OpenRouter client based on OpenAI version
        if OPENAI_V1:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPEN_ROUTER_API_KEY")
            )
        else:
            # For older versions of openai library
            openai.api_base = "https://openrouter.ai/api/v1"
            openai.api_key = os.getenv("OPEN_ROUTER_API_KEY")
            self.client = None  # Will use openai module directly
        
        # Initialize components
        self.document_processor = DocumentProcessor(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap
        )
        
        self.vector_store = VectorStore(self.config.embedding_model)
        
        # Add similarity threshold for filtering relevant queries - make it even more inclusive
        self.similarity_threshold = 0.1  # Very low threshold to catch more matches
        
        logger.info("RAG Pipeline initialized")
    
    def load_csv_data(self, csv_path: str) -> pd.DataFrame:
        """Load and validate CSV data"""
        logger.info(f"Loading data from {csv_path}")
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} rows from CSV")
        
        return df
    
    def process_customer_support_data(self, df: pd.DataFrame) -> List[Dict]:
        """Process customer support tickets into documents"""
        documents = []
        
        print(f"DEBUG: Processing {len(df)} rows from CSV")
        
        for idx, row in df.iterrows():
            # Combine relevant fields into a comprehensive text
            text_parts = []
            
            # Add ticket details - make sure we're getting the data
            if pd.notna(row.get('Ticket Subject')):
                text_parts.append(f"Subject: {row['Ticket Subject']}")
            
            if pd.notna(row.get('Ticket Description')):
                text_parts.append(f"Description: {row['Ticket Description']}")
            
            if pd.notna(row.get('Answer')):
                text_parts.append(f"Resolution: {row['Answer']}")
            
            # Create main text
            main_text = "\n\n".join(text_parts)
            cleaned_text = self.document_processor.clean_text(main_text)
            
            if not cleaned_text:
                continue
            
            # Debug: Print first few processed documents
            if idx < 3:
                print(f"DEBUG: Processed ticket {idx}:")
                print(f"  Product: {row.get('Product Purchased', 'N/A')}")
                print(f"  Text length: {len(cleaned_text)}")
                print(f"  Preview: {cleaned_text[:200]}...")
            
            # Create metadata
            metadata = {
                'ticket_id': row.get('Ticket ID', idx),
                'customer_name': row.get('Customer Name', ''),
                'product': row.get('Product Purchased', ''),
                'ticket_type': row.get('Ticket Type', ''),
                'status': row.get('Ticket Status', ''),
                'priority': row.get('Ticket Priority', ''),
                'channel': row.get('Ticket Channel', ''),
                'satisfaction_rating': row.get('Customer Satisfaction Rating', ''),
                'source_row': idx
            }
            
            # Create chunks
            chunks = self.document_processor.chunk_text(cleaned_text, metadata)
            documents.extend(chunks)
        
        print(f"DEBUG: Created {len(documents)} document chunks total")
        logger.info(f"Processed {len(documents)} document chunks from {len(df)} tickets")
        return documents
    
    def build_knowledge_base(self, csv_path: str, save_path: str = None):
        """Build knowledge base from CSV data"""
        # Load data
        df = self.load_csv_data(csv_path)
        
        # Process documents
        documents = self.process_customer_support_data(df)
        
        # Add to vector store
        self.vector_store.add_documents(documents)
        
        # Save if path provided
        if save_path:
            self.vector_store.save(save_path)
        
        logger.info("Knowledge base built successfully")
    
    def retrieve_relevant_context(self, query: str, top_k: int = None) -> List[Dict]:
        """Retrieve relevant context for a query"""
        top_k = top_k or self.config.top_k_results
        results = self.vector_store.search(query, top_k)
        
        logger.info(f"Retrieved {len(results)} relevant documents for query")
        return results
    
    def is_query_relevant(self, query: str, top_k: int = 3) -> bool:
        """Check if query is relevant to the knowledge base"""
        results = self.vector_store.search(query, top_k)
        
        if not results:
            return False
        
        # Check if any result meets the similarity threshold
        max_similarity = max([doc.get('similarity_score', 0.0) for doc in results])
        return max_similarity >= self.similarity_threshold
    
    def generate_response(self, query: str, context_docs: List[Dict]) -> str:
        """Generate response using OpenRouter API"""
        # Prepare context - extract solutions more effectively
        context_sections = []
        
        for i, doc in enumerate(context_docs, 1):
            metadata = doc.get('metadata', {})
            text_content = doc['text']
            
            # Try to extract the resolution/answer section more intelligently
            solution_text = ""
            
            if "Resolution:" in text_content:
                # Extract everything after "Resolution:"
                resolution_part = text_content.split("Resolution:", 1)[1].strip()
                solution_text = resolution_part
            elif "Answer:" in text_content:
                # Alternative format
                answer_part = text_content.split("Answer:", 1)[1].strip()
                solution_text = answer_part
            else:
                # If no clear resolution marker, look for the longest meaningful section
                parts = text_content.split('\n\n')
                # Find the part that looks most like a solution (usually the longest detailed part)
                solution_text = max(parts, key=len) if parts else text_content
            
            # Clean up the solution text
            solution_text = solution_text.strip()
            if not solution_text:
                solution_text = text_content
            
            context_sections.append({
                'index': i,
                'ticket_id': metadata.get('ticket_id', 'N/A'),
                'customer_name': metadata.get('customer_name', 'N/A'),
                'product': metadata.get('product', 'N/A'),
                'ticket_type': metadata.get('ticket_type', 'N/A'),
                'solution': solution_text,
                'similarity': doc.get('similarity_score', 0.0)
            })
        
        # Debug: Print what context we're sending
        print("DEBUG: Context being sent to LLM:")
        for section in context_sections[:2]:  # Show first 2 sections
            print(f"  Section {section['index']}: Ticket #{section['ticket_id']} - {section['customer_name']} - {section['product']} (similarity: {section['similarity']:.3f})")
            print(f"    Solution preview: {section['solution'][:150]}...")
        
        # Build context text for LLM - make it more conversational
        context_text = ""
        for section in context_sections:
            context_text += f"\n--- Similar Case ---\n"
            context_text += f"We previously helped {section['customer_name']} (Ticket #{section['ticket_id']}) with their {section['product']}.\n"
            context_text += f"Issue category: {section['ticket_type']}\n"
            context_text += f"How we resolved it: {section['solution']}\n"
        
        # Natural system prompt that doesn't explicitly mention revealing info
        system_prompt = """You are an experienced customer support representative with access to your company's case history. You pride yourself on providing personalized, helpful service by drawing from your team's collective experience.

When helping customers, you naturally:
- Share relevant experiences from previous cases you've handled
- Reference specific situations where similar issues were successfully resolved
- Mention how other customers with similar products overcame comparable challenges
- Provide concrete examples and proven solutions
- Build trust by showing your experience with similar cases

Your communication style is warm, professional, and reassuring. You make customers feel confident that their issue can be resolved because you've successfully handled similar situations before."""
        
        # User prompt that frames previous cases as team experience
        user_prompt = f"""Here are some similar cases from your team's recent experience:

{context_text}

A customer is now asking: "{query}"

Drawing from your team's experience with similar cases, provide a helpful response. Share relevant examples from your previous successful resolutions to reassure the customer and provide them with a proven solution."""
        
        try:
            if OPENAI_V1:
                completion = self.client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": "https://rag-pipeline-local",
                        "X-Title": "Customer Support RAG Pipeline",
                    },
                    model=self.config.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=self.config.max_tokens,
                    temperature=0.4,  # Slightly more creative for natural language
                )
                response = completion.choices[0].message.content
            else:
                completion = openai.ChatCompletion.create(
                    model=self.config.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=self.config.max_tokens,
                    temperature=0.4,
                    headers={
                        "HTTP-Referer": "https://rag-pipeline-local",
                        "X-Title": "Customer Support RAG Pipeline",
                    }
                )
                response = completion.choices[0].message.content
            
            logger.info("Response generated successfully")
            
            # Debug: Show what the LLM returned
            print(f"DEBUG: LLM response length: {len(response)} characters")
            print(f"DEBUG: LLM response preview: {response[:200]}...")
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I apologize, but I encountered an error while accessing our knowledge base. Please contact support directly for assistance."
    
    def query(self, question: str, top_k: int = None) -> Dict[str, Any]:
        """Main query interface with relevance filtering"""
        start_time = datetime.now()
        
        # Retrieve relevant context first
        relevant_docs = self.retrieve_relevant_context(question, top_k)
        
        # Debug: Print similarity scores
        print(f"DEBUG: Found {len(relevant_docs)} documents")
        for i, doc in enumerate(relevant_docs[:3], 1):
            print(f"  Doc {i}: Similarity {doc.get('similarity_score', 0.0):.4f} - Product: {doc.get('metadata', {}).get('product', 'N/A')}")
            print(f"    Preview: {doc['text'][:100]}...")
        
        # Use a much lower threshold - if we have any results with similarity > 0.05, proceed
        if not relevant_docs or max([doc.get('similarity_score', 0.0) for doc in relevant_docs]) < 0.05:
            return {
                'question': question,
                'answer': "I don't have a specific solution for this issue in our knowledge base. Please contact our support team for assistance with technical issues, product troubleshooting, setup, or refunds.",
                'sources': [],
                'processing_time': (datetime.now() - start_time).total_seconds(),
                'relevant': False
            }
        
        # Use all documents above the very low threshold
        filtered_docs = [doc for doc in relevant_docs if doc.get('similarity_score', 0.0) >= self.similarity_threshold]
        
        # If no docs meet even the low threshold, use the top 3 anyway
        if not filtered_docs and relevant_docs:
            filtered_docs = relevant_docs[:3]
            print("DEBUG: Using top 3 documents despite low similarity scores")
        
        if not filtered_docs:
            return {
                'question': question,
                'answer': "I don't have a specific solution for this issue in our knowledge base. Please contact our support team for assistance with technical issues, product troubleshooting, setup, or refunds.",
                'sources': [],
                'processing_time': (datetime.now() - start_time).total_seconds(),
                'relevant': False
            }
        
        print(f"DEBUG: Using {len(filtered_docs)} documents for response generation")
        
        # Generate response
        answer = self.generate_response(question, filtered_docs)
        
        # Prepare sources
        sources = []
        for doc in filtered_docs:
            metadata = doc.get('metadata', {})
            sources.append({
                'ticket_id': metadata.get('ticket_id'),
                'product': metadata.get('product'),
                'similarity_score': doc.get('similarity_score', 0.0),
                'text_preview': doc['text'][:200] + "..." if len(doc['text']) > 200 else doc['text']
            })
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'question': question,
            'answer': answer,
            'sources': sources,
            'processing_time': processing_time,
            'relevant': True
        }
    
    def chat(self):
        """Interactive chat interface"""
        print("\n" + "="*80)
        print("CUSTOMER SUPPORT CHAT - POWERED BY RAG PIPELINE")
        print("="*80)
        print("Welcome! I'm your customer support assistant.")
        print("I can help you with:")
        print("• Product troubleshooting and technical issues")
        print("• Setup and installation problems")
        print("• Refund and billing inquiries")
        print("• General product support")
        print("\nType 'quit', 'exit', or 'bye' to end the conversation.")
        print("-" * 80)
        
        conversation_history = []
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if not user_input:
                    continue
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                    print("\nThank you for using our customer support! Have a great day!")
                    break
                
                # Process the query
                print("🔍 Processing your question...")
                result = self.query(user_input)
                
                # Display response
                print(f"\n🤖 Support Assistant: {result['answer']}")
                
                # Show sources if relevant query
                if result.get('relevant', False) and result['sources']:
                    print(f"\n📊 Response based on {len(result['sources'])} similar support cases")
                    print(f"⏱️  Processing time: {result['processing_time']:.2f} seconds")
                    
                    # Show top source for reference
                    if result['sources']:
                        top_source = result['sources'][0]
                        print(f"🔗 Most relevant case: Ticket #{top_source['ticket_id']} ({top_source['product']}) - Similarity: {top_source['similarity_score']:.3f}")
                
                # Add to conversation history
                conversation_history.append({
                    'user': user_input,
                    'assistant': result['answer'],
                    'relevant': result.get('relevant', False),
                    'timestamp': datetime.now().isoformat()
                })
                
                print("-" * 80)
                
            except KeyboardInterrupt:
                print("\n\nChat interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ An error occurred: {e}")
                print("Please try again with a different question.")
        
        return conversation_history

def main():
    """Interactive chat interface for the RAG pipeline"""
    try:
        # Initialize pipeline
        print("🚀 Initializing Customer Support RAG Pipeline...")
        rag = RAGPipeline()
        
        # CSV path
        csv_path = r"c:\Tejas\BE Project\CODEBASE\BE-Project\RAG-Pipeline-Ollama\customer_support_tickets_sample_1500_balanced.csv"
        
        # Check if knowledge base exists
        kb_path = "customer_support_kb"
        
        if os.path.exists(f"{kb_path}.pkl") and os.path.exists(f"{kb_path}.faiss"):
            print("📚 Loading existing knowledge base...")
            rag.vector_store.load(kb_path)
        else:
            print("🔨 Building knowledge base from CSV data...")
            rag.build_knowledge_base(csv_path, save_path=kb_path)
        
        print("✅ Knowledge base ready!")
        print(f"📖 Loaded {len(rag.vector_store.documents)} document chunks")
        
        # Start chat interface
        conversation = rag.chat()
        
        # Optionally save conversation history
        if conversation:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            history_file = f"chat_history_{timestamp}.json"
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(conversation, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Conversation saved to {history_file}")
    
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Please ensure the CSV file exists at the specified path.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        logger.error(f"Application error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
