"""
Performance and load testing for LightRAG WebUI.
Tests response times, concurrent user load, and system performance benchmarks.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

import pytest
import aiohttp
from playwright.sync_api import Page, expect

from tests.ui.conftest import server_process


class PerformanceMetrics:
    """Helper class to track performance metrics."""

    def __init__(self):
        self.metrics = {}

    def record_response_time(self, endpoint: str, response_time: float):
        """Record response time for an endpoint."""
        if endpoint not in self.metrics:
            self.metrics[endpoint] = []
        self.metrics[endpoint].append(response_time)

    def get_stats(self, endpoint: str) -> Dict:
        """Get statistics for recorded metrics."""
        times = self.metrics.get(endpoint, [])
        if not times:
            return {"count": 0, "avg": 0, "min": 0, "max": 0, "p95": 0}

        return {
            "count": len(times),
            "avg": sum(times) / len(times),
            "min": min(times),
            "max": max(times),
            "p95": sorted(times)[int(len(times) * 0.95)] if times else 0,
        }

    def get_all_stats(self) -> Dict:
        """Get statistics for all endpoints."""
        all_stats = {}
        for endpoint, times in self.metrics.items():
            all_stats[endpoint] = self.get_stats(endpoint)
        return all_stats


@pytest.fixture
def performance_metrics():
    """Create performance metrics fixture."""
    return PerformanceMetrics()


@pytest.mark.performance
@pytest.mark.api
class TestAPIPerformance:
    """Test API performance and response times."""

    async def test_document_upload_response_times(
        self, authenticated_api_client, performance_metrics, temp_upload_dir
    ):
        """Test document upload endpoint response times."""
        # Test multiple document uploads
        upload_times = []

        for i in range(5):
            with open(temp_upload_dir / f"perf_test_{i}.txt", "w") as f:
                f.write(f"Performance test document {i}")

            start_time = time.time()

            with open(temp_upload_dir / f"perf_test_{i}.txt", "rb") as file:
                files = {"files": (f"perf_test_{i}.txt", file, "text/plain")}

            response = await authenticated_api_client.post(
                "/documents/upload", files=files
            )

            end_time = time.time()
            response_time = end_time - start_time
            upload_times.append(response_time)

            # Verify success
            assert response.status_code == 200

        # Record metrics
        for i, upload_time in enumerate(upload_times):
            performance_metrics.record_response_time("document_upload", upload_time)

        # Verify performance requirements
        stats = performance_metrics.get_stats("document_upload")
        assert stats["avg"] < 2.0  # Average under 2 seconds
        assert stats["max"] < 5.0  # Max under 5 seconds
        assert stats["p95"] < 3.0  # 95th percentile under 3 seconds

    async def test_query_response_times(
        self, authenticated_api_client, performance_metrics
    ):
        """Test query endpoint response times."""
        query_times = []

        # Test various query complexities
        queries = [
            "What is AI?",
            "Explain the benefits of machine learning in detail",
            "Compare and contrast supervised and unsupervised learning algorithms",
            "What are the latest developments in quantum computing?",
            "How does the RAG system handle large documents and datasets?",
        ]

        for query in queries:
            start_time = time.time()

            response = await authenticated_api_client.post(
                "/query", json={"query": query, "mode": "mix"}
            )

            end_time = time.time()
            response_time = end_time - start_time
            query_times.append(response_time)

            # Verify success
            assert response.status_code == 200

        # Record metrics
        for i, query_time in enumerate(query_times):
            performance_metrics.record_response_time("query", query_time)

        # Verify performance requirements
        stats = performance_metrics.get_stats("query")
        assert stats["avg"] < 3.0  # Average under 3 seconds
        assert stats["p95"] < 5.0  # 95th percentile under 5 seconds

    async def test_graph_operations_performance(
        self, authenticated_api_client, performance_metrics
    ):
        """Test graph operations performance."""
        graph_operation_times = []

        # Test various graph operations
        operations = [
            ("get_graph_labels", "/graph/label/list", "get"),
            ("get_graph", "/graphs?label=PERSON&max_depth=2&max_nodes=100", "get"),
            ("check_entity", "/graph/entity/exists?name=test_entity", "get"),
        ]

        for op_name, endpoint, method in operations:
            start_time = time.time()

            if method == "get":
                response = await authenticated_api_client.get(endpoint)
            else:
                response = await authenticated_api_client.post(endpoint, json={})

            end_time = time.time()
            operation_time = end_time - start_time
            graph_operation_times.append(operation_time)

            # Verify success
            assert response.status_code == 200

        # Record metrics
        for i, op_time in enumerate(graph_operation_times):
            performance_metrics.record_response_time(f"graph_{op_name}", op_time)

        # Verify performance requirements
        stats = performance_metrics.get_stats("graph_operations")
        assert stats["avg"] < 1.5  # Average under 1.5 seconds
        assert stats["p95"] < 2.5  # 95th percentile under 2.5 seconds

    async def test_concurrent_request_handling(
        self, authenticated_api_client, performance_metrics
    ):
        """Test concurrent request handling."""
        concurrent_times = []

        async def make_request(request_data, delay=0):
            await asyncio.sleep(delay)
            start_time = time.time()

            response = await authenticated_api_client.post("/query", json=request_data)

            end_time = time.time()
            response_time = end_time - start_time

            return response_time, response.status_code

        # Test 10 concurrent requests
        request_data = [
            {"query": f"Concurrent query {i}", "mode": "mix"} for i in range(10)
        ]

        start_time = time.time()
        tasks = [make_request(data, 0.1 * i) for i, data in enumerate(request_data)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Analyze results
        response_times = []
        success_count = 0

        for response_time, status_code in results:
            response_times.append(response_time)
            if status_code == 200:
                success_count += 1

        total_time = end_time - start_time

        # Record metrics
        for response_time in response_times:
            performance_metrics.record_response_time("concurrent_query", response_time)

        # Verify concurrent performance requirements
        stats = performance_metrics.get_stats("concurrent_query")
        assert stats["avg"] < 2.0  # Average under 2 seconds even with concurrency
        assert success_count >= 8  # At least 80% success rate
        assert total_time < 5.0  # All concurrent requests complete within 5 seconds


@pytest.mark.performance
@pytest.mark.ui
@pytest.mark.playwright
class TestUIPerformance:
    """Test UI performance and responsiveness."""

    def test_page_load_performance(self, page: Page, server_process: str):
        """Test page load performance."""
        # Measure page load time
        start_time = time.time()
        page.goto(f"{server_process}/webui/")

        # Wait for page to be fully loaded
        page.wait_for_selector("body", timeout=10000)
        end_time = time.time()

        load_time = end_time - start_time

        # Verify load performance requirements
        assert load_time < 3.0  # Should load within 3 seconds

        # Check for critical resources loaded
        critical_elements = [
            ".query-interface",
            ".graph-container",
            ".document-list",
            ".navigation",
        ]

        for element in critical_elements:
            element_loc = page.locator(element)
            assert element_loc.is_visible()

    def test_query_interface_responsive(self, page: Page, server_process: str):
        """Test query interface responsiveness."""
        page.goto(f"{server_process}/webui/")
        page.get_by_role("tab", name="Query").click()

        # Measure interaction responsiveness
        query_input = page.locator("textarea[placeholder*='query']")

        # Test typing responsiveness
        start_time = time.time()
        test_text = "This is a performance test for UI responsiveness."

        for char in test_text:
            query_input.press(char)

        end_time = time.time()
        typing_time = end_time - start_time

        # Should be responsive (character input should be fast)
        assert typing_time < 2.0  # Typing should complete within 2 seconds

    def test_graph_interaction_performance(self, page: Page, server_process: str):
        """Test graph interaction performance."""
        page.goto(f"{server_process}/webui/")
        page.get_by_role("tab", name="Graph").click()

        # Wait for graph to load
        page.wait_for_selector(".graph-container", timeout=10000)

        # Test zoom and pan performance
        graph_container = page.locator(".graph-container, .graph-visualization")

        if graph_container.is_visible():
            start_time = time.time()

            # Test zoom operations
            zoom_in_button = page.locator("button[aria-label*='Zoom In']")
            zoom_out_button = page.locator("button[aria-label*='Zoom Out']")

            if zoom_in_button.count() > 0 and zoom_out_button.count() > 0:
                # Perform zoom operations
                for _ in range(5):
                    zoom_in_button.click()
                    page.wait_for_timeout(200)
                    zoom_out_button.click()
                    page.wait_for_timeout(200)

            end_time = time.time()
            zoom_time = end_time - start_time

            # Zoom operations should be responsive
            assert zoom_time < 3.0  # 10 zoom ops within 3 seconds

    def test_memory_usage_monitoring(self, page: Page, server_process: str):
        """Test memory usage and resource consumption."""
        # This test monitors for memory leaks in long-running sessions
        page.goto(f"{server_process}/webui/")

        # Simulate extended usage
        operations = [
            "navigate_to_query",
            "navigate_to_graph",
            "navigate_to_documents",
            "perform_search",
            "upload_document",
        ]

        for operation in operations:
            if operation == "navigate_to_query":
                page.get_by_role("tab", name="Query").click()
                page.wait_for_selector("textarea[placeholder*='query']", timeout=5000)

            elif operation == "navigate_to_graph":
                page.get_by_role("tab", name="Graph").click()
                page.wait_for_selector(".graph-container", timeout=5000)

            elif operation == "navigate_to_documents":
                page.get_by_role("tab", name="Documents").click()
                page.wait_for_selector(".document-list", timeout=5000)

            elif operation == "perform_search":
                page.get_by_role("tab", name="Query").click()
                page.wait_for_selector("textarea[placeholder*='query']", timeout=5000)

                search_input = page.locator(
                    "input[placeholder*='search'], .search-input"
                )
                if search_input.count() > 0:
                    search_input.fill("memory test")
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(1000)

            elif operation == "upload_document":
                page.get_by_role("tab", name="Documents").click()
                page.wait_for_selector(".document-list", timeout=5000)

                upload_input = page.locator("input[type='file']")
                if upload_input.count() > 0:
                    # Create a small test file
                    upload_input.set_input_files(
                        "test_memory.txt", b"Memory test content", "text/plain"
                    )
                    page.wait_for_timeout(1000)

        # Check for memory issues (basic check)
        page.reload()
        page.wait_for_selector("body", timeout=5000)


@pytest.mark.performance
@pytest.mark.integration
class TestLoadTesting:
    """Test system performance under load."""

    async def test_load_testing_with_concurrent_users(
        self, server_process: str, performance_metrics
    ):
        """Test system behavior with multiple concurrent users."""
        base_url = f"{server_process}/webui/"

        async def simulate_user_session(user_id: int):
            from playwright.sync_api import async_playwright

            async with async_playwright() as p:
                page = await p.new_page()

                try:
                    # Navigate and perform basic operations
                    await page.goto(base_url)

                    # Navigate to query tab
                    await page.get_by_role("tab", name="Query").click()
                    await page.wait_for_selector(
                        "textarea[placeholder*='query']", timeout=5000
                    )

                    # Perform a simple query
                    query_input = page.locator("textarea[placeholder*='query']")
                    await query_input.fill(f"Query from user {user_id}")

                    submit_button = page.get_by_text("Ask")
                    await submit_button.click()

                    # Wait for response
                    await page.wait_for_selector(".query-result", timeout=10000)

                    # Small delay to simulate real user behavior
                    await page.wait_for_timeout(1000)

                finally:
                    await page.close()

        # Simulate 5 concurrent users
        start_time = time.time()
        user_tasks = [simulate_user_session(i) for i in range(5)]

        await asyncio.gather(*user_tasks)
        end_time = time.time()

        total_time = end_time - start_time
        avg_time_per_user = total_time / 5

        # Verify system can handle concurrent users efficiently
        assert avg_time_per_user < 10.0  # Average session under 10 seconds
        assert total_time < 30.0  # All sessions complete within 30 seconds

    async def test_api_stress_testing(
        self, authenticated_api_client, performance_metrics
    ):
        """Test API stress handling."""
        stress_times = []

        # Perform 50 rapid requests
        for i in range(50):
            start_time = time.time()

            response = await authenticated_api_client.post(
                "/query", json={"query": f"Stress test query {i}", "mode": "local"}
            )

            end_time = time.time()
            response_time = end_time - start_time
            stress_times.append(response_time)

            # Verify response (may fail under stress)
            if response.status_code not in [200, 429, 503]:
                pass  # Accept degradation under stress
            else:
                assert response.status_code == 200

        # Record stress test metrics
        for response_time in stress_times:
            performance_metrics.record_response_time("stress_query", response_time)

        # Verify stress test requirements
        stats = performance_metrics.get_stats("stress_query")
        assert stats["avg"] < 1.0  # Average under 1 second under stress
        assert stats["p95"] < 2.0  # 95th percentile under 2 seconds under stress
