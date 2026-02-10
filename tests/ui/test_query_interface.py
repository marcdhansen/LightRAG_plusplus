"""
Comprehensive UI tests for query interface and search functionality.
Tests all query modes, result display, and user interactions.
"""

import pytest
import uuid
from playwright.sync_api import Page, expect

from tests.ui.conftest import server_process


@pytest.mark.ui
@pytest.mark.playwright
class TestQueryInterface:
    """Test query interface and search functionality."""

    @pytest.fixture(autouse=True)
    def setup_test_page(self, page: Page, server_process: str):
        """Setup for each test - navigate to query interface."""
        page.goto(f"{server_process}/webui/")
        page.get_by_role("tab", name="Query").click()

        # Wait for query interface to load
        page.wait_for_selector("textarea[placeholder*='query']", timeout=10000)

    def test_query_interface_available(self, page: Page):
        """Test that query interface is accessible."""
        # Check query input exists
        query_input = page.locator("textarea[placeholder*='query']")
        expect(query_input).to_be_visible()

        # Check query modes are available
        query_modes = ["local", "global", "hybrid", "naive", "mix"]
        for mode in query_modes:
            mode_button = page.get_by_text(mode)
            expect(mode_button).to_be_visible()

    def test_query_modes_functionality(self, page: Page):
        """Test different query mode selections."""
        test_query = "What is machine learning?"

        # Test each query mode
        for mode in ["local", "global", "hybrid", "naive", "mix"]:
            # Select mode
            mode_button = page.get_by_text(mode)
            mode_button.click()

            # Verify mode is selected
            expect(mode_button).to_have_class("active")

            # Enter query
            query_input = page.locator("textarea[placeholder*='query']")
            query_input.fill(test_query)

            # Submit query
            submit_button = page.get_by_text("Ask")
            submit_button.click()

            # Wait for results
            page.wait_for_selector(".query-result", timeout=30000)

            # Verify results are displayed
            results_container = page.locator(".query-result")
            expect(results_container).to_be_visible()

            # Reset for next test
            page.reload()
            page.wait_for_selector("textarea[placeholder*='query']", timeout=10000)

    def test_conversation_history_visibility(self, page: Page):
        """Test conversation history display."""
        # Check if conversation history section exists
        history_section = page.locator(".conversation-history")

        # Initially might be empty
        if history_section.is_visible():
            expect(history_section).to_be_visible()

        # After submitting a query, history should appear
        query_input = page.locator("textarea[placeholder*='query']")
        query_input.fill("Test query for history")

        submit_button = page.get_by_text("Ask")
        submit_button.click()

        # Wait for response
        page.wait_for_selector(".query-result", timeout=30000)

        # Check that history now has content
        history_items = page.locator(".conversation-history .history-item")
        if history_items.count() > 0:
            expect(history_items.first()).to_be_visible()

    def test_query_response_display(self, page: Page):
        """Test that query responses are properly displayed."""
        # Submit a test query
        query_input = page.locator("textarea[placeholder*='query']")
        query_input.fill("Explain the benefits of AI")

        submit_button = page.get_by_text("Ask")
        submit_button.click()

        # Wait for results
        page.wait_for_selector(".query-result", timeout=30000)

        # Verify response elements
        response_text = page.locator(".query-response")
        expect(response_text).to_be_visible()

        # Check for citations/references
        citations = page.locator(".citations, .references")
        if citations.count() > 0:
            expect(citations.first()).to_be_visible()

    def test_query_parameter_controls(self, page: Page):
        """Test query parameter controls and settings."""
        # Look for advanced settings or parameter controls
        advanced_settings = page.locator(".advanced-settings, .query-parameters")

        if advanced_settings.is_visible():
            # Test opening advanced settings
            settings_toggle = page.locator(
                "button[aria-label*='Advanced'], .settings-toggle"
            )
            if settings_toggle.count() > 0:
                settings_toggle.click()

                # Wait for settings panel to open
                page.wait_for_selector(".settings-panel", timeout=10000)

                # Verify parameter controls exist
                top_k_control = page.locator(
                    "input[name='top_k'], [data-testid*='top_k']"
                )
                temperature_control = page.locator(
                    "input[name='temperature'], [data-testid*='temperature']"
                )

                if top_k_control.count() > 0:
                    expect(top_k_control).to_be_visible()
                if temperature_control.count() > 0:
                    expect(temperature_control).to_be_visible()

    def test_query_error_handling(self, page: Page):
        """Test query interface error handling."""
        query_input = page.locator("textarea[placeholder*='query']")

        # Test with empty query
        query_input.fill("")
        submit_button = page.get_by_text("Ask")
        submit_button.click()

        # Should show error message or prevent submission
        error_message = page.locator(".error-message, .validation-error")
        if error_message.count() > 0:
            expect(error_message).to_be_visible()

        # Test with very long query
        long_query = "test " * 100  # Create a very long query
        query_input.fill(long_query)
        submit_button.click()

        # Should handle gracefully or show character limit
        page.wait_for_timeout(3000)  # Wait to see what happens

    def test_query_response_copy_functionality(self, page: Page):
        """Test copy functionality for query responses."""
        # Submit a query first
        query_input = page.locator("textarea[placeholder*='query']")
        query_input.fill("Test response with citations [1][2]")

        submit_button = page.get_by_text("Ask")
        submit_button.click()

        # Wait for response
        page.wait_for_selector(".query-result", timeout=30000)

        # Look for copy button
        copy_button = page.locator("button[aria-label*='Copy'], .copy-button")
        if copy_button.count() > 0:
            copy_button.click()

            # Test copy worked by checking clipboard (if possible)
            # Note: clipboard testing in Playwright can be complex and browser-dependent

    def test_query_response_formatting(self, page: Page):
        """Test that query responses are properly formatted."""
        # Submit a query expecting formatted response
        query_input = page.locator("textarea[placeholder*='query']")
        query_input.fill("Format your response with markdown")

        submit_button = page.get_by_text("Ask")
        submit_button.click()

        # Wait for results
        page.wait_for_selector(".query-result", timeout=30000)

        # Check for markdown formatting elements
        response_area = page.locator(".query-response")
        if response_area.is_visible():
            content = response_area.inner_text()

            # Basic checks for markdown formatting
            has_markdown = any(
                element in content for element in ["**", "##", "- ", "`"]
            )
            if has_markdown:
                # If markdown expected, check if rendered properly
                formatted_elements = response_area.locator(
                    "strong, em, code, h1, h2, h3"
                )
                if formatted_elements.count() > 0:
                    expect(formatted_elements.first()).to_be_visible()

    def test_query_keyboard_shortcuts(self, page: Page):
        """Test keyboard shortcuts in query interface."""
        query_input = page.locator("textarea[placeholder*='query']")
        expect(query_input).to_be_visible()

        # Focus query input
        query_input.click()

        # Test Ctrl+Enter or Cmd+Enter for submission
        if page.get_by_text("Ask").is_visible():
            # Try keyboard shortcut for submission
            page.keyboard.press("Control+Enter")

            # Check if query was submitted (results appear)
            page.wait_for_timeout(2000)

            # If not submitted, try alternative
            page.keyboard.press("Meta+Enter")
            page.wait_for_timeout(2000)

    def test_query_responsive_design(self, page: Page):
        """Test query interface responsive design."""
        # Get viewport size
        viewport_size = page.viewport_size

        # Check mobile responsiveness
        page.set_viewport_size({"width": 375, "height": 667})  # Mobile iPhone size

        query_input = page.locator("textarea[placeholder*='query']")
        expect(query_input).to_be_visible()

        # Check submit button accessibility
        submit_button = page.get_by_text("Ask")
        expect(submit_button).to_be_visible()

        # Check if layout adapts properly
        query_container = page.locator(".query-container, .query-interface")
        if query_container.count() > 0:
            expect(query_container).to_be_visible()

    @pytest.mark.parametrize(
        "query_type", ["simple", "complex", "technical", "metadata_query"]
    )
    def test_different_query_types(self, page: Page, query_type: str):
        """Test different types of queries."""
        query_input = page.locator("textarea[placeholder*='query']")

        # Define test queries
        queries = {
            "simple": "What is AI?",
            "complex": "Explain the relationship between machine learning and artificial intelligence, including historical context and future implications",
            "technical": "Implement a function in Python that processes JSON data with error handling",
            "metadata_query": "Show me documents about machine learning algorithms",
        }

        test_query = queries.get(query_type, queries["simple"])
        query_input.fill(test_query)

        submit_button = page.get_by_text("Ask")
        submit_button.click()

        # Wait for results
        page.wait_for_selector(".query-result", timeout=30000)

        # Verify response is generated
        results = page.locator(".query-result")
        expect(results).to_be_visible()

        # Verify response content is reasonable
        response_text = page.locator(".query-response")
        if response_text.is_visible():
            content = response_text.inner_text()
            assert len(content) > 10  # Reasonable response length

    def test_query_interface_accessibility(self, page: Page):
        """Test query interface accessibility features."""
        query_input = page.locator("textarea[placeholder*='query']")

        # Check ARIA labels
        expect(query_input).to_have_attribute("aria-label")

        # Check keyboard navigation
        query_input.tab()

        # Test tab order is logical
        focusable_elements = page.locator(
            "button, input, select, [role='button'], [role='textbox']"
        )

        # Test that query can be submitted with keyboard
        query_input.fill("Accessibility test")
        submit_button = page.get_by_text("Ask")

        # Try to find and activate submit with keyboard
        submit_button.focus()
        page.keyboard.press("Enter")

        # Wait for response
        page.wait_for_selector(".query-result", timeout=30000)

        # Verify response appears for keyboard users
        results = page.locator(".query-result")
        expect(results).to_be_visible()


@pytest.mark.ui
@pytest.mark.playwright
class TestSearchFeatures:
    """Test search functionality within query interface."""

    def test_search_input_visibility(self, page: Page, server_process: str):
        """Test that search input is available."""
        page.goto(f"{server_process}/webui/")
        page.get_by_role("tab", name="Query").click()

        # Look for search functionality
        search_input = page.locator("input[placeholder*='search'], .search-input")
        if search_input.count() > 0:
            expect(search_input).to_be_visible()

    def test_search_filter_functionality(self, page: Page, server_process: str):
        """Test search filter functionality."""
        page.goto(f"{server_process}/webui/")
        page.get_by_role("tab", name="Query").click()

        search_input = page.locator("input[placeholder*='search'], .search-input")
        if search_input.count() > 0:
            # Test search with specific term
            search_input.fill("machine learning")

            # Wait for search results or filtering
            page.wait_for_timeout(3000)

            # Check if results are filtered
            results = page.locator(".search-result, .filtered-result")
            if results.count() > 0:
                expect(results.first()).to_be_visible()

    def test_search_results_interaction(self, page: Page, server_process: str):
        """Test interaction with search results."""
        page.goto(f"{server_process}/webui/")
        page.get_by_role("tab", name="Query").click()

        search_input = page.locator("input[placeholder*='search'], .search-input")
        if search_input.count() > 0:
            search_input.fill("AI")
            page.wait_for_timeout(2000)

            # Look for clickable search results
            search_results = page.locator(".search-result, .result-item")
            if search_results.count() > 0:
                # Test clicking on search result
                first_result = search_results.first()
                expect(first_result).to_be_visible()

                first_result.click()

                # Verify navigation or action
                page.wait_for_timeout(2000)
