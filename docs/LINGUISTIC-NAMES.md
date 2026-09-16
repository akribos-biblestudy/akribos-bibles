# Katalog vorhandener Eigennamen

Die [sprachliche Prüfung](LINGUISTIC-VALIDATION.md) bestätigt mit diesem Katalog
nur bereits markierte Einzelwörter. Sie ergänzt keine Strong-Nummer. Der
Katalog enthält 28 ausdrücklich geprüfte Codeeinträge, davon zehn hebräische.

## Notwendige Belege

Die deutsche Namensform und ihr Code dürfen im ganzen Zielvers nur einmal
vorkommen. Ein weiteres unmarkiertes Namenswort oder derselbe Code in einer
Mehrfachnummernspanne verhindert die Bestätigung. Im gewählten STEP-Grundtext
muss genau ein atomarer Code mit passender Eigenname-Morphologie vorhanden sein.
Im Griechischen wird das vollständige belegte Lemmafeld geprüft; beliebige
weitere Namensalternativen bestehen den Vergleich nicht. Im Hebräischen werden
Vokal- und Kantillationszeichen für den Konsonantenvergleich entfernt, keine
Buchstaben. Präfixe, Maqaf und zusammengesetzte Formen werden nicht zerlegt.

Die konkrete deutsche Wortspanne muss zusätzlich von mindestens einer privaten
BK-/CSV-Referenz exakt mit dem bestehenden Code bestätigt werden. Auch diese
Regel erhält alle Vers-, Inventar-, Editions- und Provenienzsperren. Neue
Bestätigungen dienen in späteren Läufen nicht als neue Anker.

HERR/H3068, Adonai/H136 und allgemeine Namensableitungen sind ausgeschlossen.
Abram wird nicht zu Abraham, Jakobus nicht zu Jakob und Josua nicht zu Jesus
normalisiert. Unterschiedliche Namensträger werden nicht miteinander
identifiziert; geprüft wird ausschließlich die vorhandene lexikalische Nummer.

## Formen

| Code | Explizite deutsche Formen |
|---|---|
| G2 | Aaron, Aarons |
| H175 | Aaron, Aarons |
| G11 | Abraham, Abrahams |
| H85 | Abraham, Abrahams |
| G1138 | David, Davids |
| H1732 | David, Davids |
| G2384 | Jakob, Jakobs |
| H3290 | Jakob, Jakobs |
| G2464 | Isaak, Isaaks |
| H3327 | Isaak, Isaaks |
| G2474 | Israel, Israels |
| H3478 | Israel, Israels |
| G2501 | Joseph, Josephs, Josef, Josefs |
| H3130 | Joseph, Josephs, Josef, Josefs |
| G3475 | Mose, Moses, Mosen, Mosi |
| H4872 | Mose, Moses, Mosen, Mosi |
| G4545 | Samuel, Samuels |
| H8050 | Samuel, Samuels |
| G4672 | Salomo, Salomos, Salomon, Salomons |
| H8010 | Salomo, Salomos, Salomon, Salomons |
| G2491 | Johannes, Johannis, Johannem |
| G2424 | Jesus, Jesu, Jesum |
| G3972 | Paulus, Pauli, Paulum |
| G4074 | Petrus, Petri, Petrum |
| G2264 | Herodes, Herodis, Herodem |
| G4091 | Pilatus, Pilati, Pilatum |
| G3137 | Maria, Marias, Marien, Mariam |
| G4613 | Simon, Simons, Simonem |

Historische Formen wie *Mosen*, *Jesu* und *Pauli* stehen ausdrücklich im
Katalog. Genus oder Flexion werden nicht pauschal aus der Quellsprache
übernommen. Die hebräische Kategorie `HNpl` ist ausschließlich für Israel
zugelassen; die übrigen hebräischen Katalogeinträge verlangen `HNpm`.

## Originalbelege und Rechte

[proper-name-catalog.json](../rules/proper-name-catalog.json) speichert
Originaleinträge, Definitionszeilen, STEP-Wortpositionen und Eintraghashes.
[proper-name-sources.json](../rules/proper-name-sources.json) enthält
Dateihashes und Rechteangaben. Tests prüfen die Belegzeiger gegen die wirklichen
Originaleinträge und STEP-Zeilen. Beide Dateien gehören zur Build- und
Regelidentität. Ein gespeicherter Freigabebeleg enthält den konkreten
Quellwortbezug und den Hash des überprüften Katalogbelegs.

- **Kautz:** Copyright Gerhard Kautz, Update 5/2026. Namensstichwörter,
  Eigenname-Kennzeichnung und hebräische Querverweise behalten ihre
  Quellenzuordnung und die [Veröffentlichungsbedingungen](../licenses/LicenseRef-Kautz-Akribos-Permission.md).
- **Griechisches Strong-Original:** Public Domain; James Strong, elektronische
  Bearbeitung Michael Grier / Ulrik Sandborg-Petersen.
- **Hebräisches Lexikon:** historischer Strong-Text Public Domain;
  elektronische Open-Scriptures-Daten CC BY 4.0; deutsche Akribos-Ergänzungen
  AGPLv3. Die Namensbelege verwenden die Originalschreibung und
  Eigenname-Kennzeichnung; deutsche Maschinenübersetzungen sind keine alleinige
  Beweisgrundlage.
- **STEP TAGNT/TAHOT:** CC BY 4.0; STEP Bible (www.STEPBible.org), based on work
  at Tyndale House Cambridge.

Die eigenen redaktionellen Formenlisten und der Prüfcode ändern keine Rechte
an ihren Quellen. Weitere Angaben stehen in [LICENSE-DATA.md](../LICENSE-DATA.md).
