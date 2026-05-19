"""Indicizza i documenti Markdown nella KB locale persistita su ChromaDB."""
from kb import build_index, collection_stats, load_documents


def main() -> None:
    documents = load_documents()
    build_index(documents)
    stats = collection_stats()

    print("Indicizzazione completata.")
    print(f"Documenti letti: {len(documents)}")
    print(f"Chunk presenti in Chroma: {stats['count']}")
    print("Fonti indicizzate:")
    for source in sorted({doc.metadata.get("file_name", "sconosciuto") for doc in documents}):
        print(f"- {source}")


if __name__ == "__main__":
    main()