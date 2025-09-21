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
            show_sources = input("\n📚 Show detailed case history? (y/n): ").strip().lower()
            if show_sources in ['y', 'yes']:
                print("\n" + "="*80)
                print("📊 DETAILED HISTORICAL CASES")
                print("="*80)
                
                for i, result in enumerate(chat_result['search_results'][:3], 1):
                    metadata = result['metadata']
                    print(f"\n🔍 CASE {i} - Similarity: {result['score']:.4f}")
                    print("-" * 60)
                    
                    if 'ticket_description' in metadata and 'answer' in metadata:
                        original_data = metadata.get('original_data', {})
                        
                        # Customer Information
                        print("👤 CUSTOMER DETAILS:")
                        if 'Customer Name' in original_data:
                            print(f"   Name: {original_data['Customer Name']}")
                        if 'Customer Email' in original_data:
                            print(f"   Email: {original_data['Customer Email']}")
                        if 'Customer Age' in original_data:
                            print(f"   Age: {original_data['Customer Age']}")
                        if 'Customer Gender' in original_data:
                            print(f"   Gender: {original_data['Customer Gender']}")
                        if 'Product Purchased' in original_data:
                            print(f"   Product: {original_data['Product Purchased']}")
                        if 'Date of Purchase' in original_data:
                            print(f"   Purchase Date: {original_data['Date of Purchase']}")
                        
                        # Ticket Information
                        print("\n🎫 TICKET DETAILS:")
                        if 'Ticket ID' in original_data:
                            print(f"   Ticket ID: {original_data['Ticket ID']}")
                        if 'Ticket Type' in original_data:
                            print(f"   Type: {original_data['Ticket Type']}")
                        if 'Ticket Priority' in original_data:
                            print(f"   Priority: {original_data['Ticket Priority']}")
                        if 'Ticket Channel' in original_data:
                            print(f"   Channel: {original_data['Ticket Channel']}")
                        if 'Ticket Status' in original_data:
                            print(f"   Status: {original_data['Ticket Status']}")
                        
                        # Issue and Resolution
                        print(f"\n🔍 ISSUE:")
                        print(f"   {metadata['ticket_description']}")
                        print(f"\n✅ RESOLUTION:")
                        print(f"   {metadata['answer']}")
                        
                        # Performance Metrics
                        print("\n📊 METRICS:")
                        if 'First Response Time' in original_data:
                            print(f"   First Response: {original_data['First Response Time']}")
                        if 'Time to Resolution' in original_data:
                            print(f"   Resolution Time: {original_data['Time to Resolution']}")
                        if 'Customer Satisfaction Rating' in original_data:
                            rating = original_data['Customer Satisfaction Rating']
                            stars = "⭐" * int(float(rating)) if str(rating).replace('.','').isdigit() else rating
                            print(f"   Satisfaction: {stars} ({rating}/5)")
                        
                    elif 'original_query' in metadata:
                        print(f"   Query: {metadata['original_query'][:200]}...")
                        print(f"   Response: {metadata['original_response'][:200]}...")
                    
                    print("\n" + "-" * 60)
            
            print("\n" + "="*50)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have:")
        print("1. Installed all dependencies: pip install -r requirements.txt")
        print("2. Set up your .env file with CEREBRAS_API_KEY")

if __name__ == "__main__":
    run_chatbot()