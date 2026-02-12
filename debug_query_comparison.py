#!/usr/bin/env python3
"""
Query Comparison Tool for Debugging /query vs /query/data

This script helps identify where context passing fails by running the same query
through both endpoints and comparing the complete flow.

Usage:
    python debug_query_comparison.py "Who is researcher?"
"""

import asyncio
import json
import sys
import argparse
from typing import Dict, Any, Optional
import httpx
from pathlib import Path

# Add lightrag to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lightrag.utils import set_verbose_debug, VERBOSE_DEBUG


class QueryComparator:
    """Compare /query vs /query/data endpoint behavior"""

    def __init__(self, base_url: str = "http://localhost:9621"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def test_query_endpoint(
        self, query: str, mode: str = "naive"
    ) -> Dict[str, Any]:
        """Test the /query endpoint"""
        print(f"\n🔍 Testing /query endpoint with: '{query}'")

        try:
            response = await self.client.post(
                f"{self.base_url}/query", json={"query": query, "mode": mode}
            )
            response.raise_for_status()
            result = response.json()

            print(f"✅ /query Response Status: {result.get('success', 'unknown')}")
            print(f"📝 /query Content Length: {len(result.get('response', ''))} chars")
            print(f"📄 /query Response Preview: {result.get('response', '')[:200]}...")

            return result

        except Exception as e:
            print(f"❌ /query Error: {e}")
            return {"error": str(e), "endpoint": "/query"}

    async def test_query_data_endpoint(
        self, query: str, mode: str = "naive"
    ) -> Dict[str, Any]:
        """Test the /query/data endpoint"""
        print(f"\n🔍 Testing /query/data endpoint with: '{query}'")

        try:
            response = await self.client.post(
                f"{self.base_url}/query/data", json={"query": query, "mode": mode}
            )
            response.raise_for_status()
            result = response.json()

            print(
                f"✅ /query/data Response Status: {result.get('data', {}).get('status', 'unknown')}"
            )

            # Analyze context data
            data = result.get("data", {})
            entities = data.get("entities", [])
            relations = data.get("relations", [])
            chunks = data.get("chunks", [])

            print(f"📊 Context Statistics:")
            print(f"  • Entities: {len(entities)}")
            print(f"  • Relations: {len(relations)}")
            print(f"  • Chunks: {len(chunks)}")

            if chunks:
                print(
                    f"📄 Sample Chunk Content: {chunks[0].get('content', '')[:150]}..."
                )

            return result

        except Exception as e:
            print(f"❌ /query/data Error: {e}")
            return {"error": str(e), "endpoint": "/query/data"}

    def analyze_comparison(self, query_result: Dict, data_result: Dict, query: str):
        """Analyze differences between the two endpoints"""
        print(f"\n📊 Comparison Analysis for: '{query}'")
        print("=" * 60)

        # Check for errors
        if "error" in query_result:
            print(f"❌ /query endpoint failed: {query_result['error']}")
            return

        if "error" in data_result:
            print(f"❌ /query/data endpoint failed: {data_result['error']}")
            return

        # Compare context availability
        data = data_result.get("data", {})
        context_status = data.get("status", "unknown")

        print(f"📋 Context Status from /query/data: {context_status}")

        if context_status == "failure":
            failure_reason = data.get("message", "Unknown reason")
            print(f"⚠️  Context Retrieval Failure: {failure_reason}")

            # This explains why /query has no context!
            print("\n💡 DIAGNOSIS: /query/data shows empty context retrieval")
            print("   This means the LLM in /query receives no context to work with")
            print(
                "   The generic response indicates the LLM is working, but context is missing"
            )
            return

        # Analyze content richness
        query_content = query_result.get("response", "")
        entities_count = len(data.get("entities", []))
        relations_count = len(data.get("relations", []))
        chunks_count = len(data.get("chunks", []))

        print(f"\n📈 Content Analysis:")
        print(f"  • /query Response Length: {len(query_content)} chars")
        print(f"  • Retrieved Entities: {entities_count}")
        print(f"  • Retrieved Relations: {relations_count}")
        print(f"  • Retrieved Chunks: {chunks_count}")

        # Check for generic responses
        generic_indicators = [
            "I don't have",
            "I don't know",
            "I don't have information",
            "I'm not sure",
            "I cannot",
            "no specific information",
        ]

        is_generic = any(
            indicator.lower() in query_content.lower()
            for indicator in generic_indicators
        )

        if is_generic and (entities_count > 0 or chunks_count > 0):
            print(f"\n⚠️  CRITICAL ISSUE: Generic response despite available context!")
            print(f"   • LLM received context but gave generic answer")
            print(f"   • This indicates a prompt construction or LLM binding issue")
            return

        if not is_generic and (entities_count == 0 and chunks_count == 0):
            print(f"\n🤔 Specific response but no context retrieved")
            print(f"   • LLM may be using general knowledge instead of RAG")
            return

        print(f"\n✅ Response appears appropriate for available context")


async def main():
    """Main debugging function"""
    parser = argparse.ArgumentParser(description="Compare LightRAG query endpoints")
    parser.add_argument("query", help="Query to test")
    parser.add_argument(
        "--url", default="http://localhost:9621", help="LightRAG server URL"
    )
    parser.add_argument("--mode", default="naive", help="Query mode")
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose debugging"
    )

    args = parser.parse_args()

    if args.verbose:
        set_verbose_debug(True)
        print("🔧 Verbose debugging enabled")

    # Test server availability
    print(f"🌐 Connecting to LightRAG server: {args.url}")

    comparator = QueryComparator(args.url)

    try:
        # Test both endpoints
        data_result = await comparator.test_query_data_endpoint(args.query, args.mode)
        query_result = await comparator.test_query_endpoint(args.query, args.mode)

        # Analyze the comparison
        comparator.analyze_comparison(query_result, data_result, args.query)

    except KeyboardInterrupt:
        print("\n⚠️  Debugging interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    finally:
        await comparator.close()

    print(f"\n🏁 Query comparison complete")


if __name__ == "__main__":
    asyncio.run(main())
