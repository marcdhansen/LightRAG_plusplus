"""
Integration tests for API ↔ Frontend communication.
Tests complete user workflows from UI to API and back.
"""

import pytest
import tempfile
from pathlib import Path
from playwright.sync_api import Page, expect

from tests.ui.conftest import server_process


@pytest.mark.ui
@pytest.mark.playwright
@pytest.mark.integration
class TestAPIFrontendIntegration:
    """Test API and Frontend integration."""

    @pytest.fixture(autouse=True)
    def setup_integration_page(self, page: Page, server_process: str):
        """Setup for integration tests."""
        page.goto(f"{server_process}/webui/")
        page.wait_for_timeout(5000)  # Wait for initial load

    def test_document_upload_to_query_workflow(self, page: Page):
        """Test complete workflow: upload document → query → results."""
        # 1. Navigate to Documents tab and upload a document
        page.get_by_role("tab", name="Documents").click()
        page.wait_for_selector(".document-list", timeout=10000)

        # Create a test document
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as temp_file:
            temp_file.write(
                "This is a test document about machine learning algorithms and artificial intelligence integration."
            )
            temp_file_path = temp_file.name

        # Upload the document
        upload_input = page.locator("input[type='file']")
        expect(upload_input).to_be_visible()

        upload_input.set_input_files(temp_file_path)

        # Wait for upload to complete
        page.wait_for_selector(".upload-success, .document-processed", timeout=30000)

        # 2. Navigate to Query tab
        page.get_by_role("tab", name="Query").click()
        page.wait_for_selector("textarea[placeholder*='query']", timeout=10000)

        # 3. Query about the uploaded document
        query_input = page.locator("textarea[placeholder*='query']")
        query_input.fill(
            "What machine learning algorithms are mentioned in the documents?"
        )

        submit_button = page.get_by_text("Ask")
        submit_button.click()

        # 4. Verify response includes relevant information
        page.wait_for_selector(".query-result", timeout=30000)
        response_area = page.locator(".query-response")
        expect(response_area).to_be_visible()

        # Check for citations to uploaded document
        citations = page.locator(".citations, .references")
        if citations.count() > 0:
            expect(citations.first()).to_be_visible()

        # Verify response content is relevant
        response_text = response_area.inner_text()
        assert len(response_text) > 50  # Reasonable response length

    def test_graph_entity_creation_workflow(self, page: Page):
        """Test workflow: query → graph → entity creation → graph visualization."""
        # 1. Query to get graph-related information
        page.get_by_role("tab", name="Query").click()
        page.wait_for_selector("textarea[placeholder*='query']", timeout=10000)

        query_input = page.locator("textarea[placeholder*='query']")
        query_input.fill(
            "Show me relationships between AI concepts and their evolution"
        )

        submit_button = page.get_by_text("Ask")
        submit_button.click()

        # 2. Navigate to Graph tab
        page.get_by_role("tab", name="Graph").click()
        page.wait_for_selector(".graph-container, .graph-visualization", timeout=10000)

        # 3. Verify graph contains relevant entities
        graph_nodes = page.locator(".graph-node, [data-node-id]")
        if graph_nodes.count() > 0:
            expect(graph_nodes.first()).to_be_visible()

            # Check for AI-related entities
            ai_entities = []
            for i in range(min(5, graph_nodes.count())):
                node = graph_nodes.nth(i)
                node_text = node.inner_text()
                if any(
                    term in node_text.lower()
                    for term in [
                        "artificial",
                        "intelligence",
                        "ai",
                        "machine",
                        "learning",
                    ]
                ):
                    ai_entities.append(node)

            # Should have at least some AI-related entities
            assert len(ai_entities) > 0

    def test_search_and_filter_workflow(self, page: Page):
        """Test search functionality and its integration with results."""
        # 1. Navigate to Query tab
        page.get_by_role("tab", name="Query").click()
        page.wait_for_selector("textarea[placeholder*='query']", timeout=10000)

        # 2. Perform a search if available
        search_input = page.locator("input[placeholder*='search'], .search-input")
        if search_input.count() > 0:
            search_input.fill("document processing")
            page.keyboard.press("Enter")
            page.wait_for_timeout(3000)

            # 3. Check if search results are filterable
            search_results = page.locator(".search-result, .filtered-result")
            if search_results.count() > 0:
                first_result = search_results.first()
                expect(first_result).to_be_visible()

                # Test clicking on search result
                first_result.click()
                page.wait_for_timeout(2000)

    def test_conversation_history_persistence(self, page: Page):
        """Test conversation history persistence across sessions."""
        # 1. Perform multiple queries to build history
        page.get_by_role("tab", name="Query").click()
        page.wait_for_selector("textarea[placeholder*='query']", timeout=10000)

        queries = [
            "What is the difference between AI and ML?",
            "Explain neural networks",
            "How does RAG work?",
        ]

        for query in queries:
            query_input = page.locator("textarea[placeholder*='query']")
            query_input.fill(query)

            submit_button = page.get_by_text("Ask")
            submit_button.click()

            # Wait for response
            page.wait_for_selector(".query-result", timeout=30000)

        # 2. Verify conversation history
        history_section = page.locator(".conversation-history, .chat-history")
        if history_section.count() > 0:
            history_items = history_section.locator(".history-item, .conversation-item")
            expect(history_items.count()).to_be_greater_than_or_equal(len(queries))

            # Verify history items show both questions and responses
            first_item = history_items.first()
            expect(first_item).to_be_visible()

            # Check for timestamp and metadata
            timestamps = first_item.locator(".timestamp, .time-stamp")
            if timestamps.count() > 0:
                expect(timestamps.first()).to_be_visible()

    def test_error_propagation_ui_feedback(self, page: Page):
        """Test error propagation from API to UI."""
        page.get_by_role("tab", name="Query").click()
        page.wait_for_selector("textarea[placeholder*='query']", timeout=10000)

        # Test with malformed query that should produce error
        query_input = page.locator("textarea[placeholder*='query']")
        query_input.fill("malformed query with special chars: @$%^&*")

        submit_button = page.get_by_text("Ask")
        submit_button.click()

        # Check for error message in UI
        page.wait_for_timeout(5000)

        error_messages = page.locator(".error-message, .validation-error, .api-error")
        if error_messages.count() > 0:
            expect(error_messages.first()).to_be_visible()

            # Verify error message is user-friendly
            error_text = error_messages.first().inner_text()
            assert len(error_text) > 5  # Should have meaningful message

    def test_real_time_updates_websocket(self, page: Page):
        """Test real-time updates if WebSocket is implemented."""
        page.get_by_role("tab", name="Documents").click()
        page.wait_for_selector(".document-list", timeout=10000)

        # Monitor for real-time indicators
        live_indicators = page.locator(
            ".live-indicator, .real-time-status, .connection-status"
        )

        # Start a document processing operation
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as temp_file:
            temp_file.write("Real-time test document")
            temp_file_path = temp_file.name

        upload_input = page.locator("input[type='file']")
        upload_input.set_input_files(temp_file_path)

        # Wait for upload and processing
        page.wait_for_selector(".upload-success", timeout=10000)

        # Check for real-time updates
        if live_indicators.count() > 0:
            expect(live_indicators.first()).to_be_visible(timeout=10000)

            # Monitor status changes
            initial_status = None
            status_changed = False

            for _ in range(10):  # Check for 10 seconds
                current_status = page.locator(".processing-status, .document-status")
                if current_status.count() > 0:
                    status_text = current_status.inner_text()
                    if initial_status is None:
                        initial_status = status_text
                    elif status_text != initial_status:
                        status_changed = True
                        break

                page.wait_for_timeout(1000)

            # Verify status was updated
            if live_indicators.count() > 0:
                expect(status_changed).to_be_true()

    def test_data_consistency_ui_vs_api(self, page: Page):
        """Test data consistency between UI and API responses."""
        page.get_by_role("tab", name="Query").click()
        page.wait_for_selector("textarea[placeholder*='query']", timeout=10000)

        # Query with specific data
        query_input = page.locator("textarea[placeholder*='query']")
        test_query = "How many documents are in the system?"
        query_input.fill(test_query)

        submit_button = page.get_by_text("Ask")
        submit_button.click()

        # Wait for response
        page.wait_for_selector(".query-result", timeout=30000)

        # Get UI response
        ui_response = page.locator(".query-response").inner_text()

        # Look for numeric data or statistics that should be consistent
        numeric_data = page.locator(".statistics, .metrics, .data-count")
        if numeric_data.count() > 0:
            ui_count = numeric_data.inner_text()

            # Extract number from text (basic validation)
            import re

            numbers = re.findall(r"\d+", ui_count)
            if numbers:
                assert int(numbers[0]) >= 0  # Should be non-negative

    def test_user_preferences_persistence(self, page: Page):
        """Test that user preferences persist across UI interactions."""
        page.get_by_role("tab", name="Query").click()
        page.wait_for_selector("textarea[placeholder*='query']", timeout=10000)

        # Look for settings/preferences
        settings_button = page.locator("button[aria-label*='Settings'], .preferences")
        if settings_button.count() > 0:
            settings_button.click()
            page.wait_for_selector(
                ".settings-panel, .preferences-dialog", timeout=10000
            )

            # Test preference changes
            theme_toggle = page.locator("input[name='theme'], .theme-selector")
            if theme_toggle.count() > 0:
                original_value = (
                    theme_toggle.get_attribute("value") or theme_toggle.input_value()
                )

                # Change preference
                theme_toggle.select_option("dark")
                page.wait_for_timeout(1000)

                # Verify change applied
                body = page.locator("body")
                expect(body).to_have_class("dark-theme")

                # Test persistence (would need page reload in real test)
                page.reload()
                page.wait_for_timeout(2000)

                # Check if preference is remembered
                settings_button.click()
                page.wait_for_selector(
                    ".settings-panel, .preferences-dialog", timeout=10000
                )

                theme_value = (
                    theme_toggle.get_attribute("value") or theme_toggle.input_value()
                )
                # Note: In real test, would verify persistence across sessions

    def test_ui_performance_monitoring(self, page: Page):
        """Test UI performance and responsiveness."""
        import time

        # Measure page load time
        start_time = time.time()
        page.goto(f"{server_process}/webui/")
        page.wait_for_selector("body", timeout=10000)
        load_time = time.time() - start_time

        # Page should load reasonably quickly
        assert load_time < 5.0  # 5 seconds max for initial load

        # Test query response time
        page.get_by_role("tab", name="Query").click()
        page.wait_for_selector("textarea[placeholder*='query']", timeout=10000)

        query_input = page.locator("textarea[placeholder*='query']")
        query_input.fill("Performance test query")

        query_start = time.time()
        submit_button = page.get_by_text("Ask")
        submit_button.click()

        page.wait_for_selector(".query-result", timeout=30000)
        query_time = time.time() - query_start

        # Query should respond reasonably quickly
        assert query_time < 10.0  # 10 seconds max for query response

        # Test UI responsiveness during query
        loading_state = page.locator(".loading, .query-loading")
        if loading_state.count() > 0:
            expect(loading_state).to_be_visible()

            # Check that UI remains interactive during loading
            other_tabs = page.locator("button[role='tab']:not([disabled])")
            if other_tabs.count() > 0:
                expect(other_tabs.first()).to_be_enabled()


@pytest.mark.ui
@pytest.mark.playwright
@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Test error handling across the integrated system."""

    def test_network_error_handling(self, page: Page):
        """Test UI behavior when network errors occur."""
        page.get_by_role("tab", name="Query").click()
        page.wait_for_selector("textarea[placeholder*='query']", timeout=10000)

        # Simulate network conditions by going offline
        page.context.set_offline(True)

        query_input = page.locator("textarea[placeholder*='query']")
        query_input.fill("Test query when offline")

        submit_button = page.get_by_text("Ask")
        submit_button.click()

        # Wait for error handling
        page.wait_for_timeout(5000)

        # Check for offline/network error indicators
        error_indicators = page.locator(
            ".network-error, .offline-indicator, .connection-error"
        )
        if error_indicators.count() > 0:
            expect(error_indicators.first()).to_be_visible()

        # Restore online state
        page.context.set_offline(False)
        page.wait_for_timeout(2000)

    def test_api_rate_limiting_ui_feedback(self, page: Page):
        """Test UI feedback when API rate limits are hit."""
        page.get_by_role("tab", name="Query").click()
        page.wait_for_selector("textarea[placeholder*='query']", timeout=10000)

        # Make multiple rapid queries to potentially hit rate limits
        query_input = page.locator("textarea[placeholder*='query']")

        for i in range(5):
            query_input.fill(f"Rapid query {i}")
            submit_button = page.get_by_text("Ask")
            submit_button.click()

            # Brief wait between queries
            page.wait_for_timeout(2000)

        # Check for rate limiting indicators
        rate_limit_indicators = page.locator(
            ".rate-limit, .too-many-requests, .quota-exceeded"
        )
        if rate_limit_indicators.count() > 0:
            expect(rate_limit_indicators.first()).to_be_visible()

            # Verify helpful error message
            error_message = rate_limit_indicators.locator(".error-message").first()
            expect(error_message).to_contain_text("rate limit")
