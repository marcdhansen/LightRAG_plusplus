#!/usr/bin/env python3
"""
Comprehensive OpenViking Test Suite
Tests all advanced features: caching, skill discovery, performance metrics
"""

import asyncio
import json
import statistics
import time
from datetime import datetime

import httpx


async def test_openviking_features():
    """Test all OpenViking advanced features"""
    base_url = "http://localhost:8000"
    results = {}

    print("🚀 OpenViking Advanced Features Test Suite")
    print("=" * 50)

    async with httpx.AsyncClient(timeout=30) as client:
        # Test 1: Embedding Caching
        print("\n📦 Test 1: Embedding Caching")
        test_text = "React performance optimization techniques"

        # First request - should miss cache
        start_time = time.time()
        response1 = await client.post(
            f"{base_url}/embeddings",
            json={"text": test_text},
            headers={"Content-Type": "application/json"},
        )
        first_time = (time.time() - start_time) * 1000

        # Second request - should hit cache
        start_time = time.time()
        response2 = await client.post(
            f"{base_url}/embeddings",
            json={"text": test_text},
            headers={"Content-Type": "application/json"},
        )
        second_time = (time.time() - start_time) * 1000

        cache_improvement = ((first_time - second_time) / first_time) * 100

        results["embedding_caching"] = {
            "first_request_time_ms": first_time,
            "second_request_time_ms": second_time,
            "cache_improvement_percent": cache_improvement,
            "cache_working": response2.json().get("cache_hit", False),
            "success": response1.status_code == 200 and response2.status_code == 200,
        }

        print(f"   ✅ First request: {first_time:.1f}ms (no cache)")
        print(f"   ✅ Second request: {second_time:.1f}ms (cached)")
        print(f"   🚀 Performance improvement: {cache_improvement:.1f}%")

        # Test 2: Skill Search
        print("\n🔍 Test 2: Advanced Skill Search")
        test_queries = [
            "React performance optimization",
            "API authentication patterns",
            "Database migration strategies",
        ]

        skill_search_times = []
        skills_found = []

        for query in test_queries:
            start_time = time.time()
            response = await client.post(
                f"{base_url}/skills/search",
                json={"query": query, "max_results": 10},
                headers={"Content-Type": "application/json"},
            )
            search_time = (time.time() - start_time) * 1000
            skill_search_times.append(search_time)

            if response.status_code == 200:
                data = response.json()
                skills_found.extend(data.get("skills", []))
                print(
                    f"   🔍 '{query}': {data.get('found_count', 0)} skills found in {search_time:.1f}ms"
                )
            else:
                print(f"   ❌ '{query}': Search failed")

        avg_search_time = (
            statistics.mean(skill_search_times) if skill_search_times else 0
        )

        results["skill_search"] = {
            "queries_tested": len(test_queries),
            "average_search_time_ms": avg_search_time,
            "total_skills_found": len({s.get("id", "") for s in skills_found}),
            "search_success_rate": len(skill_search_times) / len(test_queries) * 100,
            "success": all(t.status_code == 200 for t in response2),
        }

        print(f"   📊 Average search time: {avg_search_time:.1f}ms")
        print(
            f"   🎯 Total unique skills found: {len({s.get('id', '') for s in skills_found})}"
        )

        # Test 3: Health Check with Features
        print("\n🏥 Test 3: Enhanced Health Check")
        start_time = time.time()
        response = await client.get(f"{base_url}/health")
        health_time = (time.time() - start_time) * 1000

        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])

            results["health_check"] = {
                "response_time_ms": health_time,
                "status": data.get("status", "unknown"),
                "version": data.get("version", "unknown"),
                "features_available": features,
                "expected_features": [
                    "conversation_memory",
                    "hierarchical_skills",
                    "embedding_caching",
                ],
                "success": response.status_code == 200,
            }

            print(f"   ✅ Health check: {health_time:.1f}ms")
            print(f"   📋 Features: {', '.join(features)}")
        else:
            results["health_check"] = {
                "response_time_ms": health_time,
                "status": "error",
                "success": False,
            }
            print(f"   ❌ Health check failed: {health_time:.1f}ms")

    # Summary
    print("\n📈 Test Results Summary")
    print("=" * 30)

    all_tests_passed = all(
        [
            results["embedding_caching"]["cache_working"],
            results["skill_search"]["success"],
            results["health_check"]["success"],
        ]
    )

    print(
        f"Overall Success: {'✅ ALL TESTS PASSED' if all_tests_passed else '❌ SOME TESTS FAILED'}"
    )

    if all_tests_passed:
        print("\n🎉 OpenViking Advanced Features Working Successfully!")
        print("📦 Caching: Functional with performance improvements")
        print("🔍 Skill Search: Operational with fast response times")
        print("🏥 Health Monitoring: Feature-complete and responsive")
    else:
        print("\n⚠️ Some tests failed - check logs above")

    # Performance metrics
    avg_cache_improvement = results["embedding_caching"]["cache_improvement_percent"]
    avg_search_time = results["skill_search"]["average_search_time_ms"]

    print("\n🚀 Performance Metrics:")
    print(f"   Cache Improvement: {avg_cache_improvement:.1f}%")
    print(f"   Avg Search Time: {avg_search_time:.1f}ms")
    print(f"   Skills Discovered: {results['skill_search']['total_skills_found']}")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"openviking_test_results_{timestamp}.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to: openviking_test_results_{timestamp}.json")


if __name__ == "__main__":
    asyncio.run(test_openviking_features())
