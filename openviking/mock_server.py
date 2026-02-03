#!/usr/bin/env python3
"""
Basic OpenViking Mock Server
Simple implementation for demonstration and testing
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OpenViking Mock Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple data structures
skills = [
    {
        "id": "flight-director",
        "name": "FlightDirector",
        "description": "Flight planning and coordination",
        "category": "coordination",
    },
    {
        "id": "librarian",
        "name": "Librarian",
        "description": "Knowledge management and retrieval",
        "category": "information",
    },
    {
        "id": "performance-optimizer",
        "name": "PerformanceOptimizer",
        "description": "System optimization and performance tuning",
        "category": "optimization",
    },
    {
        "id": "security-expert",
        "name": "SecurityExpert",
        "description": "Security analysis and recommendations",
        "category": "security",
    },
]


# Simple Pydantic models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


class EmbeddingRequest(BaseModel):
    text: str


class EmbeddingResponse(BaseModel):
    embedding: list[float]
    dimension: int
    model: str
    cached: bool = False
    cache_hit: bool = False


class SkillSearchRequest(BaseModel):
    query: str
    max_results: int = 10


class SkillResponse(BaseModel):
    skills: list[dict[str, Any]]
    query: str
    found_count: int


class ResourceRequest(BaseModel):
    content: str
    target_uri: str


class ResourceResponse(BaseModel):
    success: bool
    resource_id: str
    message: str


# Simple caching
embedding_cache = {}


def get_embedding_hash(text: str) -> str:
    return hash(text)


# API endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy", timestamp=datetime.now().isoformat(), version="1.0.0-basic"
    )


@app.post("/embeddings", response_model=EmbeddingResponse)
async def create_embedding(request: EmbeddingRequest):
    """Create embedding from text"""
    cache_key = get_embedding_hash(request.text)

    if cache_key in embedding_cache:
        logger.info(f"Cache hit for embedding: {request.text[:50]}...")
        return EmbeddingResponse(
            embedding=embedding_cache[cache_key]["embedding"],
            dimension=len(embedding_cache[cache_key]["embedding"]),
            model="nomic-embed-text-cached",
            cached=True,
            cache_hit=True,
        )

    # Generate new embedding
    logger.info(f"Generating embedding for: {request.text[:50]}...")
    await asyncio.sleep(0.2)  # Simulate processing

    # Simple mock embedding
    text_hash = hash(request.text)
    embedding = [
        float((ord(c) % 1000) / 1000.0) for c in request.text[:100] for _ in range(768)
    ]

    # Cache the result
    embedding_cache[cache_key] = {
        "embedding": embedding,
        "timestamp": datetime.now().isoformat(),
    }

    logger.info(f"Generated {len(embedding)}D embedding")
    return EmbeddingResponse(
        embedding=embedding,
        dimension=768,
        model="nomic-embed-text-mock",
        cached=False,
        cache_hit=False,
    )


@app.post("/skills/search", response_model=SkillResponse)
async def search_skills(request: SkillSearchRequest):
    """Search for relevant skills"""
    logger.info(f"Searching skills for: {request.query}")

    query_lower = request.query.lower()
    matching_skills = []

    for skill in skills:
        if skill["name"].lower() in query_lower or any(
            keyword in skill["description"].lower() for keyword in query_lower.split()
        ):
            matching_skills.append(skill)

    return SkillResponse(
        skills=matching_skills[: request.max_results],
        query=request.query,
        found_count=len(matching_skills),
    )


@app.post("/resources", response_model=ResourceResponse)
async def add_resource(request: ResourceRequest):
    """Add resource to memory"""
    resource_id = f"resource_{hash(request.content)}"

    logger.info(f"Adding resource: {resource_id}")

    return ResourceResponse(
        success=True, resource_id=resource_id, message="Resource stored successfully"
    )


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "OpenViking Basic Mock Server",
        "version": "1.0.0-basic",
        "description": "Simplified OpenViking-compatible API for testing",
        "endpoints": {
            "health": "/health - Health check",
            "embeddings": "/embeddings - Create embeddings",
            "skills/search": "/skills/search - Search skills",
            "resources": "/resources - Add resource",
            "/": "API information",
        },
    }


if __name__ == "__main__":
    import os

    port = int(os.getenv("PORT", "8000"))

    print(f"Starting OpenViking Basic Mock Server on port {port}")
    print("Available endpoints:")
    print("  GET  /health - Health check")
    print("  POST /embeddings - Create embeddings")
    print("  POST /skills/search - Search skills")
    print("  POST /resources - Add resource")
    print("  GET  / - API info")

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
