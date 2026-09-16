# KJV als importierbare XML-Datei

Datei: **[`releases/kjv1611.xml`](../releases/kjv1611.xml)**.

Originalausgabe: **King James Version 1611/1769 mit Strongs**, digitale Ausgabe bibelkommentare.de, Revision `201909`. Original-ID: `bk_bible.kjv1611`; Sprache: Englisch. Quellmetadaten und Rechtehinweis bleiben erhalten.

## Erzeugen

```bash
python bible.py repair-kjv --rebuild
```

Ein normaler `python bible.py build --edition all` exportiert dieselbe KJV-Datei ebenfalls.

## Reparatur

Die Originaldatei enthält überkreuzte `STYLE`-/`gr`-Elemente und ist deshalb nicht durchgehend wohlgeformtes XML. Die Reparatur entfernt dekorative `STYLE`-Tags und maskiert ungeschützte `&` als `&amp;`. Sie verändert weder englischen Wortlaut noch Strong-Attribute oder Originalmetadaten. Erhalten bleiben alle **31.102 Verse** und **7.716 Originalnotizen**. Farben und kleinere Schrift innerhalb der entfernten Formatierungselemente entfallen.

Der Algorithmus ist auf den per SHA-256 festgelegten KJV-Quellstand abgestimmt. `sources/originals/kjv1611.xml` bleibt unverändert. Die fertige Datei kann als Zefania-XML importiert werden.

## Nachvollziehbarkeit

`releases/kjv1611.build.json` enthält Quell- und Ausgabeprüfsumme sowie den Pfad unter `history/prepared/kjv1611/`. Jeder Reparaturlauf enthält:

- `bible.xml`: identische Importdatei;
- `repairs.jsonl.gz`: jede entfernte bzw. ersetzte Zeichenfolge mit Originalposition;
- `report.json`: Reparaturanzahl, Notizen und Strong-/Versstatistik;
- `manifest.json`: Eingaben, Code-Prüfsummen und Ausgabedateien.

`python scripts/verify_repository.py` prüft die exportierte KJV zusammen mit ELB und Luther. `--rebuild` führt die Reparatur erneut aus und vergleicht sämtliche Laufdateien bytegenau.
