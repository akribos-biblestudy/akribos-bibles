"""Read the supplied Kautz XML without changing it; use only primary sense headings.

The downstream index is a local analytical aid, not a relicensed edition of Kautz.
Word-family appendices and cross-reference numbers must never become meanings of
the enclosing entry. Full original XML stays separately available for review.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from .common import require, file_hash, digest, tokenize, norm
from .importers import parse_xml

ROMAN = re.compile(r'^\s*([IVX]+)[.)]+\s*(.+)$')
FAMILY = re.compile(r'\bWortfamilie\b', re.I)


def definition_lines(element):
    """Keep printed text only: abbr tooltips, verse text and Strong refs aren't glosses."""
    def walk(e):
        out = [e.text or '']
        for child in e:
            if child.tag == 'br':
                out.append('\n')
            elif child.tag not in {'verseref', 'strongsref'}:
                out.append(walk(child))
            out.append(child.tail or '')
        return ''.join(out)
    return walk(element).splitlines() if element is not None else []


def heading_forms(heading, noun=False):
    # Headings only. A whole definition is not a bag of interchangeable glosses.
    heading = re.sub(r'\bd\.\s*', '', heading)
    heading = re.sub(r'\b(?:bzw\.|od\.)\s*', ' oder ', heading)
    variants = [heading]
    match = re.search(r'\(([A-Za-zÄÖÜäöüß]+)\)', heading)
    if match:
        variants = [heading[:match.start()] + middle + heading[match.end():]
                    for middle in ('', match[1])]
    forms = set()
    for value in variants:
        for phrase in re.split(r'\s+(?:oder|bzw\.)\s+|[,;/]', value):
            phrase = phrase.strip(' .…!')
            if noun:
                phrase = re.sub(r'^(?:der|die|das|ein|eine)\s+', '', phrase)
            # Explanatory headings and unexpanded grammatical placeholders stay
            # in the original entry; they are not silently reduced to keywords.
            if re.search(r'[:?()\d]|\b(?:jmd|etw|usw|vgl|Inf|Pass|Modalpartikel)\b', phrase):
                continue
            if not re.fullmatch(r'[A-Za-zÄÖÜäöüß’\- ]+', phrase):
                continue
            words = phrase.split()
            if 1 <= len(words) <= 5 and all(len(w) > 1 for w in words):
                forms.add(' '.join(words))
    return sorted(forms)


def load_kautz(path, source):
    require(file_hash(path) == source['sha256'], 'Kautz source hash differs from the registered snapshot')
    root = parse_xml(path)
    require(root.tag == 'strongsdictionary', 'Expected Kautz strongsdictionary XML')
    original = path.read_text(encoding='utf-8-sig')
    raw_entries = {int(m[1]): m[0] for m in re.finditer(
        r'<entry\s+strongs=["\'](\d+)["\'][^>]*>.*?</entry>', original, re.S)}
    entries, forms, stats = {}, [], Counter()
    seen = set()
    for element in root.iter('entry'):
        number = int(element.get('strongs', '0'))
        require(number not in seen, f'Duplicate Kautz entry: {number}')
        seen.add(number)
        stats['all_entries'] += 1
        if not 1 <= number <= 5624:
            stats['appendix_entries_excluded_from_alignment'] += 1
            continue
        code = f'G{number}'
        require(number in raw_entries, f'Unable to preserve original entry XML: {code}')
        greek = element.find('greek')
        derivation = ''.join(element.find('strongs_derivation').itertext()) if element.find('strongs_derivation') is not None else ''
        noun = 'Subst.' in derivation
        heads = []
        for line in definition_lines(element.find('strongs_def')):
            if FAMILY.search(line):
                stats['word_family_sections_excluded'] += 1
                break
            match = ROMAN.match(line)
            if not match:
                continue
            label, heading = match.groups()
            heads.append({'sense': label, 'text': heading})
            for phrase in heading_forms(heading, noun):
                forms.append({'de': phrase, 'strong': code, 'origin': 'kautz',
                              'sense': label, 'entry_sha256': digest(raw_entries[number])})
        entries[code] = {'strong': code, 'lemma': greek.get('unicode', '') if greek is not None else '',
                         'headings': heads, 'xml': raw_entries[number],
                         'entry_sha256': digest(raw_entries[number])}
    # Multiple headings can contain the same phrase; do not count this as ambiguity.
    unique = {(norm(f['de']), f['strong']): f for f in forms}
    forms = sorted(unique.values(), key=lambda f: (int(f['strong'][1:]), norm(f['de'])))
    stats.update(classical_entries=len(entries), entries_with_usable_glosses=len({f['strong'] for f in forms}),
                 primary_heading_forms=len(forms))
    return {'source': source, 'copyright': root.findtext('prologue', ''),
            'usage_notes_xml': ET.tostring(root.find('usage_notes'), encoding='unicode')
                               if root.find('usage_notes') is not None else '',
            'entries': entries, 'forms': forms, 'statistics': dict(stats)}


def add_review_context(package, lexicon):
    """Only relevant entries, unchanged; preserve their internal bold/italic and hierarchy."""
    codes = {s for v in package['verses'] for t in v['source_tokens'] for s in t['strong']}
    package['lexicon_context'] = {
        'source': lexicon['source'], 'copyright': lexicon['copyright'],
        'usage_notes_xml': lexicon['usage_notes_xml'],
        'entries': {c: {'entry_sha256': lexicon['entries'][c]['entry_sha256'],
                         'xml': lexicon['entries'][c]['xml']}
                    for c in sorted(codes) if c in lexicon['entries']},
        'notice': 'Unveränderte Quellauszüge zur lokalen Prüfung; keine CC-BY-Freigabe dieser Lexikontexte.'}
    return package
