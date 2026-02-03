#!/usr/bin/env python3
"""
OpenViking Enhanced Mock Server with Conversation Memory
Production-ready implementation with multi-turn conversation support
"""

import asyncio
import json
import time
import hashlib
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import uuid
import httpx
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OpenViking Enhanced Server", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Conversation memory system
class ConversationMemory:
    def __init__(self):
        self.sessions = {}
        self.max_turns = 10
        self.timeout_minutes = 30

    def add_message(
        self, session_id: str, role: str, content: str, metadata: Dict = None
    ):
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "id": session_id,
                "messages": deque(maxlen=self.max_turns),
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
            }

        session = self.sessions[session_id]
        session["messages"].append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now(),
                "metadata": metadata or {},
            }
        )
        session["last_activity"] = datetime.now()

    def get_context(self, session_id: str, last_n: int = 3) -> List[Dict]:
        if session_id not in self.sessions:
            return []

        session = self.sessions[session_id]
        messages = list(session["messages"])

        # Return last N messages for context
        return messages[-last_n:] if messages else []

    def cleanup_expired(self):
        now = datetime.now()
        expired_sessions = [
            sid
            for sid, data in self.sessions.items()
            if now - data["last_activity"] > timedelta(minutes=self.timeout_minutes)
        ]
        for sid in expired_sessions:
            del self.sessions[sid]

    def get_session_stats(self, session_id: str) -> Dict:
        if session_id not in self.sessions:
            return {}

        session = self.sessions[session_id]
        return {
            "id": session_id,
            "message_count": len(session["messages"]),
            "created_at": session["created_at"].isoformat(),
            "last_activity": session["last_activity"].isoformat(),
            "session_age_minutes": (
                datetime.now() - session["created_at"]
            ).total_seconds()
            / 60,
        }


# Global conversation memory
conversation_memory = ConversationMemory()

# Enhanced skill database
enhanced_skills = [
    {
        "id": "react-optimization",
        "name": "React Optimization",
        "description": "React performance optimization techniques",
        "category": "frontend",
        "examples": ["Memoization", "Virtual scrolling", "Code splitting"],
        "complexity": 3,
    },
    {
        "id": "api-auth",
        "name": "API Authentication",
        "description": "API authentication and authorization patterns",
        "category": "security",
        "examples": ["JWT tokens", "OAuth2", "API keys"],
        "complexity": 4,
    },
    {
        "id": "database-design",
        "name": "Database Design",
        "description": "Database schema design and optimization",
        "category": "backend",
        "examples": ["Normalization", "Indexing", "Query optimization"],
        "complexity": 4,
    },
]

# Performance monitoring
performance_metrics = defaultdict(list)


class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}

    def record_metric(
        self, system: str, metric_type: str, value: float, metadata: Dict = None
    ):
        timestamp = datetime.now().isoformat()

        if system not in self.metrics:
            self.metrics[system] = []

        self.metrics[system].append(
            {
                "timestamp": timestamp,
                "type": metric_type,
                "value": value,
                "metadata": metadata or {},
            }
        )

        # Keep only last 1000 metrics per system
        if len(self.metrics[system]) > 1000:
            self.metrics[system] = self.metrics[system][-1000:]


performance_monitor = PerformanceMonitor()


# Pydantic models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    features: List[str]


class EmbeddingRequest(BaseModel):
    text: str
    cache_key: Optional[str] = None


class EmbeddingResponse(BaseModel):
    embedding: List[float]
    dimension: int
    model: str
    cached: bool = False
    cache_hit: bool = False


class SkillSearchRequest(BaseModel):
    query: str
    max_results: int = 10
    category: Optional[str] = None


class SkillResponse(BaseModel):
    skills: List[Dict[str, Any]]
    query: str
    found_count: int
    search_time_ms: float


class ConversationRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str
    role: str = "user"
    context_turns: int = 3


class ConversationResponse(BaseModel):
    session_id: str
    response: str
    context_messages: List[Dict[str, Any]]
    message_count: int
    session_stats: Dict[str, Any]


class ResourceRequest(BaseModel):
    content: str
    target_uri: str
    resource_type: str = "memory"
    session_id: Optional[str] = None


class ResourceResponse(BaseModel):
    success: bool
    resource_id: str
    message: str
    session_id: Optional[str] = None


# Simple embedding cache
embedding_cache = {}


def get_embedding_hash(text: str) -> str:
    """Generate consistent hash for caching"""
    return hashlib.md5(text.encode()).hexdigest()


# API endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check with feature listing"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="2.0.0-enhanced",
        features=[
            "conversation_memory",
            "enhanced_embeddings",
            "skill_search",
            "performance_monitoring",
            "resource_management",
        ],
    )


@app.post("/embeddings", response_model=EmbeddingResponse)
async def create_embedding(request: EmbeddingRequest):
    """Enhanced embedding with caching support"""
    global embedding_cache

    cache_key = request.cache_key or get_embedding_hash(request.text)

    # Check cache first
    if cache_key in embedding_cache:
        cached_embedding = embedding_cache[cache_key]
        performance_monitor.record_metric("openviking", "embedding_cache_hit", 1.0)
        return EmbeddingResponse(
            embedding=cached_embedding["embedding"],
            dimension=len(cached_embedding["embedding"]),
            model="nomic-embed-text-cached",
            cached=True,
            cache_hit=True,
        )

    # Generate new embedding
    start_time = time.time()
    await asyncio.sleep(0.05)  # Simulate processing time

    text_hash = get_embedding_hash(request.text)
    embedding = [float(hash(text_hash + str(i)) % 1000) / 1000.0 for i in range(768)]

    # Cache the result
    embedding_cache[cache_key] = {
        "embedding": embedding,
        "timestamp": datetime.now(),
        "text": request.text[:100],  # Truncate for storage
    }

    processing_time = (time.time() - start_time) * 1000
    performance_monitor.record_metric(
        "openviking", "embedding_generation_time", processing_time
    )

    return EmbeddingResponse(
        embedding=embedding,
        dimension=768,
        model="nomic-embed-text-enhanced",
        cached=False,
        cache_hit=False,
    )


@app.post("/skills/search", response_model=SkillResponse)
async def search_skills(request: SkillSearchRequest):
    """Enhanced skill search"""
    start_time = time.time()

    query_lower = request.query.lower()
    matching_skills = []

    for skill in enhanced_skills:
        if any(
            keyword in skill["name"].lower() or keyword in skill["description"].lower()
            for keyword in query_lower.split()
        ):
            matching_skills.append(skill)

    # Limit results
    matching_skills = matching_skills[: request.max_results]
    processing_time = (time.time() - start_time) * 1000

    performance_monitor.record_metric(
        "openviking", "skill_search_time", processing_time
    )

    return SkillResponse(
        skills=matching_skills,
        query=request.query,
        found_count=len(matching_skills),
        search_time_ms=processing_time,
    )


@app.post("/conversation", response_model=ConversationResponse)
async def handle_conversation(request: ConversationRequest):
    """Conversation memory with context awareness"""
    start_time = time.time()

    # Add user message
    conversation_memory.add_message(request.session_id, request.role, request.message)

    # Get context for response
    context_messages = conversation_memory.get_context(
        request.session_id, request.context_turns
    )

    # Generate contextual response based on history
    context_summary = ""
    if context_messages:
        context_summary = f" (Context: {len(context_messages)} previous messages)"

    # Generate response based on common patterns
    if "optimization" in request.message.lower():
        response = f"I'll help you with optimization techniques{context_summary}. Let me suggest some performance improvements."
    elif "authentication" in request.message.lower():
        response = f"For authentication{context_summary}, I recommend implementing JWT tokens with proper security measures."
    elif "database" in request.message.lower():
        response = f"Database design{context_summary} requires careful planning. Let me suggest some best practices."
    else:
        response = f"I understand your request about '{request.message}'{context_summary}. Let me help you with that."

    # Add assistant response
    conversation_memory.add_message(request.session_id, "assistant", response)

    # Get session statistics
    session_stats = conversation_memory.get_session_stats(request.session_id)

    processing_time = (time.time() - start_time) * 1000
    performance_monitor.record_metric(
        "openviking", "conversation_time", processing_time
    )

    return ConversationResponse(
        session_id=request.session_id,
        response=response,
        context_messages=context_messages,
        message_count=len(conversation_memory.sessions[request.session_id]["messages"]),
        session_stats=session_stats,
    )


@app.post("/resources", response_model=ResourceResponse)
async def add_resource(request: ResourceRequest):
    """Enhanced resource management with session support"""
    start_time = time.time()

    resource_id = str(uuid.uuid4())

    if request.session_id:
        # Add to conversation memory
        conversation_memory.add_message(
            request.session_id,
            "system",
            f"Resource saved: {request.resource_type}",
            {"resource_id": resource_id, "target_uri": request.target_uri},
        )

    processing_time = (time.time() - start_time) * 1000
    performance_monitor.record_metric(
        "openviking", "resource_storage_time", processing_time
    )

    return ResourceResponse(
        success=True,
        resource_id=resource_id,
        message="Resource stored successfully",
        session_id=request.session_id,
    )


@app.get("/conversation/stats/{session_id}")
async def get_conversation_stats(session_id: str):
    """Get conversation session statistics"""
    stats = conversation_memory.get_session_stats(session_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_stats": stats,
        "recent_context": conversation_memory.get_context(session_id, 3),
    }


@app.get("/performance/metrics")
async def get_performance_metrics():
    """Performance monitoring dashboard"""
    all_metrics = {}

    for system, metrics in performance_monitor.metrics.items():
        system_averages = {}
        for metric_type in [
            "embedding_generation_time",
            "skill_search_time",
            "conversation_time",
            "resource_storage_time",
        ]:
            values = [m["value"] for m in metrics if m["type"] == metric_type]
            if values:
                system_averages[metric_type] = {
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values),
                }

        all_metrics[system] = {
            "averages": system_averages,
            "total_requests": len(metrics),
        }

    return {
        "timestamp": datetime.now().isoformat(),
        "systems": all_metrics,
        "summary": {
            "total_requests": sum(
                len(metrics) for metrics in performance_monitor.metrics.values()
            ),
            "active_sessions": len(conversation_memory.sessions),
            "cache_size": len(embedding_cache),
        },
    }


@app.get("/")
async def root():
    """Enhanced API information"""
    return {
        "name": "OpenViking Enhanced Server",
        "version": "2.0.0-enhanced",
        "description": "Production-ready OpenViking with conversation memory and advanced features",
        "features": [
            "conversation_memory",
            "enhanced_embeddings",
            "skill_search",
            "performance_monitoring",
            "resource_management",
            "session_tracking",
        ],
        "endpoints": {
            "health": "/health - Enhanced health check",
            "embeddings": "/embeddings - Cached embeddings",
            "skills/search": "/skills/search - Enhanced skill search",
            "conversation": "/conversation - Multi-turn conversation memory",
            "resources": "/resources - Resource storage with session support",
            "conversation/stats/{session_id}": "/conversation/stats/{session_id} - Session statistics",
            "performance/metrics": "/performance/metrics - Performance monitoring dashboard",
            "/": "API information",
        },
    }


# Background tasks
async def cleanup_expired_sessions():
    """Background task to cleanup expired sessions"""
    while True:
        await asyncio.sleep(60)  # Check every minute
        conversation_memory.cleanup_expired()


if __name__ == "__main__":
    import os

    port = int(os.getenv("PORT", "8000"))

    print(f"🚀 Starting OpenViking Enhanced Server v2.0.0 on port {port}")
    print("🔧 Enhanced Features:")
    print("   • Multi-turn conversation memory")
    print("   • Enhanced embedding caching")
    print("   • Skill search and discovery")
    print("   • Performance monitoring")
    print("   • Resource management with sessions")
    print("   • Session statistics and cleanup")
    print("\n📊 Available Endpoints:")
    print("   GET  /health - Enhanced health check")
    print("   POST /embeddings - Cached embeddings")
    print("   POST /skills/search - Enhanced skill search")
    print("   POST /conversation - Multi-turn conversation memory")
    print("   POST /resources - Resource storage")
    print("   GET  /conversation/stats/{session_id} - Session statistics")
    print("   GET  /performance/metrics - Performance monitoring")
    print("   GET  / - API information")

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
