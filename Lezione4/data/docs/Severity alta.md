### Severity: ALTO (rule.level 7)

**Descrizione generale e contesto operativo**  
La severity ALTO nel sistema di classificazione Wazuh corrisponde al rule.level 7 ed è posizionata immediatamente sopra la fascia MEDIO (rule.level 6) e sotto la fascia CRITICO (rule.level ≥10). A livello semantico, Wazuh descrive questo livello come eventi caratterizzati da pattern di attacco chiaramente riconoscibili e con elevata probabilità di impatto, ma non necessariamente accompagnati da evidenza diretta di compromissione riuscita o comportamento sistematico.

Nel contesto specifico del dataset analizzato — log generati dal monitoraggio di un’istanza OWASP Juice Shop — la severity ALTO rappresenta una fase ben precisa del ciclo di attacco: la fase di exploitation attiva, dove l’attaccante non si limita più a esplorare (reconnaissance, tipica di MEDIO), ma inizia a inviare payload strutturati e tecnicamente corretti per sfruttare vulnerabilità note.

È fondamentale distinguere questo livello sia da MEDIO sia da CRITICO:

* Rispetto a MEDIO, la differenza non è solo nella presenza di un payload malevolo, ma nella qualità e specificità del payload stesso. In ALTO il payload è chiaramente finalizzato allo sfruttamento di una vulnerabilità e non a un semplice probing.
* Rispetto a CRITICO, invece, manca la dimensione comportamentale: gli eventi ALTO sono generalmente singoli o poco frequenti, non parte di un flood o di un pattern ripetuto su larga scala.

In altre parole, ALTO rappresenta attacchi “seri” ma ancora non persistenti o automatizzati su larga scala, mentre CRITICO rappresenta attacchi sistematici e già in fase avanzata.

***

**Rule descriptions associate a severity ALTO nel dataset**  
Dall’analisi del file Logs-classified, la stragrande maggioranza degli eventi classificati come ALTO è associata alla seguente rule.description:

* **SQL injection attempt.**

In misura minore, ma comunque rilevante, compaiono:

* **XSS (Cross Site Scripting) attempt.**

A differenza della fascia MEDIO, non compaiono qui rule.description generiche come “Common web attack” o “Suspicious URL access”: il passaggio da MEDIO ad ALTO coincide proprio con la transizione da pattern sospetti generici a signature di exploit ben definite.

***

**Analisi dettagliata delle SQL Injection (ALTO)**  
La SQL injection è la tipologia dominante nella fascia ALTO del dataset ed è anche quella più importante da analizzare in dettaglio, perché rappresenta uno dei vettori più critici in assoluto nel contesto web.

I payload osservati nel dataset includono diverse categorie di injection, tutte riconducibili a tecniche note:

**1. Boolean-based SQL injection**
Esempi tipici:

* `' OR 1=1--`
* `" OR 'a'='a`

Questi payload cercano di modificare la logica della query in modo che la condizione WHERE sia sempre vera, permettendo bypass di autenticazione o accesso a dati non autorizzati.

Esempio concreto:
GET /api/Users?email=admin' OR 1=1--

Questo tipo di richiesta, se la query SQL fosse costruita senza sanitizzazione, trasformerebbe:
SELECT \* FROM users WHERE email = 'admin' AND password = '...'

in:
SELECT \* FROM users WHERE email = 'admin' OR 1=1

con ritorno di tutti gli utenti.

**2. UNION-based SQL injection**
Esempi:

* `' UNION SELECT NULL--`
* `' UNION SELECT username, password FROM users--`

Questa tecnica permette di unire il risultato della query originale con dati arbitrari estratti da altre tabelle.

Nel dataset, queste richieste sono frequentemente dirette a endpoint come:

* /rest/products/search
* /api/Users

La presenza di UNION è un indicatore forte di intenzione di esfiltrazione dati.

**3. Time-based blind SQL injection**
Payload osservati:

* `SLEEP(15)`
* `pg_sleep(15)`
* `WAITFOR DELAY '0:0:15'`

Esempio:
GET /rest/products/search?q=' OR SLEEP(15)--

Questa tecnica non cerca di ottenere dati direttamente, ma di inferirli attraverso delay nella risposta. Se la risposta impiega 15 secondi, significa che il payload è stato eseguito.

Nel dataset, molte di queste richieste restituiscono 500 o 200 senza delay apparente, il che indica che l’injection non è stata eseguita con successo.

**4. Query distruttive**
Payload:

* `DROP TABLE`
* `DELETE FROM`
* `INSERT INTO`

Esempio:
GET /api/Users?email=admin'; DROP TABLE Users--

Questo tipo di payload è chiaramente distruttivo e indica una fase avanzata dell’attacco, anche se nel dataset non vi è evidenza di esecuzione.

***

**Comportamento delle risposte HTTP negli eventi ALTO**  
Uno degli aspetti più importanti per l’analisi della severity ALTO è la risposta HTTP del server.

Nel dataset:

* **200 OK** → la richiesta è stata processata  
  Questo è il caso più delicato: il payload ha raggiunto la logica applicativa. Tuttavia, nel contesto Juice Shop, spesso il body rimane invariato → injection non riuscita.

* **401 Unauthorized** → intercettazione da middleware di autenticazione  
  Il payload non è arrivato alla query SQL.

* **406 Not Acceptable** → validazione applicativa fallita  
  Tipico per endpoint come /redirect.

* **500 Internal Server Error** → comportamento anomalo dell’applicazione  
  In Juice Shop è molto comune e non implica necessariamente successo dell’attacco.

La presenza di codice 200 è il principale fattore di rischio nella fascia ALTO, perché indica che l’attacco ha oltrepassato il primo livello di filtro.

***

**Analisi degli XSS (ALTO)**  
Gli eventi XSS a livello ALTO nel dataset sono meno frequenti rispetto alle SQL injection, ma comunque rilevanti.

Esempi:

* `<script>alert(1)</script>`
* `x`

Questi payload sono progettati per eseguire codice JavaScript nel browser della vittima.

Nel dataset, questi attacchi:

* colpiscono endpoint come /redirect e /api/Challenges
* producono tipicamente risposta 200 o 406

La distinzione rispetto alla fascia MEDIO è sottile ma importante:

* in MEDIO lo XSS è spesso bloccato (406) e considerato test generico
* in ALTO lo XSS è più diretto e mirato

Tuttavia, anche in ALTO, non c’è evidenza che lo script venga effettivamente eseguito nel browser — quindi si tratta comunque di tentativi.

***

**Pattern comportamentali degli eventi ALTO**  
Gli eventi ALTO nel dataset presentano caratteristiche ricorrenti:

* Provenienza da tool automatizzati:
  * sqlmap
  * curl
  * python-requests
  * Nmap scripting engine

* Target di endpoint sensibili:
  * /api/Users
  * /rest/products/search
  * /api/BasketItems
  * /rest/admin/application-configuration

* Frequenza limitata:
  * spesso singoli eventi o piccoli cluster
  * assenza di flood massivo (che invece caratterizza CRITICO)

* Payload altamente strutturati:
  * non casuali, ma derivati da tool di exploitation reali

Questo indica una fase di attacco attiva ma non ancora sistematica.

***

**Relazione tra ALTO, MEDIO e CRITICO**

**Verso MEDIO:**

* MEDIO contiene tentativi generici o non specifici
* ALTO introduce exploit concreti e riconoscibili

Esempio:

* MEDIO: richiesta con pattern sospetto generico
* ALTO: payload SQL completo con UNION o SLEEP

**Verso CRITICO:**

* ALTO: pochi tentativi mirati
* CRITICO: molti tentativi ripetuti dallo stesso IP

Un attaccante tipico segue questo pattern:

1. MEDIO → scanning e reconnaissance
2. ALTO → exploitation mirata
3. CRITICO → automazione su larga scala

***

**Falsi positivi e considerazioni specifiche su Juice Shop**  
Nel contesto Juice Shop, alcuni eventi ALTO possono sembrare più gravi di quanto siano in realtà, perché:

* l’applicazione è Node.js → molte SQL injection non sono rilevanti
* i parametri vengono spesso ignorati o sanitizzati implicitamente
* molte risposte 200 non implicano realmente esecuzione del payload

Tuttavia, in un ambiente reale:

* gli stessi log sarebbero altamente critici
* soprattutto quelli con risposta 200

***

**Correlazioni operative**  
Gli eventi ALTO devono essere sempre analizzati in correlazione con:

* eventi precedenti dallo stesso srcip (MEDIO → fase di scan)
* eventi successivi (eventuale escalation a CRITICO)
* distribuzione temporale (burst vs tentativi isolati)

Un evento ALTO isolato può essere innocuo, ma:

* 5–10 eventi ALTO nello stesso minuto → indicano attacco coordinato

***

**Azione raccomandata e soglie di escalation**

Gli eventi ALTO richiedono un livello di attenzione significativamente superiore rispetto a MEDIO.

**Operativamente:**

* Revisione manuale entro poche ore
* Analisi del response body
* Correlazione con altri eventi dello stesso IP
* Identificazione del tool utilizzato (User-Agent)

**Escalation a CRITICO se:**

* lo stesso payload viene ripetuto in modo sistematico
* il numero di richieste supera una soglia (es. >10/minuto)
* più endpoint vengono attaccati dallo stesso IP

**Segnali di compromissione reale:**

* variazione nel response body
* ritardi anomali (time-based injection)
* presenza di dati inattesi nella risposta

***

In sintesi, la severity ALTO rappresenta il punto di confine tra attacco teorico e attacco potenzialmente efficace: il payload è corretto, l’intento è chiaro e il rischio è elevato, ma manca ancora la prova concreta di exploit riuscito o comportamento sistemico che caratterizza la fascia CRITICO.
