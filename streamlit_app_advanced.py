"""
Streamlit Web Interface for Secure RAG Chatbot
Provides chat interface, security monitoring, and metrics dashboard
"""

import streamlit as st
import sys
import time
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import requests
from typing import List, Dict, Any

# Page configuration - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Secure RAG Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add RAG pipeline to path
sys.path.append(str(Path(__file__).parent / "RAG-Pipeline-Ollama"))
sys.path.append(str(Path(__file__).parent / "Health-Security-Metrics"))

# Prevent Prometheus metric re-registration issues
import os
os.environ['PROMETHEUS_DISABLE_CREATED_SERIES'] = 'True'

# Try to import RAG components with error handling
RAG_AVAILABLE = False
MONITOR_AVAILABLE = False
import_errors = []

try:
    # Import with correct class names based on diagnostic output
    from rag_pipeline_secure import RAGPipeline, RAGConfig
    # Use RAGPipeline as SecureRAGPipeline for consistency in the code
    SecureRAGPipeline = RAGPipeline
    RAG_AVAILABLE = True
except ImportError as e:
    import_errors.append(f"RAG Pipeline import error: {e}")
    SecureRAGPipeline = None
    RAGConfig = None
except ValueError as ve:
    # Handle Prometheus duplicate registration error
    if "Duplicated timeseries" in str(ve):
        import_errors.append("Warning: Prometheus metrics already registered (this is normal for Streamlit)")
        # Try to import anyway since metrics are already registered
        try:
            from rag_pipeline_secure import RAGPipeline, RAGConfig
            SecureRAGPipeline = RAGPipeline
            RAG_AVAILABLE = True
        except Exception as e3:
            import_errors.append(f"Retry import failed: {e3}")
            SecureRAGPipeline = None
            RAGConfig = None
    else:
        import_errors.append(f"Import failed with ValueError: {ve}")
        SecureRAGPipeline = None
        RAGConfig = None
except Exception as e2:
    import_errors.append(f"Unexpected import error: {e2}")
    SecureRAGPipeline = None
    RAGConfig = None

try:
    from instrumentation import RAGMonitor
    MONITOR_AVAILABLE = True
except (ImportError, ValueError) as e:
    if "Duplicated timeseries" in str(e):
        import_errors.append("Warning: RAGMonitor metrics already registered")
        # Metrics are registered, but we can still use the monitor
        try:
            import instrumentation
            if hasattr(instrumentation, 'RAGMonitor'):
                RAGMonitor = instrumentation.RAGMonitor
                MONITOR_AVAILABLE = True
        except:
            RAGMonitor = None
            MONITOR_AVAILABLE = False
    else:
        import_errors.append(f"Monitor import warning: {e}")
        RAGMonitor = None
        MONITOR_AVAILABLE = False

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2563eb;
        text-align: center;
        margin-bottom: 1rem;
    }
    .security-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 0.5rem;
        font-size: 0.875rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    .badge-safe {
        background-color: #d1fae5;
        color: #065f46;
    }
    .badge-warning {
        background-color: #fef3c7;
        color: #92400e;
    }
    .badge-danger {
        background-color: #fee2e2;
        color: #991b1b;
    }
    .metric-card {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e2e8f0;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        color: #1e293b;
    }
    .user-message {
        background-color: #dbeafe;
        margin-left: 2rem;
        color: #1e40af;
    }
    .assistant-message {
        background-color: #f1f5f9;
        margin-right: 2rem;
        color: #334155;
    }
    .chat-message strong {
        color: inherit;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.rag_pipeline = None
    st.session_state.monitor = None
    st.session_state.messages = []
    st.session_state.conversation_history = []
    st.session_state.total_queries = 0
    st.session_state.blocked_attacks = 0
    st.session_state.pii_redacted = 0

# Initialize RAG Pipeline
@st.cache_resource
def initialize_rag_pipeline():
    """Initialize the RAG pipeline and monitoring"""
    if not RAG_AVAILABLE or SecureRAGPipeline is None:
        return None, None
    
    try:
        # Initialize monitor
        monitor = None
        if MONITOR_AVAILABLE and RAGMonitor is not None:
            try:
                monitor = RAGMonitor(port=8001, host='0.0.0.0')
            except Exception as e:
                import_errors.append(f"Monitor initialization warning: {e}")
                pass  # Monitor is optional
        
        # Initialize RAG pipeline
        try:
            config = RAGConfig(
                model_name="llama3.2",
                embedding_model="all-MiniLM-L6-v2",
                max_tokens=1024,
                temperature=0.7,
                top_k_results=5
            )
        except Exception as e:
            import_errors.append(f"Config creation failed: {e}")
            return None, None
        
        try:
            pipeline = SecureRAGPipeline(config)
        except Exception as e:
            import_errors.append(f"Pipeline creation failed: {e}")
            import traceback
            import_errors.append(f"Traceback: {traceback.format_exc()}")
            return None, None
        
        # Load dataset using the correct method
        dataset_path = Path(__file__).parent / "RAG-Pipeline-Ollama" / "customer_support_tickets_updated.csv"
        if dataset_path.exists():
            try:
                # Use process_customer_support_data method
                pipeline.process_customer_support_data(str(dataset_path))
                import_errors.append(f"✅ Dataset loaded successfully from {dataset_path.name}")
                
                # Verify vector store was populated
                if hasattr(pipeline, 'vector_store') and hasattr(pipeline.vector_store, 'index'):
                    doc_count = pipeline.vector_store.index.ntotal if hasattr(pipeline.vector_store.index, 'ntotal') else 0
                    import_errors.append(f"📊 Vector store contains {doc_count} documents")
                
            except Exception as e:
                import_errors.append(f"Dataset loading warning: {e}")
                # Try alternative: load_csv_data
                try:
                    pipeline.load_csv_data(str(dataset_path))
                    import_errors.append(f"✅ Dataset loaded via load_csv_data")
                    
                    # Verify vector store
                    if hasattr(pipeline, 'vector_store') and hasattr(pipeline.vector_store, 'index'):
                        doc_count = pipeline.vector_store.index.ntotal if hasattr(pipeline.vector_store.index, 'ntotal') else 0
                        import_errors.append(f"📊 Vector store contains {doc_count} documents")
                    
                except Exception as e2:
                    import_errors.append(f"Alternative loading also failed: {e2}")
                    import_errors.append("⚠️ RAG may only work with conversation context, not knowledge base")
        else:
            import_errors.append(f"Dataset not found at: {dataset_path}")
        
        return pipeline, monitor
    
    except Exception as e:
        import_errors.append(f"Initialization failed: {e}")
        import traceback
        import_errors.append(f"Full traceback: {traceback.format_exc()}")
        return None, None

# Sidebar
with st.sidebar:
    st.markdown("### 🤖 Secure RAG Chatbot")
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "Navigation",
        ["💬 Chat", "📊 Dashboard", "🔒 Security", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Quick Stats
    st.markdown("### 📈 Quick Stats")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Queries", st.session_state.total_queries)
    with col2:
        st.metric("Blocked", st.session_state.blocked_attacks)
    
    st.metric("PII Redacted", st.session_state.pii_redacted)
    
    st.markdown("---")
    
    # Actions
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    if st.button("💾 Export History", use_container_width=True):
        export_data = {
            "messages": st.session_state.messages,
            "timestamp": datetime.now().isoformat()
        }
        st.download_button(
            "Download JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    st.markdown("---")
    
    # System Info
    st.markdown("### ℹ️ System Info")
    st.caption(f"Model: Llama 3.2")
    st.caption(f"Security: {'Enabled ✅' if RAG_AVAILABLE else 'Unavailable ❌'}")
    st.caption(f"PII Protection: {'Active 🔒' if RAG_AVAILABLE else 'Unavailable ❌'}")

# Main content based on selected page
if page == "💬 Chat":
    # Chat Page
    st.markdown('<div class="main-header">💬 Secure RAG Chatbot</div>', unsafe_allow_html=True)
    
    # Show import errors if any
    if import_errors and not RAG_AVAILABLE:
        with st.expander("⚠️ Import Issues Detected", expanded=True):
            st.error("❌ RAG Pipeline is not available. Please check the installation.")
            for error in import_errors:
                st.code(error)
            st.info("**Troubleshooting Steps:**")
            st.markdown("1. Verify `rag_pipeline_secure.py` exists in RAG-Pipeline-Ollama directory")
            st.markdown("2. Run `python check_imports.py` to see available classes")
            st.markdown("3. Check that the file exports `RAGPipeline` and `RAGConfig` classes")
        st.stop()
    
    # Initialize pipeline if not done
    if not st.session_state.initialized:
        with st.spinner("🚀 Initializing RAG Pipeline..."):
            pipeline, monitor = initialize_rag_pipeline()
            if pipeline:
                st.session_state.rag_pipeline = pipeline
                st.session_state.monitor = monitor
                st.session_state.initialized = True
                st.success("✅ RAG Pipeline initialized successfully!")
                if not MONITOR_AVAILABLE:
                    st.warning("⚠️ Monitoring features are limited (RAGMonitor not available)")
                # Show any warnings that occurred during initialization
                if import_errors:
                    with st.expander("⚠️ Initialization Warnings"):
                        for error in import_errors:
                            st.warning(error)
            else:
                st.error("❌ Failed to initialize RAG Pipeline")
                with st.expander("Show Error Details", expanded=True):
                    st.error("**Detailed Error Information:**")
                    for error in import_errors:
                        st.code(error)
                    st.info("**Common Issues:**")
                    st.markdown("- Ollama service not running")
                    st.markdown("- Model 'llama3.2' not available")
                    st.markdown("- Dependencies missing (FAISS, sentence-transformers)")
                    st.markdown("- Port 8001 already in use")
                st.stop()
    
    # Chat container
    chat_container = st.container()
    
    # Display chat messages
    with chat_container:
        for message in st.session_state.messages:
            role = message["role"]
            content = message["content"]
            
            if role == "user":
                st.markdown(f'<div class="chat-message user-message"><strong>You:</strong><br>{content}</div>', 
                           unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message assistant-message"><strong>Assistant:</strong><br>{content}</div>', 
                           unsafe_allow_html=True)
                
                # Show security badges
                if "pii_redacted" in message and message["pii_redacted"]:
                    st.markdown("**🔒 PII Protected:**")
                    badges_html = " ".join([
                        f'<span class="security-badge badge-warning">{pii_type}</span>' 
                        for pii_type in message["pii_redacted"]
                    ])
                    st.markdown(badges_html, unsafe_allow_html=True)
                
                # Show similarity scores
                if "similarity_scores" in message and message["similarity_scores"]:
                    avg_score = sum(message["similarity_scores"]) / len(message["similarity_scores"])
                    st.caption(f"📊 Relevance Score: {avg_score:.2%}")
    
    # Chat input
    st.markdown("---")
    
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_area(
            "Your message:",
            placeholder="Type your question here...",
            height=100,
            key="user_input"
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        send_button = st.button("📤 Send", use_container_width=True, type="primary")
    
    if send_button and user_input.strip():
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # Get response from RAG pipeline
        with st.spinner("🤔 Thinking..."):
            try:
                start_time = time.time()
                result = st.session_state.rag_pipeline.query(user_input)
                processing_time = time.time() - start_time
                
                # Update metrics
                st.session_state.total_queries += 1
                
                # Handle different response formats
                if isinstance(result, dict):
                    # Extract response text - try different possible keys
                    response_text = (
                        result.get("answer") or
                        result.get("response") or 
                        result.get("output") or 
                        result.get("text") or
                        str(result)
                    )
                    
                    # Check for security issues
                    if result.get('security_status') == 'blocked':
                        st.session_state.blocked_attacks += 1
                        st.error(f"🚨 Security Alert: {result.get('security_reason', 'Unknown threat')}")
                    
                    # Check for PII redaction - handle both boolean and list
                    pii_redacted_data = result.get("pii_redacted", False)
                    if pii_redacted_data:
                        # If it's a boolean True, count as 1 redaction
                        if isinstance(pii_redacted_data, bool):
                            st.session_state.pii_redacted += 1
                            pii_redacted_list = []
                        # If it's a list, count the items
                        elif isinstance(pii_redacted_data, list):
                            st.session_state.pii_redacted += len(pii_redacted_data)
                            pii_redacted_list = pii_redacted_data
                        else:
                            pii_redacted_list = []
                    else:
                        pii_redacted_list = []
                    
                    # Get similarity scores
                    similarity_scores = (
                        result.get("similarity_scores") or 
                        result.get("scores") or 
                        result.get("relevance_scores") or 
                        []
                    )
                    
                elif isinstance(result, str):
                    # Direct string response
                    response_text = result
                    pii_redacted_list = []
                    similarity_scores = []
                else:
                    # Fallback
                    response_text = str(result)
                    pii_redacted_list = []
                    similarity_scores = []
                
                # Check if response indicates no information found
                if "No relevant information found" in response_text or "No sufficiently relevant information" in response_text:
                    # Try using the chat method instead
                    try:
                        chat_result = st.session_state.rag_pipeline.chat(user_input)
                        if isinstance(chat_result, dict):
                            response_text = chat_result.get("answer") or chat_result.get("response") or str(chat_result)
                        else:
                            response_text = str(chat_result)
                    except Exception as chat_error:
                        # If chat also fails, provide helpful message
                        response_text = (
                            "I apologize, but I'm having trouble finding relevant information. "
                            "This could mean:\n"
                            "1. The knowledge base doesn't contain information about this topic\n"
                            "2. Your question might need to be more specific\n"
                            "3. Try asking about common technical issues or products\n\n"
                            f"Vector store status: {len(st.session_state.rag_pipeline.vector_store.documents)} documents loaded"
                        )
                
                # Add assistant message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "timestamp": datetime.now().isoformat(),
                    "pii_redacted": pii_redacted_list,
                    "similarity_scores": similarity_scores,
                    "processing_time": processing_time
                })
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                # Add debug info
                import traceback
                with st.expander("Debug Information"):
                    st.code(traceback.format_exc())
                    st.write("**Result type:**", type(result).__name__ if 'result' in locals() else "Not available")
                    if 'result' in locals():
                        if isinstance(result, dict):
                            st.write("**Available keys:**", list(result.keys()))
                        st.write("**Result content:**", result)
                    
                    # Add vector store diagnostic
                    if hasattr(st.session_state.rag_pipeline, 'vector_store'):
                        try:
                            vs = st.session_state.rag_pipeline.vector_store
                            if vs and hasattr(vs, 'index'):
                                doc_count = vs.index.ntotal if hasattr(vs.index, 'ntotal') else len(vs.documents)
                                st.write("**Vector store size:**", doc_count)
                        except:
                            st.write("**Vector store:** Unable to check")

elif page == "📊 Dashboard":
    # Dashboard Page
    st.markdown('<div class="main-header">📊 Monitoring Dashboard</div>', unsafe_allow_html=True)
    
    # Metrics Overview
    st.markdown("### 📈 System Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Queries", st.session_state.total_queries, delta="+1" if st.session_state.total_queries > 0 else None)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Blocked Attacks", st.session_state.blocked_attacks, 
                 delta=None, delta_color="inverse")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        success_rate = ((st.session_state.total_queries - st.session_state.blocked_attacks) / 
                       st.session_state.total_queries * 100) if st.session_state.total_queries > 0 else 100
        st.metric("Success Rate", f"{success_rate:.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("PII Protected", st.session_state.pii_redacted)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Grafana Dashboard Embed
    st.markdown("### 📊 Grafana Dashboards")
    
    tabs = st.tabs(["Executive Overview", "Security Operations", "Performance", "Quality"])
    
    with tabs[0]:
        st.markdown("#### 📊 Executive Overview")
        st.info("Access Grafana at: http://localhost:3001")
        st.markdown("**Key Metrics:**")
        st.markdown("- Total queries (24h)")
        st.markdown("- Attack attempts")
        st.markdown("- P95 Latency")
        st.markdown("- Success rate distribution")
    
    with tabs[1]:
        st.markdown("#### 🔒 Security Operations")
        st.info("Monitor security events and PII redactions")
        st.markdown("**Tracked Events:**")
        st.markdown("- Real-time attack rate")
        st.markdown("- Attack type distribution")
        st.markdown("- PII redaction activity")
        st.markdown("- Blocked vs allowed queries")
    
    with tabs[2]:
        st.markdown("#### ⚡ Performance Metrics")
        st.info("System performance and latency tracking")
        st.markdown("**Performance Indicators:**")
        st.markdown("- P50, P95, P99 latency")
        st.markdown("- Requests per second")
        st.markdown("- Latency heatmap")
        st.markdown("- Vector store size")
    
    with tabs[3]:
        st.markdown("#### ✨ Quality Metrics")
        st.info("RAG quality and accuracy monitoring")
        st.markdown("**Quality Measures:**")
        st.markdown("- Average similarity score")
        st.markdown("- Refusal rate")
        st.markdown("- Query status breakdown")
        st.markdown("- Similarity distribution")
    
    st.markdown("---")
    
    # Recent Activity
    st.markdown("### 📋 Recent Activity")
    
    if st.session_state.messages:
        recent_messages = st.session_state.messages[-5:]  # Last 5 messages
        
        activity_data = []
        for msg in recent_messages:
            if msg["role"] == "user":
                activity_data.append({
                    "Time": msg.get("timestamp", "N/A"),
                    "Type": "Query",
                    "Preview": msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"],
                    "Status": "✅ Processed"
                })
        
        if activity_data:
            df = pd.DataFrame(activity_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No activity yet. Start chatting to see metrics!")

elif page == "🔒 Security":
    # Security Page
    st.markdown('<div class="main-header">🔒 Security Center</div>', unsafe_allow_html=True)
    
    # Security Overview
    st.markdown("### 🛡️ Security Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ✅ Active Protection")
        st.success("✓ Prompt Injection Detection")
        st.success("✓ PII Redaction (6 types)")
        st.success("✓ Data Exfiltration Prevention")
        st.success("✓ Jailbreak Detection")
        st.success("✓ Role Manipulation Prevention")
    
    with col2:
        st.markdown("#### 📊 Security Metrics")
        st.metric("Total Attacks Blocked", st.session_state.blocked_attacks)
        st.metric("PII Items Redacted", st.session_state.pii_redacted)
        
        if st.session_state.total_queries > 0:
            attack_rate = (st.session_state.blocked_attacks / st.session_state.total_queries * 100)
            st.metric("Attack Rate", f"{attack_rate:.2f}%")
    
    st.markdown("---")
    
    # PII Protection Details
    st.markdown("### 🔒 PII Protection")
    
    st.markdown("""
    The following types of Personally Identifiable Information are automatically detected and redacted:
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📧 Email Addresses**")
        st.caption("example@domain.com")
        
        st.markdown("**📞 Phone Numbers**")
        st.caption("(555) 123-4567")
    
    with col2:
        st.markdown("**💳 Credit Cards**")
        st.caption("4532-1234-5678-9010")
        
        st.markdown("**🆔 SSN**")
        st.caption("123-45-6789")
    
    with col3:
        st.markdown("**🎫 Ticket IDs**")
        st.caption("TKT-12345")
        
        st.markdown("**👤 Customer Names**")
        st.caption("John Smith")
    
    st.markdown("---")
    
    # Attack Types
    st.markdown("### 🚨 Detected Attack Types")
    
    attack_types = {
        "Prompt Injection": "Attempts to manipulate system prompts or instructions",
        "Jailbreak": "Attempts to bypass security restrictions",
        "Data Exfiltration": "Attempts to extract sensitive information",
        "Role Manipulation": "Attempts to impersonate admin or privileged users"
    }
    
    for attack_name, description in attack_types.items():
        with st.expander(f"🔴 {attack_name}"):
            st.write(description)
            st.caption("Status: ✅ Protection Active")

elif page == "⚙️ Settings":
    # Settings Page
    st.markdown('<div class="main-header">⚙️ Settings</div>', unsafe_allow_html=True)
    
    # Model Configuration
    st.markdown("### 🤖 Model Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        model_name = st.selectbox(
            "Model",
            ["llama3.2", "llama3.1", "llama2"],
            disabled=True,
            help="Model selection (restart required)"
        )
        
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Controls randomness in responses"
        )
    
    with col2:
        max_tokens = st.number_input(
            "Max Tokens",
            min_value=256,
            max_value=4096,
            value=1024,
            step=256,
            help="Maximum response length"
        )
        
        top_k = st.slider(
            "Top K Results",
            min_value=1,
            max_value=10,
            value=5,
            help="Number of documents to retrieve"
        )
    
    st.markdown("---")
    
    # Security Settings
    st.markdown("### 🔒 Security Settings")
    
    pii_protection = st.checkbox("Enable PII Protection", value=True, disabled=True)
    attack_detection = st.checkbox("Enable Attack Detection", value=True, disabled=True)
    
    st.info("🔒 Security features are always enabled for data protection")
    
    st.markdown("---")
    
    # Monitoring
    st.markdown("### 📊 Monitoring")
    
    prometheus_enabled = st.checkbox("Prometheus Metrics", value=True, disabled=True)
    if prometheus_enabled:
        st.caption("Metrics available at: http://localhost:8001/metrics")
    
    grafana_url = st.text_input("Grafana URL", value="http://localhost:3001", disabled=True)
    
    st.markdown("---")
    
    # System Info
    st.markdown("### ℹ️ System Information")
    
    system_info = {
        "Model": "Llama 3.2",
        "Embedding Model": "all-MiniLM-L6-v2",
        "Vector Store": "FAISS",
        "Security": "Enabled",
        "Monitoring": "Prometheus + Grafana"
    }
    
    for key, value in system_info.items():
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"**{key}:**")
        with col2:
            st.markdown(value)

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #64748b; padding: 1rem;">'
    '🤖 Secure RAG Chatbot | Built with Streamlit | '
    '<a href="http://localhost:8001/metrics" target="_blank">Metrics</a> | '
    '<a href="http://localhost:3001" target="_blank">Grafana</a>'
    '</div>',
    unsafe_allow_html=True
)