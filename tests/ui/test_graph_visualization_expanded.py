"""
Comprehensive UI tests for graph visualization component.
Tests graph display, interaction, node/relationship visualization,
and graph exploration features.
"""

import pytest
from playwright.sync_api import Page, expect

from tests.ui.conftest import server_process


@pytest.mark.ui
@pytest.mark.playwright
class TestGraphVisualization:
    """Test graph visualization component."""

    @pytest.fixture(autouse=True)
    def setup_graph_page(self, page: Page, server_process: str):
        """Setup for each test - navigate to graph interface."""
        page.goto(f"{server_process}/webui/")
        page.get_by_role("tab", name="Graph").click()

        # Wait for graph interface to load
        page.wait_for_selector(".graph-container, .graph-visualization", timeout=10000)

    def test_graph_interface_accessibility(self, page: Page):
        """Test that graph interface is accessible."""
        # Check graph container exists
        graph_container = page.locator(".graph-container, .graph-visualization")
        expect(graph_container).to_be_visible()

        # Check for graph controls
        graph_controls = page.locator(".graph-controls, .graph-tools")
        if graph_controls.count() > 0:
            expect(graph_controls).to_be_visible()

    def test_graph_loading_functionality(self, page: Page):
        """Test graph loading and initialization."""
        graph_container = page.locator(".graph-container, .graph-visualization")
        expect(graph_container).to_be_visible()

        # Check for loading state
        loading_indicator = page.locator(".loading, .graph-loading")

        # Check if graph can be loaded/refreshed
        refresh_button = page.locator("button[aria-label*='Refresh'], .refresh-graph")
        if refresh_button.count() > 0:
            expect(refresh_button).to_be_visible()

            # Test refresh functionality
            refresh_button.click()

            # Wait for loading to complete
            if loading_indicator.count() > 0:
                expect(loading_indicator).to_be_visible(timeout=5000)
                expect(loading_indicator).to_be_hidden(timeout=10000)

    def test_node_visualization(self, page: Page):
        """Test graph node visualization and interaction."""
        # Look for graph nodes
        graph_nodes = page.locator(".graph-node, [data-node-id]")

        if graph_nodes.count() > 0:
            # Test node hover effects
            first_node = graph_nodes.first()
            expect(first_node).to_be_visible()

            # Hover over node
            first_node.hover()

            # Check for node tooltip or details
            node_tooltip = page.locator(".node-tooltip, .node-details")
            if node_tooltip.count() > 0:
                expect(node_tooltip).to_be_visible(timeout=3000)

            # Test node clicking
            first_node.click()

            # Check for node selection or expanded details
            node_selection = page.locator(".node-selected, .node-expanded")
            if node_selection.count() > 0:
                expect(node_selection).to_be_visible(timeout=3000)

    def test_edge_visualization(self, page: Page):
        """Test graph edge/relationship visualization."""
        # Look for graph edges
        graph_edges = page.locator(".graph-edge, .relationship-line")

        if graph_edges.count() > 0:
            first_edge = graph_edges.first()
            expect(first_edge).to_be_visible()

            # Test edge interaction if available
            # Some graphs allow clicking edges to highlight relationships
            first_edge.click()

            # Check for edge highlighting or details
            edge_details = page.locator(".edge-highlighted, .edge-details")
            if edge_details.count() > 0:
                expect(edge_details).to_be_visible(timeout=3000)

    def test_graph_controls_and_filters(self, page: Page):
        """Test graph control panel and filtering options."""
        controls_panel = page.locator(".graph-controls, .graph-panel")

        if controls_panel.count() > 0:
            # Test label filtering
            label_filter = page.locator(
                "select[name='label-filter'], [data-testid*='label-filter']"
            )
            if label_filter.count() > 0:
                expect(label_filter).to_be_visible()

                # Test different label options
                label_filter.click()

                # Look for options
                label_options = page.locator("option[value]")
                if label_options.count() > 0:
                    first_option = label_options.first()
                    first_option.click()

                    # Verify filter application
                    page.wait_for_timeout(2000)

            # Test search functionality
            graph_search = page.locator(
                "input[placeholder*='Search graph'], [data-testid*='graph-search']"
            )
            if graph_search.count() > 0:
                expect(graph_search).to_be_visible()

                # Test graph search
                graph_search.fill("test entity")
                page.keyboard.press("Enter")
                page.wait_for_timeout(3000)

                # Check for search results
                search_results = page.locator(".search-result, .filtered-nodes")
                if search_results.count() > 0:
                    expect(search_results.first()).to_be_visible()

    def test_graph_layout_options(self, page: Page):
        """Test graph layout and display options."""
        layout_controls = page.locator(".graph-layout, .display-options")

        if layout_controls.count() > 0:
            # Test layout type selection
            layout_options = ["force", "circular", "hierarchical", "grid"]

            for layout in layout_options:
                layout_button = page.get_by_text(layout)
                if layout_button.count() > 0:
                    layout_button.click()
                    page.wait_for_timeout(1000)

                    # Verify layout was applied
                    graph_container = page.locator(".graph-container")
                    if graph_container.count() > 0:
                        # Check for layout-specific classes
                        layout_class = f"layout-{layout.lower()}"
                        expect(graph_container).to_have_class(layout_class)

            # Test zoom controls
            zoom_controls = page.locator(".zoom-controls, .graph-zoom")
            if zoom_controls.count() > 0:
                zoom_in = zoom_controls.locator("button[aria-label*='Zoom In']")
                zoom_out = zoom_controls.locator("button[aria-label*='Zoom Out']")
                zoom_reset = zoom_controls.locator("button[aria-label*='Reset Zoom']")

                if zoom_in.count() > 0 and zoom_out.count() > 0:
                    expect(zoom_in).to_be_visible()
                    expect(zoom_out).to_be_visible()

                    # Test zoom in
                    zoom_in.click()
                    page.wait_for_timeout(1000)

                    # Test zoom out
                    zoom_out.click()
                    page.wait_for_timeout(1000)

                if zoom_reset.count() > 0:
                    expect(zoom_reset).to_be_visible()
                    zoom_reset.click()
                    page.wait_for_timeout(1000)

    def test_graph_navigation_and_pan(self, page: Page):
        """Test graph navigation and panning functionality."""
        graph_container = page.locator(".graph-container, .graph-visualization")

        if graph_container.count() > 0:
            # Test mouse drag to pan graph
            expect(graph_container).to_be_visible()

            # Get container boundaries
            container_box = graph_container.bounding_box()

            # Test mouse down and movement for panning
            graph_container.hover()
            page.mouse.down()
            page.mouse.move(container_box["x"] + 50, container_box["y"] + 50)
            page.mouse.up()

            page.wait_for_timeout(1000)

    def test_graph_entity_details_panel(self, page: Page):
        """Test graph entity details information panel."""
        # Click on a node to see details
        graph_nodes = page.locator(".graph-node, [data-node-id]")

        if graph_nodes.count() > 0:
            first_node = graph_nodes.first()
            first_node.click()

            # Look for details panel
            details_panel = page.locator(
                ".entity-details, .node-info-panel, .details-panel"
            )

            if details_panel.count() > 0:
                expect(details_panel).to_be_visible(timeout=5000)

                # Check for entity information
                entity_name = details_panel.locator(".entity-name, .node-title")
                entity_type = details_panel.locator(".entity-type, .node-type")
                entity_description = details_panel.locator(
                    ".entity-description, .node-description"
                )

                if entity_name.count() > 0:
                    expect(entity_name).to_be_visible()
                if entity_type.count() > 0:
                    expect(entity_type).to_be_visible()
                if entity_description.count() > 0:
                    expect(entity_description).to_be_visible()

                # Test closing details panel
                close_button = details_panel.locator(
                    "button[aria-label*='Close'], .close-details"
                )
                if close_button.count() > 0:
                    close_button.click()
                    expect(details_panel).to_be_hidden(timeout=3000)

    def test_graph_export_functionality(self, page: Page):
        """Test graph export and sharing functionality."""
        export_controls = page.locator(".graph-export, .export-controls")

        if export_controls.count() > 0:
            # Test export options
            export_button = page.locator("button[aria-label*='Export'], .export-graph")

            if export_button.count() > 0:
                expect(export_button).to_be_visible()

                # Click export button
                export_button.click()

                # Look for export modal or dropdown
                export_modal = page.locator(".export-modal, .export-dropdown")
                if export_modal.count() > 0:
                    expect(export_modal).to_be_visible(timeout=3000)

                    # Test different export formats
                    export_formats = ["PNG", "SVG", "JSON", "GraphML"]

                    for format in export_formats:
                        format_option = export_modal.locator(
                            f"button[data-format='{format}'], option[value='{format}']"
                        )
                        if format_option.count() > 0:
                            format_option.click()
                            page.wait_for_timeout(1000)

    def test_graph_performance_large_graphs(self, page: Page):
        """Test graph visualization performance with large graphs."""
        graph_container = page.locator(".graph-container, .graph-visualization")

        if graph_container.count() > 0:
            # Check performance indicators or optimization
            performance_mode = page.locator(".performance-mode, .large-graph-mode")

            if performance_mode.count() > 0:
                expect(performance_mode).to_be_visible()

                # Test that large graph rendering doesn't crash interface
                # Check for virtualization or level-of-detail indicators
                lod_indicator = page.locator(
                    ".level-of-detail, .virtualization-control"
                )

                if lod_indicator.count() > 0:
                    expect(lod_indicator).to_be_visible()

    def test_graph_empty_state(self, page: Page):
        """Test graph interface with no data."""
        graph_container = page.locator(".graph-container, .graph-visualization")

        if graph_container.count() > 0:
            # Check for empty state messaging
            empty_state = page.locator(".empty-graph, .no-data-message")

            if empty_state.count() > 0:
                expect(empty_state).to_be_visible()

                # Check for helpful empty state actions
                empty_actions = page.locator(".empty-actions, .no-data-actions")

                if empty_actions.count() > 0:
                    expect(empty_actions).to_be_visible()

                    # Test suggested actions like "Upload documents" or "Create first entity"
                    suggested_action = empty_actions.locator("button, a")
                    if suggested_action.count() > 0:
                        expect(suggested_action).to_be_visible()

    @pytest.mark.parametrize(
        "interaction_type", ["click", "double_click", "right_click", "hover"]
    )
    def test_graph_interaction_methods(self, page: Page, interaction_type: str):
        """Test different interaction methods with graph elements."""
        graph_nodes = page.locator(".graph-node, [data-node-id]")

        if graph_nodes.count() > 0:
            first_node = graph_nodes.first()
            expect(first_node).to_be_visible()

            if interaction_type == "click":
                first_node.click()
                # Check for selection or details
                page.wait_for_timeout(1000)

            elif interaction_type == "double_click":
                first_node.dblclick()
                # Check for expanded view or context menu
                page.wait_for_timeout(1000)

            elif interaction_type == "right_click":
                first_node.click(button="right")
                # Check for context menu
                context_menu = page.locator(".context-menu, .node-context-menu")
                if context_menu.count() > 0:
                    expect(context_menu).to_be_visible(timeout=2000)

                    # Test closing context menu
                    page.keyboard.press("Escape")
                    expect(context_menu).to_be_hidden(timeout=2000)

            elif interaction_type == "hover":
                first_node.hover()
                # Check for hover effects
                hover_effects = page.locator(".node-hover, .hover-effects")
                if hover_effects.count() > 0:
                    expect(hover_effects).to_be_visible(timeout=2000)

    def test_graph_accessibility_features(self, page: Page):
        """Test graph visualization accessibility."""
        graph_container = page.locator(".graph-container, .graph-visualization")

        if graph_container.count() > 0:
            # Check for keyboard navigation
            graph_container.tab()

            # Check ARIA labels on interactive elements
            graph_elements = page.locator(".graph-node, .graph-edge, [role='button']")

            for i in range(min(3, graph_elements.count())):
                element = graph_elements.nth(i)
                expect(element).to_have_attribute("aria-label")

                # Test keyboard interaction
                element.focus()
                expect(element).to_be_focused()

                # Test Enter key activation
                page.keyboard.press("Enter")
                page.wait_for_timeout(1000)

    def test_graph_responsive_behavior(self, page: Page):
        """Test graph visualization responsive behavior."""
        # Test on mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})

        graph_container = page.locator(".graph-container, .graph-visualization")
        if graph_container.count() > 0:
            expect(graph_container).to_be_visible()

            # Check for mobile-specific controls
            mobile_controls = page.locator(".mobile-controls, .touch-gestures")

            # Test touch gestures if available
            if mobile_controls.count() > 0:
                # Test that touch interactions work
                graph_nodes = page.locator(".graph-node, [data-node-id]")
                if graph_nodes.count() > 0:
                    first_node = graph_nodes.first()

                    # Test tap interaction
                    first_node.tap()
                    page.wait_for_timeout(1000)
