#!/usr/bin/env python3
"""
Enhanced OpenViking Mock Server with Advanced Features
Production-ready implementation with conversation memory, hierarchical skills, and performance monitoring
"""

import asyncio
import hashlib
import logging
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any

import uvicorn

# Import command registry for slash command support
from commands import CommandRegistry
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OpenViking Production Server", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Advanced data structures
class ConversationMemory:
    def __init__(self):
        self.sessions = {}
        self.max_turns = 10
        self.timeout_minutes = 30

    def add_message(
        self, session_id: str, role: str, content: str, metadata: dict = None
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

    def get_context(self, session_id: str, last_n: int = 3) -> list[dict]:
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


# Global memory and conversation management
conversation_memory = ConversationMemory()

# Global persistent memory for learnings/resources
global_memory = {}

# Global command registry for slash commands
command_registry = CommandRegistry()

# Enhanced skill hierarchy with type hints
skill_hierarchy: dict[str, Any] = {
    "Engineering": {
        "Frontend": ["React", "Vue", "Angular"],
        "Backend": ["Node.js", "Python", "Go"],
        "DevOps": ["Docker", "Kubernetes", "CI/CD"],
    },
    "Data Science": {
        "Analysis": ["Pandas", "NumPy", "Scikit-learn"],
        "ML": ["TensorFlow", "PyTorch", "MLflow"],
        "Visualization": ["Matplotlib", "Plotly", "D3.js"],
    },
    "Security": {
        "Authentication": ["JWT", "OAuth", "SAML"],
        "Penetration": ["OWASP ZAP", "Burp Suite", "Nmap"],
        "Compliance": ["GDPR", "SOC2", "HIPAA"],
    },
    "Process": {
        "Coordination": ["FlightDirector"],
        "Documentation": ["Librarian"],
        "Learning": ["Reflect"],
        "Standards": ["CodingStandards"],
        "QA": ["QualityAnalyst"],
    },
}

# Performance monitoring with proper typing
performance_metrics = defaultdict(list)


class PerformanceMonitor:
    def __init__(self) -> None:
        self.metrics: dict[str, list[dict[str, Any]]] = {}

    def record_metric(
        self,
        system: str,
        metric_type: str,
        value: float,
        metadata: dict[str, Any] | None = None,
    ) -> None:
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

    def get_average(
        self, system: str, metric_type: str, minutes: int = 5
    ) -> float | None:
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [
            m
            for m in self.metrics.get(system, [])
            if datetime.fromisoformat(m.get("timestamp", "")) > cutoff
            and m.get("type", "") == metric_type
        ]

        return (
            sum(m.get("value", 0) for m in recent_metrics) / len(recent_metrics)
            if recent_metrics
            else None
        )


# Singleton instance
performance_monitor = PerformanceMonitor()


# Enhanced Pydantic models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    features: list[str]


class EmbeddingRequest(BaseModel):
    text: str
    cache_key: str | None = None


class EmbeddingResponse(BaseModel):
    embedding: list[float]
    dimension: int
    model: str
    cached: bool = False
    cache_hit: bool = False


class SkillSearchRequest(BaseModel):
    query: str
    max_results: int = 10
    category: str | None = None
    hierarchical: bool = False


class SkillResponse(BaseModel):
    skills: list[dict[str, Any]]
    query: str
    found_count: int
    search_time_ms: float
    category: str | None = None


class ConversationRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str
    role: str = "user"
    context_turns: int = 3


class ConversationResponse(BaseModel):
    session_id: str
    response: str
    context_messages: list[dict[str, Any]]
    message_count: int


class ResourceRequest(BaseModel):
    content: str
    target_uri: str
    resource_type: str = "memory"
    session_id: str | None = None


class ResourceResponse(BaseModel):
    success: bool
    resource_id: str
    message: str
    session_id: str | None = None


class PerformanceRequest(BaseModel):
    system: str
    metric_type: str
    value: float
    metadata: dict = None


# Slash command models
class CommandRequest(BaseModel):
    name: str  # e.g., "/next" or "next"


class CommandResponse(BaseModel):
    name: str
    description: str
    instructions: str
    found: bool


class CommandListResponse(BaseModel):
    commands: list[dict[str, str]]
    source: str
    count: int


# Enhanced data models for skill categories
class Skill(BaseModel):
    id: str
    name: str
    description: str
    category: str
    subcategory: str | None = None
    examples: list[str] = []
    parent_skill: str | None = None
    related_skills: list[str] = []
    complexity: int = 1
    usage_count: int = 0


# Enhanced skill database with hierarchy
enhanced_skills = [
    Skill(
        id="flight-director",
        name="FlightDirector",
        description="Flight planning and coordination",
        category="coordination",
        examples=["Plan route", "Coordinate takeoff", "Monitor flight systems"],
        complexity=3,
        usage_count=15,
    ),
    Skill(
        id="librarian",
        name="Librarian",
        description="Knowledge management and retrieval",
        category="information",
        examples=["Search documents", "Organize knowledge", "Retrieve information"],
        complexity=2,
        usage_count=25,
    ),
    Skill(
        id="performance-optimizer",
        name="PerformanceOptimizer",
        description="System optimization and performance tuning",
        category="optimization",
        examples=["Analyze bottlenecks", "Optimize code", "Profile performance"],
        complexity=4,
        usage_count=20,
        parent_skill="flight-director",
    ),
    Skill(
        id="security-expert",
        name="SecurityExpert",
        description="Security analysis and recommendations",
        category="security",
        examples=["Audit code", "Security review", "Penetration testing"],
        complexity=4,
        usage_count=8,
    ),
    Skill(
        id="data-scientist",
        name="DataScientist",
        description="Data analysis and machine learning",
        category="analytics",
        examples=["Statistical analysis", "Machine learning", "Data visualization"],
        complexity=5,
        usage_count=12,
    ),
    Skill(
        id="frontend-expert",
        name="FrontendExpert",
        description="Frontend development and optimization",
        category="engineering",
        examples=["React optimization", "UI/UX design", "Web performance"],
        complexity=4,
        usage_count=18,
        parent_skill="performance-optimizer",
    ),
    Skill(
        id="backend-expert",
        name="BackendExpert",
        description="Backend development and scaling",
        category="engineering",
        examples=["API design", "Database optimization", "Microservices"],
        complexity=4,
        usage_count=15,
        parent_skill="performance-optimizer",
    ),
    Skill(
        id="quality-analyst",
        name="QualityAnalyst",
        description="Standards for performance evaluation and testing",
        category="testing",
        examples=["Run benchmarks", "UI testing", "E2E verification"],
        complexity=3,
        usage_count=10,
    ),
    Skill(
        id="reflect",
        name="Reflect",
        description="Self-evolution and memory capture",
        category="learning",
        examples=["Session analysis", "Memory extraction", "Self-correction"],
        complexity=3,
        usage_count=30,
    ),
    Skill(
        id="coding-standards",
        name="CodingStandards",
        description="General coding best practices and patterns",
        category="engineering",
        examples=["Input validation", "Error handling", "Documentation standards"],
        complexity=2,
        usage_count=40,
    ),
]

# Simple embedding cache
embedding_cache = {}


def get_embedding_hash(text: str) -> str:
    """Generate consistent hash for caching"""
    return hashlib.md5(text.encode()).hexdigest()


# API endpoints with enhanced features
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check with feature listing"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="2.0.0-production",
        features=[
            "conversation_memory",
            "hierarchical_skills",
            "performance_monitoring",
            "embedding_caching",
            "real_time_metrics",
            "slash_commands",
        ],
    )


# Slash command endpoints
@app.get("/commands", response_model=CommandListResponse)
async def list_commands():
    """List all available slash commands."""
    command_registry.reload()  # Refresh from disk
    commands = command_registry.list_commands()
    return CommandListResponse(
        commands=commands,
        source=str(command_registry.commands_dir),
        count=len(commands),
    )


@app.post("/commands/get", response_model=CommandResponse)
async def get_command(request: CommandRequest):
    """Retrieve a specific slash command by name."""
    cmd = command_registry.get_command(request.name)
    if cmd:
        return CommandResponse(
            name=cmd["name"],
            description=cmd["description"],
            instructions=cmd["instructions"],
            found=True,
        )
    return CommandResponse(
        name=request.name.lstrip("/"), description="", instructions="", found=False
    )


@app.get("/commands/{command_name}")
async def get_command_by_path(command_name: str):
    """Retrieve a slash command by path parameter."""
    cmd = command_registry.get_command(command_name)
    if cmd:
        return {
            "name": cmd["name"],
            "description": cmd["description"],
            "instructions": cmd["instructions"],
            "path": cmd["path"],
            "found": True,
        }
    raise HTTPException(status_code=404, detail=f"Command '/{command_name}' not found")


@app.get("/commands/search/{query}")
async def search_commands(query: str):
    """Search commands by name or description."""
    results = command_registry.search_commands(query)
    return {"query": query, "results": results, "count": len(results)}


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
    await asyncio.sleep(0.1)  # Simulate processing time

    text_hash = get_embedding_hash(request.text)
    embedding = [float(hash(text_hash) % 1000) / 1000.0 for _ in range(768)]

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
        model="nomic-embed-text-cached",
        cached=False,
        cache_hit=False,
    )


@app.post("/skills/search", response_model=SkillResponse)
async def search_skills(request: SkillSearchRequest):
    """Enhanced skill search with hierarchy and categorization"""
    start_time = time.time()

    query_lower = request.query.lower()
    category = request.category or "general"
    hierarchical = request.hierarchical

    # Search in specified category first
    matching_skills = []

    for skill in enhanced_skills:
        if (skill.category == category or category == "general") and any(
            keyword in skill.name.lower() or keyword in skill.description.lower()
            for keyword in query_lower.split()
        ):
            # Add subskills if hierarchical search
            if hierarchical:
                related_skills = [
                    s.id for s in enhanced_skills if s.parent_skill == skill.id
                ]
                sub_skills = [
                    s.name
                    for s in enhanced_skills
                    if s.parent_skill == skill.id and s.subcategory
                ]
            else:
                related_skills = []
                sub_skills = []

            matching_skills.append(
                {
                    "id": skill.id,
                    "name": skill.name,
                    "description": skill.description,
                    "category": skill.category,
                    "subcategory": skill.subcategory,
                    "examples": skill.examples,
                    "parent_skill": skill.parent_skill,
                    "related_skills": related_skills,
                    "sub_skills": sub_skills,
                    "complexity": skill.complexity,
                    "usage_count": skill.usage_count,
                }
            )

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
        category=category,
    )


@app.post("/conversation", response_model=ConversationResponse)
async def handle_conversation(request: ConversationRequest):
    """Conversation memory with context awareness"""
    # Add user message
    conversation_memory.add_message(request.session_id, request.role, request.message)

    # Get context for response
    context_messages = conversation_memory.get_context(
        request.session_id, request.context_turns
    )

    # Generate mock response
    response = f"I understand your message about '{request.message}'. Let me help you with that."

    # Add assistant response
    conversation_memory.add_message(request.session_id, "assistant", response)

    return ConversationResponse(
        session_id=request.session_id,
        response=response,
        context_messages=context_messages,
        message_count=len(conversation_memory.sessions[request.session_id]["messages"]),
    )


@app.post("/session/flush")
async def flush_sessions(session_id: str | None = None):
    """Flush all or specific conversation sessions"""
    if session_id:
        if session_id in conversation_memory.sessions:
            del conversation_memory.sessions[session_id]
            return {"status": "success", "message": f"Session {session_id} flushed"}
        else:
            return {"status": "not_found", "message": f"Session {session_id} not found"}
    else:
        count = len(conversation_memory.sessions)
        conversation_memory.sessions = {}
        return {"status": "success", "message": f"All {count} sessions flushed"}


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

    # Store in global memory
    global_memory[resource_id] = {
        "id": resource_id,
        "content": request.content,
        "target_uri": request.target_uri,
        "resource_type": request.resource_type,
        "session_id": request.session_id,
        "timestamp": datetime.now().isoformat(),
    }

    # Simple search index (by target_uri)
    if request.target_uri:
        global_memory[f"uri:{request.target_uri}"] = resource_id

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


@app.get("/resources/{resource_id}")
async def get_resource(resource_id: str):
    """Retrieve a specific resource by ID or target URI"""
    # Check if it's a URI lookup
    lookup_id = resource_id
    if resource_id.startswith("uri:"):
        lookup_id = global_memory.get(resource_id)
        if not lookup_id:
            raise HTTPException(status_code=404, detail="Resource URI not found")

    if lookup_id in global_memory:
        return global_memory[lookup_id]
    raise HTTPException(status_code=404, detail="Resource not found")


@app.get("/resources")
async def list_resources(resource_type: str | None = None):
    """List all stored resources"""
    resources = [v for k, v in global_memory.items() if not k.startswith("uri:")]
    if resource_type:
        resources = [r for r in resources if r["resource_type"] == resource_type]
    return {"resources": resources, "count": len(resources)}


@app.get("/skills/hierarchical")
async def get_skill_hierarchy():
    """Get complete skill hierarchy"""
    return {
        "categories": skill_hierarchy,
        "total_skills": len(enhanced_skills),
        "last_updated": datetime.now().isoformat(),
    }


@app.get("/performance/metrics")
async def get_performance_metrics(system: str | None = None, minutes: int = 5):
    """Real-time performance monitoring dashboard"""
    if system and system in performance_monitor.metrics:
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [
            m
            for m in performance_monitor.metrics[system]
            if datetime.fromisoformat(m["timestamp"]) > cutoff
        ]

        # Calculate averages
        metrics_by_type = defaultdict(list)
        for metric in recent_metrics:
            metrics_by_type[metric["type"]].append(metric["value"])

        averages = {
            metric_type: sum(values) / len(values)
            for metric_type, values in metrics_by_type.items()
        }

        return {
            "system": system,
            "timeframe_minutes": minutes,
            "total_metrics": len(recent_metrics),
            "averages": averages,
            "recent_metrics": recent_metrics[-20:],  # Last 20 metrics
        }

    return {
        "all_systems": list(performance_monitor.metrics.keys()),
        "system": system,
        "averages": performance_monitor.get_average(
            system, "embedding_generation_time", 5
        )
        if system
        else None,
        "status": "Specify system parameter for detailed metrics",
    }


@app.get("/performance/dashboard")
async def performance_dashboard():
    """Performance dashboard with comprehensive metrics"""
    all_metrics = {}

    for system, metrics in performance_monitor.metrics.items():
        system_averages = {}
        for metric_type in [
            "embedding_generation_time",
            "skill_search_time",
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
            "cache_hit_rate": performance_monitor.get_average(
                "openviking", "embedding_cache_hit", 5
            )
            or 0.0,
        },
    }


@app.get("/")
async def root():
    """Enhanced API information"""
    return {
        "name": "OpenViking Production Server",
        "version": "2.0.0-production",
        "description": "Production-ready OpenViking with advanced capabilities",
        "features": [
            "conversation_memory",
            "hierarchical_skills",
            "performance_monitoring",
            "embedding_caching",
            "real_time_metrics",
            "resource_management",
            "session_tracking",
            "slash_commands",
        ],
        "endpoints": {
            "health": "/health - Enhanced health check",
            "embeddings": "/embeddings - Cached embeddings",
            "skills/search": "/skills/search - Hierarchical skill search",
            "skills/hierarchical": "/skills/hierarchical - Complete skill hierarchy",
            "conversation": "/conversation - Multi-turn conversation memory",
            "resources": "/resources - Resource storage with session support",
            "commands": "/commands - List all slash commands",
            "commands/get": "/commands/get - Retrieve a specific command",
            "commands/{name}": "/commands/{name} - Get command by path",
            "commands/search/{query}": "/commands/search/{query} - Search commands",
            "performance/metrics": "/performance/metrics - Real-time performance monitoring",
            "performance/dashboard": "/performance/dashboard - Performance dashboard",
            "/": "API information",
        },
    }


# Background tasks
async def cleanup_expired_sessions():
    """Background task to cleanup expired sessions"""
    while True:
        await asyncio.sleep(60)  # Check every minute
        conversation_memory.cleanup_expired()


@app.on_event("startup")
async def startup_event():
    """Run tasks on server startup"""
    asyncio.create_task(cleanup_expired_sessions())


if __name__ == "__main__":
    import os

    import uvicorn

    port = int(os.getenv("PORT", "8000"))

    print(f"🚀 Starting OpenViking Production Server v2.0.0 on port {port}")
    print("🔧 Enhanced Features:")
    print("   • Multi-turn conversation memory")
    print("   • Hierarchical skill discovery")
    print("   • Real-time embedding caching")
    print("   • Performance monitoring")
    print("   • Resource management with sessions")
    print("   • Background session cleanup")
    print("\n📊 Available Endpoints:")
    print("   GET  /health - Enhanced health check")
    print("   POST /embeddings - Cached embeddings")
    print("   POST /skills/search - Hierarchical skill search")
    print("   POST /conversation - Multi-turn conversation memory")
    print("   POST /resources - Resource storage")
    print("   GET /performance/metrics - Real-time monitoring")
    print("   GET /performance/dashboard - Performance dashboard")
    print("   GET  / - API information")

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
