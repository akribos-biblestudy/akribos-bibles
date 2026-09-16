# Akribos Bibeln – reproduzierbare Version 1.3

Akribos bearbeitet die **Elberfelder 1932** und **Luther 1912** sprachlich und
ergänzt Strong-Zuordnungen. Es handelt sich nicht um eigene Übersetzungen.
Dieses Repository enthält die Originaldaten, Skripte, öffentlichen
Zwischenstände und fertigen Ausgaben.

Version 1.3 prüft die vorhandenen eigenen Unsicherheitshinweise gegen **ELB BK**
und die **Elberfelder Ausgabe des CSV-Verlags**. Stimmen beide Referenzen am
eindeutig zugeordneten Wortbereich vollständig überein und greift kein
Sicherheitsveto, entfällt der Hinweis. Diese Prüfstufe verändert weder
Bibeltext noch Strong-Nummern oder historische Notizen. Beide Referenzen
werden privat bereitgestellt und nicht mitveröffentlicht.

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
python bible.py build --edition all --version 1.3 \
  --elb-bk .local/references/elb-bk.xml \
  --elb-csv .local/references/elb-csv.xml
python scripts/verify_repository.py --version 1.3
```

`--edition elb` und `--edition lut` wählen eine Ausgabe einzeln aus. Ein
vorheriger `edit`-Aufruf ist nicht erforderlich. Standardversion ist **1.3**;
auch ohne `--version` benötigt ein regulärer Build beide Referenzoptionen.
Für einen späteren identischen Aufbau die privaten XML-Snapshots unverändert
aufbewahren. Ein neuer Onlineabruf kann andere Dateihashes ergeben.

## Was die Skripte prüfen

Der Aufbau verläuft in fünf Stufen: **Sprachbearbeitung → vorhandene
Strong-Zuordnungen → Lexika → weitere Übersetzungen → Referenzbestätigung**.

- Die Sprachregeln berücksichtigen Artikel und Kasus bei Jehova → HERR,
  einschließlich 1. Samuel 17,37 und Kapitel 20. Anreden werden getrennt
  behandelt. Weitere explizite Regeln modernisieren Schreibungen und
  Weib/Frau-Formen. Originalnotizen bleiben sprachlich unverändert.
- Die Anreicherung verwendet die eingecheckten deutschen Quellen, Lexika und
  STEP-Versinventare. KJV bestätigt Nummern im Vers, keine direkte
  englisch-deutsche Wortzuordnung. Das NT-Prüfprofil ist WH für ELB und TR für
  Luther; `--nt-edition` wählt es ausdrücklich.
- Stufe 05 vergleicht jede vorhandene Unsicherheitsmarkierung mit beiden
  privaten Referenzen. Vollständige Nummernmengen und eindeutige Wortbereiche
  sind erforderlich. Kontext- und Belegzahlprüfungen halten bekannte gemeinsame
  Referenzfehler konservativ offen. Eine Häufigkeitsabweichung benennt keine
  einzelne Nummer als falsch.

Die genauen Bedingungen und Grenzen stehen unter
[Referenzbestätigung](docs/REFERENCE-CONFIRMATION.md), die Sprachkorrekturen
unter [Artikelkorrektur](docs/DIVINE-NAME-CORRECTION.md). Wortabdeckung misst
vorhandene Markierungen, keine Zuordnungsgenauigkeit.

### Ergebnis der vollständigen 1.3-Prüfung

Stand: **2026-09-16**. Die Zahlen stammen aus den jeweiligen
`05-reference-confirmed.report.json` des endgültigen Builds.

| Ausgabe | Hinweise vor Stufe 05 | Entfernt | Verbleibend |
|---|---:|---:|---:|
| Elberfelder 1932 | 51.998 | 20.831 | 31.167 |
| Luther 1912 | 41.134 | 3.095 | 38.039 |

Jede Entscheidung ist im zugehörigen Audit nachvollziehbar. Der technische
Prüfer rekonstruiert die erlaubten XML-Änderungen; er beweist keine allgemeine
Fehlerfreiheit aller Strong-Zuordnungen. Frühere Messungen sind in
[docs/RESULTS.md](docs/RESULTS.md) mit ihrem jeweiligen Bearbeitungsstand dokumentiert.

## Titel und Exportmetadaten

Die Skripte setzen die Angaben bei jedem `edit`- und `build`-Aufruf:

| Angabe | ELB | Luther |
|---|---|---|
| Cover-/Tab-Titel | ELB | LUT |
| Titel in der Auswahl | Elberfelder 1932 | Luther 1912 |
| Auswahl-Untertitel | mit Strongs (Akribos 1.3) | mit Strongs (Akribos 1.3) |

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
python bible.py build --edition all --version 1.3 --rebuild \
  --elb-bk .local/references/elb-bk.xml \
  --elb-csv .local/references/elb-csv.xml
python scripts/verify_repository.py --version 1.3
```

Geänderte Quellen, Referenzhashes, Regeln oder Optionen erzeugen einen neuen
Laufordner. `releases/` behält feste Dateinamen; `.build.json` verknüpft jede
Ausgabe mit ihrer Prüfsumme und dem vollständigen Lauf. Version 1.3
veröffentlicht `05-reference-confirmed.xml`. Git-Commits und Tags bewahren
die früheren Ausgaben. **`--version` lädt keinen historischen Code:** Für
Version 1.1 oder 1.2 den passenden Tag verwenden, siehe
[Versionshistorie](docs/HISTORY.md) und [Änderungsprotokoll](CHANGELOG.md).

| Verzeichnis / Datei | Inhalt |
|---|---|
| `sources/originals/`, `config/sources.lock.json` | Quell-Snapshots, Herkunft, Rechte und Prüfsummen |
| `history/edit/` | Sprachfassung und positionsgenaue Änderungsprotokolle |
| `history/build/` | Stufen 02–05, Reports und gzip-komprimierte JSONL-Audits |
| `history/implementations/` | Für jeden Lauf archivierter Code und Regelstand |
| `alignment.jsonl.gz`, `source-occurrences.jsonl.gz` | Eigene Wortzuordnungen und STEP-Wortvorkommen |
| `05-reference-confirmed.audit.jsonl.gz` | Eine Entscheidung pro ursprünglichem Unsicherheitshinweis |
| `.local/` | Private Referenzen, Detailvergleiche und Laufzeitdateien |

Öffentliche Bestätigungsprotokolle enthalten eigene Positionen, Codes und
Ergebnisgründe. Private Referenztexte und Referenzpositionen werden nicht
kopiert. Die unveränderten Snapshots werden benötigt, um den privaten
Referenzvergleich selbst erneut auszuführen.

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

Die explizite eigene Versionsnummer fordert keine 1.3-Referenzbestätigung an;
sie bezeichnet auch keinen historischen Akribos-Code. Ein eigener Build mit
`--version 1.3` würde dagegen ebenfalls beide Referenzen benötigen. Eigene
Texte und Ergebnisse bleiben unter `.local/` und werden nicht automatisch als
gemeinfrei deklariert oder veröffentlicht. Importprofile und Erweiterungen:
[Weitere Bibeln](docs/ADDING-BIBLES.md).

## Tests und Veröffentlichung

```bash
python -m unittest discover -s tests -v
python scripts/verify_repository.py --version 1.3
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
