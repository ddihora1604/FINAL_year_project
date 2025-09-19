import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import os
from typing import List, Dict, Tuple
import re
from sklearn.metrics.pairwise import cosine_similarity
from cerebras.cloud.sdk import Cerebras
from dotenv import load_dotenv

class RAGPipeline:
    def __init__(self, model_name='all-MiniLM-L6-v2', use_cerebras=True):
        """
        Initialize the RAG pipeline with a sentence transformer model and optional Cerebras LLM
        """
        self.model = SentenceTransformer(model_name)
        self.embeddings = None
        self.documents = None
        self.index = None
        self.metadata = None
        self.use_cerebras = use_cerebras
        
        # Initialize Cerebras if requested
        if self.use_cerebras:
            self._setup_cerebras()
        
    def _setup_cerebras(self):
        """
        Setup Cerebras LLM with API key from environment
        """
        try:
            # Load environment variables
            load_dotenv()
            
            # Get API key from environment
            api_key = os.getenv('CEREBRAS_API_KEY')
            if not api_key:
                print("Warning: CEREBRAS_API_KEY not found in environment variables")
                self.use_cerebras = False
                return
            
            # Initialize Cerebras client
            self.cerebras_client = Cerebras(api_key=api_key)
            
            # Set default model
            self.cerebras_model = "llama-4-scout-17b-16e-instruct"
            print("Cerebras LLM initialized successfully!")
            
        except Exception as e:
            print(f"Failed to initialize Cerebras: {e}")
            self.use_cerebras = False
        
    def preprocess_text(self, text: str) -> str:
        """
        Clean and preprocess text data
        """
        if pd.isna(text):
            return ""
        
        # Convert to string and lowercase
        text = str(text).lower()
        
        # Remove extra whitespaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\!\?\,\-]', '', text)
        
        return text.strip()
    
    def load_and_process_data(self, csv_path: str) -> None:
        """
        Load CSV data and prepare documents for embedding
        """
        print("Loading and processing data...")
        
        # Load the CSV file
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} records from CSV")
        
        # Display column information
        print(f"Columns: {list(df.columns)}")
        
        # Assuming the CSV has columns like 'query', 'response', or similar
        # Adjust column names based on actual CSV structure
        if 'Ticket Description' in df.columns and 'Answer' in df.columns:
            # Use actual column names from the customer support dataset
            self.documents = []
            self.metadata = []
            
            for idx, row in df.iterrows():
                description = self.preprocess_text(row['Ticket Description'])
                answer = self.preprocess_text(row['Answer'])
                
                # Create a combined document
                combined_doc = f"Issue: {description} Solution: {answer}"
                
                self.documents.append(combined_doc)
                self.metadata.append({
                    'index': idx,
                    'ticket_description': row['Ticket Description'],
                    'answer': row['Answer'],
                    'original_data': row.to_dict()
                })
        
        elif 'query' in df.columns and 'response' in df.columns:
            # Fallback for other formats
            self.documents = []
            self.metadata = []
            
            for idx, row in df.iterrows():
                query = self.preprocess_text(row['query'])
                response = self.preprocess_text(row['response'])
                
                # Create a combined document
                combined_doc = f"Query: {query} Response: {response}"
                
                self.documents.append(combined_doc)
                self.metadata.append({
                    'index': idx,
                    'original_query': row['query'],
                    'original_response': row['response']
                })
        
        else:
            # If column structure is different, adapt accordingly
            # For now, use all text columns
            text_columns = df.select_dtypes(include=['object']).columns
            
            self.documents = []
            self.metadata = []
            
            for idx, row in df.iterrows():
                # Combine all text columns
                combined_text = ' '.join([
                    self.preprocess_text(str(row[col])) 
                    for col in text_columns 
                    if pd.notna(row[col])
                ])
                
                self.documents.append(combined_text)
                self.metadata.append({
                    'index': idx,
                    'original_data': row.to_dict()
                })
        
        print(f"Processed {len(self.documents)} documents")
    
    def generate_embeddings(self) -> None:
        """
        Generate embeddings for all documents
        """
        if self.documents is None:
            raise ValueError("No documents loaded. Please load data first.")
        
        print("Generating embeddings...")
        self.embeddings = self.model.encode(
            self.documents, 
            show_progress_bar=True,
            batch_size=32
        )
        
        print(f"Generated embeddings with shape: {self.embeddings.shape}")
    
    def build_vector_store(self) -> None:
        """
        Build FAISS vector store for efficient similarity search
        """
        if self.embeddings is None:
            raise ValueError("No embeddings generated. Please generate embeddings first.")
        
        print("Building vector store...")
        
        # Create FAISS index
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(self.embeddings)
        
        # Add embeddings to index
        self.index.add(self.embeddings.astype('float32'))
        
        print(f"Built vector store with {self.index.ntotal} vectors")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for similar documents given a query
        """
        if self.index is None:
            raise ValueError("Vector store not built. Please build vector store first.")
        
        # Preprocess and encode query
        processed_query = self.preprocess_text(query)
        query_embedding = self.model.encode([processed_query])
        
        # Normalize query embedding
        faiss.normalize_L2(query_embedding)
        
        # Search in vector store
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        # Prepare results
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            results.append({
                'rank': i + 1,
                'score': float(score),
                'document': self.documents[idx],
                'metadata': self.metadata[idx]
            })
        
        return results
    
    def save_pipeline(self, save_dir: str) -> None:
        """
        Save the pipeline components
        """
        os.makedirs(save_dir, exist_ok=True)
        
        # Save embeddings
        np.save(os.path.join(save_dir, 'embeddings.npy'), self.embeddings)
        
        # Save FAISS index
        faiss.write_index(self.index, os.path.join(save_dir, 'faiss_index.bin'))
        
        # Save documents and metadata
        with open(os.path.join(save_dir, 'documents.pkl'), 'wb') as f:
            pickle.dump(self.documents, f)
        
        with open(os.path.join(save_dir, 'metadata.pkl'), 'wb') as f:
            pickle.dump(self.metadata, f)
        
        print(f"Pipeline saved to {save_dir}")
    
    def load_pipeline(self, save_dir: str) -> None:
        """
        Load a saved pipeline
        """
        # Load embeddings
        self.embeddings = np.load(os.path.join(save_dir, 'embeddings.npy'))
        
        # Load FAISS index
        self.index = faiss.read_index(os.path.join(save_dir, 'faiss_index.bin'))
        
        # Load documents and metadata
        with open(os.path.join(save_dir, 'documents.pkl'), 'rb') as f:
            self.documents = pickle.load(f)
        
        with open(os.path.join(save_dir, 'metadata.pkl'), 'rb') as f:
            self.metadata = pickle.load(f)
        
        print(f"Pipeline loaded from {save_dir}")

    
    def generate_response_with_cerebras(self, query: str, context_results: List[Dict]) -> str:
        """
        Generate a response using Cerebras LLM with retrieved context
        """
        if not self.use_cerebras:
            return "Cerebras LLM is not available. Please check your API key configuration."
        
        # Prepare context from retrieved results
        context_text = ""
        for i, result in enumerate(context_results[:3], 1):  # Use top 3 results
            metadata = result['metadata']
            if 'ticket_description' in metadata and 'answer' in metadata:
                context_text += f"\nExample {i}:\n"
                context_text += f"Customer Issue: {metadata['ticket_description']}\n"
                context_text += f"Support Answer: {metadata['answer']}\n"
            elif 'original_query' in metadata and 'original_response' in metadata:
                context_text += f"\nExample {i}:\n"
                context_text += f"Customer Query: {metadata['original_query']}\n"
                context_text += f"Support Response: {metadata['original_response']}\n"
        
        # Create prompt for Cerebras
        prompt = f"""You are a helpful customer support assistant. Based on the following similar support cases, provide a clear and helpful response to the customer's question.

Customer Question: {query}

Similar Support Cases:
{context_text}

Instructions:
1. Analyze the customer's question carefully
2. Use the similar support cases as reference to understand common solutions
3. Provide a clear, helpful, and professional response
4. If the question is not well covered by the examples, provide general guidance and suggest contacting support
5. Keep your response concise but comprehensive
6. Use a friendly and professional tone

Response:"""

        try:
            # Generate response using Cerebras
            chat_completion = self.cerebras_client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.cerebras_model,
                temperature=0.7,
                max_tokens=1024
            )
            
            return chat_completion.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def chat(self, query: str, top_k: int = 5, use_llm: bool = True) -> Dict:
        """
        Complete chat function that searches and optionally generates LLM response
        """
        # First, get relevant documents
        search_results = self.search(query, top_k)
        
        result = {
            'query': query,
            'search_results': search_results,
            'llm_response': None
        }
        
        # Generate LLM response if requested and available
        if use_llm and self.use_cerebras:
            result['llm_response'] = self.generate_response_with_cerebras(query, search_results)
        
        return result

def main():
    # Initialize RAG pipeline
    rag = RAGPipeline()
    
    # Check if saved pipeline exists
    save_dir = 'saved_pipeline'
    csv_path = 'customer_support_sample_1500_balanced.csv'
    
    if os.path.exists(save_dir) and all(os.path.exists(os.path.join(save_dir, f)) for f in 
                                       ['embeddings.npy', 'faiss_index.bin', 'documents.pkl', 'metadata.pkl']):
        print("Found existing pipeline, loading...")
        rag.load_pipeline(save_dir)
        print("Pipeline loaded successfully!")
    else:
        print("No existing pipeline found, building new one...")
        # Load and process data
        rag.load_and_process_data(csv_path)
        
        # Generate embeddings
        rag.generate_embeddings()
        
        # Build vector store
        rag.build_vector_store()
        
        # Save the pipeline
        rag.save_pipeline(save_dir)
        print("Pipeline built and saved successfully!")
    
    # Example search
    query = "How to reset my password?"
    results = rag.search(query, top_k=3)
    
    print(f"\nSearch results for: '{query}'")
    print("=" * 50)
    
    for result in results:
        print(f"Rank {result['rank']} (Score: {result['score']:.4f})")
        print(f"Document: {result['document'][:200]}...")
        print("-" * 30)

if __name__ == "__main__":
    main()