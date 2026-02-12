#!/usr/bin/env python3
"""
Test with Existing Entities for Issue #2643 Analysis

Uses existing "Alex" and "Taylor" entities to test context passing
"""

import json
import sys
import asyncio
import httpx
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add lightrag to path for imports
sys.path.insert(0, str(Path(__file__).parent))


async def test_existing_entities():
    """Test queries about existing entities Alex and Taylor"""
    base_url = "http://localhost:9621"

    # Test queries about existing entities
    test_queries = [
        "What does Alex do?",
        "Tell me about Taylor",
        "Alex and Taylor",
        "Who is Taylor?",
        "What is Alex known for?",
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
            response_data = query_result["response"]
            response_text = response_data.get("response", str(response_data))
            response_length = len(response_text)
            has_context = len(response_text) > 100  # Longer than minimal response
            contains_name = any(
                name.lower() in response_text.lower() for name in ["alex", "taylor"]
            )

            print(f"   Response length: {response_length}")
            print(f"   Has substantial content: {has_context}")
            print(f"   Contains entity name: {contains_name}")
            print(f"   Response: {response_text[:150]}...")
        else:
            print(f"   Error: {query_result.get('error', 'Unknown')}")

        print(f"📊 /query/data endpoint: {'✅' if data_result['success'] else '❌'}")
        if data_result["success"]:
            data_response = data_result["response"]
            context_chunks = len(data_response.get("context_chunks", []))
            entities = len(data_response.get("entities", []))
            relationships = len(data_response.get("relationships", []))

            print(f"   Context chunks: {context_chunks}")
            print(f"   Entities: {entities}")
            print(f"   Relationships: {relationships}")
        else:
            print(f"   Error: {data_result.get('error', 'Unknown')}")

        # Check for issue pattern
        issue_detected = False
        issue_type = None

        if query_result["success"] and data_result["success"]:
            # Both endpoints work - check for quality differences
            response_data = query_result["response"]
            response_text = response_data.get("response", str(response_data))
            data_response = data_result["response"]

            has_rich_data = len(data_response.get("context_chunks", [])) > 0
            has_poor_response = (
                len(response_text) < 150
                or "no relevant context" in response_text.lower()
            )

            if has_rich_data and has_poor_response:
                issue_detected = True
                issue_type = "quality_difference"
                print(
                    "🚨 ISSUE DETECTED: /query gives poor response, /query/data has rich data!"
                )

        elif not query_result["success"] and data_result["success"]:
            issue_detected = True
            issue_type = "endpoint_failure"
            print("🚨 ISSUE DETECTED: /query failing, /query/data working!")

        elif query_result["success"] and not data_result["success"]:
            issue_detected = True
            issue_type = "data_endpoint_failure"
            print("🟡 UNUSUAL: /query working, /query/data failing")

        results[query] = {
            "query_result": query_result,
            "data_result": data_result,
            "issue_detected": issue_detected,
            "issue_type": issue_type,
        }

    return results


async def analyze_token_usage():
    """Analyze token usage patterns"""
    print(f"\n💰 Token Usage Analysis")
    print("=" * 50)

    # Check configuration
    with open(".env", "r") as f:
        env_content = f.read()

    model = None
    context_window = None

    for line in env_content.split("\n"):
        if line.startswith("LLM_MODEL="):
            model = line.split("=", 1)[1]
        elif "8192" in line:  # Looking for context window info
            context_window = 8192

    print(f"Model: {model}")
    print(f"Context Window: {context_window}")

    if "qwen2.5" in model.lower() and context_window == 8192:
        print("🔍 POTENTIAL ISSUE: qwen2.5 with 8K context window")
        print("   This could lead to token budget issues with large contexts")
        print("   Especially problematic with entity-heavy queries")
        return True

    return False


async def create_minimal_test():
    """Create minimal test by directly inserting into storage"""
    print(f"\n🧪 Creating Direct Storage Test")
    print("=" * 50)

    # Read current text chunks
    with open("rag_storage/kv_store_text_chunks.json", "r") as f:
        chunks = json.load(f)

    # Find a chunk to modify
    if chunks:
        chunk_id = list(chunks.keys())[0]
        original_chunk = chunks[chunk_id]

        # Add Alice Anderson content to existing chunk
        if isinstance(original_chunk, dict):
            original_content = original_chunk.get("content", "")
            new_content = (
                original_content
                + "\n\nDr. Alice Anderson is a prominent researcher specializing in artificial intelligence and machine learning. She has made significant contributions to natural language processing. The researcher leads a team at Stanford University."
            )

            # Update the chunk
            chunks[chunk_id]["content"] = new_content

            # Write back to storage
            with open("rag_storage/kv_store_text_chunks.json", "w") as f:
                json.dump(chunks, f, indent=2)

            print(f"✅ Added Alice Anderson content to chunk {chunk_id}")
            print(f"   Original length: {len(original_content)}")
            print(f"   New length: {len(new_content)}")

            return True

    return False


async def test_after_modification():
    """Test queries after direct storage modification"""
    print(f"\n🧪 Testing After Storage Modification")
    print("=" * 50)

    base_url = "http://localhost:9621"

    # Test queries about Alice Anderson
    test_queries = [
        "What is Alice Anderson known for?",
        "Tell me about the researcher Alice Anderson",
        "Alice Anderson research",
    ]

    for query in test_queries:
        print(f"\n🔍 Testing: {query}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {"query": query, "mode": "local"}
                response = await client.post(
                    f"{base_url}/query",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", str(result))

                    print(f"   ✅ Response length: {len(response_text)}")
                    print(f"   Contains 'Alice': {'alice' in response_text.lower()}")
                    print(
                        f"   Contains 'researcher': {'researcher' in response_text.lower()}"
                    )
                    print(f"   Response: {response_text[:200]}...")

                    # Check for minimal response issue
                    if (
                        len(response_text) < 150
                        or "no relevant context" in response_text.lower()
                    ):
                        print(
                            "   🚨 POTENTIAL ISSUE: Minimal response despite having data!"
                        )
                else:
                    print(f"   ❌ Error: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Exception: {e}")


async def main():
    """Main testing function"""
    print("🎯 LightRAG Issue #2643 - Entity-Based Testing")
    print("=" * 60)

    # Step 1: Test existing entities
    print("Step 1: Testing existing entities (Alex, Taylor)")
    results = await test_existing_entities()

    # Step 2: Analyze token usage
    print("\nStep 2: Analyzing token configuration")
    token_issue = await analyze_token_usage()

    # Step 3: Create direct storage test
    print("\nStep 3: Creating direct storage test")
    modification_success = await create_minimal_test()

    # Step 4: Test after modification
    if modification_success:
        print("\nStep 4: Testing after storage modification")
        await test_after_modification()

    # Step 5: Generate summary
    print(f"\n📋 FINAL ANALYSIS SUMMARY")
    print("=" * 50)

    total_queries = len(results)
    quality_issues = sum(
        1 for r in results.values() if r.get("issue_type") == "quality_difference"
    )
    endpoint_failures = sum(
        1 for r in results.values() if r.get("issue_type") == "endpoint_failure"
    )

    print(f"Total queries tested: {total_queries}")
    print(f"Quality difference issues: {quality_issues}")
    print(f"Endpoint failure issues: {endpoint_failures}")
    print(f"Token configuration issue: {token_issue}")
    print(f"Direct modification test: {'✅' if modification_success else '❌'}")

    # Root cause analysis
    print(f"\n🎯 ROOT CAUSE ANALYSIS:")
    if token_issue:
        print("🔴 PRIMARY SUSPECT: Token budget issues")
        print("   qwen2.5 model with 8K context window")
        print("   Entity-heavy queries may exceed token limits")
        print("   Causing empty/minimal responses from LLM")

    if quality_issues > 0:
        print("🔴 CONFIRMED: Context passing quality issues")
        print("   /query/data retrieves rich context")
        print("   /query endpoint gives poor responses")
        print("   Issue is in LLM prompt construction or token management")

    if endpoint_failures > 0:
        print("🔴 CONFIRMED: Endpoint failure pattern")
        print("   This matches GitHub Issue #2643 exactly")

    # Save results
    final_results = {
        "entity_test_results": results,
        "token_analysis": {
            "has_token_issue": token_issue,
            "model": "qwen2.5-coder:1.5b",
            "context_window": 8192,
        },
        "modification_test": {"success": modification_success},
    }

    with open("entity_test_results.json", "w") as f:
        json.dump(final_results, f, indent=2)

    print(f"\n💾 Results saved to entity_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
