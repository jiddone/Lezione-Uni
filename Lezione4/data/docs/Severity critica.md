### Severity: CRITICO (rule.level 10)

**Descrizione generale e contesto operativo**  
La severity CRITICO nel sistema di classificazione Wazuh corrisponde tipicamente ai livelli ≥10 (nel dataset osservato, in particolare rule.level 10) ed è associata a eventi che indicano attività malevola in corso con un grado elevato di evidenza operativa, continuità temporale e impatto potenziale. A differenza dei livelli inferiori, la criticità non deriva dalla singola richiesta, ma dal comportamento aggregato: frequenza, ripetizione, correlazione tra eventi e chiara impronta di automazione.

Nel contesto del dataset — generato dal monitoraggio di OWASP Juice Shop — la severity CRITICO rappresenta la fase più avanzata del ciclo di attacco osservabile nei log: non più tentativi isolati o tecnicamente corretti (ALTO), ma campagne automatizzate, scansioni aggressive, brute force sistematici o exploitation ripetuta su larga scala.

Un elemento fondamentale da comprendere è che, nel modello Wazuh, il passaggio a CRITICO è quasi sempre il risultato di un meccanismo di correlazione temporale: più eventi simili, provenienti dallo stesso source IP in una finestra temporale ristretta, vengono aggregati e generano un alert di livello superiore. Questo implica che la stessa identica richiesta, vista una volta, è BASSO o MEDIO; vista decine di volte in sequenza, diventa CRITICO.

***

**Rule descriptions associate a severity CRITICO nel dataset**  
Dall’analisi del dataset, le principali rule.description associate alla severity CRITICO sono:

* **Multiple web server 400 error codes from same source ip.**
* **Multiple web server 500 error code (Internal Error).**
* In alcuni casi: pattern aggregati equivalenti su altre categorie (es. SQL injection ripetute)

Queste regole non descrivono una tecnica specifica di attacco (come SQLi o XSS), ma un comportamento: ripetizione massiva dello stesso tipo di evento in un arco temporale ristretto.

Questo è il punto chiave: CRITICO è una proprietà comportamentale, non semantica del payload.

***

**Analisi dettagliata: Multiple web server 400 error codes**

Questa categoria rappresenta uno dei pattern più chiari di attività malevola automatizzata.

Nel dataset, i codici 400 includono:

* 401 (Unauthorized)
* 403 (Forbidden)
* 406 (Not Acceptable)

Il pattern tipico è:

* stesso srcip
* stesso endpoint (es. /rest/user/login)
* richieste ripetute in sequenza rapida
* stesso tipo di errore (es. 401)

Esempio comportamentale:
POST /rest/user/login → 401  
POST /rest/user/login → 401  
POST /rest/user/login → 401  
… (ripetuto N volte)

Questo è un classico brute force attack sulle credenziali.

Dal punto di vista Wazuh:

* i primi tentativi → rule.level 5 → BASSO
* al superamento della soglia → rule.level 10 → CRITICO

Quindi l’evento CRITICO è un evento aggregato che “riassume” un comportamento precedente già osservato in forma atomica.

Un altro pattern con 406 su /redirect indica invece:

* fuzzing del parametro to
* tentativi sistematici di open redirect bypass o injection

***

**Analisi dettagliata: Multiple web server 500 error codes**

Il codice 500 nel contesto Juice Shop è estremamente comune, ma ciò che distingue la fascia CRITICO è ancora una volta la frequenza.

Pattern osservato:

* richieste ripetute verso:
  * /rest
  * /api
  * /rest/admin
  * /ftp
  * /.env
  * /actuator/env
* tutte con risposta 500
* nello stesso intervallo temporale

Questo comportamento è tipico di:

* vulnerability scanners
* directory bruteforcing
* automated discovery tools

Esempio operativo:
GET /.env → 500  
GET /.git/config → 500  
GET /ftp/file.txt → 500  
GET /actuator/env → 500

Il significato non sta nella singola richiesta (che sarebbe BASSO), ma nella sequenza: l’attaccante sta enumerando sistematicamente risorse sensibili.

***

**Strumenti identificabili attraverso User-Agent**

Un indicatore estremamente forte nella fascia CRITICO è la presenza di User-Agent associati a tool automatizzati:

* **sqlmap** → exploitation SQL
* **Nikto** → web vulnerability scanner
* **Nmap Scripting Engine** → scanning di rete e servizi
* **curl** → scripting manuale o semi-automatico
* **python-requests** → tool custom o script

A differenza delle fasce inferiori:

* in BASSO e MEDIO prevalgono browser reali
* in CRITICO prevalgono strumenti automatizzati

Questo contribuisce alla classificazione perché rafforza l’ipotesi di attacco attivo.

***

**Pattern comportamentali caratteristici della fascia CRITICO**

Gli eventi CRITICO nel dataset condividono caratteristiche molto precise:

**1. Alta frequenza (burst di richieste)**

* decine o centinaia di richieste in pochi secondi
* stesso srcip, stesso pattern

**2. Ripetizione dello stesso errore**

* 401 ripetuti → brute force
* 500 ripetuti → scanning aggressivo

**3. Enumerazione sistematica**

* path sensibili:
  * /.env
  * /.git
  * /.svn
  * /ftp
  * /actuator
* varianti dello stesso endpoint

**4. Multi-endpoint targeting**

* l’attaccante non si limita a un endpoint
* esplora l’intera superficie applicativa

**5. Coerenza del comportamento**

* stesso ordine logico di richieste
* tipico dei tool automatizzati (scan breadth-first)

***

**Relazione tra CRITICO e livelli inferiori**

La severity CRITICO è il risultato di una **progressione naturale**:

* **BASSO** → singolo errore (es. login fallito)
* **MEDIO** → pattern sospetto o payload anomalo
* **ALTO** → exploit mirato (SQLi, XSS)
* **CRITICO** → comportamento ripetuto, automatizzato, persistente

Un punto chiave del dataset è che:

* gli stessi IP compaiono in tutte le fasce
* CRITICO è spesso preceduto da BASSO o MEDIO

Esempio reale:

1. POST /login → 401 → BASSO
2. ripetuto più volte → accumulo
3. scatta → Multiple 401 → CRITICO

Quindi CRITICO non è indipendente: è la manifestazione aggregata di eventi precedenti.

***

**Distinzione critica: payload vs comportamento**

Un aspetto fondamentale:

* ALTO = payload pericoloso (es. SQLi)
* CRITICO = comportamento pericoloso (ripetizione, automazione)

Un SQL injection:

* vista una volta → ALTO
* ripetuta 50 volte → CRITICO

Questa distinzione è centrale per l’analisi operativa:

* ALTO richiede analisi qualitativa
* CRITICO richiede risposta immediata

***

**Falsi positivi e specificità del contesto Juice Shop**

Nel dataset Juice Shop, è importante non sovrastimare alcuni eventi CRITICO:

* l’applicazione è volutamente instabile → molti 500
* molte risposte non indicano vulnerabilità reale
* endpoint inesistenti generano errori sistematici

Tuttavia, ciò che rimane valido è il **pattern di attacco**:

* anche se il target è “sicuro per design”, il comportamento dell’attaccante è reale
* in un ambiente di produzione, lo stesso pattern sarebbe critico senza ambiguità

***

**Correlazioni operative e analisi temporale**

Gli eventi CRITICO devono essere analizzati sempre con:

* finestra temporale (burst vs distribuzione)
* correlazione tra endpoint
* evoluzione del comportamento

Un pattern tipico:

* fase 1: scan (MEDIO)
* fase 2: exploit (ALTO)
* fase 3: automazione e flood (CRITICO)

Nel dataset, questa sequenza è chiaramente osservabile per diversi IP.

***

**Azione raccomandata e risposta operativa**

Gli eventi CRITICO richiedono risposta immediata.

**Azioni minime:**

* alert in tempo reale (no buffering)
* identificazione srcip
* blocco IP (firewall, WAF)
* rate limiting

**Analisi:**

* ricostruzione timeline attacco
* verifica eventuali accessi riusciti
* analisi endpoint coinvolti

**Escalation interna:**

* segnalazione al SOC
* apertura incidente
* verifica compromissione

**Indicatori di compromissione (IOC) da verificare:**

* risposte 200 inattese
* accessi autenticati sospetti
* modifiche dati

***

In sintesi, la severity CRITICO rappresenta il livello più alto di allerta nel dataset: non identifica semplicemente un attacco possibile o probabile, ma un’attività malevola concreta, in corso, strutturata e automatizzata. Il valore dell’alert non sta nel singolo evento, ma nel pattern complessivo, che indica chiaramente che l’attaccante ha superato la fase di test ed è passato a un’esecuzione sistematica dell’attacco.
