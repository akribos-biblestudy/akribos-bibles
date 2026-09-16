# Änderungen

## 1.4 — 2026-09-16

- Nach der Pflichtprüfung durch ELB BK und Edition CSV alle verbliebenen
  eigenen Unsicherheitshinweise an konkreten STEP-Wortvorkommen prüfen.
  Morphologie, ausdrückliche Formenlisten und eindeutige Nachbarbelege
  entscheiden über eine Bestätigung. Fehlende oder mehrdeutige Belege lassen
  den Hinweis stehen; es werden keine Ersatznummern aus deutschem Wortlaut
  oder bloßer Vershäufigkeit abgeleitet.
- Ausgewählte griechische Artikel G3588 ergänzen, wenn die genaue
  Artikel-Nomen-Verbindung der gewählten Ausgabe und mindestens eine private
  Wortreferenz sie bestätigen. Bestehende Eigennamen können mit ausdrücklichem
  Namenskatalog, echter Quelle und genauem Referenzbeleg bestätigt werden.
- 43 positionsgesicherte redaktionelle Regeln ergänzen: 41 betreffen den
  geprüften Bestand 1.2 (24 markierte, 17 geerbte Zuordnungen), zwei betreffen
  neue Codesätze aus dem 1.4-Neuaufbau. Falsche Nummern werden gezielt entfernt
  oder durch einen belegten Artikelcode ersetzt. Bei `Rohr` in Luther
  Offenbarung 21,16 entfällt nur G1909; G2563 bleibt erhalten. Anwendbarkeit
  und tatsächliche Änderungen werden pro Regel protokolliert.
- Weitere HERR-Artikel und Kasusformen in der vorgelagerten Sprachstufe
  berichtigen: 213 geänderte ELB-Namensersetzungen in 190 Versen gegenüber
  dem Skriptstand 1.3. Luthers Wortlaut bleibt gleich. Der erneute Abgleich
  enthält außerdem 196 zusätzliche deutsche H3068-Artikelverlinkungen in ELB
  und 176 in Luther aus bereits vorhandenen Mehrwortbezügen. Sie sind getrennt
  von neuen G3588-Artikeln zu zählen und erzeugen keine zusätzlichen
  hebräischen Wortvorkommen.
- Stufe `06-linguistic` mit geschlossenem Audit, vollständigen Quell-/Regelhashes
  und exaktem XML-Replay veröffentlichen. Prüfen, dass Stufe 05 und 06 den
  bereits bearbeiteten Wortlaut und Originalnotizen erhalten. Eigene Provenienz
  verhindert, dass neue Bestätigungen sich in Folgeläufen selbst begründen.
- Standardversion auf **1.4** setzen. Originalausgaben, Cover-/Tab-Titel und
  feste Dateinamen beibehalten; Untertitel, Revision und Rechtehinweis tragen
  die aktuelle Bearbeitungsversion. Der vollständige Build beginnt bei den
  Originalen und benötigt keinen vorherigen 1.3-Lauf.
- Endgültiger vollständiger Lauf: Stufe 06 entfernt in ELB
  **18** Hinweise und ergänzt
  **791** G3588-Artikel; in Luther
  **11** Hinweise und
  **355** Artikel. Es verbleiben
  **31.149** beziehungsweise
  **38.205** Hinweise. Tatsächlich angewandt wurden
  **19** ELB- und
  **24** Luther-Korrekturregeln. Die Hinweiszählung
  umfasst dabei tatsächlich entfernte redaktionelle Hinweise.
- Vollständigen Aufbau, echte bytegleiche Wiederholung und Repository-Verifier
  prüfen; **291** Python-Tests bestehen. Skripte, Regeln,
  Laufarchive und Ergebnisdateien gemeinsam als `v1.4` festhalten; frühere Tags
  unverändert erhalten.

Details: [Sprachliche Prüfung](docs/LINGUISTIC-VALIDATION.md),
[redaktionelle Strong-Korrekturen](docs/EDITORIAL-STRONG-CORRECTIONS.md),
[HERR-Korrekturen](docs/DIVINE-NAME-CORRECTION.md#ergänzung-in-version-14).

## 1.3 — 2026-09-16

- Jede bestehende eigene Strong-Unsicherheitsmarkierung gegen ELB BK und die
  Elberfelder Ausgabe des CSV-Verlags prüfen. Nur bei eindeutigem Wortbereich,
  identischer vollständiger Strong-Menge und bestandenen Sicherheitsprüfungen
  den Hinweis entfernen. Bibeltext, Nummern und Originalnotizen bleiben in
  dieser Prüfstufe unverändert.
- Gemeinsame Referenzfehler durch Artikelkontext, enge Funktionswortprüfungen
  und Belegzahlvetos für sechs griechische Codes sowie H259/H834 abfangen.
  Mehrfachnummerierungen zählen vollständig mit; nicht eindeutig zählbare
  hebräische L/Q-Lesarten bleiben offen. Keine Ersatznummern ableiten.
- Stufe `05-reference-confirmed` mit vollständigem Hinweis-Audit und exaktem
  XML-Replay ergänzen. STEP-/Alignmentbelege, Referenzhashes und das
  Sicherheitsprofil `greek-hebrew-function-word-vetoes-v2` an den Lauf binden.
  Private Referenztexte bleiben außerhalb öffentlicher Archive.
- Den vollständigen, fortsetzbaren CSV-Browserabruf und die deterministische
  HTML-zu-Zefania-Konvertierung dokumentieren; `--require-complete` prüft den
  vollständigen Kapitelbestand vor einem regulären Aufbau.
- Standardversion für CLI, Pipeline und Repository-Prüfung auf **1.3** setzen.
  Beide regulären Ausgaben benötigen beim Aufbau die zwei privaten Referenzen.
  Exporttitel benennen weiter Elberfelder 1932 beziehungsweise Luther 1912;
  Untertitel und Rechtehinweis tragen die aktuelle Akribos-Version.
- Ergebnisse aus dem endgültigen vollständigen Lauf: ELB
  **20.831** Hinweise entfernt,
  **31.167** verbleiben; Luther
  **3.095** entfernt,
  **38.039** verbleiben. Diese Zahlen messen geprüfte
  Hinweise, keine allgemeine Zuordnungsgenauigkeit.
- Den vollständigen Neuaufbau, dessen bytegleiche Wiederholung und den
  Repository-Verifier prüfen; **149** Python-Tests bestehen.
  Skripte, Laufarchive und feste Ergebnisdateien gemeinsam als `v1.3`
  festhalten. Frühere Tags bleiben unverändert.

Anleitung: [Referenzbestätigung](docs/REFERENCE-CONFIRMATION.md),
[CSV-Abruf](docs/CSV-REFERENCE.md), [Versionshistorie](docs/HISTORY.md).

## Export und Dokumentation — 16. September 2026

- KJV 1611/1769 als syntaxreparierte Zefania-Importdatei unter `releases/kjv1611.xml` exportieren; eigener Befehl `repair-kjv`, zusätzlich Bestandteil jedes regulären Builds.
- Quellmetadaten, englischer Wortlaut, Strong-Zuordnungen und 7.716 Originalnotizen der KJV erhalten; Reparaturen und Prüfsummen vollständig protokollieren.
- Quellen- und Lizenzdokumentation vereinheitlichen; Copyrightvermerke, Zuschreibungen, Originalquellen und Lizenztexte erhalten.

## 1.2 — 16. September 2026

- Jehova → HERR berücksichtigt weitere Artikel- und Kasusfälle, darunter 1. Samuel 17,37 und Kapitel 20. Gegenüber dem ursprünglichen Sprachlauf ändern sich 698 Ersetzungen in 667 Versen. Anreden bleiben artikellos; 441 mehrdeutige Fälle bleiben zur Prüfung protokolliert. Details: [Artikelkorrektur](docs/DIVINE-NAME-CORRECTION.md).
- Beide Ausgaben werden mit den geänderten Skripten vollständig aus den Originalen aufgebaut. Alle 9.481 historischen ELB-Studynotes bleiben erhalten.
- Exporttitel: `ELB` / `Elberfelder 1932` bzw. `LUT` / `Luther 1912`; Auswahl-Untertitel `mit Strongs (Akribos 1.2)`. Die Versionsnummer wird automatisch eingesetzt.
- Rechtehinweis gemäß Vorgabe, ergänzt um die Originalausgabe und die Klarstellung, dass Akribos keine eigene Übersetzung ist. Ausschließlich Exportskripte geändert; die Übernahme zusätzlicher Anzeigefelder durch den App-Importer ist nicht Bestandteil dieser Version.
- Öffentliche Ergebnisdateien liegen dauerhaft unter `releases/akribos.elb.xml` und `releases/akribos.lut.xml`. Skripte und Ergebnisse werden gemeinsam in Git versioniert; Tags `v1.1` und `v1.2` machen die Stände vergleichbar. Build-Manifeste verweisen weiter auf unveränderliche Laufarchive.
- Standardversion für CLI, Pipeline und Repository-Prüfung gemeinsam auf `1.2` gesetzt.

## 1.1 — ursprüngliche Ausgabe

- Sprachbearbeitung und Strong-Aufbereitung auf Grundlage der Elberfelder 1932 und Luther 1912; historische Originalnotizen bleiben erhalten.
- Bekannter Fehler: Bei Jehova → HERR fehlen in verschiedenen Satzkonstruktionen Artikel, unter anderem in 1. Samuel 17,37 und Kapitel 20.
- Der Tag `v1.1` enthält den Bibelstand vor der Artikelkorrektur. Beide Versionen verwenden einheitliche Exportmetadaten und vollständige, reproduzierbare Laufarchive. Details: [Versionshistorie](docs/HISTORY.md).
