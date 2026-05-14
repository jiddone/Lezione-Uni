import os
import time

from masking import mask_log
from ollama_client import send_to_ollama, parse_response

BATCH_SIZE = 10
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


def load_prompt(strategy: str) -> str:
    """Legge il file di prompt corrispondente alla strategia."""
    path = os.path.join(PROMPTS_DIR, strategy + ".txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def format_batch(logs: list) -> str:
    """Trasforma una lista di log in un blocco numerato '1: ...\\n2: ...'."""
    return "\n".join(f"{i}: {log}" for i, log in enumerate(logs, start=1))


def classify_dataset(logs: list, strategy: str) -> list:
    """Classifica una lista di log usando la strategia di prompting indicata."""
    template = load_prompt(strategy)
    all_labels = []
    total_batches = (len(logs) + BATCH_SIZE - 1) // BATCH_SIZE
    strategy_start = time.time()
    logs_done = 0

    for batch_num in range(total_batches):
        start = batch_num * BATCH_SIZE
        batch = logs[start:start + BATCH_SIZE]

        # 1. mascheriamo dati sensibili
        masked = [mask_log(log) for log in batch]
        # 2. costruiamo il prompt finale
        prompt = template.replace("{logs}", format_batch(masked))

        t0 = time.time()

        # 3. inviamo a Ollama e parsiamo la risposta
        raw = send_to_ollama(prompt)

        elapsed = time.time() - t0
        logs_done += len(batch)
        throughput = logs_done / (time.time() - strategy_start)

        print(
            f"[{strategy}] Batch {batch_num + 1}/{total_batches} | "
            f"tempo: {elapsed:.1f}s | "
            f"throughput: {throughput:.2f} log/s"
        )

        all_labels.extend(parse_response(raw, len(batch)))

    return all_labels
