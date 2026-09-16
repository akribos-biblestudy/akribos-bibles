# Versionshistorie

| Git-Tag | Bibelstand |
|---|---|
| `v1.4` | Aktuell: sprachliche Strong-Prüfung, belegte Artikelergänzungen, feste Einzelkorrekturen und weitere HERR-Sprachregeln |
| `v1.3` | Historisch: vorhandene Unsicherheitshinweise gegen ELB BK und Edition CSV prüfen; konservative Sicherheitsvetos |
| `v1.2` | Historisch: Artikel-/Kasuskorrektur, unter anderem 1. Samuel 17,37 und Kapitel 20 |
| `v1.1` | Historisch: ursprüngliche Sprach-/Strong-Fassung, noch mit fehlenden HERR-Artikeln |

Die Titel nennen die Originalausgaben **Elberfelder 1932** und **Luther 1912**.
Akribos-Version, Kurztitel und Rechtehinweis werden aus dem jeweiligen
Bearbeitungsstand gesetzt. Es handelt sich nicht um eigene Übersetzungen.
Historische Originalnotizen bleiben erhalten. Die englische KJV wird separat
syntaxrepariert exportiert.

## Feste Ergebnisdateien, unveränderliche Läufe

- `releases/akribos.elb.xml`
- `releases/akribos.lut.xml`
- `releases/kjv1611.xml`

Die `.build.json` nennen Version beziehungsweise Quellstand, SHA-256 und
Verarbeitungslauf. Neue Builds überschreiben diese festen Ergebnisdateien;
Git bewahrt die früheren Inhalte. Bestehende Versions-Tags werden nicht
verschoben. Das [Änderungsprotokoll](../CHANGELOG.md) beschreibt die Änderungen.

Ein Lauf unter `history/` bindet Quellen, Referenzhashes, Code, Regeln und
Optionen. Seine `manifest.json` enthält sämtliche Ergebnisprüfsummen. Der
verwendete Implementierungsstand liegt unter `history/implementations/`.
Version 1.3 veröffentlicht `05-reference-confirmed.xml`; Version 1.4
veröffentlicht `06-linguistic.xml`. Die jeweiligen Eingangsphasen bleiben
zum Vergleich und zur Wiederholung erhalten.

## Version 1.4 vollständig nachbauen

Die [Referenzanleitung](REFERENCE-CONFIRMATION.md) beschreibt die private
BK-Datei und den vollständigen [CSV-Abruf](CSV-REFERENCE.md). Für CSV muss die
Konvertierung mit `--require-complete` erfolgreich sein. Danach dieselben
privaten XML-Snapshots für alle Wiederholungen aufbewahren.

Für den exakten veröffentlichten Stand kann ein eigener Checkout dienen:

```bash
git worktree add --detach .local/worktrees/v1.4 v1.4
cd .local/worktrees/v1.4
python scripts/setup.py
mkdir -p .local/references
```

In diesem Checkout die beiden archivierten Referenz-XMLs unter
`.local/references/elb-bk.xml` und `.local/references/elb-csv.xml` ablegen.
Ihre Hashes müssen den Eingaben des gewünschten Laufmanifests entsprechen.
Dann vollständig neu berechnen und prüfen:

```bash
python bible.py build --edition all --version 1.4 --rebuild \
  --elb-bk .local/references/elb-bk.xml \
  --elb-csv .local/references/elb-csv.xml
python scripts/verify_repository.py --version 1.4
```

Ein vorheriger 1.3-Build ist nicht erforderlich. Der 1.4-Aufbau berechnet die
Sprachbearbeitung und alle Strong-Stufen aus den Originalen neu. Die
HERR-Sprachregeln ändern dabei gegenüber dem 1.3-Stand 213 ELB-Ersetzungen in
190 Versen; Luthers Wortlaut bleibt gleich. Deshalb ist Stufe 05 eines
1.4-Laufs kein Archivexemplar des früheren 1.3-Releases. Seine Hinweissummen
werden aus dem tatsächlichen neuen Eingang berechnet.

`--rebuild` prüft bei identischer Laufidentität die Bytegleichheit mit den
archivierten Ergebnissen. Andere Referenzinhalte ergeben einen neuen Lauf.
Private Referenzen sind weder im Git-Repository noch im öffentlichen ZIP
enthalten. Der öffentliche Verifier rekonstruiert 04 → 05 → 06 und prüft die
protokollierten Änderungen und STEP-Belege. Der erneute private Wortvergleich
benötigt die beiden Referenzsnapshots.

## Historische Version 1.3

`--version` setzt die Ausgabenummer und wählt die dafür vorgesehene Prüfstufe;
es lädt keinen früheren Code. Für die ursprünglichen Regeln wird deshalb der
passende Tag ausgecheckt:

```bash
git worktree add --detach .local/worktrees/v1.3 v1.3
cd .local/worktrees/v1.3
python scripts/setup.py
mkdir -p .local/references
```

Hier die zu diesem historischen Lauf gehörenden Referenzsnapshots ablegen.
Dann gelten im **Tag `v1.3`** folgende Befehle:

```bash
python bible.py build --edition all --version 1.3 --rebuild \
  --elb-bk .local/references/elb-bk.xml \
  --elb-csv .local/references/elb-csv.xml
python scripts/verify_repository.py --version 1.3
```

## Historische Versionen 1.1 und 1.2

**Nur für den historischen Tag `v1.2`** gilt dieser Aufbau ohne die erst mit
Version 1.3 eingeführten Vergleichsreferenzen:

```bash
git worktree add --detach .local/worktrees/v1.2 v1.2
cd .local/worktrees/v1.2
python scripts/setup.py
python bible.py build --edition all --version 1.2 --rebuild
python scripts/verify_repository.py --version 1.2
```

Für Version 1.1 entsprechend den Tag `v1.1` und dessen dokumentierte Befehle
verwenden. Frühere Ergebnisdateien und Implementierungssnapshots bleiben
unverändert. Stände lassen sich direkt in Git vergleichen:

```bash
git log --oneline --decorate
git diff v1.1 v1.2 -- akribos/modernize.py releases/akribos.elb.xml
git diff v1.2 v1.3 -- releases/akribos.elb.xml releases/akribos.lut.xml
git diff v1.3 v1.4 -- releases/akribos.elb.xml releases/akribos.lut.xml
```

## Einen neuen Stand veröffentlichen

1. Skripte und Regeln ändern; die Versionsnummer und das zugehörige
   Verarbeitungsprofil gemeinsam pflegen. Nur eine andere Nummer im Export
   ersetzt keine fachliche Änderung.
2. Den vollständigen Aufbau nach der Anleitung dieser Version ausführen,
   anschließend echten `--rebuild`, Repository-Prüfung und Tests durchführen.
3. Ergebniszahlen aus den endgültigen Reports in `CHANGELOG.md` und die
   Ergebnisdokumentation übernehmen; verwendete private Referenzsnapshots
   unverändert aufbewahren. Kataloggrößen, angewandte Regeln, Hinweise und
   hinzugefügte Artikel als unterschiedliche Größen ausweisen.
4. Skripte, Regeln, öffentliche Laufarchive und Ergebnisdateien gemeinsam
   committen und den neuen Versions-Tag auf diesen Commit setzen. Private
   Referenzen und vollständige externe Wortvergleiche bleiben unter `.local/`.

Builds erzeugen keine Commits oder Tags automatisch. Technische
Reproduzierbarkeit belegt keine allgemeine Fehlerfreiheit der Wortzuordnungen.
