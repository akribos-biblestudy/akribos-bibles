from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path

BOOKS = "Gen Exod Lev Num Deut Josh Judg Ruth 1Sam 2Sam 1Kgs 2Kgs 1Chr 2Chr Ezra Neh Esth Job Ps Prov Eccl Song Isa Jer Lam Ezek Dan Hos Joel Amos Obad Jonah Mic Nah Hab Zeph Hag Zech Mal Matt Mark Luke John Acts Rom 1Cor 2Cor Gal Eph Phil Col 1Thess 2Thess 1Tim 2Tim Titus Phlm Heb Jas 1Pet 2Pet 1John 2John 3John Jude Rev".split()
UBS = "Gen Exo Lev Num Deu Jos Jdg Rut 1Sa 2Sa 1Ki 2Ki 1Ch 2Ch Ezr Neh Est Job Psa Pro Ecc Sng Isa Jer Lam Ezk Dan Hos Jol Amo Oba Jon Mic Nam Hab Zep Hag Zec Mal Mat Mrk Luk Jhn Act Rom 1Co 2Co Gal Eph Php Col 1Th 2Th 1Ti 2Ti Tit Phm Heb Jas 1Pe 2Pe 1Jn 2Jn 3Jn Jud Rev".split()
ALIASES = dict(zip(UBS, BOOKS)) | {b: b for b in BOOKS}
WORD = re.compile(r"[^\W_]+(?:[’'\-][^\W_]+)*", re.UNICODE)
LICENSES = {"Public-Domain", "CC0-1.0", "CC-BY-4.0"}


class DataError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise DataError(message)


def canonical_ref(value):
    m = re.fullmatch(r"([1-3]?[A-Za-z]+)\.(\d+)\.(\d+)", value)
    require(m and m[1] in ALIASES, f"Unsupported verse reference: {value!r}")
    return f"{ALIASES[m[1]]}.{int(m[2])}.{int(m[3])}"


def ref_key(ref):
    book, chapter, verse = ref.split('.')
    return BOOKS.index(book), int(chapter), int(verse)


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read_json(path):
    with open(path, encoding='utf-8-sig') as f:
        return json.load(f)


def atomic_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def write_json(path, value):
    # The full Bible state contains millions of small fields; compact JSON avoids
    # hundreds of MB of indentation without changing its data model.
    if Path(path).name == 'state.json':
        atomic_text(path, json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n')
    else:
        atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def read_jsonl(path):
    with open(path, encoding='utf-8-sig') as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except ValueError as exc:
                    raise DataError(f'{path}:{n}: {exc}') from exc


def write_jsonl(path, values):
    atomic_text(path, ''.join(json.dumps(v, ensure_ascii=False, separators=(',', ':')) + '\n'
                            for v in values))


def norm(text):
    return unicodedata.normalize('NFC', text).casefold()


def tokenize(text):
    return [{'id': f'd{i:03}', 'text': m[0], 'start': m.start(), 'end': m.end()}
            for i, m in enumerate(WORD.finditer(text), 1)]


def strongs(raw, prefix=''):
    """Keep raw identifiers elsewhere; reduce extended identifiers only for display."""
    found = []
    # Zefania's "1254-853" denotes two entries, not a numeric range.
    for piece in re.split(r'[\s/\\+,;\-]+', raw or ''):
        piece = re.sub(r'^(?:strong|Strong|STRONG):', '', piece).strip('{}[]')
        # STEP marks repeated occurrences with _A, _B, ...; these are not
        # different dictionary entries. The importer retains the full raw ID.
        piece = re.sub(r'_[A-Za-z]+$', '', piece)
        m = re.fullmatch(r'([HG]?)(\d+)([A-Za-z]*)', piece)
        if m and (m[1] or prefix):
            key = (m[1] or prefix) + str(int(m[2]))
            if key not in found:
                found.append(key)
    return found


def project_paths(config_file):
    cfg_path = Path(config_file).resolve()
    cfg = read_json(cfg_path)
    root = (cfg_path.parent / cfg.get('root', '..')).resolve()
    return root, cfg


def local_path(root, value):
    path = (root / value).resolve()
    require(path.is_relative_to(root), f'Path escapes project: {value}')
    return path
