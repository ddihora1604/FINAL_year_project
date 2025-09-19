from rag_pipeline import RAGPipeline
import os

def run_example():
    """
    Example usage of the RAG pipeline
    """
    # Initialize the RAG pipeline
    print("Initializing RAG Pipeline...")
    rag = RAGPipeline(model_name='all-MiniLM-L6-v2')
    
    # Load and process the customer support data
    csv_path = 'customer_support_sample_1500_balanced.csv'
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found!")
        return
    
    try:
        # Check if saved pipeline exists
        save_dir = 'saved_pipeline'
        
        if os.path.exists(save_dir) and all(os.path.exists(os.path.join(save_dir, f)) for f in 
                                           ['embeddings.npy', 'faiss_index.bin', 'documents.pkl', 'metadata.pkl']):
            print("Found existing pipeline, loading...")
            rag.load_pipeline(save_dir)
            print("Pipeline loaded successfully!")
        else:
            print("No existing pipeline found, building new one...")
            # Build the pipeline
            rag.load_and_process_data(csv_path)
            rag.generate_embeddings()
            rag.build_vector_store()
            
            # Save the pipeline for future use
            rag.save_pipeline(save_dir)
            print("Pipeline built and saved successfully!")
        
        # Interactive query loop
        print("\nRAG Pipeline is ready! You can now ask questions.")
        print("Type 'quit' to exit")
        print("=" * 50)
        
        while True:
            query = input("\nEnter your question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not query:
                continue
            
            # Search for relevant documents
            results = rag.search(query, top_k=3)
            
            print(f"\nTop 3 results for: '{query}'")
            print("-" * 50)
            
            for result in results:
                score = result['score']
                document = result['document']
                metadata = result['metadata']
                
                print(f"Result {result['rank']} (Similarity: {score:.4f})")
                
                # Display relevant information based on metadata structure
                if 'original_query' in metadata and 'original_response' in metadata:
                    print(f"Original Query: {metadata['original_query']}")
                    print(f"Response: {metadata['original_response']}")
                else:
                    print(f"Document: {document[:300]}...")
                
                print("-" * 30)
    
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have installed all dependencies: pip install -r requirements.txt")

if __name__ == "__main__":
    run_example()