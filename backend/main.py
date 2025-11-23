"""
FastAPI Backend for RAG Chatbot
Provides REST API and WebSocket endpoints for the RAG pipeline
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager
import httpx
import numpy as np

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, Response
from pydantic import BaseModel, Field, ConfigDict
import uvicorn

# Add RAG pipeline to path
sys.path.append(str(Path(__file__).parent.parent / "RAG-Pipeline-Ollama"))
sys.path.append(str(Path(__file__).parent.parent / "Health-Security-Metrics"))

from rag_pipeline_secure import RAGPipeline as SecureRAGPipeline, RAGConfig
from instrumentation import RAGMonitor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global RAG pipeline instance
rag_pipeline: Optional[SecureRAGPipeline] = None
active_conversations: Dict[str, Dict[str, Any]] = {}

# ==================== Pydantic Models ====================

class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    sources: List[Dict[str, Any]]
    security_info: Dict[str, Any]
    pii_redacted: List[str]
    similarity_scores: List[float]
    processing_time: float

class ConversationHistory(BaseModel):
    conversation_id: str
    messages: List[Dict[str, Any]]
    created_at: str
    updated_at: str

class MetricsSummary(BaseModel):
    total_queries: int
    blocked_attacks: int
    avg_response_time: float
    success_rate: float
    pii_redacted_count: int

class SystemConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    model_name: str
    temperature: float
    max_tokens: int
    top_k_results: int

# ==================== Startup / Shutdown ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    global rag_pipeline
    
    try:
        logger.info("🚀 Starting RAG Chatbot API...")
        
        # Initialize RAG pipeline
        config = RAGConfig(
            model_name="meta-llama/llama-3-8b-instruct",
            embedding_model="all-MiniLM-L6-v2",
            max_tokens=1024,
            temperature=0.7,
            top_k_results=5
        )
        
        rag_pipeline = SecureRAGPipeline(config)
        
        # Load existing data
        dataset_path = Path(__file__).parent.parent / "RAG-Pipeline-Ollama" / "customer_support_tickets_updated.csv"
        if dataset_path.exists():
            logger.info(f"📂 Loading dataset from {dataset_path}")
            kb_path = Path(__file__).parent.parent / "RAG-Pipeline-Ollama" / "customer_support_kb"
            
            if kb_path.with_suffix('.pkl').exists() and kb_path.with_suffix('.faiss').exists():
                logger.info("Loading existing knowledge base...")
                rag_pipeline.vector_store.load(str(kb_path))
            else:
                logger.info("Building new knowledge base...")
                rag_pipeline.build_knowledge_base(str(dataset_path), save_path=str(kb_path))
        else:
            logger.warning("⚠️ Dataset not found, RAG pipeline initialized without data")
        
        logger.info("✅ RAG Pipeline initialized successfully")
        logger.info(f"📊 Prometheus metrics available at http://localhost:8000/metrics")
        logger.info(f"🌐 API server starting on port 8080")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG pipeline: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down RAG Chatbot API...")
    
    # Save conversations
    for conv_id, conv_data in active_conversations.items():
        try:
            save_path = Path(__file__).parent / "conversations" / f"{conv_id}.json"
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w') as f:
                json.dump(conv_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save conversation {conv_id}: {e}")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="RAG Chatbot API",
    description="Secure RAG chatbot with PII redaction and security monitoring",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite default port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Health Check ====================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "rag_pipeline": "ready" if rag_pipeline else "not initialized",
        "active_conversations": len(active_conversations),
        "metrics_available": rag_pipeline and rag_pipeline.monitor is not None,
        "prometheus_metrics_url": "http://localhost:8000/metrics",
        "api_docs_url": "http://localhost:8080/api/docs"
    }

# ==================== Chat Endpoints ====================

@app.post("/api/chat/message", response_model=ChatResponse)
async def send_message(chat_message: ChatMessage):
    """Send a message and get a response"""
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    
    start_time = time.time()
    
    try:
        # Get or create conversation ID
        conv_id = chat_message.conversation_id or f"conv_{int(time.time() * 1000)}"
        
        # Initialize conversation if new
        if conv_id not in active_conversations:
            active_conversations[conv_id] = {
                "conversation_id": conv_id,
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        
        # Query RAG pipeline
        result = rag_pipeline.query(chat_message.message)
        
        # Sanitize float values in sources to ensure JSON compliance
        sanitized_sources = []
        for source in result.get("sources", []):
            sanitized_source = {}
            for key, value in source.items():
                if isinstance(value, float):
                    # Replace NaN and Inf with 0.0
                    if np.isnan(value) or np.isinf(value):
                        sanitized_source[key] = 0.0
                    else:
                        sanitized_source[key] = value
                else:
                    sanitized_source[key] = value
            sanitized_sources.append(sanitized_source)
        result["sources"] = sanitized_sources
        
        # Update conversation history
        active_conversations[conv_id]["messages"].extend([
            {
                "role": "user",
                "content": chat_message.message,
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": result["answer"],
                "timestamp": datetime.now().isoformat(),
                "sources": result.get("sources", []),
                "security_info": {
                    "status": result.get("security_status", "unknown"),
                    "pii_redacted": result.get("pii_redacted", False)
                }
            }
        ])
        active_conversations[conv_id]["updated_at"] = datetime.now().isoformat()
        
        processing_time = time.time() - start_time
        
        return ChatResponse(
            conversation_id=conv_id,
            response=result["answer"],
            sources=result.get("sources", []),
            security_info={
                "status": result.get("security_status", "unknown"),
                "pii_redacted": result.get("pii_redacted", False)
            },
            pii_redacted=[],
            similarity_scores=[
                s.get("similarity_score", 0.0) if isinstance(s.get("similarity_score", 0.0), (int, float)) 
                and not (np.isnan(s.get("similarity_score", 0.0)) or np.isinf(s.get("similarity_score", 0.0)))
                else 0.0 
                for s in result.get("sources", [])
            ],
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/new")
async def new_conversation():
    """Start a new conversation"""
    conv_id = f"conv_{int(time.time() * 1000)}"
    
    active_conversations[conv_id] = {
        "conversation_id": conv_id,
        "messages": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    return {"conversation_id": conv_id}

@app.get("/api/chat/history")
async def get_all_conversations():
    """Get all conversation IDs"""
    conversations = []
    
    # From active conversations
    for conv_id, conv_data in active_conversations.items():
        conversations.append({
            "conversation_id": conv_id,
            "message_count": len(conv_data["messages"]),
            "created_at": conv_data["created_at"],
            "updated_at": conv_data["updated_at"],
            "preview": conv_data["messages"][0]["content"][:100] if conv_data["messages"] else ""
        })
    
    # From saved conversations
    conv_dir = Path(__file__).parent / "conversations"
    if conv_dir.exists():
        for conv_file in conv_dir.glob("*.json"):
            if conv_file.stem not in active_conversations:
                try:
                    with open(conv_file, 'r') as f:
                        data = json.load(f)
                        conversations.append({
                            "conversation_id": data["conversation_id"],
                            "message_count": len(data["messages"]),
                            "created_at": data["created_at"],
                            "updated_at": data["updated_at"],
                            "preview": data["messages"][0]["content"][:100] if data["messages"] else ""
                        })
                except Exception as e:
                    logger.error(f"Error loading conversation {conv_file}: {e}")
    
    return {"conversations": conversations}

@app.get("/api/chat/history/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a specific conversation history"""
    
    # Check active conversations first
    if conversation_id in active_conversations:
        return active_conversations[conversation_id]
    
    # Check saved conversations
    conv_file = Path(__file__).parent / "conversations" / f"{conversation_id}.json"
    if conv_file.exists():
        with open(conv_file, 'r') as f:
            return json.load(f)
    
    raise HTTPException(status_code=404, detail="Conversation not found")

@app.delete("/api/chat/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    
    # Remove from active conversations
    if conversation_id in active_conversations:
        del active_conversations[conversation_id]
    
    # Remove saved file
    conv_file = Path(__file__).parent / "conversations" / f"{conversation_id}.json"
    if conv_file.exists():
        conv_file.unlink()
    
    return {"message": "Conversation deleted", "conversation_id": conversation_id}

@app.get("/api/chat/export/{conversation_id}")
async def export_conversation(conversation_id: str, format: str = "json"):
    """Export conversation as JSON or text"""
    
    # Get conversation
    if conversation_id in active_conversations:
        conv_data = active_conversations[conversation_id]
    else:
        conv_file = Path(__file__).parent / "conversations" / f"{conversation_id}.json"
        if not conv_file.exists():
            raise HTTPException(status_code=404, detail="Conversation not found")
        with open(conv_file, 'r') as f:
            conv_data = json.load(f)
    
    if format == "json":
        return JSONResponse(content=conv_data)
    elif format == "txt":
        # Convert to text format
        text_lines = [f"Conversation: {conversation_id}", f"Created: {conv_data['created_at']}", "=" * 80, ""]
        
        for msg in conv_data["messages"]:
            role = "User" if msg["role"] == "user" else "Assistant"
            text_lines.append(f"[{msg['timestamp']}] {role}:")
            text_lines.append(msg["content"])
            text_lines.append("")
        
        return StreamingResponse(
            iter(["\n".join(text_lines)]),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={conversation_id}.txt"}
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")

# ==================== Metrics Endpoints ====================

@app.get("/api/metrics/summary", response_model=MetricsSummary)
async def get_metrics_summary():
    """Get summary metrics from Prometheus"""
    
    try:
        prometheus_url = "http://localhost:9090"
        
        # Query total queries
        total_queries = 0
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{prometheus_url}/api/v1/query", params={"query": "sum(rag_queries_total)"})
                data = response.json()
                if data["status"] == "success" and data["data"]["result"]:
                    total_queries = int(float(data["data"]["result"][0]["value"][1]))
        except Exception as e:
            logger.warning(f"Failed to query total_queries: {e}")
            
        # Query blocked attacks
        blocked_attacks = 0
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{prometheus_url}/api/v1/query", params={"query": "sum(rag_security_attacks_total)"})
                data = response.json()
                if data["status"] == "success" and data["data"]["result"]:
                    blocked_attacks = int(float(data["data"]["result"][0]["value"][1]))
        except Exception as e:
            logger.warning(f"Failed to query blocked_attacks: {e}")
            
        # Query average response time
        avg_response_time = 0.0
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{prometheus_url}/api/v1/query", 
                    params={"query": "rate(rag_request_duration_seconds_sum[5m]) / rate(rag_request_duration_seconds_count[5m])"})
                data = response.json()
                if data["status"] == "success" and data["data"]["result"]:
                    avg_response_time = float(data["data"]["result"][0]["value"][1])
        except Exception as e:
            logger.warning(f"Failed to query avg_response_time: {e}")
            
        # Query PII redacted count
        pii_redacted_count = 0
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{prometheus_url}/api/v1/query", params={"query": "sum(rag_security_pii_redacted_total)"})
                data = response.json()
                if data["status"] == "success" and data["data"]["result"]:
                    pii_redacted_count = int(float(data["data"]["result"][0]["value"][1]))
        except Exception as e:
            logger.warning(f"Failed to query pii_redacted_count: {e}")
            
        # Calculate success rate
        success_rate = 100.0
        if total_queries > 0:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{prometheus_url}/api/v1/query", 
                        params={"query": "rag_queries_total{status='success'}"})
                    data = response.json()
                    if data["status"] == "success" and data["data"]["result"]:
                        success_queries = int(float(data["data"]["result"][0]["value"][1]))
                        success_rate = (success_queries / total_queries) * 100
            except Exception as e:
                logger.warning(f"Failed to calculate success_rate: {e}")
        
        return MetricsSummary(
            total_queries=total_queries,
            blocked_attacks=blocked_attacks,
            avg_response_time=avg_response_time,
            success_rate=success_rate,
            pii_redacted_count=pii_redacted_count
        )
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")

@app.get("/api/metrics/live")
async def get_live_metrics():
    """Get real-time metrics feed"""
    # This would stream recent events
    return {"events": []}

@app.get("/api/metrics/security")
async def get_security_metrics():
    """Get security-specific metrics"""
    return {
        "attacks_blocked": 0,
        "pii_redactions": 0,
        "attack_types": {}
    }

@app.get("/api/metrics/performance")
async def get_performance_metrics():
    """Get performance metrics"""
    return {
        "p50_latency": 0.0,
        "p95_latency": 0.0,
        "p99_latency": 0.0,
        "requests_per_second": 0.0
    }

# ==================== System Endpoints ====================

@app.get("/api/system/config")
async def get_config():
    """Get current system configuration"""
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    
    return {
        "model_name": rag_pipeline.config.model_name,
        "temperature": rag_pipeline.config.temperature,
        "max_tokens": rag_pipeline.config.max_tokens,
        "top_k_results": rag_pipeline.config.top_k_results,
        "embedding_model": rag_pipeline.config.embedding_model
    }

@app.post("/api/system/config")
async def update_config(config: SystemConfig):
    """Update system configuration"""
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    
    # Update configuration
    rag_pipeline.config.model_name = config.model_name
    rag_pipeline.config.temperature = config.temperature
    rag_pipeline.config.max_tokens = config.max_tokens
    rag_pipeline.config.top_k_results = config.top_k_results
    
    return {"message": "Configuration updated", "config": config}

# ==================== WebSocket Endpoints ====================

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")

manager = ConnectionManager()

@app.websocket("/api/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message = data.get("message", "")
            conv_id = data.get("conversation_id") or f"conv_{int(time.time() * 1000)}"
            
            if not rag_pipeline:
                await manager.send_message({
                    "type": "error",
                    "message": "RAG pipeline not initialized"
                }, websocket)
                continue
            
            # Send typing indicator
            await manager.send_message({
                "type": "typing",
                "conversation_id": conv_id
            }, websocket)
            
            try:
                # Query RAG pipeline
                result = rag_pipeline.query(message)
                
                # Send response
                await manager.send_message({
                    "type": "response",
                    "conversation_id": conv_id,
                    "response": result["answer"],
                    "sources": result.get("sources", []),
                    "security_info": {
                        "status": result.get("security_status", "unknown"),
                        "pii_redacted": result.get("pii_redacted", False)
                    },
                    "similarity_scores": [s.get("similarity_score", 0.0) for s in result.get("sources", [])]
                }, websocket)
                
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await manager.send_message({
                    "type": "error",
                    "message": str(e)
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.websocket("/api/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Send periodic metrics updates
            metrics = {
                "type": "metrics_update",
                "timestamp": datetime.now().isoformat(),
                "active_conversations": len(active_conversations),
                "total_messages": sum(len(conv["messages"]) for conv in active_conversations.values())
            }
            await manager.send_message(metrics, websocket)
            
            await asyncio.sleep(5)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket metrics error: {e}")
        manager.disconnect(websocket)

# ==================== Main ====================

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "8080"))  # Changed default from 8000 to 8080
    
    logger.info("=" * 60)
    logger.info("🚀 RAG Chatbot API Server")
    logger.info("=" * 60)
    logger.info(f"📡 API Server: http://localhost:{port}")
    logger.info(f"📊 Prometheus Metrics: http://localhost:8000/metrics")
    logger.info(f"📚 API Documentation: http://localhost:{port}/api/docs")
    logger.info("=" * 60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,

        reload=True,        log_level="info"
    )
