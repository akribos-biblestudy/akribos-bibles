# Strong-Bestätigung durch zwei Referenzen – Stufe 05

Die in Version 1.3 eingeführte Stufe 05 prüft jede bestehende Unsicherheitsmarkierung der eigenen Strong-
Zuordnungen gegen **ELB BK** und die **Elberfelder Ausgabe des CSV-Verlags**.
Bestätigen beide Referenzen die vollständige bereits vorhandene Nummernmenge
am eindeutig zugeordneten Wortbereich und greift keines der unten beschriebenen
Sicherheitsvetos, entfällt ausschließlich der zugehörige Hinweis. Bibeltext,
Strong-Nummern und historische Originalnotizen bleiben
unverändert. Es werden keine neuen Nummern aus den Referenzen übernommen.

## Vollständig aufbauen

Beide Referenzdateien werden als lokale Zefania-XML-Snapshots benötigt. „CSV“
bezeichnet hier den Verlag, nicht das Dateiformat.

ELB BK wird als Zefania-Modul auf der offiziellen
[Downloadseite von bibelkommentare.de](https://www.bibelkommentare.de/downloads/module)
angeboten: [ZIP herunterladen](https://www.bibelkommentare.de/data/modules/bible_elb_bk_zefania.zip),
entpacken und `bible_elb_bk_mybible.xml` privat als
`.local/references/elb-bk.xml` ablegen. Die dortige Modulnummer 1.3 bezeichnet
die Referenzausgabe und ist unabhängig von der Akribos-Ausgabenummer.

Die CSV-Webseiten können mit dem [vorsichtigen Browser-Abruf](CSV-REFERENCE.md)
privat zwischengespeichert und reproduzierbar in dieses Eingabeformat
überführt werden. Für den vollständigen Aufbau zunächst den gesamten Cache
exportieren und mit Vollständigkeitsprüfung konvertieren:

```bash
python -m akribos.csv_reference \
  --cache-dir .local/references/csv-cache \
  --output .local/references/elb-csv.xml --require-complete
```

`--require-complete` verlangt alle Kapitel des CSV-Kapitelindex. Für einen
späteren identischen Aufbau beide privaten XML-Snapshots unverändert
aufbewahren; ein neuer Abruf kann andere Dateihashes ergeben.

```bash
python bible.py build --edition all --version 1.4 \
  --elb-bk .local/references/elb-bk.xml \
  --elb-csv .local/references/elb-csv.xml

python scripts/verify_repository.py --version 1.4
```

`--edition elb` und `--edition lut` sind einzeln möglich. Die zwei Quellen
werden für beide Zielausgaben unabhängig zugeordnet. Referenzdateien gehören
unter `.local/` und werden nicht in Git, öffentliche Laufarchive oder Pakete
kopiert. Ein vorheriger `edit`-Aufruf ist nicht erforderlich.

Die Standardversion in `akribos/project.py` ist **1.4**. Ein regulärer Build
benötigt auch ohne `--version` beide Referenzoptionen. Er führt die hier
beschriebene Stufe 05 aus und hängt die [sprachliche Strong-Prüfung](LINGUISTIC-VALIDATION.md)
als Stufe 06 an; veröffentlicht wird `06-linguistic.xml`. Version 1.3 endete
bei `05-reference-confirmed.xml`, Versionen 1.1 und 1.2 bei Stufe 04. Für den
ursprünglichen Stand einer früheren Version den passenden Git-Tag verwenden;
`--version` allein lädt keinen historischen Code. Siehe [Versionshistorie](HISTORY.md).

Der vollständige CSV-Abruf und die Konvertierung mit `--require-complete`
gehören zur Vorbereitung des vollständigen Aufbaus. Der Bestätigungskern
unterstützt daneben private Teilprüfungen: Fehlende Kapitel werden dort nicht
als erfolgreiche Bestätigung gewertet. Eine solche Teilprüfung ist kein
vollständiger Release-Aufbau.

Fehlt eine der beiden Dateien, sind ihre Prüfsummen identisch, enthält eine
Datei doppelte Vers-IDs oder passt das XML-Profil nicht, bricht der Aufruf vor
dem Anlegen eines Implementierungssnapshots und vor der Sprachbearbeitung ab.
Fehlende einzelne Verse verhindern nur die Bestätigung der jeweiligen Hinweise.

## Wann ein Hinweis entfällt

### Vollständige Quellen und unterschiedliche Verszählung

Die eingefrorenen Referenzen enthalten jeweils 66 Bücher und 1.189 Kapitel:
ELB BK hat 31.169 Haupttextverse, Edition CSV 31.166. Der vollständige
CSV-Kapitelindex wurde geprüft. Markus 15,28, Apostelgeschichte 15,34 und
28,29 stehen dort ausschließlich als Fußnotenverse ohne Haupttext und ohne
Strong-Verknüpfungen; sie ergeben keine Bestätigungsverse.

Weitere Unterschiede betreffen Versaufteilungen: ELB Lukas 17,36 entspricht
in den Referenzen 17,37; Apostelgeschichte 19,40–41 ist dort unter 19,40
zusammengefasst. In Luther sind 2. Könige 15,38–39 und Psalm 13,6–7 anders
aufgeteilt. Nehemia 7 weist ebenfalls einen Versversatz und einen anders
aufgeteilten Anschluss an 8,1 auf. Der Vergleich nummeriert diese Stellen
nicht automatisch um. Fehlende oder nicht eindeutig passende Belege
bestätigen keinen Hinweis. Gleiche Versnummern allein sind kein Beleg für
gleiche Textaufteilung.

### Bedingungen am konkreten Wortbereich

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
6. Bei G3588 muss auch das unmittelbar folgende Zielwort in beiden Referenzen
   eindeutig auf das unmittelbar folgende Wort passen. Zwischen diesen Wörtern
   darf jeweils nur Leerraum stehen. Ein Artikel am Versende, ein größerer
   Zielbereich oder ein abweichender beziehungsweise mehrdeutiger rechter
   Kontext bleibt zur Prüfung stehen. Das gilt auch für G3588 in einer
   Mehrfachnummerierung.

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

### Gemeinsame Referenzfehler konservativ abfangen

Auch zwei übereinstimmende Ausgaben können dieselbe problematische Zuordnung
enthalten. Vier eng begrenzte Prüfungen bewahren deshalb den Hinweis:

- Der oben beschriebene rechte Artikelkontext verhindert, dass ein Artikel aus
  einer Referenzphrase ein anders verwendetes deutsches Pronomen bestätigt.
- G1537 oder G4314 an einem einzelnen deutschen `zu` bleibt unsicher, wenn
  unmittelbar ein kleingeschriebenes mögliches Infinitivwort folgt und dessen
  vorhandene Nummer im gewählten STEP-Vers tatsächlich als Verb vorkommt.
  Großgeschriebene Substantivierungen und bloß ähnlich endende Possessivformen
  liefern diesen Verbbeleg nicht.
- Für G1537, G1909, G3165, G4314, G3739, G3588 sowie H259 und H834 werden die bereits vorhandenen deutschen
  Markierungsspannen mit den tatsächlichen STEP-Wortvorkommen im Vers verglichen.
  Übersteigt die Zahl der Zielspannen die Zahl der Quellvorkommen, bleiben die
  betroffenen Hinweise stehen. Codes in Mehrfachnummerierungen zählen mit;
  eine Mehrwortspanne zählt als eine Spanne. Eine griechische oder hebräische Form kann korrekt
  durch mehrere deutsche Spannen wiedergegeben sein: Das Veto erklärt deshalb
  keine einzelne Nummer für falsch und wählt keinen vermeintlich richtigen
  Ersatzplatz aus. Insbesondere wird G3165 nicht pauschal an deutschem `ich`
  gesperrt: Ein griechisches Akkusativsubjekt beim Infinitiv kann im Deutschen
  ein eigenes `ich` ergeben. Entscheidend ist hier allein die konservative
  Belegzählung, ohne Alias-Normalisierung.
- G3754 an einem isolierten deutschen `es` bleibt markiert. Dieser
  Konjunktionscode bestätigt kein solches Subjektpronomen, auch wenn beide
  Referenzen dieselbe Nummer tragen. Die Regel erfasst keine anderen Pronomen,
  leitet keine Ersatznummer ab und behandelt eine größere Spanne wie `es sei`
  nicht als isoliertes Wort.

Die hebräische Erweiterung gilt ausschließlich für H259 und H834. In Exodus
33,5 gehört das ausdrückliche `einer/einen` zum Augenblick, nicht zum deutschen
unbestimmten Artikel vor dem Volk; in Genesis 19,21 gehört H834 zur relativen
Stadtphrase. Die Zählprüfung bewahrt überzählige Hinweise, ohne selbst eine
einzelne Verlinkung zu ändern. Andere hebräische Nummern sind nicht Teil
dieser Erweiterung.

Für diese beiden Codes werden die tatsächlichen OT-Wortvorkommen übernommen.
Ihre numerischen Wortpositionen müssen eindeutig und streng aufsteigend sein.
Eine Quellenkennung wie `L(abh)` oder `LAB(h)` bezeichnet dabei genau ein
L-Wortvorkommen. Echte Q-Lesarten werden nicht als zusätzliche Wörter zu L
addiert: Enthält der betreffende Vers Q-Zeilen, konkurrierende beziehungsweise
umgestellte Positionen oder nicht deutbare Positions-/Zeugenkennungen, bleibt
der Hinweis mit `hebrew-source-occurrence-count-unproved` erhalten. Das gilt
auch dann, wenn die problematische Quellenzeile eine andere Nummer trägt.

Diese Prüfungen übernehmen die bereits beim Aufbau erzeugten
`source-occurrences.jsonl.gz` und `alignment.jsonl.gz`. Deren Hashes, die
ausgewählte NT-Ausgabe und das Sicherheitsprofil werden festgehalten. Der
Alignmenttext und seine Wortpositionen müssen zur unveränderten Stufe 04
passen; fehlende Belege, alternative Quellversnummern oder ein bereits festgestellter Inventarkonflikt
verhindern die Freigabe der betroffenen Funktionscodes.

Das Verfahren heißt `two-reference-exact-strong-set-with-vetoes-v2`, das
Eingabeprofil `zefania-word-spans-with-article-context-v2` und das
Sicherheitsprofil `greek-hebrew-function-word-vetoes-v2`. Es bestätigt eingeschränkte
Referenzübereinstimmung mit konservativen Ausschlussregeln; eine vollständige
sprachwissenschaftliche Neubewertung aller Nummerierungen ist damit nicht
behauptet.

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
zusätzlich `"artifact": "05-reference-confirmed.xml"`; in Version 1.4 verweist
es auf `06-linguistic.xml`. Fehlt dieses Feld in älteren Links, gilt weiterhin
`04-multisource.xml`.

## Wiederholung und Integrität

```bash
python bible.py build --edition all --version 1.4 --rebuild \
  --elb-bk .local/references/elb-bk.xml \
  --elb-csv .local/references/elb-csv.xml
```

Identische Eingaben und Skripte verwenden denselben geprüften Lauf. Mit
`--rebuild` werden die Ergebnisse neu berechnet und mit den archivierten Bytes
verglichen. Veränderte Referenzhashes erzeugen einen eigenen Lauf, ohne alte
Läufe zu überschreiben. Auch beim Wiederverwenden eines vorhandenen Laufs sind
die beiden Referenzsnapshots erforderlich.

Nach Stufe 05 und nach dem Schreiben ihres XML werden Bibeltext,
Strong-Attribute und Originalnotizen mit Stufe 04 verglichen. Der
Repository-Prüfer kontrolliert zusätzlich den ausgewählten Release-Bestandteil,
die unterschiedlichen Referenzhashes und die gehashten STEP-/Alignmentbelege.
Er ordnet jede protokollierte Entscheidung exakt dem ursprünglichen Hinweis
zu, berechnet die öffentlichen Sicherheitsvetos erneut und spielt ausschließlich
die erlaubten Hinweisentfernungen nach. Die gesamte rekonstruierte XML-Struktur
muss mit der Ausgabe übereinstimmen. Auditfelder und Ergebnisgründe sind
geschlossen; zusätzliche Felder oder freie Referenztexte werden abgewiesen.
Die eigentliche private Wort-/Nachbarprüfung ist anhand der festgehaltenen
Referenzsnapshots reproduzierbar; deren Texte werden dafür nicht veröffentlicht.

Der bestehende Befehl `compare` bleibt ein rein lesender Vergleich. Die
Python-Analysefunktion `confirm_uncertainty(target, bk, None)` kann eine
unvollständige Vorprüfung liefern; sie entfernt ohne zweite Referenz keinen
Hinweis und erzeugt keinen veröffentlichten Release-Bestand. Auch bei zwei Referenzen
bleiben die acht genannten Funktionscodes ohne `safety_evidence` markiert.
Für eine vollständige lokale Prüfung lädt
`load_confirmation_evidence(target, occurrences_path, alignment_path, nt_edition="WH")`
die bestehenden Belege; ihr Ergebnis wird als `safety_evidence` an
`confirm_uncertainty` beziehungsweise den XML-Replay übergeben. Der normale
CLI-Aufbau erledigt dies automatisch. Es gibt keinen Freigabeschalter zum
Umgehen der Vetos.
