# Akribos Bibeln — Version 1.1

Bibeltexte: Elberfelder 1932 und Luther 1912; regelbasierte Sprachbearbeitung und Strong-Aufbereitung. Die historischen Originalnotizen bleiben erhalten.

Dies ist der Bibelstand vor der Artikel-/Kasuskorrektur für Jehova → HERR. Die Exportmetadaten und die Dokumentation verwenden das gemeinsame Format dieses Repositorys. Version 1.2 korrigiert unter anderem 1. Samuel 17,37 und Kapitel 20.

## Dateien

- `releases/akribos.elb.xml`
- `releases/akribos.lut.xml`
- `releases/kjv1611.xml`: syntaxreparierte englische KJV 1611/1769 mit Original-Strongs.

## Vollständig ausführen

```bash
python scripts/setup.py
python -m unittest discover -s tests -v
python bible.py build --edition all --rebuild
python scripts/verify_repository.py
```

Für die KJV allein: `python bible.py repair-kjv --rebuild`. Importdatei und Reparaturprotokoll beschreibt [docs/KJV-IMPORT.md](docs/KJV-IMPORT.md).

Originaldateien: `sources/originals/`; Quellen und SHA-256: `config/sources.lock.json`. Die Manifeste neben den Ergebnisdateien verweisen auf die vollständigen, reproduzierbaren Verarbeitungsläufe unter `history/`. Quell-Snapshots jedes Laufs liegen unter `history/implementations/`.

## Rechte

Code: MIT. Neue schutzfähige Akribos-Beiträge: CC BY 4.0. Originalquellen behalten ihre jeweiligen Rechte. Vollständige Angaben: [LICENSE-DATA.md](LICENSE-DATA.md) und [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
