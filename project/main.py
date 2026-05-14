import argparse
import os
import time
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, f1_score

from classifier import classify_dataset

# percorsi
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
INPUT_CSV = os.path.join(DATA_DIR, "Logs.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "Logs-classified.csv")

# mappa il livello numerico di Wazuh nella nostra tassonomia
LEVEL_TO_LABEL = {
    10: "CRITICO",
    7:  "ALTO",
    6:  "MEDIO",
    5:  "BASSO",
    4:  "BASSO",
    3:  "BASSO",
}

STRATEGIES = ["zero_shot", "one_shot", "few_shot"]


def parse_args():
    parser = argparse.ArgumentParser(description="Classifica log Wazuh con strategie di prompt engineering.")
    parser.add_argument(
        "strategy",
        nargs="?",
        default="all",
        choices=["all", "zero_shot", "one_shot", "few_shot"],
        help="Strategia da eseguire (default: all)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    strategies = STRATEGIES if args.strategy == "all" else [args.strategy]
    print(f"Strategie selezionate: {', '.join(strategies)}")

    print("Caricamento dataset...")
    df = pd.read_csv(INPUT_CSV, usecols=["full_log", "rule.level", "rule.description"])
    df = df.dropna(subset=["full_log"]).reset_index(drop=True)
    print(f"Dataset: {len(df)} log")

    # ground truth derivata dal rule.level di Wazuh
    df["ground_truth"] = df["rule.level"].map(LEVEL_TO_LABEL).fillna("BASSO")

    # log arricchito: [descrizione Wazuh] log_grezzo
    df["enriched_log"] = "[" + df["rule.description"] + "] " + df["full_log"]

    # classifica con le strategie selezionate
    total_start = time.time()
    for strategy in strategies:
        print(f"\n=== Strategia: {strategy} ===")
        df[f"label_{strategy}"] = classify_dataset(df["enriched_log"].tolist(), strategy)
    total_elapsed = time.time() - total_start
    total_logs = len(df) * len(strategies)

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nRisultati completi salvati in: {OUTPUT_CSV}")

    # riepilogo finale
    labels_order = ["BASSO", "MEDIO", "ALTO", "CRITICO"]
    gt = df["ground_truth"]

    print("\n" + "=" * 70)
    print(f"  RIEPILOGO FINALE")
    print(f"  Tempo totale:       {total_elapsed:.1f}s")
    print(f"  Throughput medio:   {total_logs / total_elapsed:.2f} log/s")
    print("=" * 70)
    print(f"  {'Strategia':<12} {'Accuracy':>10} {'Precision':>10} {'F1-score':>10}")
    print("-" * 70)
    for strategy in strategies:
        pred = df[f"label_{strategy}"]
        # escludiamo eventuali UNKNOWN dalla valutazione
        mask = pred != "UNKNOWN"
        acc  = accuracy_score(gt[mask], pred[mask])
        prec = precision_score(gt[mask], pred[mask], labels=labels_order,
                               average="weighted", zero_division=0)
        f1   = f1_score(gt[mask], pred[mask], labels=labels_order,
                        average="weighted", zero_division=0)
        print(f"  {strategy:<12} {acc:>10.3f} {prec:>10.3f} {f1:>10.3f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
