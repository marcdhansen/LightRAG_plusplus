#!/usr/bin/env python3
"""
Direct Query Testing for Issue #2643

Tests the existing data to reproduce the /query vs /query/data issue
"""

import json
import sys
import asyncio
import httpx
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add lightrag to path for imports
sys.path.insert(0, str(Path(__file__).parent))


async def test_query_endpoints():
    """Test both query endpoints with existing data"""
    base_url = "http://localhost:9621"

    # Test queries that should trigger the context issue
    test_queries = [
        "What is Alice Anderson known for?",
        "Tell me about Alice Anderson",
        "Alice Anderson researcher",
        "What research does Alice Anderson do?",
    ]

    results = {}

    for query in test_queries:
        print(f"\n🔍 Testing query: {query}")
        print("-" * 50)

        # Test /query endpoint
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {"query": query, "mode": "local"}
                response = await client.post(
                    f"{base_url}/query",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                query_result = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response": response.json()
                    if response.status_code == 200
                    else response.text,
                }

        except Exception as e:
            query_result = {"success": False, "error": str(e)}

        # Test /query/data endpoint
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {"query": query}
                response = await client.post(
                    f"{base_url}/query/data",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                data_result = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response": response.json()
                    if response.status_code == 200
                    else response.text,
                }

        except Exception as e:
            data_result = {"success": False, "error": str(e)}

        # Analyze results
        print(f"📊 /query endpoint: {'✅' if query_result['success'] else '❌'}")
        if query_result["success"]:
            response_text = str(query_result["response"])[:200]
            print(f"   Response: {response_text}...")
        else:
            print(f"   Error: {query_result.get('error', 'Unknown')}")

        print(f"📊 /query/data endpoint: {'✅' if data_result['success'] else '❌'}")
        if data_result["success"]:
            data_response = data_result["response"]
            print(f"   Context chunks: {len(data_response.get('context_chunks', []))}")
            print(f"   Entities: {len(data_response.get('entities', []))}")
            print(f"   Relationships: {len(data_response.get('relationships', []))}")
        else:
            print(f"   Error: {data_result.get('error', 'Unknown')}")

        # Check for the issue pattern
        issue_detected = False
        if not query_result["success"] and data_result["success"]:
            issue_detected = True
            print("🚨 ISSUE DETECTED: /query failing, /query/data working!")

        if query_result["success"] and data_result["success"]:
            # Check if query response lacks context that data endpoint has
            query_text = str(query_result["response"]).lower()
            data_has_context = len(data_response.get("context_chunks", [])) > 0

            if data_has_context and len(query_text) < 100:  # Very short response
                issue_detected = True
                print(
                    "🚨 ISSUE DETECTED: /query giving minimal response, /query/data has rich context!"
                )

        results[query] = {
            "query_result": query_result,
            "data_result": data_result,
            "issue_detected": issue_detected,
        }

    return results


async def test_cosine_thresholds():
    """Test different cosine thresholds to see impact"""
    base_url = "http://localhost:9621"
    query = "What is Alice Anderson known for?"
    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]

    print(f"\n🎯 Testing cosine threshold impact")
    print("=" * 50)

    for threshold in thresholds:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "query": query,
                    "mode": "local",
                    "cosine_threshold": threshold,
                }
                response = await client.post(
                    f"{base_url}/query",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    result = response.json()
                    response_length = len(str(result))
                    contains_alice = "alice" in str(result).lower()
                    contains_researcher = "researcher" in str(result).lower()

                    print(
                        f"Threshold {threshold}: ✅ (Length: {response_length}, Alice: {contains_alice}, Researcher: {contains_researcher})"
                    )
                else:
                    print(f"Threshold {threshold}: ❌ ({response.status_code})")

        except Exception as e:
            print(f"Threshold {threshold}: ❌ (Error: {str(e)[:50]})")


async def analyze_existing_data():
    """Analyze the existing stored data for relevant entities"""
    print(f"\n📊 Analyzing existing stored data")
    print("=" * 50)

    # Check stored entities
    try:
        with open("rag_storage/kv_store_full_entities.json", "r") as f:
            entities = json.load(f)

        alice_entities = []
        researcher_entities = []

        for entity_id, entity_data in entities.items():
            if isinstance(entity_data, dict):
                entity_name = entity_data.get("entity_name", "")
                if "alice" in entity_name.lower():
                    alice_entities.append(entity_name)
                if "researcher" in entity_name.lower():
                    researcher_entities.append(entity_name)

        print(f"📋 Total entities: {len(entities)}")
        print(f"👤 Alice-related entities: {alice_entities}")
        print(f"🔬 Researcher-related entities: {researcher_entities}")

    except Exception as e:
        print(f"❌ Error analyzing entities: {e}")

    # Check text chunks
    try:
        with open("rag_storage/kv_store_text_chunks.json", "r") as f:
            chunks = json.load(f)

        alice_chunks = 0
        researcher_chunks = 0

        for chunk_id, chunk_data in chunks.items():
            if isinstance(chunk_data, dict):
                chunk_text = chunk_data.get("content", "")
                if "alice" in chunk_text.lower():
                    alice_chunks += 1
                if "researcher" in chunk_text.lower():
                    researcher_chunks += 1

        print(f"📄 Total text chunks: {len(chunks)}")
        print(f"👤 Alice-related chunks: {alice_chunks}")
        print(f"🔬 Researcher-related chunks: {researcher_chunks}")

    except Exception as e:
        print(f"❌ Error analyzing chunks: {e}")


async def main():
    """Main testing function"""
    print("🎯 LightRAG Issue #2643 - Direct Query Testing")
    print("=" * 60)

    # Step 1: Analyze existing data
    await analyze_existing_data()

    # Step 2: Test query endpoints
    results = await test_query_endpoints()

    # Step 3: Test cosine thresholds
    await test_cosine_thresholds()

    # Step 4: Generate summary
    print(f"\n📋 SUMMARY REPORT")
    print("=" * 40)

    total_queries = len(results)
    issues_detected = sum(1 for r in results.values() if r.get("issue_detected", False))

    print(f"Total queries tested: {total_queries}")
    print(f"Issues detected: {issues_detected}")

    if issues_detected > 0:
        print("🚨 ISSUE #2643 CONFIRMED!")
        print("   Pattern: /query endpoint failing while /query/data works")

        # Show which queries triggered the issue
        problem_queries = [
            q for q, r in results.items() if r.get("issue_detected", False)
        ]
        print(f"   Problem queries: {problem_queries}")
    else:
        print("✅ No issues detected with current configuration")

    # Save results
    with open("query_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to query_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
