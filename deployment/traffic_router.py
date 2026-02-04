#!/usr/bin/env python3
"""
OpenViking Traffic Router
Smart load balancer for gradual traffic routing between SMP and OpenViking
"""

import asyncio
import logging
import random
import statistics
import time
from datetime import datetime
from typing import Any

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OpenViking Traffic Router", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TrafficRouter:
    def __init__(self):
        self.smp_url = "http://localhost:9621"
        self.openviking_url = "http://localhost:8002"
        self.traffic_split = {"smp": 100, "openviking": 0}  # Start with 100% SMP
        self.performance_stats = {"smp": [], "openviking": []}
        self.health_status = {"smp": True, "openviking": True}
        self.last_health_check = datetime.now()
        self.routing_config = {
            "auto_scaling": True,
            "performance_threshold": 2.0,  # 2x performance improvement threshold
            "health_check_interval": 30,
            "stats_window": 100,  # Keep last 100 requests per system
        }

    async def health_check_system(self, system: str) -> bool:
        """Check if a system is healthy"""
        url = self.smp_url if system == "smp" else self.openviking_url

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{url}/health", timeout=5.0)
                healthy = response.status_code == 200
                self.health_status[system] = healthy
                return healthy
        except Exception as e:
            logger.warning(f"Health check failed for {system}: {e}")
            self.health_status[system] = False
            return False

    async def check_all_health(self):
        """Check health of all systems"""
        smp_healthy = await self.health_check_system("smp")
        openviking_healthy = await self.health_check_system("openviking")

        logger.info(
            f"Health status - SMP: {'✅' if smp_healthy else '❌'}, OpenViking: {'✅' if openviking_healthy else '❌'}"
        )

        # Adjust routing if systems are down
        if not smp_healthy and openviking_healthy:
            self.traffic_split = {"smp": 0, "openviking": 100}
            logger.info("SMP down, routing 100% to OpenViking")
        elif not openviking_healthy and smp_healthy:
            self.traffic_split = {"smp": 100, "openviking": 0}
            logger.info("OpenViking down, routing 100% to SMP")

    def select_system(self) -> str:
        """Select which system to route to based on traffic split"""
        # Always route to healthy systems
        if not self.health_status["smp"] and self.health_status["openviking"]:
            return "openviking"
        elif not self.health_status["openviking"] and self.health_status["smp"]:
            return "smp"

        # Use traffic split
        if random.random() * 100 < self.traffic_split["openviking"]:
            return "openviking"
        else:
            return "smp"

    async def proxy_request(
        self,
        system: str,
        endpoint: str,
        method: str,
        body: dict = None,
        headers: dict = None,
    ):
        """Proxy request to selected system"""
        url = self.smp_url if system == "smp" else self.openviking_url

        # Map endpoints between systems if needed
        if system == "smp":
            if endpoint == "/conversation":
                endpoint = "/chat"  # SMP might use different endpoint
        elif system == "openviking":
            if endpoint == "/chat":
                endpoint = "/conversation"  # Map to OpenViking endpoint

        full_url = f"{url}{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                start_time = time.time()

                if method.upper() == "GET":
                    response = await client.get(full_url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(full_url, json=body, headers=headers)
                elif method.upper() == "PUT":
                    response = await client.put(full_url, json=body, headers=headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(full_url, headers=headers)
                else:
                    raise HTTPException(status_code=405, detail="Method not allowed")

                response_time = (time.time() - start_time) * 1000

                # Record performance stats
                self.performance_stats[system].append(
                    {
                        "timestamp": datetime.now(),
                        "response_time_ms": response_time,
                        "status_code": response.status_code,
                        "success": 200 <= response.status_code < 400,
                    }
                )

                # Keep only recent stats
                if (
                    len(self.performance_stats[system])
                    > self.routing_config["stats_window"]
                ):
                    self.performance_stats[system] = self.performance_stats[system][
                        -self.routing_config["stats_window"] :
                    ]

                return {
                    "content": response.content,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "system": system,
                    "response_time_ms": response_time,
                }

        except Exception as e:
            # Record failure
            self.performance_stats[system].append(
                {
                    "timestamp": datetime.now(),
                    "response_time_ms": 30000,  # 30 second timeout
                    "status_code": 500,
                    "success": False,
                    "error": str(e),
                }
            )

            logger.error(f"Request to {system} failed: {e}")

            # Try fallback system
            fallback_system = "openviking" if system == "smp" else "smp"
            if self.health_status[fallback_system]:
                logger.info(f"Falling back to {fallback_system}")
                return await self.proxy_request(
                    fallback_system, endpoint, method, body, headers
                )

            raise HTTPException(
                status_code=503, detail=f"Both systems unavailable: {e}"
            ) from e

    def set_traffic_split(self, openviking_percentage: int):
        """Set traffic split percentage"""
        openviking_percentage = max(0, min(100, openviking_percentage))
        self.traffic_split = {
            "smp": 100 - openviking_percentage,
            "openviking": openviking_percentage,
        }
        logger.info(
            f"Traffic split updated: SMP={self.traffic_split['smp']}%, OpenViking={self.traffic_split['openviking']}%"
        )

    def get_performance_summary(self) -> dict[str, Any]:
        """Get performance summary for both systems"""
        summary = {}

        for system in ["smp", "openviking"]:
            stats = self.performance_stats[system]
            if not stats:
                summary[system] = {
                    "avg_response_time_ms": 0,
                    "success_rate": 0,
                    "total_requests": 0,
                    "healthy": self.health_status[system],
                }
                continue

            successful_requests = [s for s in stats if s["success"]]
            avg_response_time = (
                statistics.mean([s["response_time_ms"] for s in successful_requests])
                if successful_requests
                else 0
            )
            success_rate = (len(successful_requests) / len(stats)) * 100 if stats else 0

            summary[system] = {
                "avg_response_time_ms": avg_response_time,
                "success_rate": success_rate,
                "total_requests": len(stats),
                "healthy": self.health_status[system],
            }

        return summary


# Global router instance
router = TrafficRouter()


# Pydantic models
class TrafficSplitRequest(BaseModel):
    openviking_percentage: int
    reason: str | None = None


class RoutingConfigRequest(BaseModel):
    auto_scaling: bool = True
    performance_threshold: float = 2.0
    health_check_interval: int = 30


class ProxyRequest(BaseModel):
    endpoint: str
    method: str = "POST"
    body: dict | None = None
    headers: dict | None = None


# API endpoints
@app.get("/health")
async def router_health():
    """Router health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "traffic_split": router.traffic_split,
        "systems_health": router.health_status,
    }


@app.post("/traffic/split")
async def set_traffic_split(request: TrafficSplitRequest):
    """Set traffic split percentage"""
    router.set_traffic_split(request.openviking_percentage)

    return {
        "status": "success",
        "traffic_split": router.traffic_split,
        "reason": request.reason,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/traffic/status")
async def get_traffic_status():
    """Get current traffic routing status"""
    return {
        "traffic_split": router.traffic_split,
        "systems_health": router.health_status,
        "performance": router.get_performance_summary(),
        "config": router.routing_config,
    }


@app.post("/proxy")
async def proxy_request(request: ProxyRequest):
    """Proxy request to appropriate system"""
    system = router.select_system()
    result = await router.proxy_request(
        system=system,
        endpoint=request.endpoint,
        method=request.method,
        body=request.body,
        headers=request.headers,
    )

    return result


@app.post("/config")
async def update_routing_config(request: RoutingConfigRequest):
    """Update routing configuration"""
    router.routing_config.update(
        {
            "auto_scaling": request.auto_scaling,
            "performance_threshold": request.performance_threshold,
            "health_check_interval": request.health_check_interval,
        }
    )

    return {
        "status": "success",
        "config": router.routing_config,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/metrics")
async def get_metrics():
    """Get detailed metrics"""
    return {
        "timestamp": datetime.now().isoformat(),
        "traffic_split": router.traffic_split,
        "systems_health": router.health_status,
        "performance": router.get_performance_summary(),
        "config": router.routing_config,
        "performance_stats": router.performance_stats,
    }


@app.get("/")
async def root():
    """Router information"""
    return {
        "name": "OpenViking Traffic Router",
        "version": "1.0.0",
        "description": "Smart load balancer for gradual SMP to OpenViking migration",
        "endpoints": {
            "health": "/health - Router health check",
            "traffic/split": "POST /traffic/split - Set traffic split",
            "traffic/status": "/traffic/status - Get routing status",
            "proxy": "POST /proxy - Proxy requests",
            "config": "POST /config - Update configuration",
            "metrics": "/metrics - Detailed metrics",
            "/": "Router information",
        },
        "current_status": {
            "traffic_split": router.traffic_split,
            "systems_health": router.health_status,
        },
    }


# Background task for health checks
async def health_check_loop():
    """Background health check loop"""
    while True:
        await router.check_all_health()
        await asyncio.sleep(router.routing_config["health_check_interval"])


if __name__ == "__main__":
    import os

    port = int(os.getenv("ROUTER_PORT", "8003"))

    print(f"🚀 Starting OpenViking Traffic Router on port {port}")
    print("🔧 Features:")
    print("   • Smart traffic routing between SMP and OpenViking")
    print("   • Health monitoring and automatic failover")
    print("   • Performance tracking and optimization")
    print("   • Gradual rollout support")
    print("\n📊 Current Configuration:")
    print(f"   • SMP: {router.smp_url}")
    print(f"   • OpenViking: {router.openviking_url}")
    print(
        f"   • Traffic Split: SMP={router.traffic_split['smp']}%, OpenViking={router.traffic_split['openviking']}%"
    )

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
