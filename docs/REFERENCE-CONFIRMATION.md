# Strong-Bestätigung durch zwei Referenzen – Version 1.3

Version 1.3 prüft jede bestehende Unsicherheitsmarkierung der eigenen Strong-
Zuordnungen gegen **ELB BK** und die **Elberfelder Ausgabe des CSV-Verlags**.
Bestätigen beide Referenzen die vollständige bereits vorhandene Nummernmenge
am eindeutig zugeordneten Wortbereich, entfällt ausschließlich der zugehörige
Hinweis. Bibeltext, Strong-Nummern und historische Originalnotizen bleiben
unverändert. Es werden keine neuen Nummern aus den Referenzen übernommen.

## Vollständig aufbauen

Beide Referenzdateien werden als lokale Zefania-XML-Snapshots benötigt. „CSV“
bezeichnet hier den Verlag, nicht das Dateiformat.

Die CSV-Webseiten können mit dem [vorsichtigen Browser-Abruf](CSV-REFERENCE.md)
privat zwischengespeichert und reproduzierbar in dieses Eingabeformat
überführt werden.

```bash
python bible.py build --edition all --version 1.3 \
  --elb-bk .local/references/elb-bk.xml \
  --elb-csv .local/references/elb-csv.xml

python scripts/verify_repository.py --version 1.3
```

`--edition elb` und `--edition lut` sind einzeln möglich. Die zwei Quellen
werden für beide Zielausgaben unabhängig zugeordnet. Referenzdateien gehören
unter `.local/` und werden nicht in Git, öffentliche Laufarchive oder Pakete
kopiert. Ein vorheriger `edit`-Aufruf ist nicht erforderlich.

Die Standardversion in `akribos/project.py` bleibt vorerst **1.2**. Bei einem
normalen 1.2-Build wird weiterhin ausschließlich `04-multisource.xml`
veröffentlicht. Die Referenzoptionen sind dem ausdrücklich gewählten
1.3-Aufbau vorbehalten. Version 1.4 benötigt eine eigene sprachwissenschaftliche
Prüfstufe und kann mit diesem Stand noch nicht gebaut werden.

Fehlt eine der beiden Dateien, sind ihre Prüfsummen identisch, enthält eine
Datei doppelte Vers-IDs oder passt das XML-Profil nicht, bricht der Aufruf vor
dem Anlegen eines Implementierungssnapshots und vor der Sprachbearbeitung ab.
Fehlende einzelne Verse verhindern nur die Bestätigung der jeweiligen Hinweise.

## Wann ein Hinweis entfällt

Alle folgenden Bedingungen müssen in **beiden** Referenzen erfüllt sein:

1. Die Bibelstelle ist vorhanden. Es gibt keine automatische Umnummerierung.
2. Die Wörter stimmen nach Unicode-NFC-Normalisierung und Kleinschreibung
   überein. Es gibt keine Lemma-, Synonym- oder Gottesnamen-Ersetzung und kein
   pauschales `ß` → `ss`.
3. Jede optimale Wortausrichtung führt für jedes betroffene Zielwort auf
   denselben Referenzplatz. Mehrdeutige Wiederholungen bleiben markiert. Durch
   den Kontext eindeutig bestimmte Wiederholungen sind zulässig.
4. Mehrwortbereiche sind zusammenhängend und vollständig getaggt. Eine größere
   Referenzphrase bestätigt kein einzelnes Wort darin. Eine Zielphrase darf
   jedoch mehreren vollständig getaggten Referenzwörtern entsprechen.
5. Die gesamte Strong-Menge ist exakt gleich. Teilmengen, zusätzliche Nummern
   oder das bloße Vorkommen einer Nummer irgendwo im selben Vers reichen nicht.

Die Ausrichtung untersucht sämtliche optimalen längsten gemeinsamen
Wortfolgen. Sie entscheidet bei wiederholten Wörtern nicht willkürlich zwischen
mehreren gleich guten Möglichkeiten.

Wörtliche `[?]`-Platzhalter bestätigen keine Wörter. Sie verhindern außerdem
eine Bestätigung, wenn sie innerhalb einer betroffenen Referenzmarkierung oder
zwischen den Wörtern einer abgeglichenen Phrase stehen. Der Worttokenizer kann
sie daher nicht als bloße Satzzeichen verschwinden lassen.

Ungültige Strong-Nummern, verschachtelte Zielzuordnungen und Hinweise ohne
eindeutigen Bezug auf das vorhergehende Strong-Element bleiben unverändert.
Hinweise innerhalb historischer Notizen werden ebenfalls erhalten und im
Prüfprotokoll als nicht unterstützt erfasst.

Die Bestätigung belegt Übereinstimmung mit zwei Ausgaben. Sie ist keine
eigenständige sprachwissenschaftliche Neubewertung der Zuordnung.

## Ergebnisse und Nachvollziehbarkeit

Der gewöhnliche Aufbau bis `04-multisource.xml` bleibt vollständig erhalten.
Danach entstehen im selben Laufordner:

| Datei | Inhalt |
|---|---|
| `05-reference-confirmed.xml` | Bibel mit ausschließlich bestätigten Hinweisen entfernt |
| `05-reference-confirmed.audit.jsonl.gz` | Eine Entscheidung für jede ursprüngliche Markierung |
| `05-reference-confirmed.report.json` | Eingabe-/Referenz-/Ergebnishashes, Profil, Zähler und Integritätsangaben |

Das öffentliche Einzelprotokoll nennt nur die eigene Bibelstelle,
Markierungsnummer, eigene Token-IDs und vorhandene eigene Strong-Mengen sowie
die Entscheidung und Gründe je Referenz. Referenzwörter, Referenzpositionen und
kopierte Referenzzuordnungen werden nicht darin gespeichert.

`manifest.json` nimmt die Hashes beider Referenzsnapshots, das Eingabeprofil und
das Bestätigungsverfahren in die Laufidentität auf. Private Dateipfade sind
kein Bestandteil der gespeicherten Einstellungen. Unterschiedliche
Dateipfade mit identischem Inhalt zählen nicht als zwei Referenzsnapshots.
Der Aufrufer muss tatsächlich die beiden benannten Quellen bereitstellen.

Die festen Ausgabepfade bleiben `releases/akribos.elb.xml` und
`releases/akribos.lut.xml`. Das jeweilige `.build.json` enthält für Version 1.3
zusätzlich `"artifact": "05-reference-confirmed.xml"`. Fehlt dieses Feld in
älteren Links, gilt weiterhin `04-multisource.xml`.

## Wiederholung und Integrität

```bash
python bible.py build --edition all --version 1.3 --rebuild \
  --elb-bk .local/references/elb-bk.xml \
  --elb-csv .local/references/elb-csv.xml
```

Identische Eingaben und Skripte verwenden denselben geprüften Lauf. Mit
`--rebuild` werden die Ergebnisse neu berechnet und mit den archivierten Bytes
verglichen. Veränderte Referenzhashes erzeugen einen eigenen Lauf, ohne alte
Läufe zu überschreiben. Auch beim Wiederverwenden eines vorhandenen Laufs sind
die beiden Referenzsnapshots erforderlich.

Nach der Transformation und nach dem XML-Schreiben werden Bibeltext,
Strong-Attribute und Originalnotizen mit Stufe 04 verglichen. Der
Repository-Prüfer kontrolliert zusätzlich den ausgewählten Release-Bestandteil,
die unterschiedlichen Referenzhashes, die vollständige Zahl der
Einzelentscheidungen und die Zahl der entfernten Hinweise.

Der bestehende Befehl `compare` bleibt ein rein lesender Vergleich. Die
Python-Analysefunktion `confirm_uncertainty(target, bk, None)` kann eine
unvollständige Vorprüfung liefern; sie entfernt ohne zweite Referenz keinen
Hinweis und erzeugt keinen veröffentlichten 1.3-Bestand.
