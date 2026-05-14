"""
Mascheramento dei dati sensibili nei log prima dell'invio al modello LLM.

Rimuoviamo:
  - indirizzi IP -> [IP_REDACTED]
  - User-Agent del browser -> [UA_REDACTED]
"""
import re

# indirizzi IPv4, es: 10.42.1.207
IP_PATTERN = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")

# User-Agent: ultima stringa tra virgolette in fondo al log Apache
UA_PATTERN = re.compile(r'"([^"]+)"\s*$')


def mask_log(log: str) -> str:
    """Maschera IP e User-Agent in un singolo log."""
    log = IP_PATTERN.sub("[IP_REDACTED]", log)
    log = UA_PATTERN.sub('"[UA_REDACTED]"', log)
    return log
