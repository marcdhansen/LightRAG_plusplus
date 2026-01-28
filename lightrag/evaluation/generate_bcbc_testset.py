import json
import os
import random

from openai import OpenAI
from pypdf import PdfReader
from tqdm import tqdm

# Configuration
PDF_PATH = "final_report_BCBC.pdf"
OUTPUT_FILE = "lightrag/evaluation/bcbc_testset.json"
NUM_QUESTIONS = 20
MODEL_NAME = "qwen2.5-coder:1.5b"  # Use the one from .env
API_BASE = "http://localhost:11434/v1"
API_KEY = "ollama"


def extract_text_from_pdf(pdf_path):
    print(f"Reading {pdf_path}...")
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def chunk_text(text, chunk_size=1000, overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def generate_qa_pair(client, context):
    prompt = f"""
    You are an expert in the British Columbia Building Code.
    Based on the following text context, generate 1 highly specific question and its correct answer.

    Context:
    {context}

    Format your response as a valid JSON object with 'question' and 'ground_truth' fields.
    Example:
    {{
        "question": "What is the maximum height of...",
        "ground_truth": "The maximum height is..."
    }}

    Only return the JSON object. Do not add markdown formatting.
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Low temp for factual accuracy
            max_tokens=512,
        )
        content = response.choices[0].message.content.strip()
        # Clean up potential markdown code blocks
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "")
        elif content.startswith("```"):
            content = content.replace("```", "")

        return json.loads(content)
    except Exception as e:
        print(f"Error generating QA: {e}")
        return None


def main():
    if not os.path.exists(PDF_PATH):
        print(f"Error: {PDF_PATH} not found.")
        return

    # 1. Extract Text
    text = extract_text_from_pdf(PDF_PATH)
    if not text.strip():
        print("Error: No text extracted from PDF.")
        return

    print(f"Extracted {len(text)} characters.")

    # 2. Chunk Text
    chunks = chunk_text(text)
    print(f"Created {len(chunks)} text chunks.")

    # 3. Select Random Chunks for Variety
    selected_chunks = random.sample(chunks, min(NUM_QUESTIONS, len(chunks)))

    # 4. Generate QA
    client = OpenAI(base_url=API_BASE, api_key=API_KEY)
    test_cases = []

    print("Generating Questions...")
    for _i, chunk in enumerate(tqdm(selected_chunks)):
        qa = generate_qa_pair(client, chunk)
        if qa and "question" in qa and "ground_truth" in qa:
            test_cases.append(
                {
                    "question": qa["question"],
                    "ground_truth": qa["ground_truth"],
                    "project": "bcbc_evaluation",
                    "context": chunk,  # Optional: Save context for reference (not used by Ragas directly usually unless specified)
                }
            )

    # 5. Save to JSON
    output_data = {"test_cases": test_cases}
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"Successfully saved {len(test_cases)} test cases to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
