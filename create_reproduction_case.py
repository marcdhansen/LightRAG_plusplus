#!/usr/bin/env python3
"""
Reproduction Case Creator for GitHub Issue #2643

This script creates the exact scenario described in the GitHub issue to help
reproduce and debug the context passing problem.

Usage:
    python create_reproduction_case.py [--ingest] [--test]
"""

import asyncio
import json
import sys
import argparse
from typing import Dict, Any
import httpx
from pathlib import Path

# Add lightrag to path for imports
sys.path.insert(0, str(Path(__file__).parent))


class ReproductionCaseManager:
    """Manage reproduction case for context passing issue"""

    def __init__(self, base_url: str = "http://localhost:9621"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def ingest_test_document(self) -> bool:
        """Ingest the test document from GitHub issue"""
        print("\n📝 Ingesting Test Document...")

        test_document = {
            "content": "Researcher: Mark, Date: January 18, 2026\n\nThis is a test document for debugging LightRAG context passing issues. The document contains specific information that should be retrievable through RAG queries.",
            "source": "test_document.txt",
            "metadata": {"type": "test", "purpose": "debug_issue_2643"},
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/documents", json=test_document
            )

            if response.status_code == 200:
                print("✅ Document ingested successfully")
                print(f"📄 Content: {test_document['content']}")

                # Wait for processing to complete
                print("⏳ Waiting for document processing...")
                await asyncio.sleep(3)
                return True
            else:
                print(f"❌ Document ingestion failed: {response.status_code}")
                if response.headers.get("content-type", "").startswith(
                    "application/json"
                ):
                    print(f"Error details: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Document ingestion error: {e}")
            return False

    async def test_query_data_endpoint(self) -> Dict[str, Any]:
        """Test /query/data endpoint to verify context retrieval"""
        print("\n🔍 Testing /query/data Endpoint...")

        query = "Who is researcher?"

        try:
            response = await self.client.post(
                f"{self.base_url}/query/data", json={"query": query, "mode": "naive"}
            )

            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})

                print("✅ /query/data Response:")
                print(f"📊 Status: {data.get('status', 'unknown')}")

                entities = data.get("entities", [])
                relations = data.get("relations", [])
                chunks = data.get("chunks", [])

                print(f"  • Entities: {len(entities)}")
                print(f"  • Relations: {len(relations)}")
                print(f"  • Chunks: {len(chunks)}")

                # Look for the expected content
                found_mark = False
                if chunks:
                    for i, chunk in enumerate(chunks):
                        if "Mark" in chunk.get("content", ""):
                            found_mark = True
                            print(
                                f"✅ Found 'Mark' in chunk {i + 1}: {chunk.get('content', '')[:100]}..."
                            )
                            break

                if not found_mark and chunks:
                    print("⚠️  'Mark' not found in any chunks")
                    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                        print(f"  Chunk {i + 1}: {chunk.get('content', '')}")

                return result
            else:
                print(f"❌ /query/data failed: {response.status_code}")
                return {}

        except Exception as e:
            print(f"❌ /query/data error: {e}")
            return {}

    async def test_query_endpoint(self) -> Dict[str, Any]:
        """Test /query endpoint to verify LLM gets context"""
        print("\n🔍 Testing /query Endpoint...")

        query = "Who is researcher?"

        try:
            response = await self.client.post(
                f"{self.base_url}/query", json={"query": query, "mode": "naive"}
            )

            if response.status_code == 200:
                result = response.json()

                print("✅ /query Response:")
                print(f"📝 Response Length: {len(result.get('response', ''))} chars")
                response_content = result.get("response", "")
                print(f"📄 Response Preview: {response_content[:300]}...")

                # Check if response indicates no context
                no_context_indicators = [
                    "I don't have specific information about which researcher you're referring to",
                    "I don't have information about which researcher",
                    "don't have specific information",
                    "don't have information about which researcher",
                    "no specific information about which researcher",
                    "I'm not sure which researcher you're referring to",
                ]

                response_lower = response_content.lower()
                found_no_context = any(
                    indicator.lower() in response_lower
                    for indicator in no_context_indicators
                )

                if found_no_context:
                    print("⚠️  LLM Response Indicates No Context!")
                    print(
                        "💡 This confirms the bug: LLM is not receiving retrieved context"
                    )
                    return result
                elif "Mark" in response_content:
                    print("✅ LLM Correctly Identified 'Mark' - Context Working!")
                    return result
                else:
                    print("⚠️  LLM Did Not Mention 'Mark' - Possible Context Issue")
                    return "could indicate context or prompt construction problem"

            else:
                print(f"❌ /query failed: {response.status_code}")
                return {}

        except Exception as e:
            print(f"❌ /query error: {e}")
            return {}

    async def test_direct_llm(self) -> Dict[str, Any]:
        """Test LLM directly with context to verify it can use it"""
        print("\n🧪 Testing Direct LLM Call...")

        # Simulate the test from GitHub issue
        test_context = "Researcher: Mark, Date: January 18, 2026"
        test_query = "Who is researcher?"

        try:
            response = await self.client.post(
                f"{self.base_url}/test/direct_llm",
                json={"context": test_context, "query": test_query},
            )

            if response.status_code == 200:
                result = response.json()

                print("✅ Direct LLM Response:")
                print(f"📄 Response: {result.get('response', '')}")

                if "Mark" in result.get("response", ""):
                    print("✅ LLM CAN use context when provided directly")
                    return {"direct_llm_works": True}
                else:
                    print("⚠️  LLM struggled with direct context")
                    return {"direct_llm_works": False}

            else:
                print(f"❌ Direct LLM test failed: {response.status_code}")
                return {"direct_llm_works": False}

        except Exception as e:
            print(f"❌ Direct LLM test error: {e}")
            return {"direct_llm_works": False}

    def analyze_results(
        self, query_data_result: Dict, query_result: Dict, direct_llm_result: Dict
    ):
        """Analyze all test results and provide diagnosis"""
        print("\n" + "=" * 60)
        print("🔍 REPRODUCTION CASE ANALYSIS")
        print("=" * 60)

        # Check /query/data results
        query_data_status = query_data_result.get("data", {}).get("status", "unknown")
        chunks_count = len(query_data_result.get("data", {}).get("chunks", []))

        print(f"\n📊 Context Retrieval (/query/data):")
        print(f"  • Status: {query_data_status}")
        print(f"  • Chunks Found: {chunks_count}")

        if query_data_status == "failure":
            failure_reason = query_data_result.get("data", {}).get("message", "Unknown")
            print(f"  • Failure Reason: {failure_reason}")
            print(f"  ⚠️  This explains why /query has no context!")
            print("  💡 Diagnosis: Context retrieval is failing completely")
            return

        elif chunks_count == 0:
            print(f"  ⚠️  No chunks retrieved despite 'success' status")
            print("  💡 Diagnosis: Vector search or keyword extraction failing")

        # Check /query results
        query_response = query_result.get("response", "")
        query_response_lower = query_response.lower()

        print(f"\n📝 LLM Response (/query):")
        print(f"  • Length: {len(query_response)} chars")
        print(f"  • Contains 'Mark': {'Yes' if 'Mark' in query_response else 'No'}")

        no_context_indicators = [
            "don't have specific information",
            "don't have information about which researcher",
            "not sure which researcher",
        ]

        found_no_context = any(
            indicator in query_response_lower for indicator in no_context_indicators
        )

        if found_no_context:
            print(f"  ⚠️  Contains no-context indicators: {found_no_context}")

        # Check direct LLM
        direct_llm_works = direct_llm_result.get("direct_llm_works", False)

        print(f"\n🧪 Direct LLM Test:")
        print(
            f"  • LLM can use context when provided: {'Yes' if direct_llm_works else 'No'}"
        )

        # Final diagnosis
        print(f"\n🎯 FINAL DIAGNOSIS:")

        if chunks_count > 0 and found_no_context and direct_llm_works:
            print("🔥 CRITICAL BUG CONFIRMED:")
            print("  • /query/data successfully retrieves context")
            print("  • LLM can use context when provided directly")
            print("  • /query LLM response indicates no context")
            print("  • Therefore: Context is lost between retrieval and LLM call")
            print("  💡 Root Cause: Prompt construction or OpenAI binding issue")
            return True

        elif chunks_count == 0:
            print("🔍 ROOT CAUSE - CONTEXT RETRIEVAL:")
            print("  • No chunks retrieved by /query/data")
            print("  • Issue is in vector search/keyword extraction")
            print("  💡 Not the prompt/context passing bug")
            return False

        elif not direct_llm_works:
            print("🔍 ROOT CAUSE - LLM BINDING:")
            print("  • LLM cannot use context even when provided")
            print("  • Issue is in LLM model or binding")
            return False

        elif not found_no_context:
            print("✅ NO BUG - WORKING CORRECTLY:")
            print("  • Context is being passed to LLM")
            print("  • LLM is using retrieved context")
            return False

        else:
            print("🔍 UNCLEAR - MULTIPLE ISSUES:")
            print("  • Complex interaction between multiple problems")
            return False

    async def run_full_reproduction_case(self, ingest: bool = True, test: bool = True):
        """Run the complete reproduction case"""
        print("🎯 GitHub Issue #2643 Reproduction Case")
        print("=" * 60)

        query_data_result = {}
        query_result = {}
        direct_llm_result = {}

        if ingest:
            success = await self.ingest_test_document()
            if not success:
                print("❌ Cannot proceed - document ingestion failed")
                return

        if test:
            query_data_result = await self.test_query_data_endpoint()
            query_result = await self.test_query_endpoint()
            direct_llm_result = await self.test_direct_llm()

            # Analyze results
            bug_confirmed = self.analyze_results(
                query_data_result, query_result, direct_llm_result
            )

            if bug_confirmed:
                print(f"\n🚨 BUG REPRODUCTION SUCCESSFUL!")
                print("The context passing issue has been confirmed.")
                print("Next steps:")
                print("  1. Run with VERBOSE=true to see debug logs")
                print(
                    "  2. Use config_health_check.py to identify configuration issues"
                )
                print("  3. Check token allocation for 8K context models")
            elif bug_confirmed is False:
                print(f"\n✅ Bug NOT reproduced - system working correctly")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Create reproduction case for GitHub #2643"
    )
    parser.add_argument(
        "--url", default="http://localhost:9621", help="LightRAG server URL"
    )
    parser.add_argument("--ingest", action="store_true", help="Ingest test document")
    parser.add_argument("--test", action="store_true", help="Run query tests")
    parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Skip document ingestion (assumes already exists)",
    )

    args = parser.parse_args()

    print(f"🌐 LightRAG Server: {args.url}")

    manager = ReproductionCaseManager(args.url)

    try:
        await manager.run_full_reproduction_case(
            ingest=args.ingest and not args.skip_ingest, test=args.test
        )

    except KeyboardInterrupt:
        print("\n⚠️  Reproduction case interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    finally:
        await manager.close()

    print(f"\n🏁 Reproduction case complete")


if __name__ == "__main__":
    asyncio.run(main())
