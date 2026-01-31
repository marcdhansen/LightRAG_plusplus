import asyncio
import json
import sys
import tempfile
from functools import partial


def print_err(msg):
    print(msg, file=sys.stderr)


# Mock pipmaster to prevent it from hanging or doing network requests
class MockPipmaster:
    def is_installed(self, _name):
        return True

    def install(self, _name):
        pass


sys.modules["pipmaster"] = MockPipmaster()


def main():
    if len(sys.argv) < 3:
        print_err("Usage: python isolated_extract.py <repo_path> <text_json_path>")
        sys.exit(1)

    repo_path = sys.argv[1]
    input_path = sys.argv[2]

    print_err(f"Setting up PYTHONPATH: {repo_path}")
    sys.path.insert(0, repo_path)

    with open(input_path) as f:
        data = json.load(f)
        text = data["text"]

    try:
        print_err("Importing LightRAG...")
        from lightrag import LightRAG
        from lightrag.llm.ollama import ollama_embed, ollama_model_complete
        from lightrag.utils import EmbeddingFunc

        async def run():
            tmp_dir = tempfile.mkdtemp()
            print_err(f"Initializing LightRAG in {tmp_dir}...")
            # Ensure the correct model is used and passes through the hashing_kv correctly
            rag = LightRAG(
                working_dir=tmp_dir,
                llm_model_name="qwen2.5-coder:1.5b",
                llm_model_func=ollama_model_complete,
                embedding_func=EmbeddingFunc(
                    embedding_dim=768,
                    max_token_size=8192,
                    func=partial(
                        ollama_embed.func, embed_model="nomic-embed-text:v1.5"
                    ),
                ),
            )
            print_err("Initializing storages...")
            await rag.initialize_storages()
            print_err(f"Inserting text: {text[:50]}...")
            await rag.ainsert([text])
            print_err("Insertion complete.")

            entities = []
            try:
                print_err("Getting all nodes...")
                all_nodes = await rag.chunk_entity_relation_graph.get_all_nodes()
                for node in all_nodes:
                    entity_type = node.get("entity_type", node.get("type", "Unknown"))
                    entities.append({"name": node.get("id", ""), "type": entity_type})
            except Exception as e:
                print_err(f"Error getting nodes: {e}")

            print_err(f"Extracted {len(entities)} entities.")
            print(json.dumps(entities))

        asyncio.run(run())

    except Exception as e:
        print_err(f"Error during extraction: {e}")
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
