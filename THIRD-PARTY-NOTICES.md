# Quellen und Drittanbieterhinweise

Alle 14 registrierten Originaldateien sind enthalten. Die SHA-256-Werte prüfen die entpackten Originalbytes; ZIP-Transportdateien werden nicht als Original-Bibeldatei verwendet.

| Quelle | Lizenz / Veröffentlichungsgrundlage | Zuschreibung |
|---|---|---|
| [elb1932](https://www.bibelkommentare.de/data/modules/bible_elb_1932_zefania.zip) | Public-Domain | Elberfelder 1932; digitale Ausgabe bibelkommentare.de, Revision 202307 |
| [elb1905](https://raw.githubusercontent.com/akribos-biblestudy/akribos/b95299ec7f702f0898494100db0d28e83ec83a1a/data/bibles/GER_ELB1905_STRONG.xml) | Public-Domain | Elberfelder 1905 mit Strongs; Akribos-Quellrepository, XML 2009-01-22 |
| [luther1912](https://www.toledot.info/download/bibel/SF_2022-02-27_GER_LUTH1912_Strongs_xml.php) | Public-Domain | Luther 1912 mit Strongs; TOLEDOT/Jens Grabner/J. Barkowsky, 2022-02-27 |
| [TAGNT_Act-Rev](https://raw.githubusercontent.com/STEPBible/STEPBible-Data/ae39711d7843b2902d54993e432de9c12d6a4b9a/Translators%20Amalgamated%20OT%2BNT/TAGNT%20Act-Rev%20-%20Translators%20Amalgamated%20Greek%20NT%20-%20STEPBible.org%20CC-BY.txt) | CC-BY-4.0 | STEP Bible (www.STEPBible.org), based on work at Tyndale House Cambridge |
| [TAGNT_Mat-Jhn](https://raw.githubusercontent.com/STEPBible/STEPBible-Data/ae39711d7843b2902d54993e432de9c12d6a4b9a/Translators%20Amalgamated%20OT%2BNT/TAGNT%20Mat-Jhn%20-%20Translators%20Amalgamated%20Greek%20NT%20-%20STEPBible.org%20CC-BY.txt) | CC-BY-4.0 | STEP Bible (www.STEPBible.org), based on work at Tyndale House Cambridge |
| [TAHOT_Gen-Deu](https://raw.githubusercontent.com/STEPBible/STEPBible-Data/ae39711d7843b2902d54993e432de9c12d6a4b9a/Translators%20Amalgamated%20OT%2BNT/TAHOT%20Gen-Deu%20-%20Translators%20Amalgamated%20Hebrew%20OT%20-%20STEPBible.org%20CC%20BY.txt) | CC-BY-4.0 | STEP Bible (www.STEPBible.org), based on work at Tyndale House Cambridge |
| [TAHOT_Isa-Mal](https://raw.githubusercontent.com/STEPBible/STEPBible-Data/ae39711d7843b2902d54993e432de9c12d6a4b9a/Translators%20Amalgamated%20OT%2BNT/TAHOT%20Isa-Mal%20-%20Translators%20Amalgamated%20Hebrew%20OT%20-%20STEPBible.org%20CC%20BY.txt) | CC-BY-4.0 | STEP Bible (www.STEPBible.org), based on work at Tyndale House Cambridge |
| [TAHOT_Job-Sng](https://raw.githubusercontent.com/STEPBible/STEPBible-Data/ae39711d7843b2902d54993e432de9c12d6a4b9a/Translators%20Amalgamated%20OT%2BNT/TAHOT%20Job-Sng%20-%20Translators%20Amalgamated%20Hebrew%20OT%20-%20STEPBible.org%20CC%20BY.txt) | CC-BY-4.0 | STEP Bible (www.STEPBible.org), based on work at Tyndale House Cambridge |
| [TAHOT_Jos-Est](https://raw.githubusercontent.com/STEPBible/STEPBible-Data/ae39711d7843b2902d54993e432de9c12d6a4b9a/Translators%20Amalgamated%20OT%2BNT/TAHOT%20Jos-Est%20-%20Translators%20Amalgamated%20Hebrew%20OT%20-%20STEPBible.org%20CC%20BY.txt) | CC-BY-4.0 | STEP Bible (www.STEPBible.org), based on work at Tyndale House Cambridge |
| [schlachter1951](https://raw.githubusercontent.com/akribos-biblestudy/akribos/b95299ec7f702f0898494100db0d28e83ec83a1a/data/bibles/GER_SCH1951_STRONG.xml) | Public-Domain | Schlachter 1951; Jens Grabner / Free Bible Software Group |
| [kautz](https://raw.githubusercontent.com/akribos-biblestudy/akribos/b95299ec7f702f0898494100db0d28e83ec83a1a/data/stronggreek_de_kautz.xml) | LicenseRef-Kautz-Akribos-Permission | Gerhard Kautz, Update 5/2026 |
| [hebrew-de](https://raw.githubusercontent.com/akribos-biblestudy/akribos/b95299ec7f702f0898494100db0d28e83ec83a1a/data/hebrewstrong.xml) | CC-BY-4.0 AND AGPL-3.0-only | Open Scriptures Hebrew Bible / Akribos deutsche maschinelle Ergänzungen |
| [greek-pd](https://raw.githubusercontent.com/akribos-biblestudy/akribos/b95299ec7f702f0898494100db0d28e83ec83a1a/data/strongsgreek.xml) | Public-Domain | James Strong; Michael Grier; Ulrik Sandborg-Petersen |
| [kjv1611](https://www.bibelkommentare.de/data/modules/bible_kjv1611_zefania.zip) | Public-Domain | King James 1611/1769 mit Strongs, bibelkommentare.de Revision 201909 |

## Abhängigkeit

Simplemma **2.0.0**, MIT, Adrien Barbaresi / Projektmitwirkende. Original-Wheel einschließlich Wörterbüchern und Lizenz: `vendor/simplemma-2.0.0-py3-none-any.whl`. Kopie des Lizenztexts: `licenses/simplemma-0.txt`. Exakte URL und Prüfsumme: `vendor/manifest.json`. Projekt: <https://github.com/adbar/simplemma>.

Simplemma wird ausschließlich zur deutschen Grundformbestimmung verwendet. Es erkennt keinen syntaktischen Kasus im ganzen Satz und bestätigt keine hebräische/griechische Wortbedeutung.

## Unveränderte und bearbeitete Bestandteile

`sources/originals/`: unveränderte Originalbytes. `history/edit/`: protokollierte Änderungen des deutschen Bibeltexts. `history/prepared/`: KJV-Arbeitskopie ohne defekte dekorative STYLE-Tags, mit erhaltenem Wortlaut, Strong-Tags und Notizen; das vollständige Original bleibt vorhanden. `history/build/`: Annotationen und aus den Quellen abgeleitete Analysedaten. Quellenrechte gelten auch für enthaltene geschützte Ableitungen.

Der historische griechische Strong-Lexikon-Snapshot ist zusätzlich archiviert. STEP liefert die annotierte griechische Prüfgrundlage. Die im Quellenregister genannten 14 Dateien bilden den vollständigen gebündelten Quellenbestand.

CC-BY-4.0-Lizenztext: Kopie aus dem SPDX-Lizenztextarchiv (https://raw.githubusercontent.com/spdx/license-list-data/main/text/CC-BY-4.0.txt), SHA-256 `d557539df68e771cc1eedcc91d13f70fca930e508d11eedcafa4b15db49e3744`; verbindlicher Lizenzlink <https://creativecommons.org/licenses/by/4.0/>.

Die Herkunftsnachweise enthalten teilweise die ursprünglichen englischen Projektbeschreibungen; sie werden nicht als eigene Akribos-Aussagen umgeschrieben.
