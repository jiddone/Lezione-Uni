"""Classifica log usando la KB di severita come contesto RAG, senza indicizzare il dataset."""
import argparse
import time

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score

from config import (
    CLASSIFICATION_BATCH_SIZE,
    CLASSIFICATION_PROMPT_PATH,
    DEFAULT_LOG_DATASET_PATH,
    DEFAULT_CLASSIFICATION_OUTPUT_PATH,
    SIMILARITY_TOP_K,
)
from kb import build_context, collection_stats, extract_sources, load_index, reference_only_filters
from ollama_client import generate_text


LEVEL_TO_LABEL = {
    10: "CRITICO",
    7: "ALTO",
    6: "MEDIO",
    5: "BASSO",
    4: "BASSO",
    3: "BASSO",
}
VALID_LABELS = ["BASSO", "MEDIO", "ALTO", "CRITICO"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classifica log usando Lezione4 come base RAG di supporto."
    )
    parser.add_argument(
        "--input-csv",
        default=str(DEFAULT_LOG_DATASET_PATH),
        help="CSV da usare come input dei log (default: Lezione4/data/Logs.csv)",
    )
    parser.add_argument(
        "--log-id",
        type=int,
        help="Classifica un singolo log del CSV selezionandolo per log_id",
    )
    parser.add_argument(
        "--log-text",
        help="Classifica direttamente un log fornito da riga di comando",
    )
    parser.add_argument(
        "--rule-description",
        default="",
        help="Rule description opzionale da anteporre al log quando si usa --log-text",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Classifica tutto il CSV invece del solo subset iniziale",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Numero di righe del CSV da classificare quando non si usa --log-id (default: 5)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=CLASSIFICATION_BATCH_SIZE,
        help=f"Dimensione del batch di classificazione (default: {CLASSIFICATION_BATCH_SIZE})",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=SIMILARITY_TOP_K,
        help=f"Numero di documenti KB da recuperare (default: {SIMILARITY_TOP_K})",
    )
    parser.add_argument(
        "--output-csv",
        help="Salva il risultato della classificazione batch in un CSV",
    )
    parser.add_argument(
        "--show-context",
        action="store_true",
        help="Mostra il contesto recuperato per il caso singolo",
    )
    return parser.parse_args()


def load_prompt_template() -> str:
    with open(CLASSIFICATION_PROMPT_PATH, "r", encoding="utf-8") as prompt_file:
        return prompt_file.read()


def normalize_label(raw_output: str) -> str:
    cleaned = raw_output.strip().upper()
    for label in VALID_LABELS:
        if cleaned == label:
            return label

    for line in cleaned.splitlines():
        stripped = line.strip(" -:*[]()")
        for label in VALID_LABELS:
            if stripped == label or stripped.endswith(label):
                return label

    for label in VALID_LABELS:
        if label in cleaned:
            return label

    return "UNKNOWN"


def build_enriched_log(full_log: str, rule_description: str) -> str:
    description = (rule_description or "").strip()
    if description:
        return f"[{description}] {full_log}"
    return full_log


def load_logs_from_csv(csv_path: str) -> pd.DataFrame:
    dataframe = pd.read_csv(
        csv_path,
        usecols=["log_id", "full_log", "rule.level", "rule.description"],
    )
    return dataframe.dropna(subset=["full_log"]).reset_index(drop=True)


def retrieve_reference_context(index, query_text: str, top_k: int):
    retriever = index.as_retriever(
        similarity_top_k=top_k,
        filters=reference_only_filters(),
    )
    return retriever.retrieve(query_text)


def classify_text(index, prompt_template: str, log_text: str, top_k: int):
    nodes = retrieve_reference_context(index, log_text, top_k)
    context = build_context(nodes)
    prompt = prompt_template.format(context=context, log=log_text)
    raw_output = generate_text(prompt)
    predicted_label = normalize_label(raw_output)
    return predicted_label, raw_output, nodes, context


def classify_single_row(index, prompt_template: str, row: pd.Series, top_k: int) -> dict:
    enriched_log = build_enriched_log(row["full_log"], row.get("rule.description", ""))
    predicted_label, raw_output, nodes, context = classify_text(
        index,
        prompt_template,
        enriched_log,
        top_k,
    )
    expected_label = LEVEL_TO_LABEL.get(int(row["rule.level"]), "BASSO")

    return {
        "log_id": int(row["log_id"]),
        "predicted_label": predicted_label,
        "ground_truth": expected_label,
        "match": predicted_label == expected_label,
        "raw_model_output": raw_output.strip(),
        "sources": extract_sources(nodes),
        "context": context,
        "input_log": enriched_log,
    }


def print_single_result(result: dict, show_context: bool) -> None:
    print(f"log_id: {result['log_id']}")
    print(f"Predizione: {result['predicted_label']}")
    print(f"Ground truth: {result['ground_truth']}")
    print(f"Match: {result['match']}")
    print("Fonti:")
    for source in result["sources"]:
        print(f"- {source}")

    if show_context:
        print("\nContext recuperato:\n")
        print(result["context"])


def batch_output_path(custom_output: str | None) -> str:
    if custom_output:
        return custom_output
    return str(DEFAULT_CLASSIFICATION_OUTPUT_PATH)


def classify_dataframe_in_batches(
    index,
    prompt_template: str,
    dataframe: pd.DataFrame,
    top_k: int,
    batch_size: int,
) -> pd.DataFrame:
    results = []
    total_rows = len(dataframe)
    total_batches = (total_rows + batch_size - 1) // batch_size
    total_start = time.time()
    logs_done = 0

    for batch_num in range(total_batches):
        start = batch_num * batch_size
        batch = dataframe.iloc[start:start + batch_size]
        batch_start = time.time()

        for _, row in batch.iterrows():
            result = classify_single_row(index, prompt_template, row, top_k)
            results.append(
                {
                    "log_id": result["log_id"],
                    "input_log": result["input_log"],
                    "ground_truth": result["ground_truth"],
                    "predicted_label": result["predicted_label"],
                    "match": result["match"],
                    "sources": " | ".join(result["sources"]),
                    "raw_model_output": result["raw_model_output"],
                }
            )

        elapsed = time.time() - batch_start
        logs_done += len(batch)
        throughput = logs_done / (time.time() - total_start)

        print(
            f"[rag] Batch {batch_num + 1}/{total_batches} | "
            f"tempo: {elapsed:.1f}s | "
            f"throughput: {throughput:.2f} log/s"
        )

    return pd.DataFrame(results)


def print_final_summary(results_df: pd.DataFrame, total_elapsed: float) -> None:
    labels_order = ["BASSO", "MEDIO", "ALTO", "CRITICO"]
    mask = results_df["predicted_label"] != "UNKNOWN"

    if mask.any():
        accuracy = accuracy_score(
            results_df.loc[mask, "ground_truth"],
            results_df.loc[mask, "predicted_label"],
        )
        precision = precision_score(
            results_df.loc[mask, "ground_truth"],
            results_df.loc[mask, "predicted_label"],
            labels=labels_order,
            average="weighted",
            zero_division=0,
        )
        f1 = f1_score(
            results_df.loc[mask, "ground_truth"],
            results_df.loc[mask, "predicted_label"],
            labels=labels_order,
            average="weighted",
            zero_division=0,
        )
    else:
        accuracy = 0.0
        precision = 0.0
        f1 = 0.0

    total_logs = len(results_df)
    average_throughput = total_logs / total_elapsed if total_elapsed > 0 else 0.0

    print("\n" + "=" * 70)
    print("  RIEPILOGO FINALE")
    print(f"  Tempo totale:       {total_elapsed:.1f}s")
    print(f"  Throughput medio:   {average_throughput:.2f} log/s")
    print("=" * 70)
    print(f"  {'Metodo':<12} {'Accuracy':>10} {'Precision':>10} {'F1-score':>10}")
    print("-" * 70)
    print(f"  {'rag':<12} {accuracy:>10.3f} {precision:>10.3f} {f1:>10.3f}")
    print("=" * 70)


def main() -> None:
    args = parse_args()
    stats = collection_stats()
    if stats["count"] == 0:
        raise RuntimeError("La KB e vuota. Esegui prima `python Lezione4/ingest.py`.")
    if args.batch_size <= 0:
        raise RuntimeError("--batch-size deve essere maggiore di zero.")

    index = load_index()
    prompt_template = load_prompt_template()

    if args.log_text:
        enriched_log = build_enriched_log(args.log_text, args.rule_description)
        predicted_label, raw_output, nodes, context = classify_text(
            index,
            prompt_template,
            enriched_log,
            args.top_k,
        )
        print(f"Predizione: {predicted_label}")
        print("Fonti:")
        for source in extract_sources(nodes):
            print(f"- {source}")
        if args.show_context:
            print("\nContext recuperato:\n")
            print(context)
        return

    dataframe = load_logs_from_csv(args.input_csv)
    if args.log_id is not None:
        matches = dataframe[dataframe["log_id"] == args.log_id]
        if matches.empty:
            raise RuntimeError(f"log_id {args.log_id} non trovato in {args.input_csv}.")
        result = classify_single_row(index, prompt_template, matches.iloc[0], args.top_k)
        print_single_result(result, args.show_context)
        return

    subset = dataframe.copy() if args.all else dataframe.head(args.limit).copy()
    total_start = time.time()
    results_df = classify_dataframe_in_batches(
        index=index,
        prompt_template=prompt_template,
        dataframe=subset,
        top_k=args.top_k,
        batch_size=args.batch_size,
    )
    total_elapsed = time.time() - total_start

    output_path = batch_output_path(args.output_csv)
    results_df.to_csv(output_path, index=False)
    print(f"\nRisultati completi salvati in: {output_path}")
    print_final_summary(results_df, total_elapsed)


if __name__ == "__main__":
    main()