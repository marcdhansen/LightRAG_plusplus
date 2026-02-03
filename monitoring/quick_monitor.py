#!/usr/bin/env python3
"""
Simple OpenViking Health Monitor
Lightweight monitoring for production deployment
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any

import httpx


class SimpleMonitor:
    def __init__(self, openviking_url: str = "http://localhost:8002"):
        self.openviking_url = openviking_url
        self.start_time = datetime.now()

    async def check_health(self) -> dict[str, Any]:
        """Check system health"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.openviking_url}/health", timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "healthy",
                        "timestamp": data.get("timestamp"),
                        "version": data.get("version"),
                        "features": data.get("features", []),
                        "response_time_ms": response.elapsed.total_seconds() * 1000,
                    }
                else:
                    return {"status": "error", "code": response.status_code}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def test_endpoints(self) -> dict[str, Any]:
        """Test key endpoints"""
        endpoints = {
            "embeddings": {"method": "POST", "payload": {"text": "test query"}},
            "skills": {
                "method": "POST",
                "payload": {"query": "test", "max_results": 5},
            },
            "conversation": {
                "method": "POST",
                "payload": {
                    "session_id": f"test-{int(time.time())}",
                    "message": "test message",
                    "role": "user",
                },
            },
        }

        results = {}
        async with httpx.AsyncClient() as client:
            for name, config in endpoints.items():
                try:
                    start_time = time.time()
                    if config["method"] == "POST":
                        response = await client.post(
                            f"{self.openviking_url}/{name}"
                            if name != "embeddings"
                            else f"{self.openviking_url}/embeddings",
                            json=config["payload"],
                            timeout=10.0,
                        )
                    response_time = (time.time() - start_time) * 1000
                    results[name] = {
                        "success": 200 <= response.status_code < 400,
                        "response_time_ms": response_time,
                        "status_code": response.status_code,
                    }
                except Exception as e:
                    results[name] = {"success": False, "error": str(e)}

        return results

    async def get_metrics(self) -> dict[str, Any]:
        """Get performance metrics"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.openviking_url}/performance/metrics", timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception:
            pass
        return {}

    async def run_quick_check(self) -> dict[str, Any]:
        """Run a quick health and performance check"""
        health = await self.check_health()
        endpoints = await self.test_endpoints()
        metrics = await self.get_metrics()

        uptime = datetime.now() - self.start_time

        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime.total_seconds(),
            "health": health,
            "endpoints": endpoints,
            "metrics": metrics,
            "summary": {
                "overall_status": "healthy"
                if health.get("status") == "healthy"
                else "unhealthy",
                "endpasses_working": sum(
                    1 for e in endpoints.values() if e.get("success", False)
                ),
                "total_endpoints": len(endpoints),
                "avg_response_time": sum(
                    e.get("response_time_ms", 0)
                    for e in endpoints.values()
                    if e.get("success")
                )
                / len(endpoints)
                if endpoints
                else 0,
            },
        }


async def main():
    """Run a quick monitoring check"""
    monitor = SimpleMonitor()

    print("🚀 OpenViking Quick Health Monitor")
    print("=" * 40)

    try:
        result = await monitor.run_quick_check()

        print(f"📊 Timestamp: {result['timestamp']}")
        print(f"⏱️  Uptime: {result['uptime_seconds']:.1f}s")
        print(f"🏥 Health Status: {result['health'].get('status', 'unknown')}")
        print(f"📈 Overall Status: {result['summary']['overall_status']}")

        print(
            f"\n🚀 Endpoints: {result['summary']['endpasses_working']}/{result['summary']['total_endpoints']} working"
        )
        for endpoint, data in result["endpoints"].items():
            status = "✅" if data.get("success") else "❌"
            response_time = data.get("response_time_ms", 0)
            print(f"  {status} {endpoint}: {response_time:.1f}ms")

        if result.get("metrics", {}).get("summary"):
            summary = result["metrics"]["summary"]
            print("\n📋 System Metrics:")
            print(f"  Total Requests: {summary.get('total_requests', 0):,}")
            print(f"  Active Sessions: {summary.get('active_sessions', 0):,}")
            print(f"  Cache Size: {summary.get('cache_size', 0):,}")

        # Save result
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"quick_monitor_check_{timestamp}.json", "w") as f:
            json.dump(result, f, indent=2)

        print(f"\n✅ Results saved to: quick_monitor_check_{timestamp}.json")

        return 0 if result["summary"]["overall_status"] == "healthy" else 1

    except Exception as e:
        print(f"❌ Monitor failed: {e}")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(asyncio.run(main()))
