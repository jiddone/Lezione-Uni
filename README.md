# LLM Log Severity Classification

## Obiettivo

Il repository contiene due step coerenti tra loro per la classificazione di log Wazuh in quattro classi di rischio:

- `BASSO`
- `MEDIO`
- `ALTO`
- `CRITICO`

Le cartelle principali sono:

- `Lezione3/`: baseline con prompt engineering classico (`zero_shot`, `one_shot`, `few_shot`)
- `Lezione4/`: severity classification con due esperimenti separati: prompt engineering CoT e supporto RAG locale

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

La Lezione 4 estende la classificazione della severity con due approcci distinti:

- `cot`: esperimento di prompt engineering Chain of Thought senza knowledge base
- `rag`: classificazione guidata da retrieval su knowledge base locale

I due approcci sono indipendenti tra loro e possono essere eseguiti anche insieme con `--method all` per confrontare metriche e output sullo stesso dataset.

La KB contiene solo documenti di riferimento sulla severity in `Lezione4/data/docs/`.
Il dataset `Lezione4/data/Logs.csv` non viene indicizzato nella KB: viene usato solo come input per classificare i log.

Stack usato:

- LlamaIndex per ingest e retrieval
- ChromaDB per persistenza locale
- sentence-transformers per embedding
- Ollama per la classificazione finale guidata da prompt

Metodi disponibili in `Lezione4/classify_logs.py`:

- `rag`: usa la KB locale, recupera il contesto e applica il prompt `Lezione4/prompts/classification_prompt.txt`
- `cot`: non usa la KB e applica il prompt `Lezione4/prompts/cot_prompt.txt`
- `all`: esegue in sequenza `rag` e `cot` sullo stesso input

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

### Classificazione log

Singolo log del dataset:

```powershell
.\.venv\Scripts\python.exe .\Lezione4\classify_logs.py --method rag --log-id 685
.\.venv\Scripts\python.exe .\Lezione4\classify_logs.py --method cot --log-id 685
```

Subset piccolo:

```powershell
.\.venv\Scripts\python.exe .\Lezione4\classify_logs.py --method rag --limit 10 --batch-size 10
.\.venv\Scripts\python.exe .\Lezione4\classify_logs.py --method cot --limit 10 --batch-size 10
```

Cinque batch da 10:

```powershell
.\.venv\Scripts\python.exe .\Lezione4\classify_logs.py --method all --limit 50 --batch-size 10
```

Tutto il dataset in batch da 50:

```powershell
.\.venv\Scripts\python.exe .\Lezione4\classify_logs.py --method rag --all --batch-size 50
.\.venv\Scripts\python.exe .\Lezione4\classify_logs.py --method cot --all --batch-size 50
.\.venv\Scripts\python.exe .\Lezione4\classify_logs.py --method all --all --batch-size 50
```

Log manuale:

```powershell
.\.venv\Scripts\python.exe .\Lezione4\classify_logs.py --method cot --log-text "10.42.0.234 - - [12/May/2026:15:32:55 +0000] \"GET /rest/products HTTP/1.1\" 500 -" --rule-description "Web server 500 error code (Internal Error)."
```

La classificazione in `Lezione4`:

- non inserisce `Lezione4/data/Logs.csv` nella KB
- nel metodo `rag` recupera solo i documenti di severity gia indicizzati
- nel metodo `rag` usa il prompt `Lezione4/prompts/classification_prompt.txt`
- nel metodo `cot` usa il prompt `Lezione4/prompts/cot_prompt.txt` senza interrogare la KB
- nel metodo `all` esegue entrambi gli approcci nello stesso run
- invia il prompt a Ollama e normalizza la label finale
- mostra avanzamento batch in stile `Lezione3`
- lascia intatto `Lezione4/data/Logs.csv`
- salva di default i risultati in `Lezione4/data/Logs-rag-classified.csv`
- il CSV batch ha colonne stabili per entrambi i metodi: `predicted_label_rag` e `predicted_label_cot`
- se esiste gia, aggiorna solo le colonne del metodo eseguito; con `--method all` aggiorna entrambe

### File principali

- `Lezione4/ingest.py`: ingest e indicizzazione persistente
- `Lezione4/query.py`: query concettuali sulla KB
- `Lezione4/classify_logs.py`: severity classification con metodi `rag`, `cot` e `all`
- `Lezione4/kb.py`: helper condivisi per Chroma, embedding e documenti
- `Lezione4/ollama_client.py`: client HTTP verso Ollama
- `Lezione4/prompts/rag_prompt.txt`: prompt per query sulla KB
- `Lezione4/prompts/classification_prompt.txt`: prompt per severity classification
- `Lezione4/prompts/cot_prompt.txt`: prompt Chain of Thought per classificazione senza KB
