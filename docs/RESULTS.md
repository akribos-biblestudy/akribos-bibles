# Messergebnisse

## Version 1.4

Vollständiger Aufbau mit denselben eingefrorenen Referenzen: ELB BK und Edition CSV,
jeweils 66 Bücher und 1.189 Kapitel. Die Referenzen enthalten 31.169 beziehungsweise
31.166 Haupttextverse. Abweichende Verskennungen werden nicht automatisch umnummeriert.

| Ausgabe | Hinweise entfernt: 05 | Hinweise entfernt: 06 | Verbleibend | Neue G3588-Artikel | Redaktionelle Korrekturen |
|---|---:|---:|---:|---:|---:|
| ELB | 20.832 | 18 | 31.149 | 791 | 19 |
| Luther | 3.095 | 11 | 38.205 | 355 | 24 |

Die Stufen 05 und 06 erhalten ihren Eingangswortlaut und sämtliche Originalnotizen.
Die vorgelagerte Sprachstufe ändert gegenüber 1.3 genau 213 ELB-Namensersetzungen in 190 Versen;
Luthers Wortlaut bleibt gleich. Weitere 196 ELB- und 176 Luther-Verlinkungen deutscher Artikel
mit H3068 stammen aus bestehenden Mehrwortbezügen und zählen keine zusätzlichen hebräischen Vorkommen.
Die Hinweise der Stufe 06 schließen entfernte redaktionelle Hinweise bereits ein. Ihre Zahl
ist nicht mit der Anzahl redaktioneller Korrekturen gleichzusetzen.

Zwei vollständige Aufbauten sind über 396 Dateien bytegleich;
der anschließende Cache-Lauf ist ebenfalls identisch. Beide Repository-Prüfungen sind bestanden.
Der tatsächliche Akribos-Parser liest beide Ausgaben ohne Warnungen und mit unverändertem
Wortlaut der jeweiligen Prüfstufe; die Strong-Änderungen entsprechen exakt den erwarteten Änderungen.
291 Python-Tests und acht Abruf-Tests sind erfolgreich.
Originale und frühere Laufarchive bleiben unverändert.

Die Zahlen beschreiben angewandte Regeln und Prüfentscheidungen. Nicht eindeutig belegte
Zuordnungen bleiben markiert. Die aktuellen Integritätsdaten stehen in [verification.json](verification.json).

## Version 1.3

Vollständiger Aufbau mit denselben eingefrorenen Referenzen: ELB BK und Edition CSV,
jeweils 66 Bücher und 1.189 Kapitel. Die Referenzen enthalten 31.169 beziehungsweise
31.166 Haupttextverse. Abweichende Verskennungen werden nicht automatisch umnummeriert.

| Ausgabe | Hinweise geprüft | Entfernt | Verbleibend |
|---|---:|---:|---:|
| ELB | 51.998 | 20.831 | 31.167 |
| Luther | 41.134 | 3.095 | 38.039 |

Wortlaut, Strong-Nummern und Originalnotizen stimmen mit der veröffentlichten 1.2-Ausgabe überein.
Jeder eingehende Hinweis hat eine Entscheidung im öffentlichen Audit der Stufe 05.

Zwei vollständige Aufbauten sind über 286 Dateien bytegleich;
der anschließende Cache-Lauf ist ebenfalls identisch. Beide Repository-Prüfungen sind bestanden.
Der tatsächliche Akribos-Parser liest beide Ausgaben ohne Warnungen und mit unverändertem
Wortlaut der jeweiligen Prüfstufe; die Strong-Änderungen entsprechen exakt den erwarteten Änderungen.
149 Python-Tests und acht Abruf-Tests sind erfolgreich.
Originale und frühere Laufarchive bleiben unverändert.

Die Zahlen beschreiben angewandte Regeln und Prüfentscheidungen. Nicht eindeutig belegte
Zuordnungen bleiben markiert. Die aktuellen Integritätsdaten stehen in [verification.json](verification.json).

## Version 1.2

Dieser historische Abschnitt beschreibt Tag `v1.2`; seine Dateiverweise beziehen sich auf diesen Stand.

Vollständiger Skriptlauf vom 16. September 2026 nach der [Artikel-/Kasuskorrektur](DIVINE-NAME-CORRECTION.md). Die endgültigen Dateien sind in `releases/` mit dem jeweiligen Laufordner verknüpft.

### Aufbau aus Originalen

| Stufe | ELB | Luther |
|---|---:|---:|
| Vorhandene/übertragene Ausgangszuordnungen | 43,29 % | 50,24 % |
| Nach Lexika | 44,14 % | 50,40 % |
| Nach weiteren Übersetzungen und Konkordanz | 50,43 % | 56,13 % |

ELB: **367.044 von 727.791** Worttokens kodiert. Luther: **391.844 von 698.111**. Die Nenner beziehen sich auf die sprachlich bearbeiteten Ausgaben. Eingefügte Artikel können Wortzahlen und damit die Quote ändern. Die Korrektur der ELB1905-Sprachfassung verändert auch deren Strong-Übertragung als Spender für Luther; der Luther-Wortlaut bleibt gleich.

### Sprache, Notizen und offene Prüfung

| Merkmal | ELB | Luther |
|---|---:|---:|
| Protokollierte Textänderungen | 14980 | 8509 |
| Geänderte Verse/Überschriften | 10727 | 6689 |
| Vollständig erhaltene Originalnotizen | 9481 | 0 |
| Sprachliche Prüfaufgaben | 1253 | 797 |

Die ELB-Quelle enthält **9.481 Studynotes**, Luther in diesem Quell-Snapshot keine. Die Null bei Luther ist keine Löschung von Notizen. Alle vorhandenen Notiz-Unterbäume wurden vor/nach Bearbeitung und nach XML-Serialisierung verglichen.

Offen sind insbesondere **441 ELB-Vorkommen mit nicht eindeutig regelbasiert bestimmtem Kasus/Artikel des Gottesnamens**, gegenüber zuvor 1.289. Die Ausgabe setzt dort HERR und dokumentiert den Kontext in der Sprachprüfliste; nicht jeder Satz ist damit bereits grammatisch fertig. In 1. Samuel sind alle 322 Vorkommen klassifiziert. Weitere Aufgaben betreffen Genus-/Pronomenbezüge bei Frau und kontextabhängige Rechtschreibung. Sichere Präpositionsfälle wie „zu Jehova“ wurden zu „zu dem HERRN“ angepasst.

Die 29 automatisierten Tests prüfen unter anderem die Jehova-/HERR-Korrektur an Originalversen und Gegenbeispielen, Präpositionskasus, Frau-Kongruenz, HErr-Großschreibung, Notiz-/Formatierungserhalt, Strong-Mehrfachnummern, Mehrdeutigkeiten, XML-Sicherheit, OSIS-Container/Meilensteine sowie Nenner und Datenschutz des Vergleichs. Zusätzlich werden die versionierten Metadaten, das Überschreiben der festen Ergebnisdateien bei unveränderter Laufhistorie und die KJV-Reparatur einschließlich Änderungsprotokoll geprüft. Die vollständige Wiederholbarkeitsprüfung wird in `docs/verification.json` dokumentiert.

### Grenzen der Lexikonstufe

Kautz: 5.489 klassische Einträge eingelesen, 5.373 mit nutzbaren primären Bedeutungsüberschriften, 6.056 gewonnene Formulierungen. 216 Anhangeinträge außerhalb des klassischen Strong-Bereichs werden nicht als reguläre Codes verwendet. Wortfamilien und zitierte Bibelstellen werden nicht als zusätzliche Bedeutungen des jeweiligen Eintrags behandelt.

Das hebräisch-deutsche Lexikon liefert 3.557 kurze Definitionsformulierungen. Seine deutsche Fassung ist ein maschineller Entwurf. Die Lemmakandidaten und die STEP-Morphologie sind Prüfmaterial; eine eindeutige Ausrichtung jedes deutschen Wortes auf ein bestimmtes Urtextvorkommen ist damit noch nicht erreicht. Die KJV wird als zusätzliche Versbestätigung aufgeführt und nicht als verdeckte englisch-deutsche Wortübersetzung behandelt.
