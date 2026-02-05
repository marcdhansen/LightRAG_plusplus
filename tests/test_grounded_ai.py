#!/usr/bin/env python3
"""
Simple test of GroundedAI integration with LightRAG evaluation framework.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lightrag.evaluation.grounded_ai_backend import (
    GROUNDED_AI_AVAILABLE,
    GroundedAIRAGEvaluator,
)


def test_grounded_ai_basic():
    """Test basic GroundedAI functionality"""
    print("=" * 60)
    print("🧪 Testing GroundedAI Integration")
    print("=" * 60)

    if not GROUNDED_AI_AVAILABLE:
        print("❌ GroundedAI not available")
        return False

    print("✅ GroundedAI available")

    # Test 1: OpenAI backend (should work)
    print("\n1. Testing OpenAI backend...")
    try:
        os.environ["OPENAI_API_KEY"] = "test_key"
        evaluator = GroundedAIRAGEvaluator(model_id="openai/gpt-4o-mini", device="cpu")
        print("✅ OpenAI evaluator created")
    except Exception as e:
        print(f"❌ OpenAI evaluator failed: {str(e)}")

    # Test 2: Hallucination evaluation (with mock OpenAI)
    print("\n2. Testing hallucination evaluation...")
    try:
        result = evaluator.evaluate_hallucination(
            query="What is the capital of France?",
            response="London is the capital of France.",
            context="Paris is the capital of France.",
        )
        print("✅ Hallucination evaluation completed")
        print(f"   Score: {result.get('score', 'N/A')}")
        print(f"   Label: {result.get('label', 'N/A')}")
        print(f"   Success: {result.get('success', False)}")
    except Exception as e:
        print(f"❌ Hallucination evaluation failed: {str(e)}")

    # Test 3: Toxicity evaluation
    print("\n3. Testing toxicity evaluation...")
    try:
        result = evaluator.evaluate_toxicity("This is a normal, friendly response.")
        print("✅ Toxicity evaluation completed")
        print(f"   Score: {result.get('score', 'N/A')}")
        print(f"   Label: {result.get('label', 'N/A')}")
        print(f"   Success: {result.get('success', False)}")
    except Exception as e:
        print(f"❌ Toxicity evaluation failed: {str(e)}")

    print("\n" + "=" * 60)
    print("🎉 GroundedAI Integration Test Complete")
    print("=" * 60)

    return True


if __name__ == "__main__":
    test_grounded_ai_basic()
