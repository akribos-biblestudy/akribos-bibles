# Versionshistorie

| Git-Tag | Bibelstand |
|---|---|
| `v1.1` | Ursprüngliche Sprach-/Strong-Fassung, noch mit fehlenden HERR-Artikeln |
| `v1.2` | Artikel-/Kasuskorrektur, unter anderem 1. Samuel 17,37 und Kapitel 20 |

Beide Versionen verwenden einheitliche Exportmetadaten: ursprüngliche Bibelausgabe, Akribos-Ausgabenummer, Kurztitel und Rechtehinweis. Der Bibelinhalt einschließlich Strong-Zuordnungen und Originalnotizen entspricht jeweils dem zugehörigen Bearbeitungsstand. Die englische KJV wird separat syntaxrepariert exportiert.

## Feste Ergebnisdateien

- `releases/akribos.elb.xml`
- `releases/akribos.lut.xml`
- `releases/kjv1611.xml`

Die zugehörigen `.build.json` nennen Version bzw. Quellstand, SHA-256 und den vollständigen Verarbeitungslauf. Neue Builds überschreiben diese festen Pfade; Git bewahrt die früheren Stände. Das [Änderungsprotokoll](../CHANGELOG.md) beschreibt jede Ausgabe.

## Stände vergleichen und nachbauen

```bash
git log --oneline --decorate
git diff v1.1 v1.2 -- akribos/modernize.py releases/akribos.elb.xml
git worktree add --detach .local/worktrees/v1.1 v1.1
cd .local/worktrees/v1.1
python scripts/setup.py
python bible.py build --edition all --rebuild
python scripts/verify_repository.py
```

`--version` setzt die Ausgabenummer, lädt aber keinen historischen Code. Für einen früheren Bibelstand den passenden Git-Tag verwenden.

## Neue Ausgabe

1. Regeln/Skripte ändern und `VERSION` in `akribos/project.py` erhöhen.
2. Änderungen in `CHANGELOG.md` beschreiben.
3. Tests und vollständigen Aufbau ausführen:

   ```bash
   python -m unittest discover -s tests -v
   python bible.py build --edition all --rebuild
   python scripts/verify_repository.py
   ```

4. Skripte, Regeln, neue Laufarchive und Ergebnisse gemeinsam committen; anschließend den Versions-Tag anlegen. Bestehende Versions-Tags bleiben auf ihrem Commit.

## Verarbeitungsläufe

`history/` enthält die vollständigen Läufe der dokumentierten Versionen. Jede `manifest.json` erfasst Eingaben, Code-Prüfsummen und sämtliche Ergebnisdateien. Der passende Implementierungsstand liegt unter `history/implementations/`. `--rebuild` berechnet einen Lauf erneut und prüft Bytegleichheit. Private Referenzen und vollständige externe Wortvergleiche gehören in `.local/`.
