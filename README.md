# Akribos Bibeln – reproduzierbare Version 1.2

Dieses Repository enthält **die Originaldaten, den Python-Code, alle erzeugten Zwischenstände und die fertigen Bibeln**. Es erzeugt die IDs **`akribos.elb`** und **`akribos.lut`**. Die Versionsnummer steht in `revision`, im Auswahl-Untertitel und im Rechtehinweis. Der Titel benennt die Originalausgabe: **Elberfelder 1932** bzw. **Luther 1912**.

Die Verarbeitung beginnt bei den unveränderten Originalen: **Sprachbearbeitung → vorhandene Strong-Zuordnungen → Lexika → weitere Übersetzungen**. Der Referenzvergleich ist ein eigener, ausschließlich lesender Schritt. ELB-BK-Dateien sind nicht enthalten und werden vom Aufbau nicht benutzt.

## Sofort verwenden

Die fertigen Zefania-Dateien liegen unter:

- `releases/akribos.elb.xml`
- `releases/akribos.lut.xml`
- `releases/kjv1611.xml` – syntaxreparierte englische King James Version 1611/1769 mit den ursprünglichen Strong-Zuordnungen

Akribos erhält Strong-Markierungen als **`<gr str="3068">HERR</gr>`**. Mehrere Nummern stehen durch Leerzeichen getrennt im Attribut. H/G ergibt sich in diesem Ausgabeprofil aus dem Testament. Alle ursprünglichen Studynotes bleiben erhalten. Automatische unsichere Ergänzungen haben unmittelbar nach dem Wort eine eigene `NOTE`; nicht zugeordnete Urtext-Nummern stehen ausschließlich in Begleitdateien.

**Die Fassung ist ein überprüfbarer automatischer Arbeitsstand.** Wortabdeckung misst vorhandene Markierungen, keine Übersetzungs- oder Zuordnungsgenauigkeit. Messergebnisse stehen in [docs/RESULTS.md](docs/RESULTS.md).

## Titel und Rechtehinweis

Die Skripte setzen die Anzeigeangaben bei jedem `edit`-/`build`-Aufruf automatisch:

| Angabe | ELB | Luther |
|---|---|---|
| Cover-Titel / Tab-Titel | ELB | LUT |
| Titel in der Auswahl | Elberfelder 1932 | Luther 1912 |
| Untertitel in der Auswahl | mit Strongs (Akribos &lt;Version&gt;) | mit Strongs (Akribos &lt;Version&gt;) |

`<Version>` stammt aus `--version`; ohne dieses Argument gilt `VERSION` in `akribos/project.py` (aktuell **1.2**). Die XML-Dateien enthalten `title`, `description` und `rights` sowie die expliziten Akribos-Anzeigefelder `short_title`, `cover_title`, `tab_title`, `selection_title` und `selection_subtitle` unter `INFORMATION`. Die ursprüngliche Quellangabe in `source` bleibt erhalten. Der aktuelle Akribos-App-Importer übernimmt die zusätzlichen Anzeigefelder noch nicht automatisch; hier werden ausschließlich die Exportskripte angepasst.

Der Rechtehinweis benennt die Originalausgabe und kennzeichnet Akribos als sprachliche Bearbeitung mit ergänzten Strong-Zuordnungen; es handelt sich nicht um eine eigene Übersetzung. Beispiel für einen vollständigen Neuaufbau der vorhandenen Version 1.2:

```bash
python bible.py build --edition all --version 1.2 --rebuild
python scripts/verify_repository.py --version 1.2
```

## Einrichtung

Python **3.11 oder neuer** mit `pip`; keine API, kein KI-Abo und kein Internetzugriff während des Aufbaus erforderlich. Das deutsche Lemma-Wörterbuch von Simplemma 2.0.0 liegt als unverändertes Wheel im Repo.

```bash
cd akribos-bible
python scripts/setup.py
```

Das installiert nur die mitgelieferte, per SHA-256 geprüfte Abhängigkeit unter `.local/python`. Wenn auf deinem System Python `python3` heißt, verwende entsprechend `python3`.

## Befehle

### 1. Sprache bearbeiten

```bash
python bible.py edit --edition all --version 1.2
```

`elb` und `lut` sind einzeln auswählbar. ELB: Jehova/Jehovas wird anhand von Kasussignalen angepasst, beispielsweise `zu Jehova` → `zu dem HERRN`. Beide: Weib/Weibe/Weibes/Weiber einschließlich erkannter Artikel und Adjektive wird Frau/Frauen. Luther: genau `HErr`, `HErrn`, `HErrs` wird `HERR`, `HERRN`, `HERRS`; ein gewöhnliches `Herr` bleibt erhalten. Eine explizite Wort- und Phrasenliste modernisiert sichere Schreibungen wie `daß` und `muß`. Kein pauschales ß→ss und kein KI-Aufruf.

Die Jehova-Regeln berücksichtigen auch Relativsätze (`Jehova, der mich …` → `Der HERR, der mich …`), Wunschformeln (`so tue Jehova` → `so tue der HERR`) und getrennte Verb-/Objektstellungen. Anreden wie `Jehova, Gott Israels!` bleiben artikellos: `HERR, Gott Israels!`. Die Korrektur vom 15. September 2026 ist in den Skripten enthalten und wird bei jedem normalen `edit`-/`build`-Aufruf angewendet; ein `--overrides`-Argument ist dafür nicht nötig. Prüfbericht: [docs/DIVINE-NAME-CORRECTION.md](docs/DIVINE-NAME-CORRECTION.md).

Die Originalnotizen einschließlich ihrer historischen Schreibungen werden nicht sprachlich bearbeitet. Die Umstellung ist **keine vollständige Neufassung nach heutiger Grammatik und Zeichensetzung**. Unklare Kasus, lange Pronomenbezüge und kontextabhängige Schreibungen werden in `01-language.review.csv` dokumentiert.

### 2. Strong-Ausgabe erzeugen

```bash
python bible.py build --edition all --version 1.2
```

Dieser Befehl führt die Sprachbearbeitung selbst aus, falls der passende Zwischenstand fehlt. Ein vorheriger `edit`-Aufruf ist nicht nötig. Auch die deutschen Vergleichsübersetzungen werden vor dem Matching nach denselben Regeln bearbeitet.

Der Aufbau verwendet:

1. ELB1905 als primäre Zuordnungsquelle für ELB1932; bei Luther bleiben alle vorhandenen Zuordnungen erhalten.
2. Kautz-Griechisch, das hebräisch-deutsche Lexikon und dokumentierte Akribos-Startregeln; lokale deutsche Lemmatisierung verbessert Flexionsvergleiche.
3. ELB1905, Luther1912 und Schlachter1951 als weitere deutsche Quellen; STEP begrenzt neue Kandidaten auf das jeweilige Versinventar. KJV liefert zusätzliche dokumentierte Bestätigung derselben Strong-Nummern im Vers.

Die KJV bestätigt **Urtext-Nummern im Vers**, keine direkte Zuordnung eines englischen Wortes zu einem deutschen Wort. Arbiträre Prozentgewichte werden nicht als Fehlerwahrscheinlichkeit ausgegeben. Mehrere Übersetzungen können dieselbe ältere Zuordnung übernommen haben und sind deshalb keine sicher unabhängigen Stimmen.

Für ELB ist das NT-Prüfprofil `WH`, für Luther `TR`; abweichende Textgrundlagen und Verszählungen bleiben fachlich zu prüfen. Mit `--nt-edition WH` bzw. `TR` lässt sich das explizit ändern.

### 3. Mit einer beliebigen Referenz vergleichen

Die Referenz kommt in das ignorierte Verzeichnis `.local/references/`:

```bash
python bible.py compare \
  --input releases/akribos.elb.xml \
  --reference .local/references/meine-referenz.xml \
  --label meine-referenz --public-index
```

Für Luther ändere `--input` auf `releases/akribos.lut.xml`. Die Referenz kann Zefania mit `<gr>` oder `<GRAM>` verwenden. Mehrfachnummern wie `1254-853` werden als zwei Nummern interpretiert. Auch unterstützte OSIS-Profile werden importiert.

Ergebnisse:

- `comparisons/<label>/<id>/<lauf>/summary.json`: Gesamtzahlen, Abdeckung und klar benannte Nenner.
- `books.csv`: Messungen pro Buch.
- `verse-differences.csv`: mit `--public-index` eine öffentliche Liste von Versstellen und Abweichungsarten, **ohne fremde Wortlaute, Strong-Werte oder Wortpositionen**.
- `.local/comparisons/<label>/<id>/<lauf>/word-differences.jsonl.gz`: vollständige Wort- und Strong-Abweichungen zur lokalen Prüfung. Diese Datei wird nicht veröffentlicht.

Ohne `--public-index` bleibt auch der Versindex lokal. Ein Vergleich verändert keine Bibel und keine Lexikonregel. Vergleichsberichte werden bei Bedarf mit eigenen Referenzdateien erzeugt. Fremde Referenzdateien bleiben lokal. Siehe [docs/REFERENCE-COMPARISON.md](docs/REFERENCE-COMPARISON.md).

### 4. Reparierte KJV zum Import exportieren

```bash
python bible.py repair-kjv --rebuild
```

Die importierbare Datei liegt unter **`releases/kjv1611.xml`**. Auch ein normaler ELB-/Luther-`build` exportiert sie automatisch. Entfernt werden die fehlerhaft verschachtelten dekorativen `STYLE`-Tags; unmaskierte kaufmännische Und-Zeichen werden XML-konform geschrieben. Wortlaut, Strong-Tags, 7.716 Originalnotizen und Quellmetadaten bleiben erhalten. Die ursprüngliche ID lautet `bk_bible.kjv1611`.

`releases/kjv1611.build.json` verweist auf Quelle, Prüfsummen und Reparaturlauf. Dort liegen `report.json` und das vollständige Änderungsprotokoll `repairs.jsonl.gz`. Die Reparatur wird aus der unveränderten Originaldatei erzeugt und mit `--rebuild` auf Bytegleichheit geprüft. Details: [KJV-Importdatei](docs/KJV-IMPORT.md).

## Zwischenstände und Wiederholbarkeit

```text
sources/originals/                   unveränderte, mitgelieferte Quell-Snapshots
config/sources.lock.json              Download-URLs, SHA-256, Rechte und Zuschreibungen
rules/                               explizite Sprach- und lexikalische Startregeln
history/edit/<id>/<version>/<lauf>/   00-import.xml, 01-language.xml und Änderungsprotokolle
history/prepared/kjv1611/<lauf>/       reparierte Arbeitskopie und vollständiges Reparaturlog
history/build/<id>/<version>/<lauf>/  02-baseline.xml, 03-lexicon.xml, 04-multisource.xml
releases/                            fertige Bibeln plus Verweis auf ihren vollständigen Lauf
comparisons/                         öffentliche Vergleichsberichte
.local/                              private Referenzen, Detailvergleiche, Laufzeitdateien
```

Ein Lauf wird aus Quellen, Regeln, Code, Optionen und Versionsnummer identifiziert. `manifest.json` erfasst die Prüfsummen aller Ergebnisse. Unveränderte Aufrufe prüfen den vorhandenen Lauf und verwenden ihn wieder. Geänderte Regeln oder Quellen erzeugen einen **neuen Laufordner**, ohne alte Zwischenstände zu ersetzen. `releases/` enthält immer die zuletzt gebaute Ausgabe unter denselben Dateinamen. Die zugehörigen `.build.json` verknüpfen jede Datei mit Version, Prüfsumme und vollständigem Lauf. Die redaktionellen Versionen werden durch Git-Commits und Tags festgehalten; siehe [Versionshistorie](docs/HISTORY.md) und [Änderungsprotokoll](CHANGELOG.md).

Zum vollständigen Neuberechnen und Prüfen auf Bytegleichheit:

```bash
python bible.py build --edition all --version 1.2 --rebuild
```

Für den nächsten redaktionellen Stand `VERSION` in `akribos/project.py` erhöhen, vollständig bauen und Skripte, Ergebnisse und `CHANGELOG.md` gemeinsam committen und taggen. Die IDs bleiben `akribos.elb`/`akribos.lut`. **`--version` setzt nur die Ausgabenummer; für frühere Regeln muss der damalige Git-Stand ausgecheckt werden.**

XML wird mit einem Vers pro Zeile gespeichert. Gemischte Inhalte innerhalb eines Verses werden nicht eingerückt. JSONL-Audits sind reproduzierbar gzip-komprimiert, damit einzelne Dateien unter GitHubs Dateigrößenlimit bleiben. Zum Lesen eignet sich Python `gzip.open(..., 'rt', encoding='utf-8')` oder `gzip -dc`.

## Was in den Protokollen steht

- `01-language.changes.csv`: jede Ersetzung mit alter/neuer Zeichenposition, Wortlaut und Regel.
- `01-language.offset-map.jsonl`: Übertragung alter auf neue Zeichenpositionen.
- `verification.json`: jeder bearbeitete Vers wurde unabhängig aus dem Änderungslog rekonstruiert; alle ursprünglichen Notiz-Unterbäume und Strong-Attribute verglichen.
- `alignment.jsonl.gz`: Zielwörter, tatsächlich exportierte Nummern, Verfahren, Quellen, Wörterbuch-Lemmakandidaten, KJV-Bestätigung und Prüfstatus.
- `source-occurrences.jsonl.gz`: STEP-Urtextvorkommen mit Originalreferenz, Lemma, Morphologie, Editions- und Variantenangaben. Die deutschen Wörter sind noch **nicht eindeutig auf einzelne Urtextvorkommen ausgerichtet**; der Versverweis erlaubt die fachliche Prüfung.
- `review.jsonl.gz`: Mehrdeutigkeiten, auffällige Versinventare und Wörter über XML-Grenzen.
- `unassigned-source.jsonl.gz`: Urtext-Strong-Einträge ohne zugeordnetes deutsches Wort. Keine sichtbaren Hinweise am Versende.

## Weitere Bibeln und OSIS

[docs/ADDING-BIBLES.md](docs/ADDING-BIBLES.md) beschreibt Import, Aufbau, Rechte und Verszählung. Beispiel für einen eigenen deutschen Text:

```bash
python bible.py build --edition custom \
  --input .local/inputs/meine-bibel.osis.xml \
  --id akribos.meinetext --profile generic --nt-edition TR --version 1.2
```

Das führt tatsächlich die Anreicherung aus. Solche nicht registrierten Texte und ihre Ergebnisse bleiben unter `.local/`; sie werden **nicht automatisch als Public Domain deklariert oder in das öffentliche Paket aufgenommen**.

## Tests und Veröffentlichung

```bash
python -m unittest discover -s tests -v
python scripts/verify_repository.py
python scripts/package.py --output ../akribos-bible-public.zip
```

Das Paket enthält Originale einschließlich Kautz, alle öffentlichen Zwischenstände und Ergebnisse. Es schließt `.local`, fremde Referenzdateien, Caches und Git-Zugangsdaten aus. Vor einem Git-Push: `git status` prüfen. Für GitHub wird kein API-Token benötigt, um das Repo lokal zu bauen.

Die lokale Git-Historie enthält `v1.1` (Bibelstand vor der Artikelkorrektur, mit einheitlichen Exportmetadaten) und `v1.2` (korrigierte Skripte, neue Metadaten). Die Ergebnisdateien sind direkt vergleichbar:

```bash
git log --oneline --decorate
git diff v1.1 v1.2 -- akribos/modernize.py releases/akribos.elb.xml
git show v1.1:releases/akribos.elb.xml > .local/akribos.elb-1.1.xml
```

Der Ablauf für kommende Versionen steht in [docs/HISTORY.md](docs/HISTORY.md). Builds erstellen keine Commits oder Tags automatisch. Das ZIP-Paket enthält die geprüften Daten und Quell-Snapshots, jedoch nicht das Git-Verzeichnis; für die Git-Historie das Repository klonen. Ein entferntes Repository kann separat verbunden werden. Das Prüfergebnis belegt technische Integrität und Reproduzierbarkeit, nicht die fachliche Richtigkeit jeder Zuordnung.

## Rechte

**Code: MIT. Gemeinfreie Bibeltexte bleiben gemeinfrei. Neue schutzfähige Akribos-Redaktion und Strong-Aufbereitung: Copyright © 2026 Akribos, CC BY 4.0.** Diese Erklärung beansprucht keine exklusiven Rechte an Strong-Nummern und ändert keine Quelllizenzen.

Das Kautz-Lexikon wird mit Genehmigung veröffentlicht; Copyright Gerhard Kautz. STEP ist CC BY 4.0. Die hebräisch-deutschen Ergänzungen stehen unter AGPLv3. Quellen, Zuschreibungen und Lizenztexte: [LICENSE-DATA.md](LICENSE-DATA.md), [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md), `licenses/` und `sources/evidence/`.

## Quellcode früherer Läufe

Jeder Aufruf archiviert die für die Berechnung verwendeten Python-Module, Regeln, Quellregister und Abhängigkeitsangaben unter `history/implementations/<hash>/`. Der jeweilige Lauf nennt deren Einzelprüfsummen in `manifest.json`. `scripts/verify_repository.py` prüft, dass zu jedem Lauf der vollständige passende Implementierungsstand vorhanden ist.

Für einen historischen Aufbau diese Dateien in eine **separate Kopie des Repos** zurückkopieren und mit den im Laufmanifest genannten Optionen bauen. Die dort referenzierten Original-Hashes müssen ebenfalls vorhanden sein. Bei künftiger Arbeit zusätzlich jeden Regel-/Code-/Quellenwechsel gemeinsam mit den Ergebnissen committen.
