# LLM Log Classification - Setup Iniziale

## Descrizione
Pipeline Python per classificare log Wazuh in quattro classi di rischio (`BASSO`, `MEDIO`, `ALTO`, `CRITICO`) con prompt engineering (`zero_shot`, `one_shot`, `few_shot`) e modello Ollama `gpt-oss:120b-cloud`.

La logica applicativa e i file di progetto sono nella cartella `project/`.

## Prerequisiti
- Python 3.11+
- Git
- Ollama installato e server avviabile

## Setup rapido (Windows PowerShell)
1. Entra nella cartella progetto:
   ```powershell
   cd .\project
   ```
2. Crea il virtual environment (se non esiste):
   ```powershell
   python -m venv ..\.venv
   ```
3. Attiva il virtual environment:
   ```powershell
   ..\.venv\Scripts\Activate.ps1
   ```
4. Installa le dipendenze:
   ```powershell
   pip install -r requirements.txt
   ```
5. Avvia Ollama (in un altro terminale):
   ```powershell
   ollama serve
   ```
6. Scarica il modello:
   ```powershell
   ollama pull gpt-oss:120b-cloud
   ```

## Esecuzione
Dalla cartella `project/`:

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

## Input e Output
- Input: `project/data/Logs.csv`
- Output: `project/data/Logs-classified.csv`

## Struttura minima
- `project/main.py`: entrypoint, orchestrazione run e metriche finali
- `project/classifier.py`: batching, prompt injection, telemetria batch
- `project/masking.py`: masking IP e User-Agent
- `project/ollama_client.py`: chiamata HTTP a Ollama e parsing risposte
- `project/prompts/*.txt`: template prompt per ogni strategia

## Preparazione repo Git e pubblicazione su GitHub
Questa cartella e pronta per essere versionata con Git.

Comandi consigliati dalla root (`Lezione Uni/`):

```powershell
git init -b main
git add .
git commit -m "chore: initial project setup"
```

Quando crei la repo vuota su GitHub, collega il remote e fai push:

```powershell
git remote add origin https://github.com/<utente>/<nome-repo>.git
git push -u origin main
```
