# Eine weitere Bibel anreichern

## Lokaler eigener Text: Zefania oder OSIS

1. Datei unter `.local/inputs/` ablegen. Bei einer lizenzierten Schlachter2000 beispielsweise `.local/inputs/schlachter2000.osis.xml`. Die Erlaubnis zur eigenen Nutzung ist nicht automatisch eine Erlaubnis zur Veröffentlichung einer bearbeiteten Ausgabe.
2. Den folgenden Befehl mit passender Textgrundlage ausführen:

```bash
python bible.py build --edition custom \
  --input .local/inputs/schlachter2000.osis.xml \
  --id akribos.schlachter --profile none --nt-edition TR --version 0.1
```

`--profile none` erhält den bereits modernen Wortlaut. `generic` wendet die explizite Rechtschreibliste und Weib/Frau-Regeln an, `elb` zusätzlich Jehova-Regeln, `lut` zusätzlich die HErr-Schreibweise. Eine vorhandene Strong-Zuordnung bleibt erhalten; fehlende wird aus demselben freien Quellenbestand wie bei ELB/Luther ergänzt.

Ausgabe: `.local/custom-releases/0.1/akribos.schlachter.xml`. `0.1` ist hier eine eigene Ausgabenummer; der Aufbau endet bei Stufe 04 und verwendet den aktuellen Code. Alle Zwischenstände, Originalnotizen und Protokolle liegen unter `.local/custom-history/`. Die Originaldatei bleibt unverändert. Die Metadaten behaupten bei eigenen Texten **keine Gemeinfreiheit**.

3. Änderungen und Kandidaten in den CSV-/JSONL-Berichten prüfen. Für den anschließenden Vergleich kann `--input` auf diese neue Datei zeigen. Der Aufbau liest niemals Dateien aus `.local/references/` als zusätzliche Strong-Spender.

## Unterstützte XML-Profile

Zefania: `XMLBIBLE / BIBLEBOOK / CHAPTER / VERS`, Strong-Tags `gr` und `GRAM`; nicht-namespaced Standardprofil. Buchnummern 1–66, eindeutige Vers-IDs. Vers-0-Überschriften werden zu `CAPTION`, nicht entfernt. `NOTE`, `STYLE`, XREF und vorhandene Attribute werden bei einem Zefania-Import erhalten.

OSIS: Verse als Container mit `osisID="Gen.1.1"` oder Verse als `sID`/`eID`-Meilensteine. Namespace wird erkannt. `<w lemma="strong:H7225">` wird als `<gr str="7225">` ausgegeben; vorhandene Morphologie bleibt als `data-osis-morph` erhalten. Inline-Notizen werden `NOTE type="x-studynote"`; deren Inhalt, innere Markierung und Quellattribute werden in NOTE/STYLE und `data-osis` erhalten.

Das ist ein **definiertes Importprofil, keine vollständige verlustfreie Umsetzung aller denkbaren OSIS-Funktionen**. Nicht unterstützte Versbereiche, gemischte Versprofile oder Notizen außerhalb unterstützter Verse führen zu einem Fehler statt zu stillem Notizverlust. Für abweichende Kanons, separate OSIS-Notizgruppen oder komplexe Versaufteilungen wird ein eigenes Importprofil benötigt. Erst anhand einer konkreten Schlachter2000-Datei lässt sich bestätigen, welches Profil passt.

XML mit DTD oder Entity-Deklarationen wird aus Sicherheits- und Reproduzierbarkeitsgründen abgelehnt. Die interne DTD des zusätzlich archivierten historischen griechischen Lexikons ist davon getrennt: diese Archivdatei wird nicht vom allgemeinen Bibelimport geöffnet. Die mechanische KJV-Reparatur ist ausschließlich für den per SHA-256 registrierten KJV-Snapshot aktiviert; sie ist kein allgemeiner stiller Reparaturmodus für neue Dateien.

## Neue freie Quelle im öffentlichen Repo registrieren

Die Standardbefehle können jede passende lokale Datei anreichern. Um zusätzlich eine **neue öffentliche Ausgangsbibel oder einen neuen Strong-Spender** als regulären Projektbestand aufzunehmen:

1. Einen unveränderlichen Original-Snapshot in `sources/originals/` ablegen.
2. In `config/sources.lock.json` ID, relativen Pfad, Download-URL, SHA-256 der entpackten Datei, Format, tatsächliche Lizenz, Zuschreibung und Nachweisumfang ergänzen. Eine bloß lesbare Webseite ist kein Lizenznachweis.
3. Nachweis und vollständige Lizenztexte in `sources/evidence/` bzw. `licenses/` aufnehmen; `LICENSE-DATA.md` und `THIRD-PARTY-NOTICES.md` ergänzen.
4. Für einen zusätzlichen Spender die explizite Liste `donor_paths` in `akribos/pipeline.py` erweitern und das passende Sprachprofil festlegen. Es gibt bewusst keine automatische Übernahme aller XML-Dateien aus irgendeinem Verzeichnis.
5. Bei einer zusätzlichen offiziellen Ausgabe die Editionszuordnung im CLI und in `pipeline.edit` ergänzen, eine neue stabile ID vergeben und die Release-/Integritätsprüfungen erweitern. Die beiden vorhandenen IDs bleiben unverändert.
6. Neu bauen, Herkunftsprotokolle prüfen und Originale, Code, Lizenzen und den neuen Lauf gemeinsam committen. Geänderte Quellen erzeugen neue Lauf-IDs; alte Original-Snapshots unter einem neuen Dateinamen behalten.

## Regeln gezielt verbessern

Rechtschreibregeln stehen in `rules/orthography.json`. Für grammatische Einzelfälle verwenden die Befehle eine positionsgesicherte JSON-Ausnahmedatei:

```json
{
  "Gen.1.1": [
    {"start": 0, "end": 9, "before": "Im Anfang", "after": "Im Anfang", "reason": "Beispiel für das Ausnahmeformat; keine sachliche Änderung"}
  ]
}
```

Die Positionen beziehen sich auf den kanonischen Verswortlaut ohne Notizen **vor** der Sprachbearbeitung. Jede echte Änderung muss einen nachvollziehbaren Grund tragen. Falsche Ausgangspositionen oder abweichender Wortlaut lassen den Lauf abbrechen.

```bash
python bible.py build --edition elb --overrides rules/meine-ausnahmen.json \
  --elb-bk .local/references/elb-bk.xml \
  --elb-csv .local/references/elb-csv.xml
```

Der Befehl verwendet die aktuelle Standardversion und die beiden privaten Referenzen gemäß [Aufbauanleitung](REFERENCE-CONFIRMATION.md). `--version` bezeichnet die Ausgabe, lädt jedoch keinen früheren Programmstand. Historische Versionen werden vom passenden Git-Tag gebaut, siehe [Versionshistorie](HISTORY.md).

Diese Ausnahmen betreffen die Sprache. Strong-Korrekturen müssen als geprüfte freie Evidenz in den Zuordnungsregeln oder Quellen dokumentiert werden. Ein automatischer Import geschützter Vergleichspatches ist nicht vorgesehen.
