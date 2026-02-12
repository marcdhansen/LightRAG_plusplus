#!/usr/bin/env python3
"""
Simple Embedding Performance Test

This test isolates the embedding worker performance by using a mock embedding function
to measure the actual worker behavior without storage dependencies.
"""

import asyncio
import time
from lightrag.utils import priority_limit_async_func_call
from lightrag.constants import (
    DEFAULT_EMBEDDING_FUNC_MAX_ASYNC,
    DEFAULT_EMBEDDING_BATCH_NUM,
    DEFAULT_EMBEDDING_TIMEOUT,
)


# Mock embedding function that simulates computation delay
async def mock_embedding_func(texts: list[str]) -> list[list[float]]:
    """Mock embedding function that simulates actual computation time"""
    await asyncio.sleep(0.1)  # Simulate 100ms computation per text
    return [[i * 0.1 + len(text) * 0.001] for i, text in enumerate(texts)]


async def test_embedding_workers():
    """Test embedding worker performance directly"""
    print("🔍 Direct Embedding Worker Performance Test")
    print(f"Configuration:")
    print(f"  - Max async workers: {DEFAULT_EMBEDDING_FUNC_MAX_ASYNC}")
    print(f"  - Timeout: {DEFAULT_EMBEDDING_TIMEOUT}s")
    print()

    # Wrap the mock function with priority limiting
    wrapped_func = priority_limit_async_func_call(
        max_size=DEFAULT_EMBEDDING_FUNC_MAX_ASYNC,
        max_queue_size=50,
        llm_timeout=DEFAULT_EMBEDDING_TIMEOUT,
        queue_name="Embedding test",
    )(mock_embedding_func)

    # Test with different batch sizes
    test_cases = [
        ("Small batch", ["text"] * 10),
        ("Medium batch", ["text"] * 50),
        ("Large batch", ["text"] * 100),
        ("Very large batch", ["text"] * 500),
    ]

    results = []

    for case_name, texts in test_cases:
        print(f"\n📊 Testing {case_name} ({len(texts)} items)")

        try:
            start_time = time.time()

            # Process the batch
            embeddings = await wrapped_func(texts)

            end_time = time.time()
            duration = end_time - start_time

            print(f"⏱️  Duration: {duration:.2f}s")
            print(f"📈 Throughput: {len(texts) / duration:.0f} items/s")
            print(f"🔧 Worker utilization: Used {len(embeddings)} embedding results")

            results.append(
                {
                    "case": case_name,
                    "items": len(texts),
                    "duration": duration,
                    "throughput": len(texts) / duration,
                    "embeddings_count": len(embeddings),
                    "status": "success",
                }
            )

        except Exception as e:
            print(f"❌ Error: {e}")
            results.append(
                {
                    "case": case_name,
                    "items": len(texts),
                    "duration": 0,
                    "throughput": 0,
                    "embeddings_count": 0,
                    "status": "error",
                    "error": str(e),
                }
            )

    # Analysis
    print(f"\n📊 EMBEDDING WORKER ANALYSIS")
    print("=" * 50)

    successful_results = [r for r in results if r["status"] == "success"]
    if successful_results:
        # Calculate throughput efficiency
        avg_throughput = sum(r["throughput"] for r in successful_results) / len(
            successful_results
        )

        print(f"✅ Successful test cases: {len(successful_results)}/{len(results)}")
        print(f"📈 Average throughput: {avg_throughput:.1f} items/s")
        print(
            f"📊 Max throughput: {max(r['throughput'] for r in successful_results):.1f} items/s"
        )
        print(
            f"📊 Min throughput: {min(r['throughput'] for r in successful_results):.1f} items/s"
        )

        # Performance assessment
        large_batch_results = [r for r in successful_results if r["items"] >= 100]
        if large_batch_results:
            large_avg_throughput = sum(
                r["throughput"] for r in large_batch_results
            ) / len(large_batch_results)
            print(f"📊 Large batch throughput: {large_avg_throughput:.1f} items/s")

            # Performance criteria
            if large_avg_throughput < 50:  # Less than 50 items/s
                print("🚨 CRITICAL PERFORMANCE ISSUE")
                print(
                    "   Large batch processing < 50 items/s indicates severe bottlenecks"
                )
                print(
                    "   Expected: Large batches should process much faster with parallel workers"
                )
            elif large_avg_throughput < 200:  # Less than 200 items/s
                print("⚠️  SIGNIFICANT PERFORMANCE ISSUE")
                print(
                    "   Large batch processing 50-200 items/s - major optimization needed"
                )
            elif large_avg_throughput < 500:  # Less than 500 items/s
                print("⚠️  MODERATE PERFORMANCE ISSUE")
                print(
                    "   Large batch processing 200-500 items/s - some optimization needed"
                )
            else:
                print("✅ GOOD PERFORMANCE")
                print("   Large batch processing > 500 items/s - acceptable")

    return results


if __name__ == "__main__":
    asyncio.run(test_embedding_workers())
