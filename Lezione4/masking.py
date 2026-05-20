"""Masking dei dati sensibili nei log prima dell'invio al modello."""
import re


IP_PATTERN = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
UA_PATTERN = re.compile(r'"([^"]+)"\s*$')


def mask_log(log: str) -> str:
    """Maschera IP e User-Agent in un singolo log."""
    log = IP_PATTERN.sub("[IP_REDACTED]", log)
    log = UA_PATTERN.sub('"[UA_REDACTED]"', log)
    return log