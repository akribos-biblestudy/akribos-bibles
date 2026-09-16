# Positionsgesicherte Strong-Korrekturen

Der Katalog [editorial-strong-corrections.json](../rules/editorial-strong-corrections.json)
enthält **43 geprüfte Regeln**: 24 betreffen Zuordnungen, die in Version 1.2
noch einen eigenen Unsicherheitshinweis trugen, 17 geerbte Zuordnungen ohne
diesen Hinweis. Zwei weitere betreffen neue Codes aus dem vollständigen
1.4-Probeaufbau und sind ausdrücklich an dessen Eingang gebunden. Das sind
Katalogzahlen, keine Aussage über einen späteren
Release-Lauf. Welche Regeln tatsächlich greifen, weist dessen Audit aus.

## Bindung und erlaubte Änderungen

Jede Regel bindet die Bibel-ID, die gewählte NT-Ausgabe (ELB/WH oder Luther/TR),
den SHA-256 des vollständigen eigenen Verstexts, Wort-ID, Wortlaut, Offsets,
den exakten alten Codesatz und den ursprünglichen XML-Bereich ohne Tail.
Zusätzlich müssen die für die jeweilige Regel benannten originalen
Quelldateihashes und die geordnete Quellprojektion des ganzen Verses
übereinstimmen: für NT-Regeln die beiden TAGNT-Dateien, für die sechs
OT-Regeln ausschließlich `TAHOT_Gen-Deu.tsv`. Die ausgewählte NT-Ausgabe
bleibt Teil des Zielprofils; die OT-Projektion bindet ihre tatsächlichen
L/Q-Wortvorkommen einschließlich der konkreten `=L`-Kennungen. Die Projektion umfasst
`origin_id`, `strong`, `morph`, `text`, `lemma` und `edition`; sie wird als
UTF-8-JSON mit sortierten Schlüsseln, ohne ASCII-Umschreibung und mit den
Trennzeichen `,` und `:` gehasht. Zusätzliche Importfelder ändern sie nicht.

Ein entferntes `gr`-Element wird ausgepackt; sein Wortlaut, seine Formatierung
und sein Folgetext bleiben erhalten. Bei einer Ersetzung ändern sich nur
`str` und die eigenen Provenienzattribute. Bei Luthers `Rohr` in Offenbarung
21,16 entfällt ausschließlich G1909; G2563 bleibt erhalten. Ein zugehöriger
eigener Unsicherheitshinweis wird entfernt. Historische Notizen und alle
nicht ausdrücklich aufgeführten Strong-Zuordnungen bleiben unverändert.

Die Entscheidung benötigt einen positiven syntaktischen Beleg. Das bloße
Fehlen einer Nummer im STEP-Inventar genügt nicht. Beispielsweise gehört
ἐκ/G1537 in den Psalm-110-Zitaten zu `zu meiner Rechten`; das erste deutsche
`zu meinem Herrn` gibt den griechischen Dativ wieder. Infinitivisches `zu`
wird nicht als πρός/G4314 verlinkt. Relativpronomen können nicht auf alle
gleichlautenden deutschen Artikel verteilt werden. Artikelersetzungen
beachten WH/TR: In Lukas 23,29 hat WH vor `Leiber` einen Artikel, TR nicht.
Die beiden `es/G3754` in Johannes 20,15 bezeichnen dagegen nicht die
Konjunktion ὅτι. In Apostelgeschichte 25,10 steht με/G3165 als Akkusativsubjekt
des passiven Infinitivs κρίνεσθαι nach δεῖ: `wo ich gerichtet werden muss`.
Daraus entsteht keine pauschale Normalisierung von Pronomen.

### Vier feste hebräische Wortbezüge

In 1. Mose 19,21 gehört אשר/H834 zur späteren Relativphrase `von der du
geredet hast`. Das erste deutsche `dass` gibt dagegen die Konstruktion
לבלתי הפכי את העיר wieder und erhält keine eigene H834-Verlinkung.
In 2. Mose 33,5 gehört אחד/H259 zu רגע אחד, dem späteren `einen Augenblick`.
Das vorangehende `ein hartnäckiges Volk` steht für אתם עם קשה ערף und
enthält kein solches Zahlwort. Vorhandene spätere richtige Strong-Zuordnungen bleiben unverändert;
eine dort fehlende Nummer wird nicht neu ergänzt. Beide Muster sind für ELB und Luther einzeln
an Wortposition, Text und tatsächliche TAHOT-Vorkommen gebunden; andere
Verwendungen von H834/H259 werden dadurch nicht verändert.

### Zwei Fehlübertragungen aus dem 1.4-Neuaufbau

In ELB 5. Mose 32,6 gehört קנך/H7069 (Quellwort 12) zum späteren
`der dich erkauft hat`. Das frühere `also` gibt zusammen mit `Vergeltet ihr`
תגמלו זאת (03–04) wieder. Der nach der Artikelkorrektur längere Abgleich
hat `also/H7069` erstmals in Stufe 04 des Neuaufbaus erzeugt. Nur diese
Verlinkung entfällt; das bisher ungetaggte `erkauft` bleibt ungetaggt.

In Luther 5. Mose 21,10 gehört תצא/H3318 (02) zum bereits richtig
verlinkten `ziehst`. Das folgende `und` leitet dagegen den Satz `der HERR ...
gibt` ein und gehört zu ונתנו (06). Die neue Zuordnung `und/H3318` wird
entfernt. Der dort zuvor stehende Code H7617 wird nicht wiederhergestellt:
ושבית/H7617 (10) gehört zum späteren `wegführst`. Der Unsicherheitshinweis
an `und` bestand schon in 1.2, der jetzt korrigierte Codesatz erst in 1.4.

Diese Regeln sind keine allgemeine Behandlung von Konjunktionen oder
Pronomen. Insbesondere bleibt Luther 5. Mose 8,5 `dich/H3256` samt Hinweis
unverändert: מיסרך enthält ein echtes Objektsuffix (`H9031`, `Sp2ms`) und
begründet die deutsche Mehrwortwiedergabe `dich gezogen`.

## Registrierte Stellen

`∅` bedeutet: die aufgeführte Verlinkung entfernen. `markiert` und `geerbt`
beziehen sich auf den geprüften Ausgangsstand 1.2; `Neuaufbau 1.4` benennt
die zwei gesondert geprüften neuen Codesätze.

| Ausgabe | Stelle / Wort-ID | Wort | Vorher → nachher | Ursprung |
|---|---|---|---|---|
| ELB / WH | Matt.22.44 / d004 | zu | G1537 → ∅ | markiert |
| ELB / WH | Mark.12.36 / d013 | zu | G1537 → ∅ | markiert |
| ELB / WH | Luke.20.42 / d012 | zu | G1537 → ∅ | markiert |
| ELB / WH | Acts.2.34 / d016 | zu | G1537 → ∅ | markiert |
| ELB / WH | Luke.14.6 / d007 | zu | G4314 → ∅ | markiert |
| ELB / WH | Luke.20.9 / d010 | zu | G4314 → ∅ | markiert |
| ELB / WH | Luke.23.29 / d011 | die | G3739 → G3588 | markiert |
| ELB / WH | Luke.23.29 / d014 | die | G3739 → G3588 | markiert |
| ELB / WH | Luke.23.29 / d020 | die | G3739 → ∅ | markiert |
| ELB / WH | Acts.1.12 / d010 | welcher | G3739 → ∅ | markiert |
| ELB / WH | John.1.29 / d019 | der | G4314 → G3588 | markiert |
| ELB / WH | John.20.15 / d016 | es | G3754 → ∅ | markiert |
| LUT / TR | Matt.22.44 / d005 | zu | G1537 → ∅ | geerbt |
| LUT / TR | Mark.12.36 / d013 | zu | G1537 → ∅ | geerbt |
| LUT / TR | Luke.20.42 / d012 | zu | G1537 → ∅ | geerbt |
| LUT / TR | Acts.2.34 / d015 | zu | G1537 → ∅ | geerbt |
| LUT / TR | Luke.20.9 / d005 | zu | G4314 → ∅ | markiert |
| LUT / TR | Luke.23.29 / d005 | die | G3739 → ∅ | geerbt |
| LUT / TR | Luke.23.29 / d015 | die | G3739 → G3588 | geerbt |
| LUT / TR | Luke.23.29 / d018 | die | G3739 → ∅ | geerbt |
| LUT / TR | Luke.23.29 / d025 | die | G3739 → ∅ | geerbt |
| LUT / TR | Matt.13.32 / d002 | das | G3739 → ∅ | markiert |
| LUT / TR | Acts.1.12 / d013 | der | G3739 → ∅ | markiert |
| LUT / TR | John.1.29 / d018 | der | G4314 → G3588 | markiert |
| LUT / TR | Luke.14.6 / d009 | geben | G4314 → ∅ | geerbt |
| LUT / TR | John.20.15 / d014 | es | G3754 → ∅ | markiert |
| ELB / WH | Acts.25.10 / d004 | Ich | G3165 → ∅ | markiert |
| ELB / WH | Acts.21.37 / d022 | zu | G4314 → ∅ | markiert |
| ELB / WH | Phil.2.25 / d024 | zu | G4314 → ∅ | markiert |
| LUT / TR | Rev.21.16 / d020 | mit | G1909 → ∅ | markiert |
| LUT / TR | Jude.1.15 / d028 | die | G3739 → ∅ | markiert |
| LUT / TR | Rev.21.16 / d022 | Rohr | G1909, G2563 → G2563 | geerbt |
| ELB / WH | Rev.21.16 / d020 | mit | G1909 → ∅ | geerbt |
| LUT / TR | Acts.25.10 / d004 | Ich | G3165 → ∅ | geerbt |
| LUT / TR | Acts.25.10 / d019 | ich | G3165 → ∅ | geerbt |
| LUT / TR | Phil.2.25 / d013 | zu | G4314 → ∅ | geerbt |
| LUT / TR | Jude.1.15 / d025 | das | G3739 → G3588 | geerbt |
| ELB / WH | Exod.33.5 / d015 | ein | H259 → ∅ | geerbt |
| ELB / WH | Gen.19.21 / d015 | dass | H834 → ∅ | geerbt |
| LUT / TR | Exod.33.5 / d014 | ein | H259 → ∅ | markiert |
| LUT / TR | Gen.19.21 / d015 | dass | H834 → ∅ | markiert |
| ELB / WH | Deut.32.6 / d003 | also | H7069 → ∅ | Neuaufbau 1.4, markiert |
| LUT / TR | Deut.21.10 / d010 | und | H3318 → ∅ | Neuaufbau 1.4, markiert |

Die ausführliche Begründung und die konkreten STEP-Wörter stehen pro Regel
im Katalog. Bewusst nicht geändert werden ELB Apostelgeschichte 1,2
`dem/G3739`, Luther Johannes 1,29 `das/G3588` vor `ist` sowie das zweite
ELB-`ich/G3165` in Apostelgeschichte 25,10 (d019). Für den letzten Fall wird
die entscheidende Verbvariante nicht als eigenständiger Beleg importiert.
Kolosser 1,9 und 1. Korinther 10,13 erhalten ebenfalls keine pauschale Regel.

## Audit und Wiederholbarkeit

Jede registrierte Regel erhält einen `editorial-correction`-Eintrag, auch
wenn der Zielvers fehlt oder eine Bindung abweicht. `applied` dokumentiert
die genaue Änderung mit `before_strong`, `after_strong`, Regel-ID und
Quellhashes. `not-applicable` behält den tatsächlichen Codesatz; die
katalogisierte Absicht steht separat in `proposed_strong`. Sein eventuell
vorhandener Hinweis wird zusätzlich durch die normale Prüfung erfasst.
Ein angewandter Eintrag mit `hint_id` ersetzt genau diesen Hinweis-Auditeintrag.
Damit wird jede eingehende Unsicherheitsmarkierung weiterhin genau einmal geprüft.

Der öffentliche Replay berechnet sämtliche Bedingungen aus den unveränderten
Eingabedaten erneut und vergleicht den vollständigen erwarteten Auditeintrag.
Zusatzfelder, freie Meldungen und nicht katalogisierte Deltas werden
abgelehnt, auch wenn äußere Datei- und Manifesthashes neu berechnet wurden.
Katalogdatei und Regelmodul gehören zur gehashten Implementierungsidentität.

Der Bericht trennt `editorial_corrections_marked` und
`editorial_corrections_inherited` nach dem jeweiligen Katalogbefund.
Unabhängig davon trennen `editorial_corrections_baseline` und
`editorial_corrections_rebuild` die 41 älteren von den zwei neu entstandenen
Codesätzen. Beide Zählerpaare summieren sich jeweils zu
`editorial_corrections`; sie dürfen nicht miteinander addiert werden.
`reviewed_input_version` steht geschlossen als `1.2` oder `1.4` in Katalog
und Audit und wird beim Replay erneut an die konkrete Regel gebunden.
`editorial_hints_removed` zählt die tatsächlich noch vorhandenen entfernten
Hinweise; eine vorherige Bestätigung in Stufe 05 kann diese Zahl verringern.
`editorial_not_applicable` zählt zurückgestellte Regeln. Alle übrigen
Strong-Zuordnungen müssen unverändert sein (`unlisted_strong_values_preserved`).

Alle Entscheidungen beruhen auf demselben eingefrorenen Eingangszustand.
Die im Katalog genannten Verse bleiben in der jeweiligen Bibelausgabe
dauerhaft für automatische Bestätigungen und Artikelergänzungen gesperrt.
So kann eine Entlinkung auch im zweiten Lauf keine zuvor mehrdeutige
Nachbarzuordnung plötzlich als Beweisanker nutzbar machen. Wiederholte Läufe
ändern die fertige XML nicht; bereits angewandte Regeln erfüllen ihre alte
Codesatz-/Spannenbindung nicht mehr und werden als nicht anwendbar protokolliert.

## Quellen und Rechte

- STEP Bible, Tyndale House Cambridge: die eingecheckten TAGNT-/TAHOT-Grundtextdaten
  und die daraus ausgewiesenen Wort-/Morphologiebelege, **CC BY 4.0**.
  [Projekt und Attribution](https://github.com/STEPBible/STEPBible-Data),
  [Lizenz](https://creativecommons.org/licenses/by/4.0/).
- Zielpositionen und redaktionelle Entscheidungen: Akribos, **CC BY 4.0**.
  Die eigenen Testausschnitte stammen aus den veröffentlichten Akribos-1.2-Ausgaben
  und dem ausdrücklich getrennten eigenen 1.4-Probeaufbau;
  Grundtexte sind Elberfelder 1932 beziehungsweise Luther 1912.
- Private BK-/CSV-Referenztexte und deren Wortpositionen werden weder im
  Katalog noch in den Testausschnitten übernommen.
