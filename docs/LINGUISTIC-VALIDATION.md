# Sprachliche Strong-Prüfung – Version 1.4

Der Aufbau für Version 1.4 führt zuerst die [Bestätigung durch beide Referenzen](REFERENCE-CONFIRMATION.md)
aus. Danach prüft eine eigene Stufe jeden verbleibenden Unsicherheitshinweis
an konkreten griechischen oder hebräischen Wortvorkommen. Sie entfernt nur
belegte Hinweise und ergänzt ausgewählte, belegte griechische Artikel.
Bibeltext und historische Originalnotizen bleiben erhalten. Vorhandene
Strong-Nummern ändern sich ausschließlich durch die unten beschriebenen
positionsgesicherten redaktionellen Regeln. Nicht ausreichend belegte Fälle
behalten ihren Hinweis.

Die Standardversion und die veröffentlichten Dateien tragen **1.4**. Die
folgenden Befehle nennen diese Version ausdrücklich; derselbe Aufbau ist
auch ohne `--version` möglich. Frühere Stände werden vom jeweiligen Git-Tag
aufgebaut, siehe [Versionshistorie](HISTORY.md).

## Vollständig aufbauen

```bash
python bible.py build --edition all --version 1.4 \
  --elb-bk .local/references/elb-bk.xml \
  --elb-csv .local/references/elb-csv.xml

python scripts/verify_repository.py --version 1.4
```

Beide privaten Zefania-Referenzen sind Pflicht. Ihre Bereitstellung und das
CSV-Eingabeformat sind in [REFERENCE-CONFIRMATION.md](REFERENCE-CONFIRMATION.md)
und [CSV-REFERENCE.md](CSV-REFERENCE.md) beschrieben. Der Aufbau verarbeitet
zuerst `04-multisource.xml`, dann `05-reference-confirmed.xml` und zuletzt
`06-linguistic.xml`. Nur Stufe 06 wird für Version 1.4 veröffentlicht. Ein
vorheriger 1.3-Build ist nicht erforderlich.

Die eigene Sprachstufe kann für 1.4 zusätzliche Korrekturen der deutschen
HERR-Formen ausführen und protokollieren. Dieser Textunterschied zwischen
Releases wird gesondert geprüft. Die hier beschriebene Strong-Stufe 05 → 06
verändert dagegen weiterhin keinerlei Bibelwortlaut.

Für ELB wird die STEP-Grundtextauswahl `WH`, für Luther `TR` verwendet; mit
`--nt-edition` lässt sie sich ausdrücklich wählen. Ausgewählte Ausgabe,
Quellhashes, Regelcode und beide privaten Referenzhashes gehören zur
Laufidentität. `--rebuild` berechnet denselben Lauf erneut und vergleicht die
erzeugten Bytes mit dem archivierten Ergebnis. Geänderte Eingaben erzeugen
einen neuen Lauf und überschreiben keine alten Laufarchive.

## Wann eine Änderung erlaubt ist

### Griechische Artikel

G3588 bezeichnet den griechischen Artikel mit seinen verschiedenen
Flexionsformen. Ein deutsches `der`, `die` oder `das` kann dagegen auch ein
Pronomen sein oder ohne entsprechenden Artikel im Grundtext stehen.
Deshalb genügt das deutsche Wort allein nicht zur Verlinkung.

Die automatische Regel verlangt alle folgenden Belege:

1. Ein tatsächliches G3588-Vorkommen in der ausgewählten griechischen Ausgabe
   ist durch die STEP-Verknüpfung mit seinem unmittelbar folgenden Nomen
   verbunden. Artikel und Nomen stimmen in griechischem Kasus, Numerus und
   Genus überein.
2. Das deutsche Nomen ist bereits unabhängig, eindeutig und als Einzelwort
   mit derselben Nummer verknüpft. Sein deutscher Genus-/Numerusbefund steht
   in einer ausdrücklichen kleinen Formenliste. Griechisches Genus wird
   nicht als deutsches Genus behandelt: beispielsweise ist `das Wort` im
   Griechischen maskulin.
3. Ein bereits bestätigtes Wort unmittelbar links steht auch im Grundtext
   unmittelbar links vor dem Artikel. Alternativ beginnt der Vers in beiden
   Sprachen mit Artikel und Nomen. Wiederholte Nummern, breite Wortspannen,
   Satzzeichengrenzen und pronominale Anker verhindern die automatische
   Zuordnung.
4. Eigennamen sowie Quellen mit Wortverschiebungen oder abweichender
   Versifikation sind ausgeschlossen. Eine deutsche Präposition als linker
   Anker benötigt eine tatsächliche griechische Präposition; historisches
   `nach dem Gott …` in Römer 12,3 wird dadurch nicht als Artikelphrase gelesen.
5. Mindestens eine der beiden privaten Vergleichsausgaben bestätigt genau
   dieses deutsche Artikelwort eindeutig mit ausschließlich G3588. Ein
   irgendwo im Vers vorhandener Artikel oder eine breiter markierte Phrase
   bestätigt es nicht. Unsichere Referenzmarkierungen bestätigen nichts.

Die zusätzlichen deutschen Formen und ihre überprüfbaren Lexikonbelege sind
in [LINGUISTIC-NOUNS.md](LINGUISTIC-NOUNS.md) aufgeführt. Formen wie *Engel* und
*Tage* benötigen trotz gleicher Schreibung weiterhin den passenden Numerus.

Bei bereits markiertem G3588 entfällt nur der Hinweis. Bei einem bisher
unmarkierten, vollständig belegten Artikel entsteht ein neues
`<gr str="3588">…</gr>`-Element. Der veröffentlichte Aufbau und die
Befehlszeilenwerkzeuge bieten keinen Schalter zum Abschalten des zweiten
Artikelbelegs.

### Weitere griechische und hebräische Zuordnungen

Die Regeln prüfen ausgewählte Konjunktionen, Negationen, hebräische Partikeln
und eine kleine hebräische Nomenliste. Das konkrete deutsche Wort muss zum
Quelllexem und dessen Wortart passen. Zwei bereits unabhängig bestätigte
Nachbarwörter müssen dasselbe einzelne Quellvorkommen einschließen.

Mehrwortspannen, mehrere Strong-Nummern am Wort, zusammengesetzte hebräische
Formen, H900x-Präfixkennungen, wiederholte Lexeme, Varianten und fehlende
Belege bleiben zur Prüfung stehen. Auch bekannte Versinventarprobleme aus
dem vorherigen Alignment sperren automatische Änderungen. Kein Hinweis
entfällt allein, weil seine Nummer im Versinventar vorkommt.

Jeder Hinweis erhält eine Entscheidung: `accepted` entfernt den bewiesenen
Hinweis, `review` erhält ihn wegen fehlender Beweise. Fehlt eine Nummer sowohl
in den Haupt- als auch den Alternativangaben der gewählten Quelle, lautet der
Prüfgrund `code-absent-in-selected-source`. Das beweist keinen lexikalischen
Fehler: Verschiedene Quellen können ein Lemma und seine Flexionsformen mit
unterschiedlichen Nummern kennzeichnen. Beispielsweise führt STEP in
Matthäus 22,44 das Lemma ἐγώ, die Form `μου` unter G3165 und zusätzlich G3450
als Alternativnummer. Ein hypothetischer G1473-Lemmaeintrag bleibt deshalb
zur Prüfung erhalten. Daraus entstehen weder Aliasnormalisierungen noch
Freigaben oder Ersatznummern. Die vorhandenen Regeln erzeugen kein `reject`;
ein tatsächlicher Widerspruch benötigt einen gesonderten positiven Beleg.

### Bestehende Eigennamen

Ein [ausdrücklicher Namenskatalog](LINGUISTIC-NAMES.md) erlaubt zusätzlich die
Bestätigung einzelner bereits unsicher markierter Namen. Dazu müssen deutsche
Namensform, vorhandener Code, tatsächliches einmaliges STEP-Namensvorkommen,
Eigenname-Morphologie und belegtes Lemma beziehungsweise hebräische
Konsonantenschreibung übereinstimmen. Name und Code müssen im ganzen deutschen
Vers jeweils eindeutig sein; auch unmarkierte Namenswiederholungen und Codes
in größeren Spannen zählen mit.

Mindestens eine genaue BK-/CSV-Wortbestätigung bleibt zwingend. Die Regel
entfernt ausschließlich den vorhandenen Hinweis, ergänzt keine Namensnummern
und ersetzt keine Namen. Alle bisherigen Vers-, Varianten-, Inventar- und
Provenienzprüfungen gelten weiter. Katalog, Quellenbelege und Prüfcode werden
gehasht; der öffentliche Replay prüft den tatsächlichen STEP-/Katalogbeleg erneut.

### Fest geprüfte redaktionelle Korrekturen

[EDITORIAL-STRONG-CORRECTIONS.md](EDITORIAL-STRONG-CORRECTIONS.md) dokumentiert
43 einzeln geprüfte Regeln. Sie entfernen konkret falsch verteilte Nummern
oder ersetzen sie durch den belegten Artikelcode. Eine Mischspanne verliert
nur ihren falschen Zusatzcode. Auch geerbte Zuordnungen ohne eigenen
Unsicherheitshinweis sind ausdrücklich und getrennt erfasst.

Die Regeln gelten ausschließlich für eine festgelegte Bibelausgabe,
WH-/TR-Auswahl, unveränderten ganzen Verstext, genaue Wortposition, den
ursprünglichen XML-Bereich und dieselben tatsächlichen STEP-Wortvorkommen. Sechs hebräische Fälle binden
ausdrücklich die benötigte TAHOT-Datei und ihre L/Q-Vorkommen.
Die 41 im älteren Bestand geprüften Regeln und zwei erst beim vollständigen
1.4-Neuaufbau entstandene falsche Codesätze werden getrennt gezählt.
Fehlt eine Bedingung, bleibt die Stelle unverändert (`not-applicable`). Das
ist keine allgemeine Löschregel und keine Aliasnormalisierung. Die Pflicht
für einen unabhängigen Zweitbeleg bei automatischen Artikelergänzungen
bleibt bestehen; redaktionelle Korrekturen haben einen eigenen Audittyp.

### Artikelverlinkungen der vorgelagerten Sprachkorrektur

Der vollständige Vergleich der Strong-Stufen vor der Referenzprüfung weist
372 zusätzliche H3068-Verlinkungen an deutschen Artikeln aus: 196 in ELB
und 176 in Luther. Jede wurde bis zum selben ursprünglichen einzelnen
`Jehova/H3068`-Abschnitt des Spendertexts zurückverfolgt. Sie verteilen dessen
Zuordnung auf die deutsche Mehrwortwiedergabe mit `HERR`; die Zahl der
hebräischen Wortvorkommen bleibt gleich. Diese Verlinkungen bleiben erhalten
und werden getrennt von den neuen G3588-Artikelbelegen der Stufe 06 gezählt.

## Protokolle und Erhaltung

Im unveränderlichen Laufarchiv entstehen zusätzlich:

| Datei | Inhalt |
|---|---|
| `06-linguistic.xml` | Finale Bibel einschließlich Versionsmetadaten |
| `06-linguistic.audit.jsonl.gz` | Jede eingehende Markierung, jeder belegte Artikelkandidat und jede registrierte redaktionelle Regel mit Entscheidung und Begründung |
| `06-linguistic.report.json` | Zähler, Erhaltungsprüfungen, Regel- und Quellidentität |
| `06-linguistic.manifest.json` | Hashes der Eingabe, Quellen, Regeln, Referenzen, Alignment und aller Ausgaben |

Öffentliche Protokolle enthalten eigene Wortbereiche und die benannten
STEP-Wortbelege. Private Referenztexte, ihre Wortpositionen und lokale
Dateipfade werden nicht übernommen; für diese Quellen werden Hashes und
Prüfergebnisse gespeichert. Ein zurückgestellter Artikelkandidat unterscheidet
die vorgeschlagene Nummer ausdrücklich vom unveränderten Ergebnis.
Das öffentliche Audit erlaubt nur festgelegte Felder und Statuscodes.
Zusatzfelder und freie Referenzmeldungen werden abgelehnt. Auch zurückgestellte
Wortbereiche müssen exakt zum eigenen Eingabetext passen; ihre gespeicherten
Artikelbelege werden erneut gegen STEP geprüft.

Alle Entscheidungen verwenden denselben unveränderten Eingabestand. In
Stufe 05 bestätigte Zuordnungen können als Anker dienen. Neu in Stufe 06
bestätigte oder ergänzte Spannen erhalten das eigene Attribut
`data-akribos-linguistic="1.4.0"`. Solche Spannen dienen auch bei einem
erneuten Lauf nicht als neue Beweisanker. Dadurch können wiederholte Läufe
keine Kette sich selbst bestätigender Zuordnungen erzeugen. Redaktionell
ersetzte Spannen tragen zusätzlich `data-akribos-editorial` mit ihrer Regel-ID.
Verse mit registrierten redaktionellen Korrekturen bleiben dauerhaft für
automatische Beweise gesperrt: Auch eine entfernte falsche Doppelzuordnung
kann deshalb in einem Folgelauf keinen neuen Beweis freischalten.

Der Dateidurchlauf vergleicht sämtliche Vers-/Überschriftentexte,
Originalnotizen und bisherigen Strong-Elemente vor und nach der Bearbeitung.
Der Repository-Prüfer prüft zusätzlich alle Hashes und rekonstruiert die
protokollierten XML-Änderungen aus Stufe 05 gegen die wirklichen STEP-Belege.
Er erlaubt nur protokollierte Hinweisentfernungen, eigene Provenienz,
G3588-Ergänzungen, die exakt katalogisierten redaktionellen Strong-Deltas
und die vorgesehenen Ausgabemetadaten. Der private
Referenzvergleich lässt sich mit denselben privaten Snapshots wiederholen;
deren Inhalt wird nicht im öffentlichen Repository abgelegt.

## Einzelne Phase verwenden

Für einen vorhandenen bestätigten Zwischenstand gibt es einen eigenen Helfer:

```bash
python scripts/validate_linguistic.py pfad/05-reference-confirmed.xml \
  --output pfad/06-linguistic.xml --nt-edition WH \
  --elb-bk .local/references/elb-bk.xml \
  --elb-csv .local/references/elb-csv.xml \
  --alignment pfad/alignment.jsonl.gz
```

Dieser Helfer führt nur die einzelne Prüfung aus und veröffentlicht keine
Release-Dateien. Für lokale Teilprüfungen genügt ihm eine Artikelreferenz.
Ein Release wird immer mit `bible.py build --version 1.4` und beiden Quellen
erstellt. Eingaben und verwendete Quellen dürfen nicht als Ausgabeziele
überschrieben werden.

Die Python-API bietet `akribos.linguistic.validate_files(...)` für Dateien
sowie `validate_tree(...)` für bereits geladene Bäume. Beide verändern ihre
Eingaben nicht. Beim Baum-API werden bekannte Versprobleme mit `verse_guards`
übergeben. Redaktionelle Korrekturen benötigen außerdem die tatsächliche
`source_metadata`-Dateiidentität; ohne sie bleiben sie unverändert. Das
Datei-API lädt diese Identität selbst und liest den übergebenen oder benachbarten
`alignment.jsonl.gz` und prüft die vollständige Übereinstimmung seiner Texte.

## Quellen der Regeln

- [STEPBible-Datensätze](https://github.com/STEPBible/STEPBible-Data): Wortvorkommen, Ausgabe, Morphologie, Verknüpfungen und Versifikation.
- [Goodell: Artikel](https://dcc.dickinson.edu/grammar/goodell/article): Formen und syntaktischer Gebrauch des griechischen Artikels.
- [Goodell: Relativpronomen](https://dcc.dickinson.edu/grammar/goodell/relative-pronouns): das eigenständige Pronomenparadigma.
- [Open Scriptures: Hebräische Morphologie](https://hb.openscriptures.org/parsing/HebrewMorphologyCodes.html): Wortarten, Partikeln, Affixe und Sprachkennzeichen.
