from rag_pipeline import RAGPipeline
import os
from dotenv import load_dotenv

def run_chatbot():
    """
    Command-line chatbot interface
    """
    print("🤖 Customer Support Chatbot")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Initialize the RAG pipeline with Cerebras
    print("Initializing RAG Pipeline with Cerebras LLM...")
    rag = RAGPipeline(model_name='all-MiniLM-L6-v2', use_cerebras=True)
    
    # Load pipeline
    csv_path = 'customer_support_sample_1500_balanced.csv'
    save_dir = 'saved_pipeline'
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found!")
        return
    
    try:
        if os.path.exists(save_dir) and all(os.path.exists(os.path.join(save_dir, f)) for f in 
                                           ['embeddings.npy', 'faiss_index.bin', 'documents.pkl', 'metadata.pkl']):
            print("Loading existing pipeline...")
            rag.load_pipeline(save_dir)
            print("✅ Pipeline loaded successfully!")
        else:
            print("Building new pipeline...")
            rag.load_and_process_data(csv_path)
            rag.generate_embeddings()
            rag.build_vector_store()
            rag.save_pipeline(save_dir)
            print("✅ Pipeline built and saved successfully!")
        
        print(f"🤖 Cerebras LLM Status: {'✅ Active' if rag.use_cerebras else '❌ Inactive'}")
        
        # Interactive chat loop
        print("\n🎉 Chatbot is ready! Ask me anything about customer support.")
        print("Type 'quit', 'exit', or 'q' to stop chatting.")
        print("-" * 50)
        
        while True:
            query = input("\n💬 You: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Thanks for chatting! Goodbye!")
                break
            
            if not query:
                continue
            
            print("🤔 Thinking...")
            
            # Get chat response
            chat_result = rag.chat(query, top_k=3, use_llm=True)
            
            # Display response
            print(f"\n🤖 Assistant: {chat_result['llm_response']}")
            
            # Optionally show sources
            show_sources = input("\n📚 Show source documents? (y/n): ").strip().lower()
            if show_sources in ['y', 'yes']:
                print("\n📊 Sources:")
                print("-" * 30)
                
                for i, result in enumerate(chat_result['search_results'][:3], 1):
                    metadata = result['metadata']
                    print(f"\n{i}. Similarity: {result['score']:.4f}")
                    
                    if 'ticket_description' in metadata:
                        print(f"   Issue: {metadata['ticket_description'][:100]}...")
                        print(f"   Answer: {metadata['answer'][:100]}...")
                    elif 'original_query' in metadata:
                        print(f"   Query: {metadata['original_query'][:100]}...")
                        print(f"   Response: {metadata['original_response'][:100]}...")
            
            print("\n" + "="*50)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have:")
        print("1. Installed all dependencies: pip install -r requirements.txt")
        print("2. Set up your .env file with CEREBRAS_API_KEY")

if __name__ == "__main__":
    run_chatbot()