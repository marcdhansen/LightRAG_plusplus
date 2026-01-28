import uuid

from playwright.sync_api import Page, expect


# @pytest.mark.skip(reason="Flaky in automated environment, requires investigation")
# Unskipping for debugging
# @pytest.mark.skip(reason="Flaky in automated environment, requires investigation")
def test_document_upload_flow(page: Page, server_process: str, tmp_path):
    """
    Verifies that a user can upload a document successfully.
    """
    # Create a dummy text file with unique name to avoid 'duplicated' error which prevents list refresh
    # keeping filename short (<20 chars) to avoid UI truncation
    unique_id = uuid.uuid4().hex[:6]
    file_name = f"t_{unique_id}.txt"
    file_content = f"This is a dummy document for automated UI testing. ID: {unique_id}"
    file_path = tmp_path / file_name
    file_path.write_text(file_content)

    # 1. Navigate to the web UI
    page.goto(f"{server_process}/webui/")

    # 2. Navigate to "Documents" tab (it's the default, but let's be explicit)
    # The 'Documents' tab value is 'documents'
    documents_tab = page.get_by_role("tab", name="Documents")
    if documents_tab.is_visible():
        documents_tab.click()

    # 3. Open Upload Dialog
    # Button has text "Upload" (from en.json: documentPanel.uploadDocuments.button)
    # Using exact=False to match even if there's an icon
    upload_btn = page.get_by_role("button", name="Upload", exact=True)
    upload_btn.click()

    # 4. Upload the file
    # react-dropzone usually creates a hidden input[type="file"]
    # We use force=True because dropzone inputs are often hidden
    file_input = page.locator("input[type='file']")
    file_input.set_input_files(str(file_path))

    # 5. Wait for the file to appear in the list
    # The upload triggers a list refresh.
    # We wait for the filename to appear in the table.
    # This acts as confirmation of success.
    # We allow a longer timeout for the upload and processing.
    try:
        # Use get_by_text which is often more robust than role for cell content
        expect(page.get_by_text(file_name)).to_be_visible(timeout=30000)
    except AssertionError:
        # If not initially visible, try reloading page
        print(f"\n[DEBUG] File {file_name} not found, reloading...")
        page.reload()
        # Wait for table to load
        page.wait_for_selector("table")
        try:
            expect(page.get_by_text(file_name)).to_be_visible(timeout=10000)
        except AssertionError:
            print(
                f"\n[DEBUG] Page Text Content:\n{page.locator('body').text_content()}"
            )
            raise

    # 6. Close the dialog if it doesn't close automatically
    # Check if dialog is still open (look for Close button or title)
    dialog_close = page.locator("button[aria-label='Close']")
    if dialog_close.is_visible():
        dialog_close.click()
    else:
        # Press Escape just in case
        page.keyboard.press("Escape")

    # 7. Final verification
    expect(page.get_by_text(file_name)).to_be_visible()
