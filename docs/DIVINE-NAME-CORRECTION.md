# Jehova → HERR: Artikel- und Kasuskorrektur

Regelkorrektur: 15. September 2026; veröffentlicht als **Version 1.2** am 16. September 2026. Die Korrektur liegt in `akribos/modernize.py` und gilt sowohl für die ELB1932-Ausgabe als auch für den ELB1905-Spender. Der normale Aufbau aus den Originalen benötigt keine redaktionelle Override-Datei.

## Ursache und Regeln

Die bisherige Ersetzung setzte bei nicht erkannten Satzkonstruktionen `HERR` und legte einen Prüfhinweis an. Dadurch fehlte unter anderem vor einem eingeschobenen Relativsatz der Artikel. Die Regeln berücksichtigen jetzt zusätzlich:

- Subjekte mit Relativsatz oder Gottesbezeichnung als Einschub;
- Wunschformeln und Subjekte hinter dem Verb, auch mit dazwischenstehendem Pronomen;
- Prädikate wie „dass ich der HERR bin“;
- Dativ- und Akkusativobjekte mit getrennten Verben, Opfergaben und Infinitiven;
- historische Verbformen und pluralische Relativsätze wie „die den HERRN suchen“;
- vorhandene Artikel und Titel sowie Großschreibung nach dem Doppelpunkt.

Echte Anreden bleiben artikellos. Die Regeln unterscheiden beispielsweise „HERR, der du …“ von „Der HERR, der mich …“. Auch die zuvor fälschlich mit Artikel versehenen Anreden „HERR, sei …“ in Psalmen und Jesaja werden korrigiert. Mehrdeutige Konstruktionen bleiben im Prüfprotokoll.

## Beispiele aus den Originalversen

| Stelle | Korrigierte Ausgabe |
|---|---|
| 1. Samuel 17,37 | Und David sprach: **Der HERR, der mich** aus den Klauen des Löwen … |
| 1. Samuel 20,13 | so tue **der HERR** dem Jonathan … |
| 1. Samuel 20,16 | So fordere es **der HERR** von der Hand der Feinde Davids! |
| 1. Samuel 1,28 | So habe auch ich ihn **dem HERRN geliehen** … |
| 1. Samuel 23,4 | Da befragte David wiederum **den HERRN** … |
| 4. Mose 6,25 | **Der HERR lasse** sein Angesicht über dir leuchten … |
| Psalm 105,3 | … das Herz derer, die **den HERRN suchen**! |

In 1. Samuel 20,12 steht weiterhin **„HERR, Gott Israels!“**, weil dies eine Anrufung ist.

## Umfang und Prüfung

Der Gesamtvergleich mit der Sprachfassung von Version 1.1 erfasst **6.871 Vorkommen** von Jehova/Jehovas im Bibeltext einschließlich Überschriften. Originalnotizen werden nicht modernisiert.

- **698 Ersetzungen in 667 Versen** unterscheiden sich vom bisherigen Lauf: 642 betreffen Artikel/Kasus bzw. vorhandene Titel, 56 ausschließlich die Großschreibung des Artikels.
- In **1. Samuel** sind alle **322 Vorkommen** regelbasiert klassifiziert; 53 Ersetzungen in 49 Versen wurden angepasst.
- Die offenen Syntaxprüfungen sinken von **1.289 auf 441**. Dies ist keine Behauptung vollständiger grammatischer Fehlerfreiheit: Die übrigen Fälle enthalten unter anderem Anreden, Ellipsen und mehrdeutige Satzstellungen und werden weiterhin in `01-language.review.csv` ausgegeben.
- Die Regressionstests in `tests/test_divine_name.py` prüfen die gemeldeten Verse, weitere Bücher, Anreden, Objektfälle, Satzgrenzen und den Dateidurchlauf mit verschachteltem XML und unveränderten Notizen/Strong-Attributen.

Die vollständigen Änderungs-, Offset- und Prüfprotokolle liegen im Sprachlauf [`01bd45d3ce55e640`](../history/edit/akribos.elb/1.2/01bd45d3ce55e640/01-language.report.json). Jeder bearbeitete Vers wird aus dem Änderungsprotokoll rekonstruiert. Alte Originale und ausgelieferte Historienläufe bleiben erhalten.

## Selbst vollständig ausführen

```bash
python scripts/setup.py
python -m unittest discover -s tests -v
python bible.py build --edition all --version 1.2 --rebuild
python scripts/verify_repository.py
```

`build` führt die Sprachbearbeitung selbst aus. Bei erneutem Aufruf mit `--rebuild` müssen alle Dateien des jeweiligen Laufordners bytegleich entstehen; die Pipeline bricht andernfalls mit einem Reproduzierbarkeitsfehler ab. Die fertigen Dateien stehen unter `releases/`.

## Ergänzung in Version 1.4

Beim Referenzabgleich fiel eine weitere Verwechslung von Anrede und Beifügung
auf: Die ältere Regel behandelte auch `Jehova, dein Gott` als Anrede. Die
Skripte berücksichtigen jetzt die ausdrücklich bezeichneten Fälle:

- `Jehova, dein Gott` → `der HERR, dein Gott` (Nominativ), etwa 5. Mose 5,12 und 5,15.
- `Jehova, deinen Gott` → `den HERRN, deinen Gott` (Akkusativ), etwa 1. Samuel 12,19.
- `Jehova, deinem Gott` → `dem HERRN, deinem Gott` (Dativ), auch nach `bist du`, etwa 5. Mose 7,6.
- Dasselbe gilt für die ausdrücklich aufgeführten Gottestitel Erlöser, Erbarmer und Herr.
- In `spricht Jehova, du wirst …` ist der HERR der Sprecher; das folgende `du`
  gehört zur Aussage. In `Vergeltet ihr also Jehova` (5. Mose 32,6) ist er der
  Empfänger und steht im Dativ.
- In Psalm 24,8 und 24,10 beantwortet der Name die unmittelbar vorangehende
  Frage nach dem König der Herrlichkeit. Diese Antworten stehen im Nominativ;
  ohne die Frage liefert eine ähnliche Anrede keine Grundlage für diese Regel.

Der vollständige Vergleich der ELB-Originalverse mit dem Skriptstand von 1.3
ergibt **213 geänderte Namensersetzungen in 190 Versen**: 162 nominative,
23 dative und 18 akkusative Titelbeifügungen, sechs Sprecher-Konstruktionen und
den genannten Dativ nach `vergeltet ihr` sowie drei Antworten in Psalm 24.
Die unabhängige Prüfung umfasst alle
geänderten Positionen. Anreden wie `Jehova, dein Name …`, `Lehre mich, Jehova,
deinen Weg` und `Jehova, du bist mein Gott` bleiben artikellos.

Diese Sprachkorrektur erfolgt in Stufe 01 und wird im normalen Änderungs- und
Offsetprotokoll erfasst. Der anschließende Strong-Abgleich in Stufe 05 und die
sprachwissenschaftliche Strong-Prüfung in Stufe 06 verändern den dort bereits
fertigen Wortlaut nicht. Die vollständigen Aufrufe für 1.4 stehen in
[LINGUISTIC-VALIDATION.md](LINGUISTIC-VALIDATION.md).
