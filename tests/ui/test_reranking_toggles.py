from playwright.sync_api import Page, expect


def test_reranking_toggles_visibility(page: Page, server_process: str):
    """
    Verifies that reranking-specific toggles are conditionally visible based on the 'Enable Rerank' switch.
    """
    # 1. Navigate to the Retrieval tab
    page.goto(f"{server_process}/webui/")

    # Click "Retrieval" tab if not active (it usually is by default)
    retrieval_tab = page.get_by_role("tab", name="Retrieval")
    retrieval_tab.click()

    # 2. Locate the main 'Enable Rerank' switch
    # In QuerySettings.tsx: <Checkbox id="enable_rerank" ... />
    enable_rerank_checkbox = page.locator("#enable_rerank")

    # 3. Initially, we check what the state is.
    # If checked, then the sub-toggles should be visible.
    # If unchecked, they should be hidden.

    is_rerank_enabled = enable_rerank_checkbox.is_checked()

    rerank_entities_checkbox = page.locator("#rerank_entities")
    rerank_relations_checkbox = page.locator("#rerank_relations")

    if is_rerank_enabled:
        expect(rerank_entities_checkbox).to_be_visible()
        expect(rerank_relations_checkbox).to_be_visible()
        # Uncheck it and verify they disappear
        enable_rerank_checkbox.click()
        expect(rerank_entities_checkbox).not_to_be_visible()
        expect(rerank_relations_checkbox).not_to_be_visible()
    else:
        expect(rerank_entities_checkbox).not_to_be_visible()
        expect(rerank_relations_checkbox).not_to_be_visible()
        # Check it and verify they appear
        enable_rerank_checkbox.click()
        expect(rerank_entities_checkbox).to_be_visible()
        expect(rerank_relations_checkbox).to_be_visible()


def test_reranking_toggles_defaults(page: Page, server_process: str):
    """
    Verifies that reranking-specific toggles are enabled by default when 'Enable Rerank' is active.
    """
    page.goto(f"{server_process}/webui/")

    enable_rerank_checkbox = page.locator("#enable_rerank")

    # Ensure Rerank is enabled
    if not enable_rerank_checkbox.is_checked():
        enable_rerank_checkbox.click()

    rerank_entities_checkbox = page.locator("#rerank_entities")
    rerank_relations_checkbox = page.locator("#rerank_relations")

    expect(rerank_entities_checkbox).to_be_checked()
    expect(rerank_relations_checkbox).to_be_checked()
