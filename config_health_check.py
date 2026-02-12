#!/usr/bin/env python3
"""
Configuration Health Check for LightRAG Context Issues

This script validates common configuration problems that lead to context passing failures
between /query and /query/data endpoints.

Usage:
    python config_health_check.py [--url http://localhost:9621]
"""

import asyncio
import json
import sys
import argparse
from typing import Dict, Any, List, Optional
import httpx
from pathlib import Path

# Add lightrag to path for imports
sys.path.insert(0, str(Path(__file__).parent))


class ConfigHealthChecker:
    """Validate LightRAG configuration for context flow issues"""

    def __init__(self, base_url: str = "http://localhost:9621"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.issues = []

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    def add_issue(
        self, severity: str, category: str, description: str, suggestion: str = ""
    ):
        """Add a configuration issue to the report"""
        self.issues.append(
            {
                "severity": severity,
                "category": category,
                "description": description,
                "suggestion": suggestion,
            }
        )

    async def check_server_health(self) -> bool:
        """Check if LightRAG server is accessible"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ LightRAG server is accessible")
                return True
            else:
                self.add_issue(
                    "ERROR", "Server", f"Server returned status {response.status_code}"
                )
                return False
        except Exception as e:
            self.add_issue("ERROR", "Server", f"Cannot connect to server: {e}")
            return False

    async def check_model_info(self) -> Dict[str, Any]:
        """Get model and embedding information"""
        try:
            response = await self.client.get(f"{self.base_url}/models")
            if response.status_code == 200:
                return response.json()
            else:
                self.add_issue(
                    "WARNING",
                    "Models",
                    f"Could not get model info: {response.status_code}",
                )
                return {}
        except Exception as e:
            self.add_issue("WARNING", "Models", f"Error getting model info: {e}")
            return {}

    async def test_embedding_quality(self) -> Dict[str, Any]:
        """Test embedding quality and similarity search"""
        print("\n🧪 Testing Embedding Quality...")

        test_words = ["researcher", "Researcher", "Mark", "mark"]

        try:
            response = await self.client.post(
                f"{self.base_url}/test/embedding", json={"texts": test_words}
            )

            if response.status_code == 200:
                data = response.json()
                embeddings = data.get("embeddings", [])

                if len(embeddings) != len(test_words):
                    self.add_issue("ERROR", "Embedding", "Embedding count mismatch")
                    return {}

                # Calculate similarities
                import numpy as np

                researcher_emb = (
                    np.array(embeddings[0]) if len(embeddings) > 0 else None
                )
                researcher_cap_emb = (
                    np.array(embeddings[1]) if len(embeddings) > 1 else None
                )

                if researcher_emb is not None and researcher_cap_emb is not None:
                    similarity = np.dot(researcher_emb, researcher_cap_emb) / (
                        np.linalg.norm(researcher_emb)
                        * np.linalg.norm(researcher_cap_emb)
                    )

                    print(
                        f"📊 Similarity 'researcher' vs 'Researcher': {similarity:.3f}"
                    )

                    if similarity < 0.8:
                        self.add_issue(
                            "WARNING",
                            "Embedding",
                            f"Low case sensitivity similarity ({similarity:.3f})",
                            "Consider case normalization in preprocessing",
                        )
                    elif similarity < 0.6:
                        self.add_issue(
                            "ERROR",
                            "Embedding",
                            f"Very low case sensitivity similarity ({similarity:.3f})",
                            "Embedding model may have quality issues",
                        )

                return {
                    "embeddings_count": len(embeddings),
                    "case_similarity": similarity
                    if researcher_emb is not None and researcher_cap_emb is not None
                    else None,
                }

            else:
                self.add_issue(
                    "WARNING",
                    "Embedding",
                    f"Embedding test failed: {response.status_code}",
                )
                return {}

        except Exception as e:
            self.add_issue("WARNING", "Embedding", f"Embedding test error: {e}")
            return {}

    async def test_vector_search_threshold(self) -> Dict[str, Any]:
        """Test cosine threshold settings"""
        print("\n🧪 Testing Vector Search Threshold...")

        try:
            response = await self.client.post(
                f"{self.base_url}/test/vector_search",
                json={
                    "query": "researcher",
                    "top_k": 5,
                    "threshold": 0.1,  # User's current setting
                },
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                print(
                    f"📊 Vector search with threshold 0.1 returned {len(results)} results"
                )

                if len(results) == 0:
                    self.add_issue(
                        "ERROR",
                        "Vector Search",
                        "No results with threshold 0.1",
                        "Try increasing threshold to 0.3-0.4",
                    )
                elif len(results) < 2:
                    self.add_issue(
                        "WARNING",
                        "Vector Search",
                        f"Few results ({len(results)}) with threshold 0.1",
                        "Threshold may be too restrictive",
                    )

                # Test with different thresholds
                for threshold in [0.2, 0.3, 0.4, 0.5]:
                    try:
                        resp = await self.client.post(
                            f"{self.base_url}/test/vector_search",
                            json={
                                "query": "researcher",
                                "top_k": 5,
                                "threshold": threshold,
                            },
                        )
                        if resp.status_code == 200:
                            results = resp.json().get("results", [])
                            print(f"📊 Threshold {threshold}: {len(results)} results")
                    except:
                        pass

                return {"results_count": len(results), "threshold_tested": 0.1}

            else:
                self.add_issue(
                    "WARNING",
                    "Vector Search",
                    f"Vector search test failed: {response.status_code}",
                )
                return {}

        except Exception as e:
            self.add_issue("WARNING", "Vector Search", f"Vector search test error: {e}")
            return {}

    async def test_token_allocation(self) -> Dict[str, Any]:
        """Test token budget allocation"""
        print("\n🧪 Testing Token Allocation...")

        try:
            response = await self.client.post(
                f"{self.base_url}/test/token_allocation",
                json={
                    "query": "Who is researcher?",
                    "context_size": "large",  # Simulate large context
                },
            )

            if response.status_code == 200:
                data = response.json()

                print(f"📊 Token Allocation:")
                print(f"  • Max Total: {data.get('max_total_tokens', 'unknown')}")
                print(
                    f"  • System Prompt: {data.get('system_prompt_tokens', 'unknown')}"
                )
                print(f"  • Query: {data.get('query_tokens', 'unknown')}")
                print(
                    f"  • Available for Chunks: {data.get('available_chunk_tokens', 'unknown')}"
                )

                available_chunks = data.get("available_chunk_tokens", 0)
                if available_chunks <= 0:
                    self.add_issue(
                        "ERROR",
                        "Token Allocation",
                        f"Negative chunk budget: {available_chunks}",
                        "Model context window too small for configuration",
                    )
                elif available_chunks < 100:
                    self.add_issue(
                        "WARNING",
                        "Token Allocation",
                        f"Very low chunk budget: {available_chunks}",
                        "May result in minimal context",
                    )

                return data

            else:
                self.add_issue(
                    "WARNING",
                    "Token Allocation",
                    f"Token allocation test failed: {response.status_code}",
                )
                return {}

        except Exception as e:
            self.add_issue(
                "WARNING", "Token Allocation", f"Token allocation test error: {e}"
            )
            return {}

    async def check_cosine_threshold_setting(self) -> Dict[str, Any]:
        """Check current cosine threshold configuration"""
        print("\n🔍 Checking Cosine Threshold Setting...")

        try:
            response = await self.client.get(f"{self.base_url}/config")
            if response.status_code == 200:
                config = response.json()

                cosine_threshold = config.get("cosine_threshold", 0.2)  # Default
                print(f"📊 Current COSINE_THRESHOLD: {cosine_threshold}")

                if cosine_threshold == 0.1:
                    self.add_issue(
                        "WARNING",
                        "Configuration",
                        "Very low cosine threshold (0.1)",
                        "Consider 0.3-0.4 for better results",
                    )
                elif cosine_threshold < 0.2:
                    self.add_issue(
                        "INFO",
                        "Configuration",
                        f"Low cosine threshold ({cosine_threshold})",
                        "May allow low-quality matches",
                    )
                elif cosine_threshold > 0.5:
                    self.add_issue(
                        "WARNING",
                        "Configuration",
                        f"High cosine threshold ({cosine_threshold})",
                        "May miss relevant matches",
                    )

                return {"cosine_threshold": cosine_threshold}

            else:
                self.add_issue(
                    "WARNING",
                    "Configuration",
                    f"Could not get config: {response.status_code}",
                )
                return {}

        except Exception as e:
            self.add_issue("INFO", "Configuration", f"Config check error: {e}")
            return {}

    def generate_report(self) -> str:
        """Generate a comprehensive health report"""
        if not self.issues:
            return "\n✅ No configuration issues detected!"

        report = ["\n🏥 Configuration Health Report", "=" * 50]

        # Group by severity
        errors = [i for i in self.issues if i["severity"] == "ERROR"]
        warnings = [i for i in self.issues if i["severity"] == "WARNING"]
        info = [i for i in self.issues if i["severity"] == "INFO"]

        if errors:
            report.append("\n🚨 ERRORS:")
            for issue in errors:
                report.append(f"  ❌ {issue['category']}: {issue['description']}")
                if issue["suggestion"]:
                    report.append(f"     💡 {issue['suggestion']}")

        if warnings:
            report.append("\n⚠️  WARNINGS:")
            for issue in warnings:
                report.append(f"  ⚠️  {issue['category']}: {issue['description']}")
                if issue["suggestion"]:
                    report.append(f"     💡 {issue['suggestion']}")

        if info:
            report.append("\n💡 INFO:")
            for issue in info:
                report.append(f"  ℹ️  {issue['category']}: {issue['description']}")
                if issue["suggestion"]:
                    report.append(f"     💡 {issue['suggestion']}")

        report.append("\n" + "=" * 50)
        report.append("📋 Summary:")
        report.append(f"  • Total Issues: {len(self.issues)}")
        report.append(f"  • Errors: {len(errors)}")
        report.append(f"  • Warnings: {len(warnings)}")
        report.append(f"  • Info: {len(info)}")

        if errors:
            report.append("\n🎯 RECOMMENDED ACTIONS:")
            report.append("  1. Fix all ERROR level issues first")
            report.append("  2. Test with different cosine thresholds (0.3, 0.4)")
            report.append("  3. Verify model context size matches configuration")
            report.append("  4. Check embedding quality with test documents")

        return "\n".join(report)


async def main():
    """Main health checking function"""
    parser = argparse.ArgumentParser(description="Check LightRAG configuration health")
    parser.add_argument(
        "--url", default="http://localhost:9621", help="LightRAG server URL"
    )

    args = parser.parse_args()

    print(f"🏥 LightRAG Configuration Health Check")
    print(f"🌐 Server: {args.url}")
    print(f"Checking for common context flow issues...\n")

    checker = ConfigHealthChecker(args.url)

    try:
        # Check server availability first
        if not await checker.check_server_health():
            print("\n❌ Cannot connect to LightRAG server")
            await checker.close()
            return

        # Run all health checks
        await checker.check_cosine_threshold_setting()
        await checker.test_embedding_quality()
        await checker.test_vector_search_threshold()
        await checker.test_token_allocation()

        # Generate final report
        report = checker.generate_report()
        print(report)

    except KeyboardInterrupt:
        print("\n⚠️  Health check interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    finally:
        await checker.close()

    print(f"\n🏁 Health check complete")


if __name__ == "__main__":
    asyncio.run(main())
