# Datenrechte und Akribos-Urhebervermerk

## Eigene Beiträge

**Copyright © 2026 Akribos** für neue, schutzfähige redaktionelle Leistungen, Dokumentation und Strong-Aufbereitung. Diese Beiträge stehen unter [Creative Commons Namensnennung 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). Der Lizenztext liegt unter `licenses/CC-BY-4.0.txt`.

Namensnennung: „Akribos, Version <Ausgabeversion>; regelbasierte Sprachbearbeitung und automatische Strong-Aufbereitung“, mit Projekt-/Quellenlink und Kennzeichnung eigener Änderungen. Die jeweilige Ausgabeversion steht in den XML-Metadaten und den Build-Manifesten.

Der Python-Code sowie eigene Konfigurationen, Regeln und Tests stehen unter MIT (`LICENSE`). Fremde Quellen behalten ihre jeweiligen Rechte. Keine ausschließlichen Rechte an Strong-Nummern oder gemeinfreien Texten.

## Bibeltexte und historische Strong-Quelle

| Bestandteil | Rechteangabe der Quelle | Herkunft und Umfang |
|---|---|---|
| Elberfelder 1932 | Public Domain | Bibeltext und historische Studynotes; digitale Ausgabe bibelkommentare.de. |
| Elberfelder 1905 mit Strongs | Public Domain laut Quellmetadaten | Bibeltext mit Strong-Zuordnungen; Originaldatei und Metadaten im Quellenarchiv. |
| Luther 1912 mit Strongs | Public Domain laut TOLEDOT/Quellmetadaten | Bibeltext mit Strong-Zuordnungen; TOLEDOT, Jens Grabner und J. Barkowsky. |
| Schlachter 1951 mit Strongs | Public Domain laut Quellmetadaten | Bibeltext mit Strong-Zuordnungen; Jens Grabner / Free Bible Software Group. |
| King James Version 1611/1769 mit Strongs | Public Domain laut Quellmetadaten | Digitale Ausgabe bibelkommentare.de; zusätzlich als syntaxreparierte Importdatei unter `releases/kjv1611.xml`. |
| Historisches griechisches Strong-Lexikon | Public Domain | James Strong; elektronische Bearbeitung Michael Grier / Ulrik Sandborg-Petersen; Originalprolog in `sources/originals/strongsgreek.xml`. |

Die unveränderten Originaldateien enthalten ihre jeweiligen Rechte- und Quellenangaben. Download-URLs, Zuschreibungen und SHA-256-Werte stehen in `config/sources.lock.json`; Auszüge der Originalmetadaten unter `sources/evidence/`. Die [TOLEDOT-Dokumentation](https://www.toledot.info/die-welt-der-bibel.php?t=info%2Freformation%2Ftextueberarbeitung) beschreibt die digitale Luther-Fassung und ihre Strong-Zuordnungen.

## STEP Bible

TAHOT und TAGNT: **CC BY 4.0**. Zuschreibung:

> STEP Bible (www.STEPBible.org), based on work at Tyndale House Cambridge

Projekt: <https://github.com/STEPBible/STEPBible-Data>. Commit, Download-URLs und Prüfsummen stehen in `config/sources.lock.json`. Die Originaldateien sind enthalten. Akribos wählt Textzeugen, normalisiert Strong-Darstellungen, exportiert Lemma-/Morphologiedaten und verwendet diese als Versinventar für neue Wortzuordnungen. Diese Bearbeitungen sind im jeweiligen Lauf protokolliert.

## Kautz-Lexikon

**Copyright © Gerhard Kautz, Update 5/2026.** Die Originaldatei `sources/originals/stronggreek_de_kautz.xml` wird mit Genehmigung im öffentlichen Akribos-GitHub-Repository veröffentlicht. Copyright, Benutzungshinweise und Quellenangaben bleiben erhalten. Veröffentlichungsbedingungen: `licenses/LicenseRef-Kautz-Akribos-Permission.md`.

Die aus dem Lexikon erzeugten Suchindizes bleiben der Kautz-Quelle zugeordnet. Der Lexikontext gehört nicht zu den unter MIT oder CC BY 4.0 veröffentlichten eigenen Akribos-Beiträgen.

## Hebräisch-deutsches Lexikon

Quelle: [Open Scriptures Hebrew Lexicon](https://github.com/openscriptures/HebrewLexicon), ergänzt um deutsche Texte im Akribos-Quellrepository. Historischer englischer Strong-Text: Public Domain. Elektronische Open-Scriptures-Ausgabe: **CC BY 4.0**. Deutsche Ergänzungen: **AGPLv3**.

Der vollständige XML-Quellstand, die Herkunftsangaben, der Code zur Indexbildung und der AGPLv3-Lizenztext (`licenses/AGPL-3.0.txt`) sind enthalten. Originale und abgeleitete Indizes behalten ihre Quellen- und Lizenzhinweise. Der deutsche Text ist eine maschinelle Übersetzung; die technische Entstehung beschreibt `sources/evidence/hebrew-lexicon.md`.

## Referenzvergleiche

Die ELB-BK-Referenz trägt **Copyright 2023 www.bibelkommentare.de**. Öffentlich enthalten sind eigene aggregierte Messungen sowie ein Index aus Versstellen und Abweichungskategorien. Die Referenzdatei und vollständige Wortvergleiche bleiben unter `.local/` und sind vom öffentlichen Paket ausgeschlossen. Das Verfahren beschreibt `docs/REFERENCE-COMPARISON.md`.
