"""Pinned STEP TSV profiles and safe UTF-8 XML parsing."""
from __future__ import annotations
import csv
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from .common import canonical_ref,require,strongs

def tag(e):
    return e.tag.rsplit('}', 1)[-1] if isinstance(e.tag, str) else ''


def parse_xml(path):
    data = Path(path).read_bytes()
    # Avoid external entities/DTD and entity expansion. Encoding is intentionally UTF-8.
    require(not any(x in data.upper() for x in (b'<!DOCTYPE', b'<!ENTITY')),
            f'DTD/entity declarations are unsupported: {path}')
    require(b'\x00' not in data, 'Use UTF-8 XML; UTF-16 is not accepted')
    return ET.fromstring(data)


def import_reference_tsv(path, source_id, options):
    """Column mapping is explicit; supports STEP rows and canonical TSV. Fail on bad data rows."""
    columns = options['columns']
    groups = {}
    row_pattern = re.compile(options.get('row_pattern', r'^[1-3]?[A-Za-z]+\.\d+\.\d+'))
    edition = options.get('edition')
    with open(path, encoding='utf-8-sig', newline='') as f:
        for lineno, row in enumerate(csv.reader(f, delimiter='\t'), 1):
            if not row or not row_pattern.match(row[0]):
                continue
            def value(name, default=''):
                pos = columns.get(name)
                if pos is None:
                    return default
                require(pos < len(row), f'{path}:{lineno}: missing {name} column')
                return row[pos].strip()
            if edition:
                marks = re.split(r'[^A-Za-z0-9]+', value('editions'))
                if edition not in marks:
                    continue
            raw_ref = value('ref')
            m = re.match(r'^([1-3]?[A-Za-z]+\.\d+\.\d+)', raw_ref)
            require(m, f'{path}:{lineno}: invalid ref')
            ref = canonical_ref(m[1])
            group = groups.setdefault(ref, [])
            raw = value('strong')
            prefix = options.get('prefix', 'G')
            lemma = value('lemma')
            surface, morph = value('text'), value('morph')
            if options.get('profile') == 'tagnt':
                surface = surface.split(' (', 1)[0]
                lemma = lemma.split('=', 1)[0]
                morph = value('combined').split('=', 1)[-1]
            if options.get('profile') == 'tahot':
                # Explicitly exclude secondary textual witnesses; Qere remains labelled.
                witness = raw_ref.split('=', 1)[-1]
                if not witness.startswith(('L', 'Q')):
                    continue
            group.append({'id': f'{source_id}:{ref}:s{len(group)+1:03}', 'text': surface,
                          'strong': strongs(raw, prefix), 'lemma': lemma,
                          'strong_raw': raw, 'lexical_raw': value('combined').split('=', 1)[0], 'morph': morph,
                          'morph_scheme': options.get('morph_scheme', 'source-specific'),
                          'gloss': value('gloss'), 'origin_id': raw_ref,
                          'source': source_id, 'variants': value('variants'),
                          'edition': edition or options.get('witness', ''),
                          'word': raw_ref.split('#', 1)[1].split('=', 1)[0] if '#' in raw_ref else '',
                          'conjoined': value('conjoined'),
                          'alternate': strongs(value('alternate'), prefix),
                          'editions_raw': value('editions')})
    require(groups, f'No TSV data matched profile: {path}')
    return [{'ref': ref, 'tokens': toks} for ref, toks in groups.items()]


