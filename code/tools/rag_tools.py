from smolagents import Tool
import chromadb
from paths import VECTOR_DB_DIR

client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
collection = client.get_or_create_collection(name="knowledge_base")

class WriteToRAGTool(Tool):
    name = "write_to_rag"
    description = "Writes cleaned data or findings into the RAG/Knowledge Base."
    inputs = {
        "key": {
            "type": "string",
            "description": "The key to store the data under."
        },
        "data": {
            "type": "string",
            "description": "The information to store."
        }
    }
    output_type = "string"

    def forward(self, key: str, data: str) -> str:
        collection.upsert(ids=[key], documents=[data])
        return f"Successfully wrote data to {key}"

class ReadFromRAGTool(Tool):
    name = "read_from_rag"
    description = "Reads context or data from the RAG/Knowledge Base by key."
    inputs = {
        "key": {
            "type": "string",
            "description": "The key to read data from."
        }
    }
    output_type = "string"

    def forward(self, key: str) -> str:
        result = collection.get(ids=[key])
        if result and result.get("documents") and len(result["documents"]) > 0:
            return result["documents"][0]
        return "Key not found in Knowledge Base."
