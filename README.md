# LLM Log Severity Classification

## Obiettivo

Il repository contiene due step coerenti tra loro per la classificazione di log Wazuh in quattro classi di rischio:

- `BASSO`
- `MEDIO`
- `ALTO`
- `CRITICO`

Le cartelle principali sono:

- `Lezione3/`: baseline con prompt engineering classico (`zero_shot`, `one_shot`, `few_shot`)
- `Lezione4/`: evoluzione verso severity classification con supporto RAG locale e vector database

Il file `requirements.txt` si trova nella root del progetto.

## Prerequisiti

- Python 3.11+
- Git
- Ollama installato e server avviabile

## Setup rapido (Windows PowerShell)

Dalla root del progetto:

1. Crea il virtual environment, se non esiste:
   ```powershell
   python -m venv .venv
   ```
2. Attiva il virtual environment:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
3. Installa le dipendenze:
   ```powershell
   pip install -r .\requirements.txt
   ```
4. Avvia Ollama in un altro terminale:
   ```powershell
   ollama serve
   ```
5. Scarica il modello se non e gia presente:
   ```powershell
   ollama pull gpt-oss:120b-cloud
   ```

## Lezione 3

### Descrizione

Pipeline baseline per classificare i log Wazuh con prompt engineering tradizionale.

Strategie disponibili:

- `zero_shot`
- `one_shot`
- `few_shot`

### Esecuzione

Dalla cartella `Lezione3/`:

- Tutte le strategie:
  ```powershell
  ..\.venv\Scripts\python.exe main.py all
  ```
- Solo una strategia:
  ```powershell
  ..\.venv\Scripts\python.exe main.py zero_shot
  ..\.venv\Scripts\python.exe main.py one_shot
  ..\.venv\Scripts\python.exe main.py few_shot
  ```

### Input e Output

- Input: `Lezione3/data/Logs.csv`
- Output: `Lezione3/data/Logs-classified.csv`

### File principali

- `Lezione3/main.py`: entrypoint e metriche finali
- `Lezione3/classifier.py`: batching, prompt injection e telemetria batch
- `Lezione3/masking.py`: masking IP e User-Agent
- `Lezione3/ollama_client.py`: chiamata HTTP a Ollama
- `Lezione3/prompts/*.txt`: prompt per ogni strategia

## Lezione 4

### Descrizione

Evoluzione della severity classification verso una pipeline con supporto RAG locale.

La KB contiene solo documenti di riferimento sulla severity in `Lezione4/data/docs/`.
Il dataset `Lezione4/data/Logs.csv` non viene indicizzato nella KB: viene usato solo come input per classificare i log.

Stack usato:

- LlamaIndex per ingest e retrieval
- ChromaDB per persistenza locale
- sentence-transformers per embedding
- Ollama per la classificazione finale guidata da prompt

### Ingest della KB

Dalla root del progetto:

```powershell
.\.venv\Scripts\python.exe .\Lezione4\ingest.py
```

Cosa fa:

- legge i file `.md` in `Lezione4/data/docs/`
- ricrea la collection Chroma locale
- chunka i documenti
- genera gli embedding locali
- salva la persistenza in `Lezione4/storage/chroma/`

### Query sulla KB

```powershell
.\.venv\Scripts\python.exe .\Lezione4\query.py "Which severity corresponds to rule.level 6?"
```

Opzioni utili:

```powershell
.\.venv\Scripts\python.exe .\Lezione4\query.py "Question" --top-k 5
.\.venv\Scripts\python.exe .\Lezione4\query.py "Question" --show-context
```

### Classificazione log con supporto RAG

Singolo log del dataset:

```powershell
.\.venv\Scripts\python.exe .\Lezione4\classify_logs.py --log-id 685
```

Subset piccolo:

```powershell
.\.venv\Scripts\python.exe .\Lezione4\classify_logs.py --limit 10 --batch-size 10
```

Cinque batch da 10:

```powershell
.\.venv\Scripts\python.exe .\Lezione4\classify_logs.py --limit 50 --batch-size 10
```

Tutto il dataset in batch da 50:

```powershell
.\.venv\Scripts\python.exe .\Lezione4\classify_logs.py --all --batch-size 50
```

Log manuale:

```powershell
.\.venv\Scripts\python.exe .\Lezione4\classify_logs.py --log-text "10.42.0.234 - - [12/May/2026:15:32:55 +0000] \"GET /rest/products HTTP/1.1\" 500 -" --rule-description "Web server 500 error code (Internal Error)."
```

La classificazione in `Lezione4`:

- non inserisce `Lezione4/data/Logs.csv` nella KB
- recupera solo i documenti di severity gia indicizzati
- usa il prompt `Lezione4/prompts/classification_prompt.txt`
- invia il contesto a Ollama e normalizza la label finale
- mostra avanzamento batch in stile `Lezione3`
- lascia intatto `Lezione4/data/Logs.csv`
- salva di default i risultati in `Lezione4/data/Logs-rag-classified.csv`

### File principali

- `Lezione4/ingest.py`: ingest e indicizzazione persistente
- `Lezione4/query.py`: query concettuali sulla KB
- `Lezione4/classify_logs.py`: severity classification con supporto RAG
- `Lezione4/kb.py`: helper condivisi per Chroma, embedding e documenti
- `Lezione4/ollama_client.py`: client HTTP verso Ollama
- `Lezione4/prompts/rag_prompt.txt`: prompt per query sulla KB
- `Lezione4/prompts/classification_prompt.txt`: prompt per severity classification
