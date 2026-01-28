import pypdf
import os

pdf_path = "/Users/marchansen/antigravity_lightrag/LightRAG/docs/LightRAG-simple and fast retrieval-augmented generation.pdf"
output_path = (
    "/Users/marchansen/antigravity_lightrag/LightRAG/docs/beekeeping_test_data.txt"
)

if not os.path.exists(pdf_path):
    print(f"Error: {pdf_path} does not exist.")
    exit(1)

try:
    reader = pypdf.PdfReader(pdf_path)
    text = ""
    # Only extract a few pages if it's large, but let's try the whole thing first
    # or look for "beekeeping"
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if (
            "beekeeping" in page_text.lower()
            or "beekeeper" in page_text.lower()
            or "honey" in page_text.lower()
        ):
            text += f"--- Page {i + 1} ---\n"
            text += page_text + "\n"

    with open(output_path, "w") as f:
        f.write(text)
    print(f"Extraction successful. Saved to {output_path}")
except Exception as e:
    print(f"Error extracting PDF: {e}")
