#!/usr/bin/env python3
"""
Targeted Analysis for Issue #2643 - User Scenario Testing

This script creates the exact scenario from the GitHub issue:
1. Ingests a document about "Alice Anderson, a researcher"
2. Tests query for "What is Alice Anderson known for?"
3. Analyzes why /query/data works but /query fails
"""

import json
import sys
import asyncio
import httpx
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add lightrag to path for imports
sys.path.insert(0, str(Path(__file__).parent))


async def create_test_document():
    """Create the exact test document from the GitHub issue"""
    content = """Alice Anderson Research Profile

Dr. Alice Anderson is a prominent researcher specializing in artificial intelligence 
and machine learning. She has made significant contributions to natural language 
processing and computer vision. Dr. Anderson leads a research team at Stanford 
University focusing on advanced neural networks and deep learning architectures.

Her research interests include:
- Large language models and their applications
- Ethical AI development and deployment
- Multi-modal learning systems
- Transfer learning in neural networks

Dr. Anderson has published numerous papers in top-tier conferences including 
NeurIPS, ICML, and ICLR. She is also a frequent collaborator with other leading 
researchers in the field of AI safety and alignment.

The researcher has received several awards for her contributions to the field, 
including the prestigious Turing Fellowship. Her work on attention mechanisms 
and transformer architectures has been widely cited and implemented in various 
commercial applications.

Key accomplishments:
- Developed novel attention mechanisms for transformers
- Created efficient training methods for large models
- Published over 50 peer-reviewed papers
- Mentored 12 PhD students who are now successful researchers

Alice Anderson continues to push the boundaries of what's possible in artificial 
intelligence, making her one of the most influential researchers in the field today.
"""

    with open("test_researcher_document.txt", "w") as f:
        f.write(content)

    print("✅ Created test document: test_researcher_document.txt")
    return "test_researcher_document.txt"


async def test_endpoint_with_server(
    url: str, endpoint: str, query: str
) -> Dict[str, Any]:
    """Test a specific endpoint with the given query"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {"query": query}

            # Add parameters based on endpoint type
            if endpoint == "/query":
                payload["mode"] = "local"

            response = await client.post(
                f"{url}{endpoint}",
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response": result,
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text,
                }

    except Exception as e:
        return {"success": False, "error": str(e)}


async def analyze_query_differences(
    query_result: Dict[str, Any], data_result: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze differences between /query and /query/data responses"""
    analysis = {
        "query_analysis": {},
        "data_analysis": {},
        "differences": {},
        "context_analysis": {},
    }

    # Analyze /query response
    if query_result.get("success"):
        query_response = query_result["response"]
        analysis["query_analysis"] = {
            "has_response": True,
            "response_length": len(str(query_response)),
            "contains_context": "context" in str(query_response).lower(),
            "contains_researcher": "researcher" in str(query_response).lower(),
            "contains_alice": "alice" in str(query_response).lower(),
        }
    else:
        analysis["query_analysis"] = {
            "has_response": False,
            "error": query_result.get("error", "Unknown error"),
        }

    # Analyze /query/data response
    if data_result.get("success"):
        data_response = data_result["response"]
        analysis["data_analysis"] = {
            "has_response": True,
            "response_length": len(str(data_response)),
            "context_chunks": len(data_response.get("context_chunks", [])),
            "entities": len(data_response.get("entities", [])),
            "relationships": len(data_response.get("relationships", [])),
            "data_types": list(data_response.keys()),
        }
    else:
        analysis["data_analysis"] = {
            "has_response": False,
            "error": data_result.get("error", "Unknown error"),
        }

    # Compare key differences
    if query_result.get("success") and data_result.get("success"):
        query_str = str(query_response).lower()
        data_str = str(data_response).lower()

        analysis["differences"] = {
            "query_has_researcher": "researcher" in query_str,
            "query_has_alice": "alice" in query_str,
            "data_has_researcher": "researcher" in data_str,
            "data_has_alice": "alice" in data_str,
            "query_contains_context_details": "stanford" in query_str
            or "neural" in query_str,
            "data_contains_context_details": "stanford" in data_str
            or "neural" in data_str,
        }

    return analysis


async def test_cosine_thresholds(url: str, query: str) -> Dict[str, Any]:
    """Test different cosine threshold values"""
    thresholds = [0.1, 0.3, 0.4, 0.5, 0.7]
    results = {}

    for threshold in thresholds:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "query": query,
                    "mode": "local",
                    "cosine_threshold": threshold,
                }

                response = await client.post(
                    f"{url}/query",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    result = response.json()
                    results[str(threshold)] = {
                        "success": True,
                        "response_length": len(str(result)),
                        "contains_researcher": "researcher" in str(result).lower(),
                        "contains_alice": "alice" in str(result).lower(),
                    }
                else:
                    results[str(threshold)] = {
                        "success": False,
                        "error": response.text[:200],  # Truncate error messages
                    }

        except Exception as e:
            results[str(threshold)] = {"success": False, "error": str(e)}

    return results


async def main():
    """Main analysis function"""
    print("🎯 LightRAG Issue #2643 - Targeted User Scenario Analysis")
    print("=" * 70)

    # Configuration
    base_url = "http://localhost:9621"
    test_query = "What is Alice Anderson known for?"

    # Step 1: Create test document
    print("📝 Step 1: Creating test document...")
    test_doc = await create_test_document()

    # Step 2: Ingest document (server running)
    print("\n📥 Step 2: Ingesting test document...")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(test_doc, "rb") as f:
                files = {"file": (test_doc, f, "text/plain")}
                response = await client.post(f"{base_url}/upload", files=files)

            if response.status_code == 200:
                print("   ✅ Document ingested successfully")
            else:
                print(f"   ❌ Document ingestion failed: {response.text}")
                return
    except Exception as e:
        print(f"   ❌ Cannot ingest document - server may not be running: {e}")
        print("   💡 Please start LightRAG server on port 9621 and try again")
        return

    # Wait a moment for processing
    print("   ⏳ Waiting for document processing...")
    await asyncio.sleep(5)

    # Step 3: Test /query endpoint
    print(f"\n🔍 Step 3: Testing /query endpoint...")
    print(f"   Query: {test_query}")
    query_result = await test_endpoint_with_server(base_url, "/query", test_query)

    if query_result["success"]:
        print("   ✅ /query endpoint responded successfully")
        response_text = str(query_result["response"])[:300]
        print(f"   Response preview: {response_text}...")
    else:
        print(
            f"   ❌ /query endpoint failed: {query_result.get('error', 'Unknown error')}"
        )

    # Step 4: Test /query/data endpoint
    print(f"\n📊 Step 4: Testing /query/data endpoint...")
    data_result = await test_endpoint_with_server(base_url, "/query/data", test_query)

    if data_result["success"]:
        print("   ✅ /query/data endpoint responded successfully")
        data_response = data_result["response"]
        print(f"   Context chunks: {len(data_response.get('context_chunks', []))}")
        print(f"   Entities: {len(data_response.get('entities', []))}")
        print(f"   Relationships: {len(data_response.get('relationships', []))}")
    else:
        print(
            f"   ❌ /query/data endpoint failed: {data_result.get('error', 'Unknown error')}"
        )

    # Step 5: Analyze differences
    print(f"\n🔬 Step 5: Analyzing response differences...")
    analysis = await analyze_query_differences(query_result, data_result)

    print("   📋 Analysis Results:")
    for key, value in analysis.items():
        print(f"   {key}: {value}")

    # Step 6: Test cosine thresholds (if query failed)
    if not query_result["success"] and data_result["success"]:
        print(f"\n🎯 Step 6: Testing cosine threshold impact...")
        threshold_results = await test_cosine_thresholds(base_url, test_query)

        print("   📊 Threshold Test Results:")
        for threshold, result in threshold_results.items():
            status = "✅" if result["success"] else "❌"
            print(f"   Threshold {threshold}: {status}")
            if result["success"]:
                print(
                    f"      Contains 'researcher': {result.get('contains_researcher', False)}"
                )
                print(f"      Contains 'alice': {result.get('contains_alice', False)}")

    # Step 7: Generate final report
    print(f"\n📄 FINAL ANALYSIS REPORT")
    print("=" * 40)

    if query_result["success"] and data_result["success"]:
        print("🟢 Both endpoints working - issue may be intermittent")
    elif not query_result["success"] and data_result["success"]:
        print("🔴 CONFIRMED: /query failing, /query/data working")
        print("   This matches the GitHub issue #2643 pattern")

        # Analyze likely cause
        if analysis["data_analysis"].get("context_chunks", 0) > 0:
            print("   📊 Data is being retrieved successfully")
            print(
                "   🔍 Issue is likely in the LLM prompt construction or token management"
            )

        if analysis["differences"].get("data_has_researcher", False):
            print("   ✅ 'researcher' entity exists in data")
            print("   ❌ Context lost during LLM processing")

    elif query_result["success"] and not data_result["success"]:
        print("🟡 Unexpected: /query working, /query/data failing")
    else:
        print("🔴 Both endpoints failing - different issue")

    # Save detailed results
    final_results = {
        "query_result": query_result,
        "data_result": data_result,
        "analysis": analysis,
        "threshold_results": threshold_results
        if "threshold_results" in locals()
        else {},
        "test_query": test_query,
        "test_document": test_doc,
    }

    with open("targeted_analysis_results.json", "w") as f:
        json.dump(final_results, f, indent=2)

    print(f"\n💾 Detailed results saved to targeted_analysis_results.json")


if __name__ == "__main__":
    asyncio.run(main())
