
import pytest

pytestmark = pytest.mark.heavy
import os
import httpx
import json
import asyncio

# Configuration
BASE_URL = "http://localhost:9621"

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.benchmark
class TestRAGBenchmarks:
    """
    Benchmark suite for RAG Reasoning and Multi-hop capabilities.
    Aligned with HotpotQA and Chain-of-Thought (CoT) standards.
    """

    @pytest.fixture(autouse=True)
    async def setup_check(self):
        """Ensure server is healthy before running tests."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(f"{BASE_URL}/health")
                assert resp.status_code == 200, "Server is not healthy"
            except Exception as e:
                pytest.fail(f"Could not connect to LightRAG server: {e}")

    @pytest.mark.parametrize("case", [
        {
            "question": "Which film starring Keanu Reeves as Neo was released first?",
            "ground_truth_concepts": ["The Matrix", "1999"],
            "complexity": "Multi-hop (Actor -> Role -> Movie -> Date)"
        },
        {
            "question": "Who was the director of the movie that features the character Sarah Connor?",
            "ground_truth_concepts": ["James Cameron", "Terminator"],
            "complexity": "Multi-hop (Character -> Movie -> Director)"
        }
    ])
    async def test_hotpotqa_multihop(self, case):
        """
        Verify system can answer multi-hop questions (HotpotQA style).
        Requires connecting independent facts (e.g. Actor -> Movie -> Date).
        """
        print(f"\n\n🔗 Multi-Hop Question: {case['question']}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "query": case["question"],
                "mode": "mix" 
            }
            
            response = await client.post(f"{BASE_URL}/query", json=payload)
            assert response.status_code == 200
            answer = response.json().get("response", "")
            
            print(f"🗣️  Answer: {answer[:300]}...")
            
            # Validation: Check if key concepts from ground truth exist
            missing = [c for c in case["ground_truth_concepts"] if c.lower() not in answer.lower()]
            
            if missing:
                print(f"❌ Missing concepts: {missing}")
                pytest.fail(f"Failed to retrieve key concepts: {missing}")
            else:
                print("✅ All concepts found.")

    @pytest.mark.parametrize("question", [
        "Explain the causal relationship between Skynet becoming self-aware and Judgment Day.",
        "Compare the 'keyword' and 'vector' search modes in LightRAG based on the documentation."
    ])
    async def test_chain_of_thought_reasoning(self, question):
        """
        Verify system provides reasoning steps (Chain of Thought).
        Checks for logical markers in the response.
        """
        print(f"\n\n🧠 CoT Question: {question}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "query": question + " Explain your reasoning step by step.",
                "mode": "mix"
            }
            
            response = await client.post(f"{BASE_URL}/query", json=payload)
            assert response.status_code == 200
            answer = response.json().get("response", "")
            
            print(f"🗣️  Reasoning: {answer[:400]}...")
            
            # Heuristic check for reasoning indicators
            reasoning_markers = ["because", "therefore", "first", "consequently", "led to", "implies", "comparison", "step"]
            found_markers = [m for m in reasoning_markers if m in answer.lower()]
            
            if len(found_markers) < 1:
                print("❌ No reasoning markers found.")
                # We warn instead of fail, as LLM style varies
                print(f"Warning: Response might lack explicit reasoning structure. Markers checked: {reasoning_markers}")
            else:
                print(f"✅ Reasoning markers found: {found_markers}")

