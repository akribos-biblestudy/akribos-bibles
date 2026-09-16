# Edition CSV als private Vergleichsquelle abrufen

Die Edition CSV wird ausschließlich zur Kontrolle vorhandener Zuordnungen
verwendet. Die heruntergeladenen Seiten und das daraus erzeugte Referenz-XML
bleiben unter `.local/`. Der öffentliche Prüfbericht enthält die eigenen
Zuordnungen und Entscheidungen, keinen kopierten Referenztext.

## Einmaliger Abruf im Browser

1. Eine Kapitelseite auf <https://www.csv-bibel.de/bibel/matthaeus-1> im normalen
   Browser öffnen. Die Bibel muss bereits sichtbar sein.
2. [collect_csv_reference.js](../scripts/collect_csv_reference.js) in der
   Entwicklerkonsole dieser Seite ausführen. Das Skript selbst startet noch
   keinen Download.
3. Den Abruf starten:

   ```javascript
   void akribosCSV.start();
   ```

4. Den Fortschritt prüfen:

   ```javascript
   await akribosCSV.status();
   ```

5. Wenn `running` falsch, `error` leer und `done` gleich `total` ist, den
   privaten Cache exportieren:

   ```javascript
   await akribosCSV.download();
   ```

6. Die heruntergeladene `chunk-browser.json` nach
   `.local/references/csv-cache/` verschieben.

Das Skript arbeitet seriell und beachtet die `Crawl-delay`-Angabe der
`robots.txt`, mindestens aber zehn Sekunden. Beim derzeitigen Umfang von
1.189 Kapiteln dauert der erste vollständige Abruf ungefähr 3½ Stunden.
HTTP-Fehler, Zugriffssperren oder unerwartete Inhalte stoppen den Lauf;
es gibt keine automatischen Wiederholungen oder Umgehungen.

Eine browserweite Sperre verhindert versehentliche parallele Läufe in
mehreren Tabs. Dafür wird ein Browser mit Unterstützung für Web Locks benötigt.

Die bereits gespeicherten Kapitel bleiben in der IndexedDB dieses Browsers.
`akribosCSV.stop()` hält den Lauf an. Ein späteres `start()` setzt ihn mit
demselben Cache fort, ohne gespeicherte Kapitel erneut abzurufen. Nach einem
Neuladen muss das Skript erneut ausgeführt werden; die IndexedDB bleibt
erhalten. Während des Abrufs keine weiteren automatisierten Zugriffe auf
denselben Server starten.

## Referenz-XML aus dem Cache erzeugen

```bash
python -m akribos.csv_reference \
  --cache-dir .local/references/csv-cache \
  --output .local/references/elb-csv.xml --require-complete
```

Der Import prüft die Prüfsummen, Kapitel- und Versnummern sowie die
Übereinstimmung der Strong-Angaben in den HTML-Attributen und sichtbaren
Nummern. Mehrfachnummern werden vollständig erhalten. Qualifizierte Angaben,
Textvarianten und nicht unterstützte Unterkennungen bleiben unbestätigt.
Fußnoten und Bedienoberfläche werden nicht als Bibeltext eingelesen.
Nummerierte Verse, deren Text nur in einer Fußnote steht, bleiben fehlende
Vergleichsverse; der Fußnotentext wird nicht als Haupttext übernommen.

`--require-complete` prüft alle 1.189 Kapitel gegen den Kapitelindex dieser
Ausgabe, einschließlich Joel 1–4 und Maleachi 1–3. Ein unvollständiger Cache
ersetzt damit keinen vorhandenen Snapshot. Für private Zwischenprüfungen
während des Abrufs kann der Schalter entfallen.

Die Ausgabe nennt Herausgeber, Herkunftsseiten und deren Prüfsummen.
Identische Cache-Dateien erzeugen identisches XML. Für spätere Builds genügt
dieser private Snapshot; ein erneuter Onlineabruf ist nicht erforderlich.

Der anschließende Aufbau steht unter
[Strong-Bestätigung durch zwei Referenzen](REFERENCE-CONFIRMATION.md).
