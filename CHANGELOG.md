# Änderungen

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
