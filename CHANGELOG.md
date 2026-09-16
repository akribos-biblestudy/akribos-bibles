# Änderungen

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
