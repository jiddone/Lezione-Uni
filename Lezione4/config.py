"""Configurazione condivisa per la KB locale della Lezione 4."""
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "data" / "docs"
CHROMA_DIR = BASE_DIR / "storage" / "chroma"
PROMPT_PATH = BASE_DIR / "prompts" / "rag_prompt.txt"
CLASSIFICATION_PROMPT_PATH = BASE_DIR / "prompts" / "classification_prompt.txt"
COT_CLASSIFICATION_PROMPT_PATH = BASE_DIR / "prompts" / "cot_prompt.txt"
DEFAULT_LOG_DATASET_PATH = BASE_DIR / "data" / "Logs.csv"
DEFAULT_CLASSIFICATION_OUTPUT_PATH = BASE_DIR / "data" / "Logs-rag-classified.csv"

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gpt-oss:120b-cloud"
OLLAMA_TIMEOUT = 600
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHROMA_COLLECTION = "lezione4_kb"
SUPPORTED_EXTENSIONS = [".md"]
CHUNK_SIZE = 700
CHUNK_OVERLAP = 120
SIMILARITY_TOP_K = 3
CLASSIFICATION_BATCH_SIZE = 50