## Severity: BASSO (rule.level 3, 4, 5)

**Descrizione generale e contesto operativo**

La severity BASSO nel sistema di classificazione Wazuh comprende i livelli 3, 4 e 5 della scala ufficiale, che va da 0 a 16. Il livello 3 è denominato "Successful/Authorized Events" e riguarda accessi autorizzati riusciti, eventi di sistema normali, operazioni completate correttamente. Il livello 4 è denominato "System Low Priority Error" e riguarda errori di configurazione, dispositivi non più in uso, software in testing. Il livello 5 è denominato "User Generated Error" e riguarda password errate singole, azioni negate per mancanza di permessi, accessi a risorse non autorizzate senza pattern sistematico. Nel contesto specifico di questo dataset, prodotto dal monitoraggio di un'istanza OWASP Juice Shop attraverso Wazuh, la quasi totalità degli eventi BASSO appartiene al livello 5 e corrisponde a due macro-categorie: errori HTTP 4xx singoli e errori HTTP 5xx singoli. La parola chiave è "singoli" — la stessa tipologia di richiesta, se ripetuta sistematicamente dallo stesso IP in un breve arco temporale, triggera regole di livello 10 in Wazuh e produce severity CRITICO. La distinzione tra BASSO e CRITICO in questo dataset non dipende quindi dalla natura della richiesta ma dalla frequenza con cui Wazuh l'ha osservata prima di generare l'alert.

OWASP Juice Shop è un'applicazione web volutamente vulnerabile, progettata per il training sulla sicurezza. Questa caratteristica è fondamentale per interpretare correttamente gli eventi BASSO: molti endpoint di Juice Shop restituiscono HTTP 500 anche su richieste normali, non perché stia avvenendo un attacco, ma perché l'applicazione è instabile per design. Un GET su `/rest/products` che restituisce 500 in un'applicazione di produzione sarebbe allarmante; in Juice Shop è comportamento atteso. Questo contesto deve essere tenuto presente nell'analisi degli eventi BASSO per evitare falsi positivi massivi.

---

**Rule descriptions associate a severity BASSO nel dataset**

Dall'analisi del CSV, le `rule.description` che Wazuh assegna agli eventi classificati BASSO sono esattamente due, entrambe a rule.level 5:

**`Web server 400 error code.`** — Questa regola si attiva quando il web server restituisce un singolo codice HTTP nella famiglia 4xx. Nel dataset, i codici osservati sono 401 (Unauthorized), 406 (Not Acceptable). Il 401 compare quasi esclusivamente su `POST /rest/user/login` e indica un tentativo di autenticazione fallito con credenziali errate. Il 406 compare su `GET /redirect` e indica che il server ha rifiutato la richiesta perché il parametro `to` non soddisfa i criteri di validazione — Juice Shop implementa una whitelist di redirect consentiti e risponde 406 su tutto il resto.

**`Web server 500 error code (Internal Error).`** — Questa regola si attiva quando il web server restituisce un singolo codice HTTP 500. Nel dataset, il 500 compare su una varietà molto ampia di endpoint: `/rest/products`, `/rest/admin`, `/rest/user`, `/api`, `/api/Challenges`, `/api/Feedbacks`, `/api/Quantitys`, `/api/Addresss`, `/rest/user/login` (sia GET che POST), e decine di varianti con path obfuscation, estensioni backup, path traversal.

---

**Analisi dettagliata degli eventi HTTP 401 BASSO**

Il pattern più frequente nel dataset per severity BASSO è il seguente:

```
POST /rest/user/login HTTP/1.1 401 26
Referer: https://juice-shop.vtsolutions.it/
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0
```

Il response body di esattamente 26 byte è il messaggio di errore standard di Juice Shop per credenziali errate: `{"status":"error"}` o equivalente. Questo pattern da solo — un singolo 401 da un IP con Firefox su Linux — è completamente normale. Un utente che inserisce la password sbagliata una volta genera esattamente questo log. La rule.description "Web server 400 error code." con rule.level 5 è la risposta corretta di Wazuh.

Gli IP sorgente che generano questi 401 singoli nel dataset sono principalmente 10.42.0.234, 10.42.2.150, 10.42.1.207. Questi stessi IP generano anche eventi CRITICO quando Wazuh rileva che i 401 si accumulano su `/rest/user/login` in sequenza rapida — in quel caso la rule.description diventa "Multiple web server 400 error codes from same source ip." con rule.level 10. La coesistenza di eventi BASSO e CRITICO dallo stesso IP riflette la dinamica reale: i primi tentativi di brute force vengono visti come BASSO, poi Wazuh accumula il contatore e scatta CRITICO.

Altri endpoint con 401 classificato BASSO nel dataset:

```
GET /api/Addresss HTTP/1.1 401 31
```

Il response body di 31 byte indica una risposta di errore autenticazione leggermente più lunga. `/api/Addresss` (con doppia s) è l'endpoint Juice Shop per la gestione degli indirizzi utente — richiede autenticazione. Un accesso non autenticato produce 401 e rule.level 5. Niente di preoccupante in isolamento.

```
POST /api/Quantitys HTTP/1.1 401
POST /api/SecurityQuestions HTTP/1.1 401
POST /api/Challenges HTTP/1.1 401
```

Tutti endpoint protetti di Juice Shop. Accesso non autenticato → 401 → rule.level 5 → BASSO. Pattern identico.

---

**Analisi dettagliata degli eventi HTTP 406 BASSO**

Il codice 406 (Not Acceptable) compare esclusivamente su richieste verso `/redirect` con parametri `to` rifiutati dalla logica applicativa di Juice Shop. Esempi dal dataset:

```
GET /redirect?to=%2B HTTP/1.1 406
GET /redirect?to=%7D%29%3B HTTP/1.1 406
GET /redirect?to=..%2F..%2F..%2F..%2F..%2F..%2F HTTP/1.1 406
GET /redirect?to=%5CWEB-INF%5Cweb.xml HTTP/1.1 406
GET /redirect?to=c%3A%2FWindows%2Fsystem.ini HTTP/1.1 406
GET /redirect?to=%5Credirect HTTP/1.1 406
GET /redirect?to=redirect HTTP/1.1 406
GET /redirect?to=https%3A%2F%2F2582958944412320189%252eowasp%252eorg HTTP/1.1 406
GET /redirect?to=%23%7B%25x%28sleep+15%29%7D HTTP/1.1 406
```

Questi sono chiaramente tentativi di path traversal, open redirect, template injection, e directory traversal — ma il server li ha bloccati con 406. Juice Shop ha una protezione sul parametro `to` che valida il valore rispetto a una whitelist. Il fatto che il server risponda 406 invece di eseguire il redirect significa che l'attacco non è andato a segno. Wazuh classifica correttamente questi eventi come rule.level 5 perché il server ha gestito la situazione autonomamente senza compromissione. Se uno di questi avesse restituito 302 o 200 invece di 406, la classificazione sarebbe completamente diversa.

Un caso particolare da notare:

```
GET /redirect?to=%22%3Bprint%28chr%28122%29.chr%2897%29.chr%28112%29...%29%29%3B%24var%3D%22 HTTP/1.1 406
```

Questo è un tentativo di PHP code injection attraverso il parametro `to` — la stringa decodificata produce `";print(chr(122).chr(97)...);$var="` che è una tecnica per rilevare se il server esegue PHP. Risposta 406 → server non vulnerabile → BASSO.

---

**Analisi dettagliata degli eventi HTTP 500 BASSO**

La categoria HTTP 500 BASSO è la più numerosa nel dataset e la più variegata. Si articola in diversi sotto-pattern.

**Sotto-pattern 1: accesso a endpoint REST base senza autenticazione o con path errato**

```
GET /rest HTTP/1.1 500
GET /rest/products HTTP/1.1 500
GET /rest/admin HTTP/1.1 500
GET /rest/user HTTP/1.1 500
GET /api HTTP/1.1 500
GET /rest/captcha HTTP/1.1 500
POST /rest/captcha HTTP/1.1 500
POST /rest/user/login HTTP/1.1 500
```

Questi 500 sono caratteristici di Juice Shop: l'applicazione crasha su richieste che non gestisce correttamente invece di restituire 404 o 401. Un GET su `/rest` senza subpath causa un Internal Server Error perché il router Express non trova il handler corretto. Non indica un attacco — indica che qualcuno sta navigando l'applicazione o che uno scanner ha trovato il path base.

**Sotto-pattern 2: enumerazione di file backup e file sensibili**

Questo è il sotto-pattern più interessante della categoria BASSO. Nel dataset compaiono decine di richieste verso path con estensioni tipiche di backup:

```
GET /rest/admin/application-version.tar HTTP/1.1 500
GET /api/Quantitys.tar HTTP/1.1 500
GET /rest/user/login.bac HTTP/1.1 500
GET /rest/products/search.backup HTTP/1.1 500
GET /rest/admin.bak HTTP/1.1 500
GET /rest/admin.old HTTP/1.1 500
GET /rest.zip HTTP/1.1 500
GET /rest.old HTTP/1.1 500
GET /rest.swp HTTP/1.1 500
GET /api.bak HTTP/1.1 500
GET /api.backup HTTP/1.1 500
GET /rest/products.~bk HTTP/1.1 500
GET /rest/products/search.swp HTTP/1.1 500
GET /rest/user/whoami.~bk HTTP/1.1 500
GET /rest/languages.bak HTTP/1.1 500
GET /rest/languages.zip HTTP/1.1 500
GET /rest/languages.old HTTP/1.1 500
GET /rest/languages.bac HTTP/1.1 500
GET /rest/admin/application-configuration.swp HTTP/1.1 500
GET /rest/admin/application-version.old HTTP/1.1 500
```

Tutti questi producono 500 perché i file non esistono — Juice Shop non ha file di backup esposti. La classificazione BASSO è corretta perché nessuna informazione è stata esfiltrata. Tuttavia, questo pattern di enumerazione sistematica di backup files è una fase di reconnaissance riconoscibile — in un ambiente reale con file di backup effettivamente presenti, alcune di queste richieste avrebbero restituito 200 e sarebbero state MEDIO o ALTO.

**Sotto-pattern 3: path obfuscation e varianti di directory**

```
GET /rest/admin%20-%20Copy%20(3) HTTP/1.1 500
GET /rest/admin%20-%20Copy%20(2) HTTP/1.1 500
GET /rest%20-%20Copy%20(2)/products HTTP/1.1 500
GET /rest/Copy%20(3)%20of%20admin HTTP/1.1 500
GET /rest%20-%20Copy%20(3)/languages HTTP/1.1 500
GET /api%20-%20Copy/Challenges HTTP/1.1 500
GET /api/SecurityQuestions%20-%20Copy%20(3) HTTP/1.1 500
```

Questo pattern simula i nomi di file che Windows genera quando si copia una cartella ("Copia di", "Copy (2)", ecc.). È una tecnica di enumerazione automatizzata che cerca copie accidentali di directory. Tutti producono 500 → nessuna esposizione → BASSO.

**Sotto-pattern 4: enumerazione di file di controllo versione**

```
GET /api/.git/index HTTP/1.1 500
GET /rest/admin/.svn/text-base/application-version.svn-base HTTP/1.1 500
GET /api/.svn/text-base/Quantitys.svn-base HTTP/1.1 500
GET /rest/user/.svn/text-base/whoami.svn-base HTTP/1.1 500
GET /api/.svn/text-base/Challenges.svn-base HTTP/1.1 500
```

Tentativi di accedere a repository Git e SVN esposti accidentalmente. Un `.git/config` o `.svn/entries` accessibile su un server di produzione è una vulnerabilità critica perché contiene credenziali e storia del codice. In questo caso tutti producono 500 → repository non esposto → BASSO.

**Sotto-pattern 5: TRACE method**

```
TRACE /api/Challenges HTTP/1.1 500
TRACE /rest/admin HTTP/1.1 500
TRACE /api/Quantitys HTTP/1.1 500
TRACE /rest/memories/ HTTP/1.1 500
TRACE /rest/captcha HTTP/1.1 500
TRACE /rest/user/whoami HTTP/1.1 500
TRACE /rest/languages HTTP/1.1 500
```

Il metodo HTTP TRACE è storicamente associato agli attacchi Cross-Site Tracing (XST) che permettono di rubare cookie HttpOnly bypassando le protezioni browser. In un server correttamente configurato TRACE dovrebbe essere disabilitato. Juice Shop risponde 500 su TRACE — il server non lo gestisce esplicitamente, il router Express crasha. Il server non è vulnerabile a XST in questo caso → BASSO. In un server che rispondesse 200 a TRACE, questi eventi sarebbero MEDIO.

**Sotto-pattern 6: User-Agent rotation**

Un elemento caratteristico degli eventi BASSO nel dataset è la presenza di User-Agent molto datati o inusuali su richieste verso endpoint standard:

```
Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)
Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1)
Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)
Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us)
Mozilla/5.0 (iPhone; CPU iPhone OS 8_0_2 ...)
Mozilla/5.0 (Windows NT 10.0; Trident/7.0; rv:11.0) like Gecko
Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/91.0
msnbot/1.1 (+http://search.msn.com/msnbot.htm)
```

Questi User-Agent anomali compaiono su richieste GET ordinarie verso `/rest`, `/rest/user`, `/rest/admin`, `/api` — richieste che producono 500. Non c'è nessun payload malevolo nella richiesta stessa, solo il path. Si tratta di un tool automatizzato che ruota gli User-Agent per evitare detection basata su fingerprinting dell'agente. Il fatto che producano solo 500 li mantiene in fascia BASSO, ma la presence di UA rotation su uno stesso srcip è un indicatore comportamentale da annotare.

---

**Falsi positivi caratteristici della fascia BASSO in questo dataset**

Ci sono eventi nel dataset che la ground truth classifica BASSO ma che a una prima lettura sembrano meritare classificazione superiore. Esempi:

```
GET /rest/.htaccess HTTP/1.1 500 — rule.description: Suspicious URL access, rule.level 6
GET /rest/admin/.htaccess HTTP/1.1 500 — rule.description: Suspicious URL access, rule.level 6
GET /api/Feedbacks/.htaccess HTTP/1.1 401 — rule.description: Suspicious URL access, rule.level 6
GET /rest/products/.htaccess HTTP/1.1 500 — rule.description: Suspicious URL access, rule.level 6
```

Questi eventi hanno rule.level 6 ("Low relevance attack") ma ground truth BASSO. La spiegazione è che il server ha risposto con 500 o 401 — il file `.htaccess` non è stato esposto. Un `.htaccess` accessibile (risposta 200) sarebbe pericoloso perché contiene direttive Apache incluse potenzialmente credenziali o configurazioni di sicurezza. Il criterio di classificazione BASSO qui è la risposta del server, non la natura della richiesta.

```
GET /rest/products/search?q=5%3BURL%3D%27https%3A%2F%2F2582958944412320189.owasp.org%2F%3F%27 HTTP/1.1 500
```

Questo è un tentativo di SSRF (Server-Side Request Forgery) — il parametro `q` contiene un URL verso un dominio OWASP. Il server risponde 500 → richiesta non elaborata → BASSO. In un server vulnerabile che avesse seguito il redirect, sarebbe ALTO.

---

**Correlazioni importanti tra eventi BASSO e altri livelli**

Il dataset mostra un pattern ricorrente: lo stesso srcip genera sia eventi BASSO che eventi CRITICO sullo stesso endpoint nello stesso arco temporale. Esempio paradigmatico con 10.42.1.207 su `/rest/user/login`:

- `POST /rest/user/login HTTP/1.1 401` con rule.level 5 → BASSO
- `POST /rest/user/login HTTP/1.1 401` con rule.level 5 → BASSO
- `POST /rest/user/login HTTP/1.1 401` con rule.level 10, rule.description "Multiple web server 400 error codes from same source ip." → CRITICO

Wazuh incrementa un contatore interno per IP sorgente. I primi N tentativi producono alert singoli a livello 5. Quando il contatore supera la soglia configurata, Wazuh genera un alert aggregato a livello 10. Questo significa che in un flusso di analisi real-time, gli eventi BASSO che precedono un CRITICO dallo stesso IP sono parte dello stesso attacco — la classificazione BASSO è accurata per l'evento singolo, ma il contesto temporale li rende componenti di un pattern più grave.

---

**Azione raccomandata e soglie di escalation**

Gli eventi BASSO isolati non richiedono azione immediata. Il protocollo operativo corretto è:

Logging completo con retention minima di 90 giorni per permettere correlazione retroattiva. Nessuna notifica real-time. Nessuna escalation automatica.

Un evento BASSO deve essere rivalutato verso livello superiore se si verifica almeno una delle seguenti condizioni:

Il campo `srcip` dello stesso evento appare anche come sorgente di eventi ALTO o CRITICO nel medesimo arco temporale di 5 minuti — in questo caso l'evento BASSO è parte della catena di attacco e va trattato come tale.

La risposta HTTP cambia: se un endpoint che in precedenza produceva 500 ora produce 200 sulla stessa richiesta, il livello di rischio è radicalmente diverso indipendentemente dalla rule.level assegnata da Wazuh.

Il path richiesto contiene estensioni di backup (`.bak`, `.old`, `.tar`, `.zip`, `.swp`, `.~bk`, `.backup`, `.bac`) e la risposta è 200 invece di 500 — questo indica file di backup effettivamente esposti.

Il metodo HTTP è TRACE e la risposta è 200 invece di 500 — server vulnerabile a XST.

Il numero di eventi BASSO dallo stesso srcip sullo stesso endpoint in una finestra di 60 secondi supera 10 — Wazuh dovrebbe già aver generato un CRITICO, ma se per qualsiasi motivo non lo avesse fatto, questa soglia è l'indicatore manuale.