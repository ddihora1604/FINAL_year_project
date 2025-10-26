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
        
        # Add similarity threshold for filtering relevant queries
        self.similarity_threshold = 0.1
        
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
        
        for idx, row in df.iterrows():
            # Combine relevant fields into a comprehensive text
            text_parts = []
            
            # Add ticket details
            if pd.notna(row.get('Ticket Subject')):
                text_parts.append(f"Subject: {row['Ticket Subject']}")
            
            if pd.notna(row.get('Ticket Description')):
                text_parts.append(f"Description: {row['Ticket Description']}")
            
            if pd.notna(row.get('Answer')):
                text_parts.append(f"Solution: {row['Answer']}")
            
            # Create main text
            main_text = "\n\n".join(text_parts)
            cleaned_text = self.document_processor.clean_text(main_text)
            
            if not cleaned_text:
                continue
            
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
    
    def generate_response(self, query: str, context_docs: List[Dict]) -> str:
        """Generate response using OpenRouter API"""
        # Prepare context - extract information more effectively
        context_sections = []
        
        for i, doc in enumerate(context_docs, 1):
            metadata = doc.get('metadata', {})
            text_content = doc['text']
            
            # Extract different parts of the document
            subject = ""
            description = ""
            solution = ""
            
            # Split content into sections
            if "Subject:" in text_content:
                parts = text_content.split("Subject:", 1)[1]
                if "Description:" in parts:
                    subject = parts.split("Description:", 1)[0].strip()
                    remaining = parts.split("Description:", 1)[1]
                    if "Solution:" in remaining:
                        description = remaining.split("Solution:", 1)[0].strip()
                        solution = remaining.split("Solution:", 1)[1].strip()
                    else:
                        description = remaining.strip()
                else:
                    subject = parts.strip()
            
            # If no clear structure, try alternative patterns
            if not solution and "Answer:" in text_content:
                solution = text_content.split("Answer:", 1)[1].strip()
            elif not solution and "Resolution:" in text_content:
                solution = text_content.split("Resolution:", 1)[1].strip()
            
            # If still no solution, use the longest meaningful part
            if not solution:
                text_parts = text_content.split('\n\n')
                solution = max(text_parts, key=len) if text_parts else text_content
            
            context_sections.append({
                'index': i,
                'ticket_id': metadata.get('ticket_id', 'N/A'),
                'customer_name': metadata.get('customer_name', 'N/A'),
                'product': metadata.get('product', 'N/A'),
                'ticket_type': metadata.get('ticket_type', 'N/A'),
                'subject': subject,
                'description': description,
                'solution': solution,
                'similarity': doc.get('similarity_score', 0.0)
            })
        
        # Build structured context text
        context_text = "RELEVANT SUPPORT CASES:\n\n"
        
        for section in context_sections:
            context_text += f"Case {section['index']}:\n"
            context_text += f"Ticket ID: {section['ticket_id']}\n"
            context_text += f"Customer: {section['customer_name']}\n"
            context_text += f"Product: {section['product']}\n"
            context_text += f"Issue Type: {section['ticket_type']}\n"
            
            if section['subject']:
                context_text += f"Subject: {section['subject']}\n"
            
            if section['description']:
                context_text += f"Problem: {section['description']}\n"
            
            if section['solution']:
                context_text += f"Solution: {section['solution']}\n"
            
            context_text += f"Relevance Score: {section['similarity']:.3f}\n"
            context_text += "-" * 50 + "\n\n"
        
        # Simple, raw system prompt
        system_prompt = "You are a customer support assistant. Use the provided support cases to help answer the customer's question. Be helpful and direct."
        
        # Simple, raw user prompt
        user_prompt = f"{context_text}CUSTOMER QUESTION: {query}\n\nYOUR RESPONSE:"
        
        try:
            if OPENAI_V1:
                completion = self.client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": "https://rag-pipeline-local",
                        "X-Title": "RAG Pipeline",
                    },
                    model=self.config.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
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
                    temperature=self.config.temperature,
                    headers={
                        "HTTP-Referer": "https://rag-pipeline-local",
                        "X-Title": "RAG Pipeline",
                    }
                )
                response = completion.choices[0].message.content
            
            logger.info("Response generated successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {e}"
    
    def query(self, question: str, top_k: int = None) -> Dict[str, Any]:
        """Main query interface"""
        start_time = datetime.now()
        
        # Retrieve relevant context
        relevant_docs = self.retrieve_relevant_context(question, top_k)
        
        if not relevant_docs:
            return {
                'question': question,
                'answer': "No relevant information found.",
                'sources': [],
                'processing_time': (datetime.now() - start_time).total_seconds(),
                'relevant': False
            }
        
        # Filter by similarity threshold
        filtered_docs = [doc for doc in relevant_docs if doc.get('similarity_score', 0.0) >= self.similarity_threshold]
        
        if not filtered_docs:
            return {
                'question': question,
                'answer': "No sufficiently relevant information found.",
                'sources': [],
                'processing_time': (datetime.now() - start_time).total_seconds(),
                'relevant': False
            }
        
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
        """Simple chat interface"""
        print("RAG Pipeline Chat - Type 'quit' to exit")
        
        while True:
            try:
                user_input = input("\nQuestion: ").strip()
                
                if user_input.lower() in ['quit', 'exit']:
                    break
                
                result = self.query(user_input)
                print(f"\nAnswer: {result['answer']}")
                print(f"Processing time: {result['processing_time']:.2f}s")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    """Main function"""
    try:
        # Initialize pipeline
        rag = RAGPipeline()
        
        # CSV path
        csv_path = r"c:\Tejas\BE Project\CODEBASE\BE-Project\RAG-Pipeline-Ollama\customer_support_tickets_sample_1500_balanced.csv"
        
        # Check if knowledge base exists
        kb_path = "customer_support_kb"
        
        if os.path.exists(f"{kb_path}.pkl") and os.path.exists(f"{kb_path}.faiss"):
            print("Loading existing knowledge base...")
            rag.vector_store.load(kb_path)
        else:
            print("Building knowledge base...")
            rag.build_knowledge_base(csv_path, save_path=kb_path)
        
        print(f"Knowledge base ready with {len(rag.vector_store.documents)} documents")
        
        # Start chat
        rag.chat()
    
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Application error: {e}", exc_info=True)

if __name__ == "__main__":
    main()