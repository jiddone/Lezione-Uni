"""Esegue query RAG sulla KB locale usando Chroma per retrieval e Ollama per synthesis."""
import argparse

from config import PROMPT_PATH, SIMILARITY_TOP_K
from kb import build_context, collection_stats, extract_sources, load_index, reference_only_filters
from ollama_client import generate_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interroga la KB locale della Lezione 4.")
    parser.add_argument("question", help="Domanda da porre alla knowledge base")
    parser.add_argument(
        "--top-k",
        type=int,
        default=SIMILARITY_TOP_K,
        help=f"Numero di chunk da recuperare (default: {SIMILARITY_TOP_K})",
    )
    parser.add_argument(
        "--show-context",
        action="store_true",
        help="Mostra anche il contesto recuperato prima della risposta finale",
    )
    return parser.parse_args()


def load_prompt_template() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as prompt_file:
        return prompt_file.read()


def main() -> None:
    args = parse_args()
    stats = collection_stats()
    if stats["count"] == 0:
        raise RuntimeError("La KB e vuota. Esegui prima `python Lezione4/ingest.py`.")

    index = load_index()
    retriever = index.as_retriever(
        similarity_top_k=args.top_k,
        filters=reference_only_filters(),
    )
    nodes = retriever.retrieve(args.question)

    if not nodes:
        print("Risposta:\nLa risposta non e presente nella knowledge base.")
        return

    context = build_context(nodes)
    prompt = load_prompt_template().format(context=context, question=args.question)
    answer = generate_text(prompt)

    if args.show_context:
        print("Context recuperato:\n")
        print(context)
        print("\n" + "=" * 70 + "\n")

    print("Risposta:\n")
    print(answer.strip())

    print("\nFonti:")
    for source in extract_sources(nodes):
        print(f"- {source}")


if __name__ == "__main__":
    main()