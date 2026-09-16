"""Conservative proper-name rule: confirm an existing name tag; never assign a code.

Explicit German name family + exact classical Strong ID + unique STEP occurrence
+ proper-name grammar/lexeme + precise independent reference confirmation.
The decision core never mutates XML. Its loader verifies the explicit catalog
and the hashes of its local original lexica; it downloads or publishes nothing.
"""
from __future__ import annotations
import re
import hashlib
import json
from pathlib import Path
from .common import file_hash, require
import unicodedata
from .linguistic_rules import _source_shape_problem, selected_verse_has_movement


def normal_name(value):
    return unicodedata.normalize('NFC', value).casefold()


def lexical_letters(value):
    """Compare documented lexical forms; remove pointing/accents, never letters."""
    return ''.join(c for c in unicodedata.normalize('NFD', value)
                   if unicodedata.category(c).startswith('L')).casefold()


def proper_name_decision(ref, tokens, index, source, catalog, *, nt_edition,
                         reference_statuses, verse_guard=None):
    def retain(reason):
        return {'status': 'review', 'reason': reason}

    token = tokens[index]
    if verse_guard:
        return retain('prior-verse-alignment-guard')
    if not source:
        return retain('missing-source-verse')
    is_nt = any(code.startswith('G') for code in token.get('strong', []))
    problem = _source_shape_problem(source, nt_edition, is_nt, ref)
    if problem:
        return retain(problem)
    if selected_verse_has_movement(source):
        return retain('source-order-or-versification-variation')
    own_codes = {code for t in tokens for code in t.get('strong', [])}
    source_codes = {code for t in source for code in t.get('strong', [])}
    if len(own_codes) >= 3 and len(own_codes & source_codes) / len(own_codes) < .65:
        return retain('verse-inventory-mismatch')
    codes = token.get('strong', [])
    if (len(codes) != 1 or not re.fullmatch(r'[GH][1-9][0-9]*', codes[0])
            or not token.get('uncertain') or token.get('blocked')
            or token.get('phrase_tokens', 1) != 1):
        return retain('not-single-existing-uncertain-name-span')
    code = codes[0]
    entry = catalog.get(code)
    if entry is None:
        return retain('name-code-outside-explicit-catalog')
    forms = {normal_name(form) for form in entry['german_forms']}
    word = token.get('text', '')
    if not word[:1].isupper() or normal_name(word) not in forms:
        return retain('german-name-form-not-confirmed')
    # Count even untagged names and codes hidden inside multi-code spans.
    if sum(normal_name(t.get('text', '')) in forms for t in tokens) != 1:
        return retain('repeated-german-name-family')
    if sum(code in t.get('strong', []) for t in tokens) != 1:
        return retain('repeated-target-code-including-composite-spans')
    occurrences = [t for t in source if code in t.get('strong', [])]
    if len(occurrences) != 1:
        return retain('source-name-occurrence-not-unique')
    occurrence = occurrences[0]
    if occurrence.get('strong') != [code]:
        return retain('source-name-is-composite')
    morph = occurrence.get('morph', '')
    if code.startswith('G'):
        if not re.fullmatch(r'N-[NGDAV]S[MF]-P', morph):
            return retain('not-greek-personal-proper-name-morphology')
        # STEP's complete lemma field must match a reviewed entry verbatim after
        # harmless NFC normalization; arbitrary extra lemma alternatives fail.
        actual = unicodedata.normalize('NFC', occurrence.get('lemma', ''))
        if actual not in {unicodedata.normalize('NFC', s) for s in entry['source_lemmas']}:
            return retain('source-name-lemma-not-confirmed')
    else:
        if morph not in entry['source_morphs']:
            return retain('not-hebrew-proper-name-morphology')
        if lexical_letters(occurrence.get('text', '')) not in entry['hebrew_consonants']:
            return retain('hebrew-name-surface-not-confirmed')
        # Prefixes/maqaf/slashes are not silently erased by the lexical comparison.
        if any(c in occurrence.get('text', '') for c in '/־-'):
            return retain('hebrew-compound-surface')
    statuses = {label: value for label, value in reference_statuses.items()
                if label in {'elb-bk', 'elb-csv'}}
    if 'confirmed' not in statuses.values():
        return retain('no-independent-word-level-name-corroboration')
    return {'status': 'accepted', 'reason': 'unique-proper-name-with-independent-reference',
            'proof': {'rule': 'unique-proper-name-with-independent-reference',
                      'source_token': occurrence['origin_id'], 'strong': code,
                      'morph': morph, 'catalog_entry_sha256': entry['evidence_sha256']},
            'references': statuses}


CATALOG_PATH = Path(__file__).resolve().parents[1] / 'rules/proper-name-catalog.json'
SOURCES_PATH = CATALOG_PATH.with_name('proper-name-sources.json')
RULE = 'unique-proper-name-with-independent-reference'


def load_name_catalog():
    """Load checked, explicit names and bind their evidence to local originals."""
    catalog = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
    sources = json.loads(SOURCES_PATH.read_text(encoding='utf-8'))
    root = CATALOG_PATH.parents[1]
    require(len(catalog) == sources['catalog_entries'], 'Proper-name catalog count differs')
    for name, sha in sources['lexica'].items():
        path = (root / name).resolve()
        require(path.is_relative_to(root) and file_hash(path) == sha, 'Proper-name lexicon source differs')
    for code, entry in catalog.items():
        require(code == entry['strong'] and code not in {'H136','H3068'}, 'Invalid proper-name catalog code')
        encoded = json.dumps(entry['evidence'], ensure_ascii=False, sort_keys=True).encode()
        require(hashlib.sha256(encoded).hexdigest() == entry['evidence_sha256'],
                'Proper-name entry evidence hash differs')
    return catalog
