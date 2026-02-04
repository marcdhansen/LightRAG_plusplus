"""
TDD Benchmarking tests for Community Detection performance in MemgraphStorage.

This module implements proper TDD approach by creating performance benchmarks
that measure the speed and memory tradeoffs of community detection features
compared to baseline operations.
"""

import gc
import os
import time
import tracemalloc
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import psutil
import pytest

from lightrag.kg.memgraph_impl import MemgraphStorage


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""

    operation: str
    execution_time: float
    memory_usage_mb: float
    result_count: int
    success: bool
    error_message: str = ""


@dataclass
class PerformanceComparison:
    """Container for performance comparison results."""

    baseline: BenchmarkResult
    optimized: BenchmarkResult
    speed_improvement: float
    memory_overhead: float
    recommendation: str


class CommunityDetectionBenchmarkSuite:
    """TDD Benchmark suite for community detection performance."""

    def __init__(self):
        self.process = psutil.Process()
        self.baseline_results: dict[str, BenchmarkResult] = {}
        self.optimized_results: dict[str, BenchmarkResult] = {}
        self.comparisons: dict[str, PerformanceComparison] = {}

    def start_memory_tracking(self) -> None:
        """Start memory tracking for performance measurement."""
        tracemalloc.start()
        gc.collect()  # Force garbage collection for clean measurement

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        tracemalloc.stop()
        current, peak = tracemalloc.get_traced_memory()
        return peak / (1024 * 1024)  # Convert to MB

    async def benchmark_operation(
        self, operation: str, func, *args, **kwargs
    ) -> BenchmarkResult:
        """Benchmark an operation with timing and memory measurement."""
        self.start_memory_tracking()
        start_time = time.perf_counter()
        process_memory_start = self.process.memory_info().rss / (1024 * 1024)

        try:
            result = await func(*args, **kwargs)
            success = True
            error_message = ""
            result_count = len(result) if isinstance(result, (list, dict)) else 1
        except Exception as e:
            success = False
            error_message = str(e)
            result = None
            result_count = 0

        end_time = time.perf_counter()
        execution_time = end_time - start_time
        process_memory_end = self.process.memory_info().rss / (1024 * 1024)
        memory_usage = max(
            process_memory_end - process_memory_start, self.get_memory_usage()
        )

        return BenchmarkResult(
            operation=operation,
            execution_time=execution_time,
            memory_usage_mb=memory_usage,
            result_count=result_count,
            success=success,
            error_message=error_message,
        )

    def compare_performance(
        self, baseline: BenchmarkResult, optimized: BenchmarkResult, operation_name: str
    ) -> PerformanceComparison:
        """Compare performance between baseline and optimized operations."""
        if not baseline.success or not optimized.success:
            return PerformanceComparison(
                baseline=baseline,
                optimized=optimized,
                speed_improvement=0.0,
                memory_overhead=0.0,
                recommendation="ERROR: One or both operations failed",
            )

        speed_improvement = (
            (
                (baseline.execution_time - optimized.execution_time)
                / baseline.execution_time
            )
            * 100
            if baseline.execution_time > 0
            else 0
        )

        memory_overhead = (
            (
                (optimized.memory_usage_mb - baseline.memory_usage_mb)
                / baseline.memory_usage_mb
            )
            * 100
            if baseline.memory_usage_mb > 0
            else 0
        )

        # Generate recommendation based on performance metrics
        if speed_improvement > 20 and memory_overhead < 50:
            recommendation = "EXCELLENT: Significant speed improvement with acceptable memory overhead"
        elif speed_improvement > 10 and memory_overhead < 100:
            recommendation = (
                "GOOD: Moderate speed improvement with reasonable memory overhead"
            )
        elif speed_improvement > 0:
            recommendation = (
                "ACCEPTABLE: Minor speed improvement, consider memory tradeoff"
            )
        else:
            recommendation = "POOR: No speed improvement, review implementation"

        return PerformanceComparison(
            baseline=baseline,
            optimized=optimized,
            speed_improvement=speed_improvement,
            memory_overhead=memory_overhead,
            recommendation=recommendation,
        )


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "embedding_batch_num": 32,
        "vector_db_storage_cls_kwargs": {"cosine_better_than_threshold": 0.2},
    }


@pytest.fixture
def mock_embedding_func():
    """Mock embedding function."""
    mock_func = MagicMock()
    mock_func.embedding_dim = 768
    return mock_func


@pytest.fixture
def memgraph_storage(mock_config, mock_embedding_func):
    """Create MemgraphStorage instance for testing."""
    with patch.dict(
        os.environ,
        {
            "MEMGRAPH_URI": "bolt://localhost:7687",
            "MEMGRAPH_USERNAME": "",
            "MEMGRAPH_PASSWORD": "",
            "MEMGRAPH_DATABASE": "memgraph",
        },
    ):
        storage = MemgraphStorage(
            namespace="benchmark_test",
            global_config=mock_config,
            embedding_func=mock_embedding_func,
            workspace="benchmark_workspace",
        )

        # Mock the driver
        storage._driver = MagicMock()
        storage._DATABASE = "memgraph"

        return storage


@pytest.fixture
def benchmark_suite():
    """Create benchmark suite instance."""
    return CommunityDetectionBenchmarkSuite()


@pytest.fixture
def mock_large_session():
    """Mock session for large dataset simulation."""
    session = AsyncMock()

    # Simulate large dataset results
    large_results = []
    for i in range(1000):
        large_results.append(
            {
                "node_id": f"node_{i}",
                "community_id": i % 10,  # 10 communities
            }
        )

    session.run.return_value.__aiter__.return_value = iter(large_results)
    return session


@pytest.fixture
def mock_small_session():
    """Mock session for small dataset simulation."""
    session = AsyncMock()

    # Simulate small dataset results
    small_results = []
    for i in range(50):
        small_results.append(
            {
                "node_id": f"node_{i}",
                "community_id": i % 5,  # 5 communities
            }
        )

    session.run.return_value.__aiter__.return_value = iter(small_results)
    return session


class TestCommunityDetectionPerformance:
    """TDD Performance tests for community detection functionality."""

    @pytest.mark.asyncio
    async def test_benchmark_community_detection_vs_baseline(
        self, memgraph_storage, benchmark_suite, mock_large_session, mock_small_session
    ):
        """
        TDD Test: Benchmark community detection performance compared to baseline graph traversal.

        This test implements TDD by first defining the expected performance characteristics,
        then measuring actual performance against those expectations.
        """

        # TDD: Define expected performance characteristics
        EXPECTED_SPEED_IMPROVEMENT_THRESHOLD = (
            15.0  # At least 15% faster for focused searches
        )
        EXPECTED_MEMORY_OVERHEAD_LIMIT = 50.0  # Memory overhead should be under 50%

        # Setup mock responses for different scenarios
        def setup_mock_session(session_type, search_type):
            session = (
                mock_large_session if session_type == "large" else mock_small_session
            )

            if search_type == "baseline":
                # Baseline search returns more results (no community filtering)
                baseline_results = []
                for i in range(200 if session_type == "large" else 20):
                    baseline_results.append({"label": f"entity_{i}"})
                session.run.return_value.__aiter__.return_value = iter(baseline_results)
            else:
                # Community-filtered search returns fewer, more focused results
                filtered_results = []
                for i in range(50 if session_type == "large" else 10):
                    filtered_results.append({"label": f"entity_{i}"})
                session.run.return_value.__aiter__.return_value = iter(filtered_results)

            return session

        # TDD: Test 1 - Baseline search performance
        memgraph_storage._driver.session.return_value.__aenter__.return_value = (
            setup_mock_session("large", "baseline")
        )
        baseline_result = await benchmark_suite.benchmark_operation(
            operation="baseline_search_large_dataset",
            func=memgraph_storage.search_labels,
            query="test_query",
            limit=100,
        )

        # TDD: Test 2 - Community-filtered search performance
        memgraph_storage._driver.session.return_value.__aenter__.return_value = (
            setup_mock_session("large", "filtered")
        )
        optimized_result = await benchmark_suite.benchmark_operation(
            operation="community_filtered_search_large_dataset",
            func=memgraph_storage.search_labels_with_community_filter,
            query="test_query",
            limit=100,
            community_ids=[0, 1, 2],  # Filter to specific communities
            algorithm="louvain",
        )

        # TDD: Analyze and assert performance expectations
        comparison = benchmark_suite.compare_performance(
            baseline=baseline_result,
            optimized=optimized_result,
            operation_name="search_performance",
        )

        # TDD Assertions - Verify performance meets expectations
        assert baseline_result.success, "Baseline search should succeed"
        assert optimized_result.success, "Community-filtered search should succeed"

        # TDD: Verify speed improvement (community filtering should be faster)
        assert comparison.speed_improvement >= EXPECTED_SPEED_IMPROVEMENT_THRESHOLD, (
            f"Speed improvement {comparison.speed_improvement:.2f}% is below expected "
            f"{EXPECTED_SPEED_IMPROVEMENT_THRESHOLD}%"
        )

        # TDD: Verify memory overhead is reasonable
        assert comparison.memory_overhead <= EXPECTED_MEMORY_OVERHEAD_LIMIT, (
            f"Memory overhead {comparison.memory_overhead:.2f}% exceeds limit "
            f"{EXPECTED_MEMORY_OVERHEAD_LIMIT}%"
        )

        # TDD: Verify result quality (fewer, more focused results)
        assert optimized_result.result_count < baseline_result.result_count, (
            "Community filtering should return fewer, more focused results"
        )

        # TDD: Verify recommendation indicates good performance
        assert (
            "GOOD" in comparison.recommendation
            or "EXCELLENT" in comparison.recommendation
        ), f"Performance should be good or excellent, got: {comparison.recommendation}"

    @pytest.mark.asyncio
    async def test_benchmark_scalability_performance(
        self, memgraph_storage, benchmark_suite
    ):
        """
        TDD Test: Benchmark scalability of community detection across different graph sizes.

        This test follows TDD by defining scalability expectations and verifying the implementation
        meets those expectations as dataset size grows.
        """

        # TDD: Define scalability expectations
        EXPECTED_MAX_DEGRADATION = (
            2.0  # Performance should not degrade more than 2x for 10x data
        )

        def create_mock_session_for_size(size: int):
            """Create mock session that simulates different dataset sizes."""
            session = AsyncMock()

            # Simulate results based on dataset size
            results = []
            for i in range(size):
                results.append({"node_id": f"node_{i}", "community_id": i % 20})

            session.run.return_value.__aiter__.return_value = iter(results)
            return session

        # TDD: Test different dataset sizes
        sizes = [100, 500, 1000, 2000]  # Progressive dataset sizes
        performance_results = []

        for size in sizes:
            memgraph_storage._driver.session.return_value.__aenter__.return_value = (
                create_mock_session_for_size(size)
            )

            result = await benchmark_suite.benchmark_operation(
                operation=f"community_detection_size_{size}",
                func=memgraph_storage.detect_communities,
                algorithm="louvain",
            )

            performance_results.append((size, result))

        # TDD: Analyze scalability
        assert all(result.success for _, result in performance_results), (
            "All community detection operations should succeed"
        )

        # TDD: Verify performance degradation is within acceptable limits
        base_time = performance_results[0][1].execution_time
        base_size = performance_results[0][0]

        for size, result in performance_results[1:]:
            size_ratio = size / base_size
            time_ratio = result.execution_time / base_time
            degradation_factor = time_ratio / size_ratio

            assert degradation_factor <= EXPECTED_MAX_DEGRADATION, (
                f"Performance degradation {degradation_factor:.2f}x for {size_ratio}x data "
                f"exceeds expected {EXPECTED_MAX_DEGRADATION}x"
            )

    @pytest.mark.asyncio
    async def test_benchmark_memory_efficiency(self, memgraph_storage, benchmark_suite):
        """
        TDD Test: Benchmark memory efficiency of community detection and assignment.

        This test follows TDD by defining memory usage expectations and verifying
        the implementation stays within reasonable memory bounds.
        """

        # TDD: Define memory efficiency expectations
        MAX_DETECTION_MEMORY_MB = (
            100.0  # Community detection should use less than 100MB
        )
        MAX_ASSIGNMENT_MEMORY_MB = 50.0  # Assignment should use less than 50MB

        def create_mock_communities_session():
            """Create mock session for community detection."""
            session = AsyncMock()
            results = []
            for i in range(2000):  # Large number of nodes
                results.append({"node_id": f"node_{i}", "community_id": i % 50})
            session.run.return_value.__aiter__.return_value = iter(results)
            return session

        def create_mock_assignment_session():
            """Create mock session for community assignment."""
            session = AsyncMock()
            mock_record = {"updated_count": 2000}
            session.run.return_value.single.return_value = mock_record
            return session

        # TDD: Test memory usage for community detection
        memgraph_storage._driver.session.return_value.__aenter__.return_value = (
            create_mock_communities_session()
        )
        detection_result = await benchmark_suite.benchmark_operation(
            operation="community_detection_memory_test",
            func=memgraph_storage.detect_communities,
            algorithm="louvain",
        )

        # TDD: Test memory usage for community assignment
        test_communities = {f"node_{i}": i % 50 for i in range(2000)}
        memgraph_storage._driver.session.return_value.__aenter__.return_value = (
            create_mock_assignment_session()
        )
        assignment_result = await benchmark_suite.benchmark_operation(
            operation="community_assignment_memory_test",
            func=memgraph_storage.assign_community_ids,
            communities=test_communities,
            algorithm="louvain",
        )

        # TDD: Verify memory usage expectations
        assert detection_result.success, "Community detection should succeed"
        assert assignment_result.success, "Community assignment should succeed"

        assert detection_result.memory_usage_mb <= MAX_DETECTION_MEMORY_MB, (
            f"Community detection memory usage {detection_result.memory_usage_mb:.2f}MB "
            f"exceeds expected {MAX_DETECTION_MEMORY_MB}MB"
        )

        assert assignment_result.memory_usage_mb <= MAX_ASSIGNMENT_MEMORY_MB, (
            f"Community assignment memory usage {assignment_result.memory_usage_mb:.2f}MB "
            f"exceeds expected {MAX_ASSIGNMENT_MEMORY_MB}MB"
        )

    @pytest.mark.asyncio
    async def test_benchmark_algorithm_comparison(
        self, memgraph_storage, benchmark_suite
    ):
        """
        TDD Test: Benchmark performance comparison between Louvain and Leiden algorithms.

        This test follows TDD by comparing algorithm performance and establishing
        expectations about their relative efficiency.
        """

        def create_mock_session_for_algorithm(algorithm: str):
            """Create mock session that simulates different algorithm performance."""
            session = AsyncMock()
            results = []

            # Simulate different performance characteristics
            if algorithm == "louvain":
                # Louvain: Faster but fewer, larger communities
                for i in range(1000):
                    results.append({"node_id": f"node_{i}", "community_id": i % 10})
            else:  # leiden
                # Leiden: Slower but more, smaller communities
                for i in range(1000):
                    results.append({"node_id": f"node_{i}", "community_id": i % 25})

            session.run.return_value.__aiter__.return_value = iter(results)
            return session

        # TDD: Test Louvain algorithm
        memgraph_storage._driver.session.return_value.__aenter__.return_value = (
            create_mock_session_for_algorithm("louvain")
        )
        louvain_result = await benchmark_suite.benchmark_operation(
            operation="louvain_community_detection",
            func=memgraph_storage.detect_communities,
            algorithm="louvain",
        )

        # TDD: Test Leiden algorithm
        memgraph_storage._driver.session.return_value.__aenter__.return_value = (
            create_mock_session_for_algorithm("leiden")
        )
        leiden_result = await benchmark_suite.benchmark_operation(
            operation="leiden_community_detection",
            func=memgraph_storage.detect_communities,
            algorithm="leiden",
        )

        # TDD: Verify both algorithms succeed
        assert louvain_result.success, "Louvain algorithm should succeed"
        assert leiden_result.success, "Leiden algorithm should succeed"

        # TDD: Verify Louvain is generally faster (expectation based on algorithm characteristics)
        # Note: This expectation can be adjusted based on actual requirements
        speed_ratio = leiden_result.execution_time / louvain_result.execution_time

        # TDD: Allow some flexibility - Leiden might be faster in some cases
        # but performance difference shouldn't be extreme
        assert 0.5 <= speed_ratio <= 3.0, (
            f"Performance ratio between algorithms {speed_ratio:.2f}x is outside acceptable range"
        )

        # TDD: Verify both produce reasonable numbers of communities
        assert louvain_result.result_count > 0, "Louvain should detect communities"
        assert leiden_result.result_count > 0, "Leiden should detect communities"

    @pytest.mark.asyncio
    async def test_benchmark_community_filtering_effectiveness(
        self, memgraph_storage, benchmark_suite
    ):
        """
        TDD Test: Benchmark the effectiveness of community filtering for query performance.

        This test follows TDD by defining expectations about how much faster
        community-filtered queries should be compared to full graph queries.
        """

        # TDD: Define filtering effectiveness expectations
        MIN_FILTERING_SPEEDUP = (
            1.2  # Community filtering should provide at least 20% speedup
        )
        MAX_RESULT_REDUCTION = 0.8  # Should reduce results by at least 20%

        def create_mock_search_session(filtered: bool, result_size: int):
            """Create mock session for search operations."""
            session = AsyncMock()
            results = [{"label": f"entity_{i}"} for i in range(result_size)]
            session.run.return_value.__aiter__.return_value = iter(results)
            return session

        # TDD: Test unfiltered search (baseline)
        memgraph_storage._driver.session.return_value.__aenter__.return_value = (
            create_mock_search_session(filtered=False, result_size=200)
        )
        unfiltered_result = await benchmark_suite.benchmark_operation(
            operation="unfiltered_search",
            func=memgraph_storage.search_labels,
            query="test_query",
            limit=200,
        )

        # TDD: Test community-filtered search
        memgraph_storage._driver.session.return_value.__aenter__.return_value = (
            create_mock_search_session(filtered=True, result_size=40)
        )
        filtered_result = await benchmark_suite.benchmark_operation(
            operation="community_filtered_search",
            func=memgraph_storage.search_labels_with_community_filter,
            query="test_query",
            limit=200,
            community_ids=[0, 1, 2],  # Filter to specific communities
            algorithm="louvain",
        )

        # TDD: Verify both searches succeed
        assert unfiltered_result.success, "Unfiltered search should succeed"
        assert filtered_result.success, "Filtered search should succeed"

        # TDD: Verify speed improvement
        speedup = unfiltered_result.execution_time / filtered_result.execution_time
        assert speedup >= MIN_FILTERING_SPEEDUP, (
            f"Filtering speedup {speedup:.2f}x is below expected {MIN_FILTERING_SPEEDUP}x"
        )

        # TDD: Verify result reduction (more focused results)
        result_ratio = filtered_result.result_count / unfiltered_result.result_count
        assert result_ratio <= MAX_RESULT_REDUCTION, (
            f"Result ratio {result_ratio:.2f} is above maximum {MAX_RESULT_REDUCTION}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
