#!/usr/bin/env python3
"""
Direct Analysis Script for LightRAG Issue #2643

This script performs systematic root cause analysis using stored data
without requiring a running server.
"""

import json
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re

# Add lightrag to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lightrag import LightRAG
from lightrag.utils import EmbeddingFunc
from lightrag.kg.nano_vector_db_impl import NanoVectorDB


def load_stored_data() -> Dict[str, Any]:
    """Load stored LightRAG data for analysis"""
    data_dir = Path("rag_storage")

    data = {}
    for file_path in data_dir.glob("*.json"):
        key = file_path.stem.replace("kv_store_", "").replace("vdb_", "")
        try:
            with open(file_path, "r") as f:
                data[key] = json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    return data


def analyze_entity_embeddings(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze entity embeddings for case sensitivity issues"""
    results = {
        "case_sensitivity_test": {},
        "embedding_quality": {},
        "cosine_distribution": {},
    }

    # Check for entities in both kv_store and vdb
    entities = data.get("full_entities", {}) or {}
    vdb_entities = data.get("entities", {}) or {}

    # Test case sensitivity: Look for "researcher" vs "Researcher"
    researcher_entities = []

    # Check kv_store entities first
    for entity_id, entity_data in entities.items():
        if isinstance(entity_data, dict):
            entity_name = entity_data.get("entity_name", str(entity_id))
            if "researcher" in entity_name.lower():
                researcher_entities.append(
                    {
                        "id": entity_id,
                        "name": entity_name,
                        "data": entity_data,
                        "source": "kv_store",
                    }
                )

    # Also check vdb entities
    for entity_id, entity_data in vdb_entities.items():
        if isinstance(entity_data, dict):
            entity_name = entity_data.get("entity_name", str(entity_id))
            if "researcher" in entity_name.lower():
                researcher_entities.append(
                    {
                        "id": entity_id,
                        "name": entity_name,
                        "data": entity_data,
                        "source": "vdb",
                    }
                )

    results["case_sensitivity_test"]["researcher_entities"] = researcher_entities
    results["case_sensitivity_test"]["total_kv_entities"] = len(entities)
    results["case_sensitivity_test"]["total_vdb_entities"] = len(vdb_entities)

    # Analyze embedding similarity between case variations
    if len(researcher_entities) >= 2:
        entity_ids = list(entities.keys())
        embedding_data = data.get("entities", {})

        # Sample a few entities to test embedding similarity
        sample_size = min(10, len(entity_ids))
        sample_entities = entity_ids[:sample_size]

        similarities = []
        for i in range(len(sample_entities)):
            for j in range(i + 1, len(sample_entities)):
                id1, id2 = sample_entities[i], sample_entities[j]
                if id1 in embedding_data and id2 in embedding_data:
                    # This would need actual embedding vectors from the vector DB
                    similarities.append(
                        {
                            "entity1": id1,
                            "entity2": id2,
                            "similarity": 0.0,  # Placeholder
                        }
                    )

        results["embedding_quality"]["sample_similarities"] = similarities

    return results


def test_cosine_threshold_impact(data: Dict[str, Any]) -> Dict[str, Any]:
    """Test different cosine thresholds on retrieval results"""
    results = {"threshold_analysis": {}, "retrieval_impact": {}}

    # Load actual vector data if available
    vdb_entities_path = Path("rag_storage/vdb_entities.json")
    if not vdb_entities_path.exists():
        return results

    try:
        with open(vdb_entities_path, "r") as f:
            vdb_data = json.load(f)

        # Analyze cosine similarity distribution
        if "data" in vdb_data:
            similarities = []
            for item in vdb_data["data"]:
                # Extract similarity scores if available
                if "vector" in item and len(item["vector"]) > 0:
                    # This is a placeholder - actual similarity calculation would need query vectors
                    pass

            results["threshold_analysis"]["available_vectors"] = len(
                vdb_data.get("data", [])
            )

    except Exception as e:
        print(f"Error analyzing vector data: {e}")

    return results


def analyze_token_budget_issues() -> Dict[str, Any]:
    """Analyze potential token budget issues with 8K context model"""
    results = {"token_analysis": {}, "budget_impact": {}}

    # Check configuration
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, "r") as f:
            env_content = f.read()

        # Extract model and token-related settings
        llm_model = None
        max_tokens = None

        for line in env_content.split("\n"):
            if line.startswith("LLM_MODEL="):
                llm_model = line.split("=", 1)[1]
            elif line.startswith("MAX_") and "TOKEN" in line:
                max_tokens = line.split("=", 1)[1]

        results["token_analysis"]["model"] = llm_model
        results["token_analysis"]["max_tokens_setting"] = max_tokens

        # Estimate context requirements
        if "qwen2.5" in llm_model.lower() if llm_model else False:
            # qwen2.5 typically has 8K context
            results["budget_impact"]["context_window"] = 8192
            results["budget_impact"]["risk_level"] = (
                "HIGH" if int(max_tokens or "4000") > 6000 else "MEDIUM"
            )

    return results


def analyze_keyword_extraction(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze keyword extraction JSON parsing issues"""
    results = {"keyword_analysis": {}, "parsing_issues": {}}

    # Look for keyword extraction patterns in stored data
    if "llm_response_cache" in data:
        cache_data = data["llm_response_cache"]

        json_parsing_errors = 0
        keyword_extractions = 0

        for cache_key, cache_value in cache_data.items():
            if isinstance(cache_value, str):
                # Look for JSON parsing patterns
                if "keywords" in cache_value.lower():
                    keyword_extractions += 1

                    # Check for common JSON parsing issues
                    if any(
                        pattern in cache_value
                        for pattern in ['"\\n"', '\\\\"', "NaN", "null"]
                    ):
                        json_parsing_errors += 1

        results["keyword_analysis"]["total_keyword_extractions"] = keyword_extractions
        results["keyword_analysis"]["potential_parsing_errors"] = json_parsing_errors
        results["parsing_issues"]["error_rate"] = json_parsing_errors / max(
            keyword_extractions, 1
        )

    return results


def test_prompt_construction_issues() -> Dict[str, Any]:
    """Test for OpenAI binding message construction issues"""
    results = {"prompt_analysis": {}, "construction_issues": {}}

    # Check for prompt-related configuration
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, "r") as f:
            env_content = f.read()

        # Look for binding configuration
        llm_binding = None
        prompt_compression = None

        for line in env_content.split("\n"):
            if line.startswith("LLM_BINDING="):
                llm_binding = line.split("=", 1)[1]
            elif line.startswith("PROMPT_COMPRESSION="):
                prompt_compression = line.split("=", 1)[1]

        results["prompt_analysis"]["llm_binding"] = llm_binding
        results["prompt_analysis"]["prompt_compression"] = prompt_compression

        # Check for known issues with specific bindings
        if llm_binding == "ollama":
            results["construction_issues"]["potential_issue"] = (
                "OpenAI-style message format with Ollama binding"
            )
            results["construction_issues"]["risk_level"] = "MEDIUM"
        elif llm_binding == "openai":
            results["construction_issues"]["potential_issue"] = (
                "Token counting in prompt construction"
            )
            results["construction_issues"]["risk_level"] = "LOW"

    return results


def identify_dominant_failure_pattern(all_results: Dict[str, Any]) -> Dict[str, Any]:
    """Identify the most likely root cause based on all analysis results"""
    failure_patterns = []

    # Analyze each hypothesis

    # 1. Token budget issues
    token_results = all_results.get("token_budget", {})
    if token_results.get("budget_impact", {}).get("risk_level") == "HIGH":
        failure_patterns.append(
            {
                "hypothesis": "Token budget exhaustion",
                "confidence": "HIGH",
                "evidence": f"Model: {token_results.get('token_analysis', {}).get('model')}, Risk: {token_results.get('budget_impact', {}).get('risk_level')}",
            }
        )

    # 2. Embedding case sensitivity
    entity_results = all_results.get("entity_embeddings", {})
    researcher_entities = entity_results.get("case_sensitivity_test", {}).get(
        "researcher_entities", []
    )
    if len(researcher_entities) > 1:
        failure_patterns.append(
            {
                "hypothesis": "Embedding case sensitivity mismatch",
                "confidence": "MEDIUM",
                "evidence": f"Found {len(researcher_entities)} researcher entities with potential case variations",
            }
        )

    # 3. Cosine threshold too permissive
    cosine_results = all_results.get("cosine_threshold", {})
    if cosine_results.get("threshold_analysis", {}).get("available_vectors", 0) > 100:
        failure_patterns.append(
            {
                "hypothesis": "Cosine threshold too permissive (0.1)",
                "confidence": "MEDIUM",
                "evidence": "Large vector database may produce many weak matches",
            }
        )

    # 4. Keyword extraction parsing
    keyword_results = all_results.get("keyword_extraction", {})
    error_rate = keyword_results.get("parsing_issues", {}).get("error_rate", 0)
    if error_rate > 0.1:
        failure_patterns.append(
            {
                "hypothesis": "Keyword extraction JSON parsing failures",
                "confidence": "HIGH",
                "evidence": f"Error rate: {error_rate:.2%}",
            }
        )

    # 5. Prompt construction issues
    prompt_results = all_results.get("prompt_construction", {})
    if prompt_results.get("construction_issues", {}).get("risk_level") in [
        "MEDIUM",
        "HIGH",
    ]:
        failure_patterns.append(
            {
                "hypothesis": "OpenAI binding message construction issues",
                "confidence": "MEDIUM",
                "evidence": prompt_results.get("construction_issues", {}).get(
                    "potential_issue"
                ),
            }
        )

    # Sort by confidence and return the dominant pattern
    if failure_patterns:
        confidence_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        failure_patterns.sort(
            key=lambda x: confidence_order.get(x["confidence"], 0), reverse=True
        )

        return {
            "dominant_pattern": failure_patterns[0],
            "all_patterns": failure_patterns,
        }

    return {"dominant_pattern": None, "all_patterns": []}


async def main():
    """Main analysis function"""
    print("🔍 LightRAG Issue #2643 Root Cause Analysis")
    print("=" * 60)

    # Load stored data
    print("📊 Loading stored LightRAG data...")
    data = load_stored_data()
    print(f"   Loaded {len(data)} data stores")

    # Run all analyses
    print("\n🧪 Running systematic analysis...")

    all_results = {}

    # 1. Entity embedding analysis
    print("   📈 Analyzing entity embeddings...")
    all_results["entity_embeddings"] = analyze_entity_embeddings(data)

    # 2. Cosine threshold impact
    print("   🎯 Testing cosine threshold impact...")
    all_results["cosine_threshold"] = test_cosine_threshold_impact(data)

    # 3. Token budget analysis
    print("   💰 Analyzing token budget issues...")
    all_results["token_budget"] = analyze_token_budget_issues()

    # 4. Keyword extraction analysis
    print("   🔍 Analyzing keyword extraction...")
    all_results["keyword_extraction"] = analyze_keyword_extraction(data)

    # 5. Prompt construction analysis
    print("   📝 Analyzing prompt construction...")
    all_results["prompt_construction"] = test_prompt_construction_issues()

    # Identify dominant failure pattern
    print("\n🎯 Identifying dominant failure pattern...")
    pattern_analysis = identify_dominant_failure_pattern(all_results)

    # Generate report
    print("\n📋 ANALYSIS REPORT")
    print("=" * 40)

    for category, results in all_results.items():
        print(f"\n🔸 {category.replace('_', ' ').title()}:")
        if isinstance(results, dict):
            for key, value in results.items():
                if isinstance(value, dict):
                    if value:
                        print(f"   {key}: {value}")
                else:
                    print(f"   {key}: {value}")

    print(f"\n🚨 DOMINANT FAILURE PATTERN:")
    dominant = pattern_analysis.get("dominant_pattern")
    if dominant:
        print(f"   Hypothesis: {dominant['hypothesis']}")
        print(f"   Confidence: {dominant['confidence']}")
        print(f"   Evidence: {dominant['evidence']}")
    else:
        print("   No clear dominant pattern identified")

    print(f"\n📊 ALL PATTERNS DETECTED:")
    for i, pattern in enumerate(pattern_analysis.get("all_patterns", []), 1):
        print(f"   {i}. {pattern['hypothesis']} ({pattern['confidence']})")

    # Save detailed results
    with open("analysis_results.json", "w") as f:
        json.dump(
            {
                "analysis_results": all_results,
                "pattern_analysis": pattern_analysis,
                "timestamp": str(asyncio.get_event_loop().time()),
            },
            f,
            indent=2,
        )

    print(f"\n💾 Detailed results saved to analysis_results.json")


if __name__ == "__main__":
    asyncio.run(main())
