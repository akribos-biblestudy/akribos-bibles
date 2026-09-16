"""Apply only fixed, reviewed corrections bound to complete target/source hashes."""
from __future__ import annotations
import copy
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from .common import BOOKS, digest, require
from .confirm import GRAMMAR, _remove_preserving_tail
from .importers import tag

CATALOG_PATH = Path(__file__).resolve().parents[1] / 'rules/editorial-strong-corrections.json'
METHOD = 'fixed-position-source-bound-editorial-corrections-v1'
PROVENANCE = 'data-akribos-editorial'
SOURCE_FIELDS = ('origin_id', 'strong', 'morph', 'text', 'lemma', 'edition')
NT_FILES = frozenset({'sources/originals/TAGNT_Mat-Jhn.tsv', 'sources/originals/TAGNT_Act-Rev.tsv'})
OT_FILES = frozenset({'sources/originals/TAHOT_Gen-Deu.tsv'})
REASONS = frozenset({
    'curated-position-and-source-proof', 'wrong-target-edition', 'missing-target-verse',
    'target-text-hash-mismatch', 'target-token-mismatch', 'target-span-mismatch',
    'target-strong-set-mismatch', 'target-span-hash-mismatch', 'ambiguous-target-hint',
    'source-file-identity-mismatch', 'source-projection-mismatch',
})


def text_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def span_hash(element):
    clone = copy.deepcopy(element); clone.tail = None
    return text_hash(ET.tostring(clone, encoding='unicode'))


def load_catalog():
    catalog = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
    require(catalog.get('schema') == 1 and catalog.get('method') == METHOD, 'Invalid editorial catalog')
    require(set(catalog['source_files']) == NT_FILES | OT_FILES, 'Invalid editorial source files')
    ids = set()
    for rule in catalog['rules']:
        require(rule['id'] not in ids, 'Duplicate editorial rule ID'); ids.add(rule['id'])
        require(rule['id'] == f"{rule['bible_id']}:{rule['ref']}:{rule['token']}", 'Invalid editorial rule ID')
        require(rule['bible_id'] in {'akribos.elb','akribos.lut'} and rule['nt_edition'] in {'WH','TR'},
                'Invalid editorial Bible or edition')
        require((len(rule['before_strong']) == 1 and rule['after_strong'] in ([], ['G3588'])) or
                (rule['id']=='akribos.lut:Rev.21.16:d022' and
                 rule['before_strong']==['G1909','G2563'] and rule['after_strong']==['G2563']),
                'Editorial correction exceeds the reviewed operation scope')
        require(rule['action'] == ('replace-strong' if rule['after_strong'] else 'unwrap-strong-span'),
                'Editorial operation and replacement differ')
        require(rule['annotation_origin'] in {'uncertain','inherited'}, 'Unknown editorial annotation origin')
        require(rule['reviewed_input_version'] in {'1.2','1.4'}, 'Unknown editorial reviewed input version')
        is_ot = BOOKS.index(rule['ref'].split('.')[0]) < 39
        require(set(rule['source_files']) == (OT_FILES if is_ot else NT_FILES),
                'Editorial rule uses unrelated source files')
        require(all(code.startswith('H' if is_ot else 'G') for code in rule['before_strong']) and
                all(token['edition'] == ('L/Q' if is_ot else rule['nt_edition'])
                    for token in rule['source_projection']), 'Editorial source witness differs')
        require(digest(rule['source_projection']) == rule['binding']['source_projection_sha256'],
                'Editorial source projection hash differs')
    return catalog


def decide(rule, view, source, *, nt_edition, source_metadata, source_files, hint_ids, rule_version):
    """Return a complete closed audit row plus the exact span/hint to change."""
    projection = [{key: token.get(key) for key in SOURCE_FIELDS} for token in source]
    required_files = {path:source_files[path] for path in rule['source_files']}
    actual_files = {row['path']:row['sha256'] for row in (source_metadata or {}).get('files', [])}
    proof = {'rule_sha256':digest(rule),
             'source_projection_sha256':digest(projection),
             'verse_text_sha256':text_hash(view.text) if view else None,
             'source_file_hashes':{name:actual_files.get(name) for name in required_files}}
    token = next((t for t in view.tokens if t['id'] == rule['token']), None) if view else None
    spans = ([span for span in view.spans if span.start < token['end'] and span.end > token['start']]
             if token else [])
    span = spans[0] if len(spans) == 1 else None
    before = sorted({code for item in spans for code in item.codes})
    row = {'kind':'editorial-correction','rule_id':rule['id'],'bible_id':rule['bible_id'],
           'nt_edition':nt_edition,'ref':rule['ref'],'target_token':rule['token'],
           'target_text':token['text'] if token else None,
           'target_start':token['start'] if token else None,'target_end':token['end'] if token else None,
           'before_strong':before,'after_strong':before,'proposed_strong':rule['after_strong'],
           'annotation_origin':rule['annotation_origin'],
           'reviewed_input_version':rule['reviewed_input_version'],'hint_id':None,
           'status':'not-applicable','action':'retain','reason':None,
           'rule_version':rule_version,'proof':proof}
    reason = None; hint = None
    if nt_edition != rule['nt_edition']:reason = 'wrong-target-edition'
    elif view is None:reason = 'missing-target-verse'
    elif proof['verse_text_sha256'] != rule['binding']['verse_text_sha256']:reason = 'target-text-hash-mismatch'
    elif token is None or (token['text'],token['start'],token['end']) != (
            rule['target_word'],rule['target_start'],rule['target_end']):reason = 'target-token-mismatch'
    elif (span is None or not span.valid or span.start != token['start'] or span.end != token['end']
          or any(tag(node) in GRAMMAR for node in list(span.element.iter())[1:])):reason = 'target-span-mismatch'
    elif list(span.codes) != rule['before_strong']:reason = 'target-strong-set-mismatch'
    elif span_hash(span.element) != rule['binding']['span_xml_without_tail_sha256']:reason = 'target-span-hash-mismatch'
    else:
        matches = [candidate for candidate in view.hints if view.hint_span(candidate)[0] is span]
        if len(matches) > 1:reason = 'ambiguous-target-hint'
        elif proof['source_file_hashes'] != required_files:reason = 'source-file-identity-mismatch'
        elif proof['source_projection_sha256'] != rule['binding']['source_projection_sha256']:reason = 'source-projection-mismatch'
        else:hint = matches[0] if matches else None
    if reason:
        row['reason'] = reason
        return row, None, None
    row.update(status='applied',action=rule['action'],reason='curated-position-and-source-proof',
               after_strong=rule['after_strong'],hint_id=hint_ids.get(hint))
    return row, span.element, hint


def validate_audit(row, rule_version):
    fields = {'kind','rule_id','bible_id','nt_edition','ref','target_token','target_text','target_start',
              'target_end','before_strong','after_strong','proposed_strong','annotation_origin',
              'reviewed_input_version','hint_id',
              'status','action','reason','rule_version','proof'}
    require(type(row) is dict and set(row) == fields, 'Unexpected public editorial audit fields')
    require(row['kind'] == 'editorial-correction' and row['rule_version'] == rule_version,
            'Unknown editorial audit version')
    for key in ('rule_id','bible_id','nt_edition','ref','target_token','annotation_origin','status','action'):
        require(type(row[key]) is str, 'Invalid editorial audit identifier')
    require(row['bible_id'] in {'akribos.elb','akribos.lut'} and row['nt_edition'] in {'WH','TR'} and
            re.fullmatch(r'[1-3]?[A-Za-z]+\.\d+\.\d+',row['ref']) and
            re.fullmatch(r'd\d{3,}',row['target_token']) and
            row['rule_id'] == f"{row['bible_id']}:{row['ref']}:{row['target_token']}" and
            row['annotation_origin'] in {'uncertain','inherited'}, 'Invalid editorial audit location')
    require(type(row['reviewed_input_version']) is str and row['reviewed_input_version'] in {'1.2','1.4'},
            'Invalid editorial reviewed input version')
    require(row['hint_id'] is None or (type(row['hint_id']) is str and
            re.fullmatch(r'u\d{6,}',row['hint_id'])), 'Invalid editorial uncertainty identifier')
    require(row['target_text'] is None or type(row['target_text']) is str, 'Invalid editorial target text')
    require((row['target_text'] is None and row['target_start'] is None and row['target_end'] is None) or
            (type(row['target_start']) is int and type(row['target_end']) is int and
             0 <= row['target_start'] < row['target_end']), 'Invalid editorial target positions')
    for key in ('before_strong','after_strong','proposed_strong'):
        require(type(row[key]) is list and all(type(code) is str and re.fullmatch(r'[HG][1-9]\d*',code)
                for code in row[key]), 'Invalid editorial Strong values')
    require(row['proposed_strong'] in ([],['G3588']) or
            (row['rule_id']=='akribos.lut:Rev.21.16:d022' and row['proposed_strong']==['G2563']),
            'Invalid editorial replacement scope')
    require(type(row['reason']) is str and row['reason'] in REASONS, 'Invalid editorial audit reason')
    require((row['status']=='applied' and row['action'] in {'replace-strong','unwrap-strong-span'}
             and row['reason']=='curated-position-and-source-proof') or
            (row['status']=='not-applicable' and row['action']=='retain'
             and row['reason']!='curated-position-and-source-proof'), 'Invalid editorial audit action')
    require((row['status']=='applied' and row['after_strong']==row['proposed_strong']) or
            (row['status']=='not-applicable' and row['after_strong']==row['before_strong']
             and row['hint_id'] is None), 'Invalid editorial Strong delta')
    proof = row['proof']
    require(type(proof) is dict and set(proof) == {'rule_sha256','source_projection_sha256',
            'verse_text_sha256','source_file_hashes'}, 'Unexpected public editorial proof fields')
    for key in ('rule_sha256','source_projection_sha256','verse_text_sha256'):
        require((key=='verse_text_sha256' and proof[key] is None) or
                (type(proof[key]) is str and re.fullmatch(r'[a-f0-9]{64}',proof[key])), 'Invalid editorial proof hash')
    require(row['ref'].split('.')[0] in BOOKS, 'Unknown editorial target book')
    expected_files = OT_FILES if BOOKS.index(row['ref'].split('.')[0]) < 39 else NT_FILES
    require(type(proof['source_file_hashes']) is dict and set(proof['source_file_hashes']) == expected_files and
            all(value is None or (type(value) is str and re.fullmatch(r'[a-f0-9]{64}',value))
                for value in proof['source_file_hashes'].values()), 'Invalid editorial source-file proof')


def apply(row, span, hint, parents, rule_version):
    """Apply the already proved edit while preserving all mixed-content text."""
    require(row['status']=='applied' and span is not None, 'Unapproved editorial mutation')
    if hint is not None:_remove_preserving_tail(parents[hint], hint)
    if row['action']=='replace-strong':
        span.set('str',' '.join(code[1:] for code in row['after_strong']))
        span.set('data-akribos-linguistic',rule_version)
        span.set(PROVENANCE,row['rule_id'])
    else:
        parent = parents[span]; index = list(parent).index(span)
        previous = parent[index-1] if index else None
        def append_text(text):
            if previous is None:parent.text = (parent.text or '') + (text or '')
            else:previous.tail = (previous.tail or '') + (text or '')
        append_text(span.text)
        for child in list(span):
            span.remove(child);parent.insert(index,child);index+=1;previous=child
        append_text(span.tail);parent.remove(span)
