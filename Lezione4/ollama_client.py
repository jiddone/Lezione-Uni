"""Client HTTP Ollama riusabile per la pipeline RAG locale."""
import requests

from config import OLLAMA_MODEL, OLLAMA_TIMEOUT, OLLAMA_URL


def generate_text(prompt: str, timeout: int = OLLAMA_TIMEOUT) -> str:
    """Invia un prompt a Ollama e restituisce il testo generato."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_gpu": 0,
            "temperature": 0,
        },
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(
            "Impossibile contattare Ollama. Verifica che `ollama serve` sia attivo."
        ) from exc

    data = response.json()
    if "response" not in data:
        raise RuntimeError("Risposta Ollama non valida: campo 'response' assente.")
    return data["response"]