import streamlit as st
import pandas as pd
import os
import sys
from typing import List, Dict
import time

# Add the current directory to Python path to import our RAG pipeline
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_pipeline import RAGPipeline

@st.cache_resource
def load_rag_pipeline():
    """
    Load RAG pipeline with caching to avoid reloading on every interaction
    """
    rag = RAGPipeline(model_name='all-MiniLM-L6-v2', use_cerebras=True)
    
    save_dir = 'saved_pipeline'
    csv_path = 'customer_support_sample_1500_balanced.csv'
    
    # Check if saved pipeline exists
    if os.path.exists(save_dir) and all(os.path.exists(os.path.join(save_dir, f)) for f in 
                                       ['embeddings.npy', 'faiss_index.bin', 'documents.pkl', 'metadata.pkl']):
        with st.spinner("Loading existing pipeline..."):
            rag.load_pipeline(save_dir)
        st.success("Pipeline loaded successfully!")
    else:
        if not os.path.exists(csv_path):
            st.error(f"CSV file not found: {csv_path}")
            return None
            
        with st.spinner("Building new pipeline... This may take a few minutes."):
            rag.load_and_process_data(csv_path)
            rag.generate_embeddings()
            rag.build_vector_store()
            rag.save_pipeline(save_dir)
        st.success("Pipeline built and saved successfully!")
    
    return rag

def display_chat_message(message, is_user=True):
    """
    Display a chat message with appropriate styling
    """
    if is_user:
        st.markdown(f"""
        <div style='text-align: right; margin-bottom: 1rem;'>
            <div style='display: inline-block; background-color: #007bff; color: white; padding: 0.5rem 1rem; border-radius: 15px; max-width: 70%;'>
                <strong>You:</strong> {message}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='text-align: left; margin-bottom: 1rem;'>
            <div style='display: inline-block; background-color: #f8f9fa; color: black; padding: 0.5rem 1rem; border-radius: 15px; max-width: 70%; border: 1px solid #dee2e6;'>
                <strong>🤖 Assistant:</strong><br>{message}
            </div>
        </div>
        """, unsafe_allow_html=True)

def format_search_results(results: List[Dict], in_expander=False) -> None:
    """
    Display search results in a formatted way with enhanced customer context
    """
    if not in_expander:
        st.subheader("📊 Retrieved Historical Cases")
    
    for i, result in enumerate(results):
        # Use different display format when already inside an expander
        if in_expander:
            st.markdown(f"**📄 Case {result['rank']} - Similarity: {result['score']:.4f}**")
            metadata = result['metadata']
            
            if 'ticket_description' in metadata and 'answer' in metadata:
                original_data = metadata.get('original_data', {})
                
                # Customer Info
                if 'Customer Name' in original_data or 'Customer Email' in original_data:
                    customer_info = []
                    if 'Customer Name' in original_data:
                        customer_info.append(f"**Customer:** {original_data['Customer Name']}")
                    if 'Customer Email' in original_data:
                        customer_info.append(f"**Email:** {original_data['Customer Email']}")
                    if 'Customer Age' in original_data:
                        customer_info.append(f"**Age:** {original_data['Customer Age']}")
                    if 'Product Purchased' in original_data:
                        customer_info.append(f"**Product:** {original_data['Product Purchased']}")
                    
                    st.markdown(" | ".join(customer_info))
                
                # Ticket Details
                if 'Date of Purchase' in original_data:
                    st.markdown(f"**Purchase Date:** {original_data['Date of Purchase']}")
                if 'Ticket Type' in original_data and 'Ticket Priority' in original_data:
                    st.markdown(f"**Type:** {original_data['Ticket Type']} | **Priority:** {original_data['Ticket Priority']}")
                
                # Issue and Solution
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.write("**🎫 Issue:**")
                    st.write(metadata['ticket_description'][:150] + "..." if len(metadata['ticket_description']) > 150 else metadata['ticket_description'])
                
                with col2:
                    st.write("**✅ Resolution:**")
                    st.write(metadata['answer'][:150] + "..." if len(metadata['answer']) > 150 else metadata['answer'])
                
                # Performance Metrics
                if 'Customer Satisfaction Rating' in original_data:
                    rating = original_data['Customer Satisfaction Rating']
                    stars = "⭐" * int(rating) if pd.notna(rating) and str(rating).replace('.', '').isdigit() else "N/A"
                    resolution_time = original_data.get('Time to Resolution', 'N/A')
                    st.markdown(f"**Satisfaction:** {stars} ({rating}) | **Resolution Time:** {resolution_time}")
                
                st.markdown("---")
            
            elif 'original_query' in metadata and 'original_response' in metadata:
                st.write("**Query:**", metadata['original_query'][:100] + "...")
                st.write("**Response:**", metadata['original_response'][:100] + "...")
                st.markdown("---")
            
            else:
                st.write("**Document:**")
                st.write(result['document'][:200] + "..." if len(result['document']) > 200 else result['document'])
                st.markdown("---")
        
        else:
            # Use expanders only when not already inside one
            with st.expander(f"📄 Case {result['rank']} - Similarity: {result['score']:.4f}", expanded=i<2):
                metadata = result['metadata']
                
                if 'ticket_description' in metadata and 'answer' in metadata:
                    original_data = metadata.get('original_data', {})
                    
                    # Customer Information Section
                    st.subheader("👤 Customer Information")
                    col1, col2, col3 = st.columns([1, 1, 1])
                    
                    with col1:
                        if 'Customer Name' in original_data:
                            st.write(f"**Name:** {original_data['Customer Name']}")
                        if 'Customer Age' in original_data:
                            st.write(f"**Age:** {original_data['Customer Age']}")
                        if 'Customer Gender' in original_data:
                            st.write(f"**Gender:** {original_data['Customer Gender']}")
                    
                    with col2:
                        if 'Customer Email' in original_data:
                            st.write(f"**Email:** {original_data['Customer Email']}")
                        if 'Product Purchased' in original_data:
                            st.write(f"**Product:** {original_data['Product Purchased']}")
                        if 'Date of Purchase' in original_data:
                            st.write(f"**Purchase Date:** {original_data['Date of Purchase']}")
                    
                    with col3:
                        if 'Ticket ID' in original_data:
                            st.write(f"**Ticket ID:** {original_data['Ticket ID']}")
                        if 'Ticket Channel' in original_data:
                            st.write(f"**Channel:** {original_data['Ticket Channel']}")
                        if 'Ticket Status' in original_data:
                            st.write(f"**Status:** {original_data['Ticket Status']}")
                    
                    # Ticket Details Section
                    st.subheader("🎫 Ticket Details")
                    col_ticket1, col_ticket2 = st.columns([1, 1])
                    
                    with col_ticket1:
                        if 'Ticket Type' in original_data:
                            st.write(f"**Type:** {original_data['Ticket Type']}")
                        if 'Ticket Priority' in original_data:
                            priority = original_data['Ticket Priority']
                            priority_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "")
                            st.write(f"**Priority:** {priority_color} {priority}")
                    
                    with col_ticket2:
                        if 'First Response Time' in original_data:
                            st.write(f"**First Response:** {original_data['First Response Time']}")
                        if 'Time to Resolution' in original_data:
                            st.write(f"**Resolution Time:** {original_data['Time to Resolution']}")
                    
                    # Issue and Resolution Section
                    st.subheader("🔍 Issue & Resolution")
                    
                    st.write("**🎫 Customer Issue:**")
                    st.write(metadata['ticket_description'])
                    
                    st.write("**✅ Support Resolution:**")
                    st.write(metadata['answer'])
                    
                    # Performance Metrics
                    if 'Customer Satisfaction Rating' in original_data:
                        st.subheader("📊 Performance Metrics")
                        rating = original_data['Customer Satisfaction Rating']
                        if pd.notna(rating) and str(rating).replace('.', '').isdigit():
                            rating_float = float(rating)
                            stars = "⭐" * int(rating_float)
                            color = "green" if rating_float >= 4 else "orange" if rating_float >= 3 else "red"
                            st.markdown(f"**Customer Satisfaction:** :{color}[{stars} ({rating}/5)]")
                        else:
                            st.write(f"**Customer Satisfaction:** {rating}")
                
                elif 'original_query' in metadata and 'original_response' in metadata:
                    st.write("**Original Customer Query:**")
                    st.write(metadata['original_query'])
                    st.write("**Support Response:**")
                    st.write(metadata['original_response'])
                
                else:
                    st.write("**Document:**")
                    st.write(result['document'][:500] + "..." if len(result['document']) > 500 else result['document'])

def main():
    st.set_page_config(
        page_title="🤖 RAG Customer Support Chatbot",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 RAG Customer Support Chatbot")
    st.markdown("### Powered by Cerebras Llama-4 & Vector Search")
    st.markdown("---")
    
    # Load RAG pipeline
    rag = load_rag_pipeline()
    
    if rag is None:
        st.error("Failed to load RAG pipeline. Please check your setup.")
        return
    
    # Check if Cerebras is available
    cerebras_status = "✅ Connected" if rag.use_cerebras else "❌ Not Available"
    st.markdown(f"**Cerebras LLM Status:** {cerebras_status}")
    
    if not rag.use_cerebras:
        st.warning("⚠️ Cerebras LLM is not available. Please check your CEREBRAS_API_KEY in the .env file.")
    
    # Sidebar with controls and info
    with st.sidebar:
        st.header("🛠️ Settings")
        
        top_k = st.slider("Number of results to retrieve", min_value=1, max_value=10, value=3)
        use_llm = st.checkbox("Use Cerebras LLM Response", value=True, disabled=not rag.use_cerebras)
        show_sources = st.checkbox("Show source documents", value=True)
        
        st.header("ℹ️ How it works")
        st.write("""
        1. **🔍 Search**: Your question is converted to vectors and matched against our knowledge base
        2. **📚 Retrieve**: Similar customer support cases are found
        3. **🤖 Generate**: Cerebras Llama-4 creates a personalized response using the context
        4. **✨ Respond**: You get a helpful answer with sources
        """)
        
        st.header("💡 Example Questions")
        example_queries = [
            "How to reset my password?",
            "I want to return my product",
            "My order hasn't arrived yet",
            "How do I update my account?",
            "I'm having trouble logging in",
            "How to cancel my subscription?",
            "Product is damaged, what to do?",
            "How to change my shipping address?"
        ]
        
        for example in example_queries:
            if st.button(example, key=f"example_{example}", use_container_width=True):
                st.session_state.user_input = example
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hello! I'm your customer support assistant. How can I help you today?",
            "sources": None
        })
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                display_chat_message(message["content"], is_user=True)
            else:
                display_chat_message(message["content"], is_user=False)
                
                # Show sources if available
                if show_sources and message.get("sources"):
                    with st.expander("📚 Sources", expanded=False):
                        format_search_results(message["sources"], in_expander=True)
    
    # Chat input
    st.markdown("---")
    col_input, col_send = st.columns([4, 1])
    
    with col_input:
        if "user_input" not in st.session_state:
            st.session_state.user_input = ""
        
        user_input = st.text_input(
            "Ask your question:",
            value=st.session_state.user_input,
            placeholder="e.g., How do I reset my password?",
            key="chat_input"
        )
    
    with col_send:
        send_button = st.button("🚀 Send", type="primary", use_container_width=True)
    
    # Handle user input
    if (send_button or st.session_state.user_input) and user_input.strip():
        # Clear the input for next use
        if "user_input" in st.session_state:
            st.session_state.user_input = ""
        
        # Add user message to chat history
        st.session_state.messages.append({
            "role": "user", 
            "content": user_input,
            "sources": None
        })
        
        # Get response from RAG pipeline
        with st.spinner("🤔 Thinking..."):
            start_time = time.time()
            chat_response = rag.chat(user_input, top_k=top_k, use_llm=use_llm)
            response_time = time.time() - start_time
        
        # Prepare assistant response
        if use_llm and chat_response['llm_response']:
            assistant_response = chat_response['llm_response']
        else:
            # Fallback to showing search results if no LLM response
            if chat_response['search_results']:
                best_result = chat_response['search_results'][0]
                metadata = best_result['metadata']
                
                if 'answer' in metadata:
                    assistant_response = f"Based on similar cases, here's what I found:\n\n{metadata['answer']}"
                elif 'original_response' in metadata:
                    assistant_response = f"Based on similar cases:\n\n{metadata['original_response']}"
                else:
                    assistant_response = "I found some relevant information, but couldn't generate a specific response. Please check the sources below."
            else:
                assistant_response = "I couldn't find relevant information for your question. Please contact our support team for assistance."
        
        # Add assistant response to chat history
        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_response,
            "sources": chat_response['search_results'] if show_sources else None
        })
        
        # Show response time
        st.success(f"Response generated in {response_time:.2f} seconds")
        
        # Rerun to display new messages
        st.experimental_rerun()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat", key="clear_chat"):
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Hello! I'm your customer support assistant. How can I help you today?",
            "sources"j: None
        }]
        st.experimental_rerun()
    
    # Footer with stats
    if st.session_state.messages:
        st.markdown("---")
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        with col_stat1:
            user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
            st.metric("💬 Questions Asked", user_messages)
        
        with col_stat2:
            assistant_messages = len([m for m in st.session_state.messages if m["role"] == "assistant"]) - 1  # Exclude welcome message
            st.metric("🤖 Responses Given", assistant_messages)
        
        with col_stat3:
            st.metric("🔍 LLM Status", "Active" if rag.use_cerebras else "Inactive")

if __name__ == "__main__":
    main()