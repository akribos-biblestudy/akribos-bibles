# Akribos Bibeln – reproduzierbare Version 1.4

Akribos bearbeitet die **Elberfelder 1932** und **Luther 1912** sprachlich und
ergänzt Strong-Zuordnungen. Es handelt sich nicht um eigene Übersetzungen.
Dieses Repository enthält die Originaldaten, Skripte, öffentlichen
Zwischenstände und fertigen Ausgaben.

Version 1.4 prüft nach dem Referenzabgleich alle verbliebenen eigenen
Unsicherheitshinweise an konkreten griechischen und hebräischen Wortbelegen.
Sie bestätigt belegte Zuordnungen, ergänzt ausgewählte griechische Artikel
und korrigiert einzeln geprüfte Fehlverlinkungen. Fälle ohne ausreichenden
Beleg bleiben markiert. Weitere Sprachregeln verbessern die HERR-Artikel und
Kasusformen der ELB; historische Originalnotizen bleiben erhalten.

## Fertige Dateien importieren

- [Elberfelder 1932](releases/akribos.elb.xml), ID `akribos.elb`
- [Luther 1912](releases/akribos.lut.xml), ID `akribos.lut`
- [King James Version 1611/1769](releases/kjv1611.xml), syntaxreparierter
  Zefania-Export mit ursprünglichen Strong-Zuordnungen

Strong-Markierungen stehen beispielsweise als `<gr str="3068">HERR</gr>` im
XML. Mehrere Nummern werden durch Leerzeichen getrennt; H/G ergibt sich in
diesem Exportprofil aus dem Testament. Offene automatische Zuordnungen haben
eine eigene `NOTE` unmittelbar nach dem Wort. Historische Studynotes bleiben
erhalten; nicht zugeordnete Urtextnummern stehen nur in Begleitdateien.

## Einrichten und vollständig aufbauen

Voraussetzung: Python **3.11 oder neuer** mit `pip`. Das benötigte
Simplemma-Wheel liegt mit Prüfsumme im Repository; Einrichtung und Aufbau
benötigen nach Beschaffung der Referenzen keinen Internetzugriff und kein
KI-Abonnement.

```bash
git clone https://github.com/akribos-biblestudy/akribos-bibles.git
cd akribos-bibles
python scripts/setup.py
mkdir -p .local/references/csv-cache
```

`setup.py` installiert die mitgelieferte Abhängigkeit unter `.local/python`.
Falls Python auf deinem System `python3` heißt, verwende diesen Namen.

Die beiden Referenzen werden einmalig beschafft:

1. **ELB BK:** Das offizielle Zefania-Modul nach der
   [Downloadanleitung](docs/REFERENCE-CONFIRMATION.md#vollständig-aufbauen)
   entpacken und als `.local/references/elb-bk.xml` ablegen.
2. **Edition CSV:** Dem [fortsetzbaren Browser-Abruf](docs/CSV-REFERENCE.md)
   folgen und den vollständigen Cache unter `.local/references/csv-cache/`
   speichern. „CSV“ bezeichnet den Verlag, nicht ein Dateiformat. Anschließend
   alle 1.189 Kapitel prüfen und in das private Referenz-XML umwandeln:

   ```bash
   python -m akribos.csv_reference \
     --cache-dir .local/references/csv-cache \
     --output .local/references/elb-csv.xml --require-complete
   ```

Danach beide Ausgaben einschließlich der KJV-Importdatei aufbauen:

```bash
python bible.py build --edition all --version 1.4 \
  --elb-bk .local/references/elb-bk.xml \
  --elb-csv .local/references/elb-csv.xml
python scripts/verify_repository.py --version 1.4
```

`--edition elb` und `--edition lut` wählen eine Ausgabe einzeln aus. Ein
vorheriger `edit`-Aufruf oder 1.3-Build ist nicht erforderlich. Standardversion
ist **1.4**; auch ohne `--version` benötigt ein regulärer Build beide
Referenzoptionen. Für einen späteren identischen Aufbau die privaten
XML-Snapshots unverändert aufbewahren. Ein neuer Onlineabruf kann andere
Dateihashes ergeben. Die Referenztexte werden nicht mitveröffentlicht.

## Was Version 1.4 prüft und korrigiert

Der Aufbau verläuft in sechs Stufen: **Sprachbearbeitung → vorhandene
Strong-Zuordnungen → Lexika → weitere Übersetzungen → Referenzbestätigung →
sprachliche Strong-Prüfung**.

- **Sprachbearbeitung:** Weitere Regeln unterscheiden Titelbeifügungen,
  Anreden und Sprecher-Konstruktionen bei Jehova → HERR. Gegenüber dem
  Skriptstand von 1.3 ändern sich in ELB 213 Namensersetzungen in 190 Versen.
  Luthers Wortlaut bleibt gleich. Die
  [Sprachdokumentation](docs/DIVINE-NAME-CORRECTION.md#ergänzung-in-version-14)
  nennt Beispiele und Gegenfälle.
- **Referenzbestätigung, Stufe 05:** Eine bestehende Unsicherheitsmarkierung
  entfällt nur, wenn ELB BK und Edition CSV denselben eindeutigen Wortbereich
  mit derselben vollständigen Nummernmenge bestätigen und kein Sicherheitsveto
  greift. Bekannte gemeinsame Referenzfehler bleiben dadurch offen. Diese
  Stufe ändert weder Bibeltext noch Strong-Nummern oder Originalnotizen.
- **Sprachliche Prüfung, Stufe 06:** Echte STEP-Wortvorkommen, Morphologie,
  eindeutige Nachbarwörter und ausdrückliche Formenlisten prüfen die noch
  offenen Zuordnungen. Neue G3588-Artikel benötigen zudem eine genaue
  Wortbestätigung durch mindestens eine private Referenz. Deutsche Artikel
  werden nicht allein wegen ihrer Form verlinkt; `der`, `die`, `das` können
  auch Pronomen sein. Fehlende oder mehrdeutige Belege lassen den Hinweis
  stehen. Bibelwortlaut und Originalnotizen bleiben in dieser Stufe erhalten.
- **Feste redaktionelle Korrekturen:** Der
  [Katalog](docs/EDITORIAL-STRONG-CORRECTIONS.md) umfasst 43 positionsgenau
  geprüfte Regeln: 41 aus dem Bestand 1.2 (24 markierte und 17 geerbte
  Zuordnungen) sowie zwei neue Codesätze des 1.4-Neuaufbaus. Jede Änderung
  benötigt die festgelegte Ausgabe, Wortposition, den vollständigen Verstext,
  alten Codesatz und dieselben Quellbelege. Die Kataloggröße ist keine
  Ergebniszahl; der jeweilige Lauf weist die tatsächlich angewandten Regeln aus.

Die vorgelagerte deutsche Mehrwortzuordnung enthält zusätzlich 196 H3068-
Artikelverlinkungen in ELB und 176 in Luther. Sie gehören jeweils zu einem
bereits vorhandenen ursprünglichen Jehova/H3068-Bezug und zählen keine neuen
hebräischen Wortvorkommen. Diese Änderungen werden getrennt von den neuen
G3588-Artikelbelegen der Stufe 06 ausgewiesen.

Details: [Referenzbestätigung](docs/REFERENCE-CONFIRMATION.md),
[sprachliche Strong-Prüfung](docs/LINGUISTIC-VALIDATION.md),
[Namen](docs/LINGUISTIC-NAMES.md) und [Nomenformen](docs/LINGUISTIC-NOUNS.md).
Das NT-Prüfprofil ist WH für ELB und TR für Luther; `--nt-edition` wählt es
ausdrücklich. KJV bestätigt Nummern im Vers, keine direkte englisch-deutsche
Wortzuordnung. Wortabdeckung misst Markierungen, keine Zuordnungsgenauigkeit.

### Ergebnis des vollständigen 1.4-Aufbaus

Stand: **2026-09-16**. Alle Zahlen stammen aus den endgültigen
Reports dieses 1.4-Laufs; Stufe 05 wird dabei mit dem aktuellen Eingang neu
berechnet. Ihre Zähler müssen deshalb nicht dem früheren 1.3-Release entsprechen.

| Ausgabe | Hinweise entfernt: Stufe 05 | Hinweise entfernt: Stufe 06 | Hinweise verbleibend |
|---|---:|---:|---:|
| Elberfelder 1932 | 20.832 | 18 | 31.149 |
| Luther 1912 | 3.095 | 11 | 38.205 |

| Ausgabe | Neue G3588-Artikel | Angewandte redaktionelle Korrekturen |
|---|---:|---:|
| Elberfelder 1932 | 791 | 19 |
| Luther 1912 | 355 | 24 |

Die Hinweiszahl der Stufe 06 enthält auch tatsächlich entfernte Hinweise bei
redaktionellen Korrekturen. Diese Korrekturen betreffen teils geerbte,
unmarkierte Spannen und sind daher eine eigene Zählung. Die beiden Tabellen
werden nicht addiert. Jede Entscheidung steht im Audit. Frühere Messungen
bleiben mit ihrem jeweiligen Stand in [docs/RESULTS.md](docs/RESULTS.md).

## Titel und Exportmetadaten

Die Skripte setzen die Angaben bei jedem `edit`- und `build`-Aufruf:

| Angabe | ELB | Luther |
|---|---|---|
| Cover-/Tab-Titel | ELB | LUT |
| Titel in der Auswahl | Elberfelder 1932 | Luther 1912 |
| Auswahl-Untertitel | mit Strongs (Akribos 1.4) | mit Strongs (Akribos 1.4) |

Die Versionsnummer stammt aus `--version` beziehungsweise `VERSION` in
`akribos/project.py`; sie steht auch in `revision` und im Rechtehinweis.
`INFORMATION` enthält `title`, `description`, `rights`, `short_title`,
`cover_title`, `tab_title`, `selection_title` und `selection_subtitle`.
Die ursprüngliche Angabe in `source` bleibt erhalten. Der Rechtehinweis
benennt Originalausgabe und Akribos-Bearbeitung. Die zusätzlichen Anzeigefelder
werden vom aktuellen App-Importer noch nicht automatisch übernommen; dieses
Repository enthält ausschließlich die Exportskripte.

## Wiederholen und überprüfen

Ein unveränderter Build prüft und verwendet seinen archivierten Lauf erneut.
Ein echter Neuaufbau prüft zusätzlich die Bytegleichheit mit diesem Lauf:

```bash
python bible.py build --edition all --version 1.4 --rebuild \
  --elb-bk .local/references/elb-bk.xml \
  --elb-csv .local/references/elb-csv.xml
python scripts/verify_repository.py --version 1.4
```

Geänderte Quellen, Referenzhashes, Regeln oder Optionen erzeugen einen neuen
Laufordner. `releases/` behält feste Dateinamen; `.build.json` verknüpft jede
Ausgabe mit ihrer Prüfsumme und dem vollständigen Lauf. Version 1.4
veröffentlicht `06-linguistic.xml`. Git-Commits und Tags bewahren die früheren
Ausgaben. **`--version` lädt keinen historischen Code:** Für Version 1.3,
1.2 oder 1.1 den passenden Tag verwenden, siehe
[Versionshistorie](docs/HISTORY.md) und [Änderungsprotokoll](CHANGELOG.md).

| Verzeichnis / Datei | Inhalt |
|---|---|
| `sources/originals/`, `config/sources.lock.json` | Quell-Snapshots, Herkunft, Rechte und Prüfsummen |
| `history/edit/` | Sprachfassung und positionsgenaue Änderungsprotokolle |
| `history/build/` | Stufen 02–06, Reports und gzip-komprimierte JSONL-Audits |
| `history/implementations/` | Für jeden Lauf archivierter Code und Regelstand |
| `alignment.jsonl.gz`, `source-occurrences.jsonl.gz` | Eigene Wortzuordnungen und STEP-Wortvorkommen |
| `05-reference-confirmed.audit.jsonl.gz` | Eine Entscheidung pro eingehendem Unsicherheitshinweis |
| `06-linguistic.audit.jsonl.gz` | Verbleibende Hinweise, Artikelkandidaten und feste Korrekturregeln |
| `.local/` | Private Referenzen, Detailvergleiche und Laufzeitdateien |

Der Verifier rekonstruiert die protokollierten XML-Änderungen von 04 → 05 → 06
und prüft die öffentlichen Quellbelege. Neu erzeugte Verlinkungen dienen bei
einer Wiederholung nicht als neue Beweisanker. Öffentliche Audits enthalten
eigene Positionen, Codes, festgelegte Gründe und STEP-Belege; private
Referenztexte und deren Wortpositionen werden nicht kopiert. Die unveränderten
privaten Snapshots werden benötigt, um den Referenzvergleich selbst erneut
auszuführen. Technische Reproduzierbarkeit beweist keine allgemeine
Fehlerfreiheit aller Strong-Zuordnungen.

## Weitere Befehle

Ein rein lesender Vergleich verändert keine Bibel:

```bash
python bible.py compare \
  --input releases/akribos.elb.xml \
  --reference .local/references/meine-referenz.xml \
  --label meine-referenz --public-index
```

Mit `--public-index` werden nur Versstellen und Abweichungsarten öffentlich
protokolliert. Vollständige Wortvergleiche bleiben unter `.local/comparisons/`.
Details: [Referenzvergleich](docs/REFERENCE-COMPARISON.md).

Die KJV-Syntaxreparatur lässt sich unabhängig und ohne Vergleichsreferenzen
wiederholen:

```bash
python bible.py repair-kjv --rebuild
```

Sie erhält Wortlaut, Strong-Zuordnungen, Originalnotizen und Quellmetadaten;
Protokoll und Prüfsummen stehen im zugehörigen Lauf.
Details: [KJV-Importdatei](docs/KJV-IMPORT.md).

### Eigene Texte ohne Referenzbestätigungsstufe

Ein eigener Text kann mit einer eigenen Ausgabenummer, hier **0.1**, bis
Stufe 04 angereichert werden:

```bash
python bible.py build --edition custom \
  --input .local/inputs/meine-bibel.osis.xml \
  --id akribos.meinetext --profile generic --nt-edition TR --version 0.1
```

Die explizite eigene Versionsnummer fordert keine 1.3-/1.4-Prüfstufe an;
sie bezeichnet auch keinen historischen Akribos-Code. Ein eigener Build mit
`--version 1.3` oder `--version 1.4` benötigt dagegen ebenfalls beide
Referenzen. Eigene Texte und Ergebnisse bleiben unter `.local/` und werden
nicht automatisch als gemeinfrei deklariert oder veröffentlicht. Importprofile
und Erweiterungen: [Weitere Bibeln](docs/ADDING-BIBLES.md).

## Tests und Veröffentlichung

```bash
python -m unittest discover -s tests -v
python scripts/verify_repository.py --version 1.4
python scripts/package.py --output ../akribos-bibles-public.zip
```

Das Paket enthält die öffentlichen Quellen, Archive und Ergebnisse.
`.local/`, private Referenzen, Caches und Git-Zugangsdaten sind ausgeschlossen.
Für die Versionshistorie das Git-Repository klonen. Builds erzeugen keine
Commits oder Tags automatisch. Die Schritte zur gemeinsamen Versionierung
von Skripten und Ergebnissen stehen in [docs/HISTORY.md](docs/HISTORY.md).

## Rechte

**Code: MIT. Gemeinfreie Bibeltexte bleiben gemeinfrei. Neue schutzfähige Akribos-Redaktion und Strong-Aufbereitung: Copyright © 2026 Akribos, CC BY 4.0.** Diese Erklärung beansprucht keine exklusiven Rechte an Strong-Nummern und ändert keine Quelllizenzen.

Das Kautz-Lexikon wird mit Genehmigung veröffentlicht; Copyright Gerhard Kautz. STEP ist CC BY 4.0. Die hebräisch-deutschen Ergänzungen stehen unter AGPLv3. Quellen, Zuschreibungen und Lizenztexte: [LICENSE-DATA.md](LICENSE-DATA.md), [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md), `licenses/` und `sources/evidence/`.
