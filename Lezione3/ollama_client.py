"""
Client HTTP per Ollama.

Inviamo un prompt al server locale (http://localhost:11434) e parsiamo
la risposta in una lista di etichette.
"""
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gpt-oss:120b-cloud"
VALID_LABELS = {"BASSO", "MEDIO", "ALTO", "CRITICO"}


def send_to_ollama(prompt: str) -> str:
    """Invia un prompt a Ollama e restituisce la stringa di risposta."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_gpu": 0,     # forziamo l'esecuzione su CPU
            "temperature": 0  # risposte deterministiche
        }
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()["response"]


def parse_response(raw: str, n: int) -> list:
    """
    Estrae N etichette dalla risposta del modello.
    Il modello risponde nel formato:
        1: ALTO
        2: BASSO
        ...
    """
    labels = []
    for line in raw.strip().splitlines():
        line = line.strip()
        if ":" in line:
            label = line.split(":", 1)[1].strip().upper()
            if label in VALID_LABELS:
                labels.append(label)

    # se il modello restituisce meno etichette del previsto, riempiamo con UNKNOWN
    while len(labels) < n:
        labels.append("UNKNOWN")
    return labels[:n]
