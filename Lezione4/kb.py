"""Helper condivisi per ingest e query della KB locale."""
from pathlib import Path

import chromadb
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.vector_stores.types import MetadataFilter, MetadataFilters
from llama_index.vector_stores.chroma import ChromaVectorStore

from config import (
    CHROMA_COLLECTION,
    CHROMA_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DOCS_DIR,
    EMBED_MODEL,
    SUPPORTED_EXTENSIONS,
)


def build_metadata(file_path: str) -> dict:
    path = Path(file_path)
    return {
        "doc_type": "reference",
        "file_name": path.name,
        "source": str(path.resolve()),
    }


def get_embed_model() -> HuggingFaceEmbedding:
    return HuggingFaceEmbedding(model_name=EMBED_MODEL)


def get_chroma_client() -> chromadb.PersistentClient:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_collection(recreate: bool = False):
    client = get_chroma_client()
    if recreate:
        try:
            client.delete_collection(CHROMA_COLLECTION)
        except Exception:
            pass
    return client.get_or_create_collection(CHROMA_COLLECTION)


def get_vector_store(recreate: bool = False) -> ChromaVectorStore:
    return ChromaVectorStore(chroma_collection=get_collection(recreate=recreate))


def load_documents() -> list:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    documents = SimpleDirectoryReader(
        input_dir=str(DOCS_DIR),
        required_exts=SUPPORTED_EXTENSIONS,
        file_metadata=build_metadata,
        filename_as_id=True,
    ).load_data()

    if not documents:
        raise RuntimeError(f"Nessun documento trovato in {DOCS_DIR}.")
    return documents


def reference_only_filters() -> MetadataFilters:
    return MetadataFilters(
        filters=[MetadataFilter(key="doc_type", value="reference")]
    )


def build_index(documents: list) -> VectorStoreIndex:
    storage_context = StorageContext.from_defaults(
        vector_store=get_vector_store(recreate=True)
    )
    splitter = SentenceSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_model=get_embed_model(),
        transformations=[splitter],
        show_progress=True,
    )


def load_index() -> VectorStoreIndex:
    return VectorStoreIndex.from_vector_store(
        vector_store=get_vector_store(recreate=False),
        embed_model=get_embed_model(),
    )


def collection_stats() -> dict:
    collection = get_collection(recreate=False)
    return {
        "name": CHROMA_COLLECTION,
        "count": collection.count(),
    }


def get_source_name(metadata: dict) -> str:
    file_name = metadata.get("file_name")
    if file_name:
        return file_name

    source = metadata.get("source")
    if source:
        return Path(source).name

    return "sorgente-sconosciuta"


def build_context(nodes: list) -> str:
    chunks = []
    for index, node in enumerate(nodes, start=1):
        source_name = get_source_name(node.metadata)
        chunks.append(f"[Fonte {index}: {source_name}]\n{node.get_content()}")
    return "\n\n".join(chunks)


def extract_sources(nodes: list) -> list:
    sources = []
    for node in nodes:
        source_name = get_source_name(node.metadata)
        if source_name not in sources:
            sources.append(source_name)
    return sources