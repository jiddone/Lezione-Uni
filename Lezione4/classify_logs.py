"""Classifica log con metodi RAG, CoT o entrambi, salvando risultati in un CSV unico."""
import argparse
import time
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score

from config import (
    CLASSIFICATION_BATCH_SIZE,
    CLASSIFICATION_PROMPT_PATH,
    COT_CLASSIFICATION_PROMPT_PATH,
    DEFAULT_LOG_DATASET_PATH,
    DEFAULT_CLASSIFICATION_OUTPUT_PATH,
    SIMILARITY_TOP_K,
)
from kb import build_context, collection_stats, extract_sources, load_index, reference_only_filters
from masking import mask_log
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
CLASSIFICATION_METHODS = ["rag", "cot"]
BASE_RESULT_COLUMNS = ["log_id", "input_log", "ground_truth"]
METHOD_RESULT_COLUMNS = {
    "rag": [
        "predicted_label_rag",
        "match_rag",
        "sources_rag",
        "raw_model_output_rag",
    ],
    "cot": [
        "predicted_label_cot",
        "match_cot",
        "raw_model_output_cot",
    ],
}
LEGACY_RAG_COLUMNS = {
    "predicted_label": "predicted_label_rag",
    "match": "match_rag",
    "sources": "sources_rag",
    "raw_model_output": "raw_model_output_rag",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classifica log con RAG few-shot, CoT o entrambi."
    )
    parser.add_argument(
        "--method",
        default="rag",
        choices=["rag", "cot", "all"],
        help="Metodo da eseguire: rag, cot oppure all (default: rag)",
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
        help=(
            f"Numero di documenti KB da recuperare per RAG "
            f"(default: {SIMILARITY_TOP_K})"
        ),
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


def load_prompt_template(method: str) -> str:
    prompt_paths = {
        "rag": CLASSIFICATION_PROMPT_PATH,
        "cot": COT_CLASSIFICATION_PROMPT_PATH,
    }
    with open(prompt_paths[method], "r", encoding="utf-8") as prompt_file:
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
    enriched_log = full_log
    if description:
        enriched_log = f"[{description}] {full_log}"
    return mask_log(enriched_log)


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


def classify_text(index, prompt_template: str, method: str, log_text: str, top_k: int):
    if method == "rag":
        nodes = retrieve_reference_context(index, log_text, top_k)
        context = build_context(nodes)
        prompt = prompt_template.format(context=context, log=log_text)
    elif method == "cot":
        nodes = []
        context = ""
        prompt = prompt_template.format(log=log_text)
    else:
        raise RuntimeError(f"Metodo non supportato: {method}")

    raw_output = generate_text(prompt)
    predicted_label = normalize_label(raw_output)
    return predicted_label, raw_output, nodes, context


def classify_single_row(
    index,
    prompt_template: str,
    row: pd.Series,
    method: str,
    top_k: int,
) -> dict:
    enriched_log = build_enriched_log(row["full_log"], row.get("rule.description", ""))
    predicted_label, raw_output, nodes, context = classify_text(
        index,
        prompt_template,
        method,
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
        "sources": extract_sources(nodes) if nodes else [],
        "context": context,
        "input_log": enriched_log,
    }


def print_single_result(method: str, result: dict, show_context: bool) -> None:
    print(f"\n=== Metodo: {method} ===")
    if "log_id" in result:
        print(f"log_id: {result['log_id']}")
    print(f"Predizione: {result['predicted_label']}")
    if "ground_truth" in result:
        print(f"Ground truth: {result['ground_truth']}")
        print(f"Match: {result['match']}")

    if result["sources"]:
        print("Fonti:")
        for source in result["sources"]:
            print(f"- {source}")
    elif method == "cot":
        print("Fonti: nessuna (CoT senza KB)")

    if show_context:
        if result["context"]:
            print("\nContext recuperato:\n")
            print(result["context"])
        elif method == "cot":
            print("\nContext recuperato:\n")
            print("Nessuno: il metodo CoT non usa la knowledge base.")


def output_columns() -> list[str]:
    columns = BASE_RESULT_COLUMNS.copy()
    for method in CLASSIFICATION_METHODS:
        columns.extend(METHOD_RESULT_COLUMNS[method])
    return columns


def normalize_output_schema(dataframe: pd.DataFrame) -> pd.DataFrame:
    normalized = dataframe.copy()

    for legacy_column, target_column in LEGACY_RAG_COLUMNS.items():
        if legacy_column not in normalized.columns:
            continue
        if target_column in normalized.columns:
            normalized[target_column] = normalized[target_column].combine_first(
                normalized[legacy_column]
            )
        else:
            normalized[target_column] = normalized[legacy_column]

    for column in output_columns():
        if column not in normalized.columns:
            normalized[column] = pd.NA

    return normalized[output_columns()]


def load_existing_results(output_path: str) -> pd.DataFrame:
    path = Path(output_path)
    if not path.exists():
        return pd.DataFrame(columns=output_columns())
    return normalize_output_schema(pd.read_csv(path))


def update_existing_results(
    existing_df: pd.DataFrame,
    new_results_df: pd.DataFrame,
    methods: list[str],
) -> pd.DataFrame:
    existing = normalize_output_schema(existing_df).set_index("log_id")
    incoming = normalize_output_schema(new_results_df).set_index("log_id")

    if existing.empty:
        return incoming.sort_index().reset_index()

    missing_ids = incoming.index.difference(existing.index)
    if not missing_ids.empty:
        existing = pd.concat([existing, incoming.loc[missing_ids]], axis=0)

    existing.loc[incoming.index, ["input_log", "ground_truth"]] = incoming[
        ["input_log", "ground_truth"]
    ]

    columns_to_update = []
    for method in methods:
        columns_to_update.extend(METHOD_RESULT_COLUMNS[method])

    existing.loc[incoming.index, columns_to_update] = incoming[columns_to_update]
    return existing.sort_index().reset_index()


def batch_output_path(custom_output: str | None) -> str:
    if custom_output:
        return custom_output
    return str(DEFAULT_CLASSIFICATION_OUTPUT_PATH)


def classify_dataframe_in_batches(
    index,
    prompt_template: str,
    dataframe: pd.DataFrame,
    method: str,
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
            result = classify_single_row(index, prompt_template, row, method, top_k)
            results.append(
                {
                    "log_id": result["log_id"],
                    "input_log": result["input_log"],
                    "ground_truth": result["ground_truth"],
                    f"predicted_label_{method}": result["predicted_label"],
                    f"match_{method}": result["match"],
                    f"raw_model_output_{method}": result["raw_model_output"],
                    **(
                        {f"sources_{method}": " | ".join(result["sources"])}
                        if method == "rag"
                        else {}
                    ),
                }
            )

        elapsed = time.time() - batch_start
        logs_done += len(batch)
        throughput = logs_done / (time.time() - total_start)

        print(
            f"[{method}] Batch {batch_num + 1}/{total_batches} | "
            f"tempo: {elapsed:.1f}s | "
            f"throughput: {throughput:.2f} log/s"
        )

    return pd.DataFrame(results)


def merge_batch_results(results_by_method: list[pd.DataFrame]) -> pd.DataFrame:
    combined = results_by_method[0]
    for method_df in results_by_method[1:]:
        combined = combined.merge(
            method_df,
            on=["log_id", "input_log", "ground_truth"],
            how="left",
        )
    return combined


def print_final_summary(
    results_df: pd.DataFrame,
    methods: list[str],
    total_elapsed: float,
) -> None:
    labels_order = ["BASSO", "MEDIO", "ALTO", "CRITICO"]
    total_logs = len(results_df) * len(methods)
    average_throughput = total_logs / total_elapsed if total_elapsed > 0 else 0.0

    print("\n" + "=" * 70)
    print("  RIEPILOGO FINALE")
    print(f"  Tempo totale:       {total_elapsed:.1f}s")
    print(f"  Throughput medio:   {average_throughput:.2f} log/s")
    print("=" * 70)
    print(f"  {'Metodo':<12} {'Accuracy':>10} {'Precision':>10} {'F1-score':>10}")
    print("-" * 70)
    for method in methods:
        prediction_column = f"predicted_label_{method}"
        mask = results_df[prediction_column] != "UNKNOWN"

        if mask.any():
            accuracy = accuracy_score(
                results_df.loc[mask, "ground_truth"],
                results_df.loc[mask, prediction_column],
            )
            precision = precision_score(
                results_df.loc[mask, "ground_truth"],
                results_df.loc[mask, prediction_column],
                labels=labels_order,
                average="weighted",
                zero_division=0,
            )
            f1 = f1_score(
                results_df.loc[mask, "ground_truth"],
                results_df.loc[mask, prediction_column],
                labels=labels_order,
                average="weighted",
                zero_division=0,
            )
        else:
            accuracy = 0.0
            precision = 0.0
            f1 = 0.0

        print(f"  {method:<12} {accuracy:>10.3f} {precision:>10.3f} {f1:>10.3f}")
    print("=" * 70)


def main() -> None:
    args = parse_args()
    if args.batch_size <= 0:
        raise RuntimeError("--batch-size deve essere maggiore di zero.")
    if args.method in {"rag", "all"} and args.top_k <= 0:
        raise RuntimeError("--top-k deve essere maggiore di zero quando si usa RAG.")

    methods = CLASSIFICATION_METHODS if args.method == "all" else [args.method]
    print(f"Metodi selezionati: {', '.join(methods)}")

    index = None
    if "rag" in methods:
        stats = collection_stats()
        if stats["count"] == 0:
            raise RuntimeError("La KB e vuota. Esegui prima `python Lezione4/ingest.py`.")
        index = load_index()

    prompt_templates = {method: load_prompt_template(method) for method in methods}

    if args.log_text:
        enriched_log = build_enriched_log(args.log_text, args.rule_description)
        for method in methods:
            predicted_label, raw_output, nodes, context = classify_text(
                index,
                prompt_templates[method],
                method,
                enriched_log,
                args.top_k,
            )
            print_single_result(
                method,
                {
                    "predicted_label": predicted_label,
                    "raw_model_output": raw_output.strip(),
                    "sources": extract_sources(nodes) if nodes else [],
                    "context": context,
                },
                args.show_context,
            )
        return

    dataframe = load_logs_from_csv(args.input_csv)
    if args.log_id is not None:
        matches = dataframe[dataframe["log_id"] == args.log_id]
        if matches.empty:
            raise RuntimeError(f"log_id {args.log_id} non trovato in {args.input_csv}.")
        for method in methods:
            result = classify_single_row(
                index,
                prompt_templates[method],
                matches.iloc[0],
                method,
                args.top_k,
            )
            print_single_result(method, result, args.show_context)
        return

    subset = dataframe.copy() if args.all else dataframe.head(args.limit).copy()
    total_start = time.time()
    batch_results = []
    for method in methods:
        batch_results.append(
            classify_dataframe_in_batches(
                index=index,
                prompt_template=prompt_templates[method],
                dataframe=subset,
                method=method,
                top_k=args.top_k,
                batch_size=args.batch_size,
            )
        )
    results_df = merge_batch_results(batch_results)
    total_elapsed = time.time() - total_start

    output_path = batch_output_path(args.output_csv)
    existing_results_df = load_existing_results(output_path)
    final_results_df = update_existing_results(existing_results_df, results_df, methods)
    final_results_df.to_csv(output_path, index=False)
    print(f"\nRisultati completi salvati in: {output_path}")
    print_final_summary(results_df, methods, total_elapsed)


if __name__ == "__main__":
    main()