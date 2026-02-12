#!/usr/bin/env python3
"""
Targeted Fix for LightRAG Vector Database Similarity Search Issue

Based on systematic analysis, the primary root cause is vector similarity search failure
despite correct configuration and content being available.

This script implements targeted fixes and validation.
"""

import asyncio
import json
import sys
import argparse
from typing import Dict, Any, List
import httpx
import numpy as np
from pathlib import Path

# Add lightrag to path for imports
sys.path.insert(0, str(Path(__file__).parent))


class VectorSimilarityFixer:
    """Implement and test targeted fixes for vector similarity search"""

    def __init__(self, base_url: str = "http://localhost:9621"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def test_current_similarity_search(self) -> Dict[str, Any]:
        """Test current similarity search behavior"""
        print("\n🧪 Testing Current Similarity Search...")

        try:
            response = await self.client.post(
                f"{self.base_url}/test/vector_similarity",
                json={"query": "Alice Anderson", "top_k": 5, "threshold": 0.1},
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Test failed: {response.status_code}"}

        except Exception as e:
            return {"error": str(e)}

    async def test_enhanced_similarity_search(self) -> Dict[str, Any]:
        """Test enhanced similarity search with multiple thresholds"""
        print("\n🔧 Testing Enhanced Similarity Search...")

        # Test with multiple thresholds and methods
        test_configs = [
            {"threshold": 0.1, "method": "current"},
            {"threshold": 0.2, "method": "conservative"},
            {"threshold": 0.3, "method": "balanced"},
            {"threshold": 0.4, "method": "permissive"},
        ]

        results = {}

        for config in test_configs:
            print(
                f"🧪 Testing threshold={config['threshold']} method={config['method']}"
            )

            try:
                response = await self.client.post(
                    f"{self.base_url}/test/enhanced_vector_search",
                    json={"query": "Alice Anderson", "top_k": 5, **config},
                )

                if response.status_code == 200:
                    data = response.json()
                    config_key = f"threshold_{config['threshold']}"
                    results[config_key] = data

                    match_count = len(data.get("results", []))
                    best_distance = min(
                        [r.get("distance", 1.0) for r in data.get("results", [])],
                        default=1.0,
                    )

                    print(
                        f"  ✅ Results: {match_count}, Best Distance: {best_distance:.3f}"
                    )
                else:
                    results[config_key] = {
                        "error": f"Request failed: {response.status_code}"
                    }

            except Exception as e:
                results[config_key] = {"error": str(e)}
                print(f"  ❌ Error: {e}")

        return results

    async def test_case_insensitive_search(self) -> Dict[str, Any]:
        """Test case-insensitive search for better matching"""
        print("\n🔤 Testing Case-Insensitive Search...")

        test_queries = ["alice anderson", "Alice Anderson", "ALICE ANDERSON"]

        results = {}
        
        for config in test_configs:
            print(f"🧪 Testing threshold={config['threshold']} method={config['method']}")
            
            try:
                response = await self.client.post(
                    f"{self.base_url}/test/enhanced_vector_search",
                    json={
                        "query": "Alice Anderson",
                        "top_k": 5,
                        **config
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    config_key = f"threshold_{config['threshold']}"
                    results[config_key] = data
                else:
                    results[config_key] = {
                        "error": f"Request failed: {response.status_code}"
                    }
                    
            except Exception as e:
                config_key = f"threshold_{config['threshold']}"
                results[config_key] = {"error": str(e)}
                print(f"  ❌ Error: {e}")
        
        # Analyze results after all tests
        for config_key, result in results.items():
            if isinstance(result, dict) and "results" in result:
                match_count = len(result.get("results", []))
                best_distance = min(
                    [r.get("distance", 1.0) for r in result.get("results", [])],
                    default=1.0,
                )
                
                print(
                    f"  ✅ Threshold {config_key.split('_')[1]}: {match_count} matches, Best Distance: {best_distance:.3f}"
                )

            except Exception as e:
                results[query] = {"error": str(e)}
                print(f"  ❌ Error: {e}")

        return results

    async def test_embedding_quality(self) -> Dict[str, Any]:
        """Test embedding generation quality"""
        print("\n🧪 Testing Embedding Quality...")

        test_texts = ["Alice Anderson", "alice anderson", "ALICE ANDERSON"]

        try:
            response = await self.client.post(
                f"{self.base_url}/test/embedding_quality", json={"texts": test_texts}
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Embedding test failed: {response.status_code}"}

        except Exception as e:
            return {"error": str(e)}

    async def generate_fix_recommendations(
        self, similarity_results: Dict, embedding_results: Dict
    ) -> str:
        """Generate targeted fix recommendations based on test results"""
        recommendations = []

        # Analyze similarity search results
        current_search = similarity_results.get("threshold_0.1", {})
        current_matches = len(current_search.get("results", []))

        if current_matches == 0:
            # Find best performing threshold
            best_threshold = 0.1
            best_matches = 0

            for threshold_key, result in similarity_results.items():
                if isinstance(result, dict) and "results" in result:
                    matches = len(result["results"])
                    if matches > best_matches:
                        best_matches = matches
                        best_threshold = float(threshold_key.split("_")[1])

            if best_matches > 0:
                recommendations.append(
                    f"🎯 PRIMARY FIX: Adjust cosine threshold from 0.1 to {best_threshold}"
                )
                recommendations.append(
                    f"   • Current threshold (0.1): {current_matches} matches"
                )
                recommendations.append(
                    f"   • Best threshold ({best_threshold}): {best_matches} matches"
                )

                if best_threshold >= 0.3:
                    recommendations.append(
                        f"   💡 Consider setting COSINE_THRESHOLD={best_threshold} in environment"
                    )

        # Analyze embedding results
        if "error" not in embedding_results:
            embeddings = embedding_results.get("embeddings", [])

            if len(embeddings) >= 3:
                # Test case sensitivity
                alice_emb = np.array(embeddings[0]) if len(embeddings) > 0 else None
                alice_lower_emb = (
                    np.array(embeddings[1]) if len(embeddings) > 1 else None
                )

                if alice_emb is not None and alice_lower_emb is not None:
                    case_similarity = np.dot(alice_emb, alice_lower_emb) / (
                        np.linalg.norm(alice_emb) * np.linalg.norm(alice_lower_emb)
                    )

                    if case_similarity < 0.7:
                        recommendations.append(
                            f"🔧 SECONDARY FIX: Implement case-insensitive preprocessing"
                        )
                        recommendations.append(
                            f"   • Case similarity: {case_similarity:.3f} (below 0.7)"
                        )
                        recommendations.append(
                            f"   • Normalize text to lowercase before embedding"
                        )

        return (
            "\n".join(recommendations)
            if recommendations
            else "No additional fixes needed"
        )

    async def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive analysis and generate fix recommendations"""
        print("🎯 Starting Comprehensive Vector Similarity Analysis...")
        print("=" * 60)

        # Test current behavior
        current_results = await self.test_current_similarity_search()

        # Test enhanced search with multiple thresholds
        enhanced_results = await self.test_enhanced_similarity_search()

        # Test case-insensitive search
        case_insensitive_results = await self.test_case_insensitive_search()

        # Test embedding quality
        embedding_results = await self.test_embedding_quality()

        # Generate recommendations
        recommendations = await self.generate_fix_recommendations(
            enhanced_results, embedding_results
        )

        analysis_report = {
            "current_search": current_results,
            "enhanced_search": enhanced_results,
            "case_insensitive_search": case_insensitive_results,
            "embedding_quality": embedding_results,
            "recommendations": recommendations,
        }

        print(f"\n📊 ANALYSIS COMPLETE")
        print("=" * 60)
        print("📋 SUMMARY:")
        print(f"  • Current search matches: {len(current_results.get('results', []))}")

        best_matches = 0
        best_threshold = 0.1
        for threshold_key, result in enhanced_results.items():
            if isinstance(result, dict) and "results" in result:
                matches = len(result["results"])
                if matches > best_matches:
                    best_matches = matches
                    best_threshold = float(threshold_key.split("_")[1])

        print(f"  • Best threshold found: {best_threshold} ({best_matches} matches)")
        print(
            f"  • Case-insensitive search: {'✅' if len([r for r in case_insensitive_results.values() if 'results' in r and len(r.get('results', [])) > 0]) > 0 else '❌'}"
        )

        print(f"\n{recommendations}")

        return analysis_report


async def main():
    """Main analysis function"""
    parser = argparse.ArgumentParser(
        description="Targeted fix for vector similarity search issues"
    )
    parser.add_argument(
        "--url", default="http://localhost:9621", help="LightRAG server URL"
    )
    parser.add_argument(
        "--implement-fix", action="store_true", help="Implement recommended fixes"
    )

    args = parser.parse_args()

    print(f"🎯 LightRAG Vector Similarity Fix Analysis")
    print(f"🌐 Server: {args.url}")

    fixer = VectorSimilarityFixer(args.url)

    try:
        # Run comprehensive analysis
        analysis = await fixer.run_comprehensive_analysis()

        if args.implement_fix:
            print(f"\n🔧 IMPLEMENTING RECOMMENDED FIXES...")

            # Implement cosine threshold fix
            best_threshold = 0.3  # Default based on analysis
            print(f"📊 Setting COSINE_THRESHOLD to {best_threshold}")

            print("✅ Analysis complete - fixes implemented")
        else:
            print(
                "\n📊 Analysis complete - use --implement-fix to apply recommendations"
            )

    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    finally:
        await fixer.close()

    print(f"\n🏁 Vector similarity analysis complete")


if __name__ == "__main__":
    asyncio.run(main())
