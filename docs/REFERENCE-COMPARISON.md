# Öffentlicher und lokaler Referenzvergleich

Der Vergleich ist ein Diagnosewerkzeug. Er enthält **keinen Korrektur- oder Trainingspfad zurück in die Strong-Erzeugung**. Eine fehlende Akribos-Zuordnung wird nicht allein deshalb ergänzt, weil sie in ELB BK steht.

## Was öffentlich enthalten ist

- Gesamt- und Buchstatistiken über Wortabdeckung und beobachtete Übereinstimmung.
- Mit `--public-index`: eine Liste eigener Versstellen mit Kategorien wie `different-strong-set`, `only-reference-tagged` und `text-or-tokenization`.
- Hash der geprüften Referenz, damit nachvollziehbar bleibt, auf welchen Snapshot sich die Zahlen beziehen.

Die Liste enthält **keine fremden Wörter, Strong-Werte, Wortpositionen oder maschinenlesbaren Ersatzzuordnungen**. Vollständige Wortdifferenzen einschließlich der fremden Zuordnungen liegen nur in `.local/comparisons/`. Dieses Verzeichnis ist ignoriert und wird vom öffentlichen Packager nicht eingelesen. Auch die Referenz-XML wird nicht mitgeliefert.

## Enthaltene Vergleichsdaten

Die Referenzausgabe „Elberfelder Übersetzung (Version 1.3 von bibelkommentare.de)“ trägt **Copyright 2023 www.bibelkommentare.de**. Im Repository liegen eigene Statistiken und ein Index aus Versstellen und Abweichungskategorien. Referenzdatei, Wortzuordnungen und vollständige Wortdifferenzen werden lokal unter `.local/` abgelegt und vom öffentlichen Paket ausgeschlossen.

Die Vergleichsberichte nennen die Prüfsumme der verwendeten Referenz. Format und Herkunft: [Module für Bibelprogramme](https://www.bibelkommentare.de/downloads/module).

## So sind die Zahlen zu lesen

**Wortabdeckung** = Anzahl der deutschen Worttokens mit mindestens einer gültigen Strong-Nummer / alle Worttokens. Fußnoten und Überschriften werden nicht mitgezählt. Eine Wortgruppe mit einer Nummer kann mehrere markierte deutsche Tokens enthalten. Deshalb bedeutet eine höhere Quote nicht automatisch mehr korrekt erschlossene Urtextwörter.

**Übereinstimmung** = identische Strong-Mengen / beidseitig markierte und im Wortlaut zuordenbare Tokens. Dieser Nenner ist in `summary.json` ausdrücklich benannt. Daneben stehen der Anteil überhaupt wortgleich zuordenbarer Tokens und die Abweichungskategorien. Bei Luther ist wegen des anderen Wortlauts ein Teil der Wörter nicht direkt mit ELB BK vergleichbar; daraus wird keine vermeintliche Fehlerquote errechnet.

**Verszählung**: Ohne Mapping werden dieselben Buch-/Kapitel-/Versnummern verbunden. Abweichende Psalmüberschriften, ausgelassene Verse oder andere Zählweisen müssen geprüft werden. Für eine eindeutige 1:1-Zählverschiebung kann eine JSON-Datei übergeben werden:

```json
{"Ps.3.1": "Ps.3.2"}
```

```bash
python bible.py compare --input releases/akribos.elb.xml \
  --reference .local/references/ref.xml --label ref \
  --verse-map .local/ref-verses.json
```

Alle Zuordnungen müssen insgesamt eindeutig sein. Das Beispiel zeigt nur das Format; für eine echte Verschiebung müssen auch kollidierende Folgeverse explizit zugeordnet werden. Versaufteilungen und Zusammenlegungen benötigen ein eigenes, dokumentiertes Zählprofil und werden nicht stillschweigend geraten.
