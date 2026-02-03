#!/usr/bin/env python3
"""
Simple OpenViking Feature Demo
Demonstrates core functionality without complex syntax
"""

import asyncio
import httpx
import json
from datetime import datetime


async def demo_openviking():
    """Simple demonstration of OpenViking features"""
    base_url = "http://localhost:8000"

    print("🚀 OpenViking Feature Demonstration")
    print("=" * 40)

    async with httpx.AsyncClient(timeout=30) as client:
        # Test 1: Basic Health Check
        print("\n1️⃣ Health Check")
        response = await client.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data.get('status')}")
            print(f"   📋 Version: {data.get('version')}")
        else:
            print("   ❌ Health check failed")

        # Test 2: Embedding with Caching
        print("\n2️⃣ Embedding Caching")
        test_text = "React performance optimization"

        # First request
        response1 = await client.post(
            f"{base_url}/embeddings", json={"text": test_text}
        )
        cache_hit_1 = response1.json().get("cache_hit", False)
        print(f"   First request cache hit: {cache_hit_1}")

        # Second request (should hit cache)
        response2 = await client.post(
            f"{base_url}/embeddings", json={"text": test_text}
        )
        cache_hit_2 = response2.json().get("cache_hit", False)
        print(f"   Second request cache hit: {cache_hit_2}")

        caching_works = cache_hit_1 == False and cache_hit_2 == True
        print(f"   🚀 Caching working: {'✅ YES' if caching_works else '❌ NO'}")

        # Test 3: Skill Search
        print("\n3️⃣ Skill Search")
        response = await client.post(
            f"{base_url}/skills/search",
            json={"query": "React optimization", "max_results": 5},
        )
        if response.status_code == 200:
            data = response.json()
            skills_found = data.get("found_count", 0)
            print(f"   ✅ Skills found: {skills_found}")
        else:
            print("   ❌ Skill search failed")

        # Test 4: Features List
        print("\n4️⃣ Features Available")
        response = await client.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])
            print(f"   ✅ Features: {', '.join(features)}")
        else:
            print("   ❌ Features check failed")

        # Summary
        print("\n📊 Summary")
        all_good = (
            response.status_code == 200
            and caching_works
            and skills_found > 0
            and len(features) > 2
        )

        print(f"Overall Status: {'🎉 ALL GOOD' if all_good else '⚠️ SOME ISSUES'}")

        if all_good:
            print("✅ Health monitoring working")
            print("✅ Embedding caching functional")
            print("✅ Skill discovery operational")
            print("✅ Multiple features available")
            print("\n🎯 OpenViking Ready for Production!")
        else:
            print("⚠️ Some features need attention")


if __name__ == "__main__":
    asyncio.run(demo_openviking())
