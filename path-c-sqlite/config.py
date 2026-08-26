"""Tunable settings for the SQLite-backed RAG assistant.

Everything a student is likely to experiment with lives here, mirroring the role
of src/config.js in Path A.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Shared knowledge base - the same markdown corpus that feeds Path A
DOCS_DIR = ROOT.parent / "knowledge-base"

# SQLite database holding chunks and their embedding vectors
DB_PATH = ROOT / "data" / "rag.db"

# Model aliases. Verify against `foundry model list` before changing these -
# an alias that does not exist fails confusingly at download time.
EMBEDDING_MODEL = "qwen3-embedding-0.6b"
CHAT_MODEL = "qwen2.5-0.5b"

# Chunking. Token counts are approximated by whitespace-separated words.
CHUNK_SIZE = 200
CHUNK_OVERLAP = 25

# How many chunks to put in front of the model
TOP_K = 3

APP_NAME = "summer_school_local_rag"

SYSTEM_PROMPT = (
    "You are an offline teaching assistant for a summer school in which students "
    "build a local RAG application with Microsoft Foundry Local.\n\n"
    "Answer the user's question using ONLY the context below. If the context does "
    "not contain enough information, say so plainly and do not guess.\n"
    "Never invent commands, package names, model aliases, or version numbers.\n"
    "Keep the answer short. Prefer bullet points and numbered steps.\n"
    "End with a Reference line naming the source documents you used.\n\n"
    "Context:\n{context}"
)
