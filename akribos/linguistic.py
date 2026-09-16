"""Reproducible post-confirmation linguistic review with explicit occurrence proofs.

Only designated Akribos uncertainty notes may disappear. Existing Strong numbers,
Bible text, original notes, and other annotations are immutable. New article tags
need both German syntax evidence and a linked Greek article occurrence. Accepted
results carry provenance and cannot become new proof anchors in a repeated run.
"""
from __future__ import annotations

import copy
import csv
import gzip
import importlib
import hashlib
import json
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from .common import BOOKS, atomic_text, canonical_ref, digest, file_hash, require, strongs, write_json
from .confirm import (HINT, GRAMMAR, _Verse, _preserved_notes, _remove_preserving_tail,
                      forced_alignment, _verse_index)
from .importers import import_reference_tsv, parse_xml, tag
from .linguistic_rules import (ARTICLES, atomic_bridge_proof, classify_uncertain,
                              linked_article_proof, selected_verse_has_movement, _source_shape_problem)
from .linguistic_names import (RULE as NAME_RULE, CATALOG_PATH, SOURCES_PATH,
                               load_name_catalog, proper_name_decision)
from .xmlio import EXCLUDED, annotate, plain, slots, write_xml, zef_verses

METHOD = 'source-linked-linguistic-review-v1'
RULES_VERSION = '1.4.0'
PROVENANCE = 'data-akribos-linguistic'
SOURCE_PROFILE = 'step-occurrence-links-and-atomic-morphology-v1'

# Public audit fields are deliberately closed. These are result codes, never
# messages supplied by a private reference or a caller's local file paths.
ARTICLE_REFERENCE_STATUSES = frozenset({
    'confirmed', 'missing-reference-verse', 'uncertain-reference-verse',
    'word-not-aligned', 'ambiguous-word-alignment', 'noncontiguous-reference-span',
    'reference-placeholder-in-span', 'invalid-reference-strong-set',
    'reference-annotation-crosses-span', 'incomplete-reference-word-span',
    'missing-reference-strong-tags', 'different-strong-set',
})
ARTICLE_RULE = 'greek-article-linked-noun-with-left-anchor'
ACCEPTED_RULES = frozenset({ARTICLE_RULE, NAME_RULE, 'atomic-function-word-between-confirmed-anchors',
    'hebrew-atomic-noun-between-confirmed-anchors', 'hebrew-divine-name-between-confirmed-anchors'})
REVIEW_REASONS = frozenset({
    'structured-uncertainty-note', 'no-preceding-strong-span',
    'text-between-assignment-and-hint', 'target-placeholder-in-span',
    'invalid-target-strong-set', 'nested-target-strong-spans', 'incomplete-target-word-span',
    'duplicate-or-missing-source-occurrence-id', 'invalid-source-verse-reference',
    'source-occurrence-belongs-to-other-verse', 'wrong-selected-nt-edition',
    'unsupported-hebrew-witness', 'verse-inventory-mismatch', 'prior-verse-inventory-mismatch',
    'already-reviewed-linguistic-annotation', 'multiword-target-span',
    'multiple-target-strong-codes', 'unsupported-target-annotation',
    'no-independent-article-corroboration', 'source-occurrence-already-used',
    'outside-supported-verse-text', 'verse-reference-mismatch', 'missing-reference-verse',
    'source-order-or-versification-variation', 'alternate-strong-encoding', 'code-absent-in-selected-source',
    'multi-code-translation-span', 'repeated-source-lexeme',
    'shared-german-translation-span', 'alignment-needs-semantic-evidence',
    'prior-verse-alignment-guard', 'missing-source-verse',
    'not-single-existing-uncertain-name-span', 'name-code-outside-explicit-catalog',
    'german-name-form-not-confirmed', 'repeated-german-name-family',
    'repeated-target-code-including-composite-spans', 'source-name-occurrence-not-unique',
    'source-name-is-composite', 'not-greek-personal-proper-name-morphology',
    'source-name-lemma-not-confirmed', 'not-hebrew-proper-name-morphology',
    'hebrew-name-surface-not-confirmed', 'hebrew-compound-surface',
    'no-independent-word-level-name-corroboration',
})


def _validate_audit_schema(row, reference_labels):
    """Reject extra/nested fields and free-text result codes before publication."""
    require(isinstance(row, dict), 'Linguistic audit row must be an object')
    kind = row.get('kind'); status = row.get('status'); action = row.get('action')
    require(type(status) is str and type(action) is str and type(row.get('reason')) is str,
            'Linguistic audit decision fields must be result codes')
    require(row.get('rule_version') == RULES_VERSION, 'Unknown linguistic audit rule version')
    require(row.get('ref') is None or (type(row['ref']) is str
            and re.fullmatch(r'[1-3]?[A-Za-z]+\.\d+\.\d+', row['ref'])),
            'Invalid linguistic audit verse reference')
    common = {'kind', 'ref', 'status', 'action', 'reason', 'rule_version'}
    targets = {'target_text', 'target_strong', 'target_tokens'}
    if kind == 'uncertainty':
        fields = common | {'hint_id'}
        if targets.intersection(row):
            fields |= targets
        if status == 'accepted':
            require(action == 'remove-hint' and row['reason'] in ACCEPTED_RULES,
                    'Invalid accepted uncertainty decision')
            fields |= targets | {'proof'}
            if row['reason'] in {ARTICLE_RULE, NAME_RULE}:
                fields.add('references')
        else:
            require(action == 'retain' and status == 'review' and row['reason'] in REVIEW_REASONS,
                    'Invalid retained uncertainty decision')
            if row['reason'] in {'no-independent-article-corroboration',
                                 'no-independent-word-level-name-corroboration'}:
                fields |= targets | {'references'}
            elif row['reason'] == 'source-occurrence-already-used' and 'references' in row:
                fields |= targets | {'references'}
        require(type(row.get('hint_id')) is str and re.fullmatch(r'u\d{6,}', row['hint_id']),
                'Invalid uncertainty audit identifier')
        if targets.intersection(row):
            require(type(row.get('target_text')) is str and type(row.get('target_strong')) is list
                    and type(row.get('target_tokens')) is list, 'Invalid uncertainty target fields')
            require(all(type(code) is str and re.fullmatch(r'[HG][1-9]\d*', code)
                        for code in row['target_strong']), 'Invalid audited target Strong values')
            require(all(type(token) is str and re.fullmatch(r'd\d{3,}', token)
                        for token in row['target_tokens']), 'Invalid audited target token IDs')
    elif kind == 'article-addition':
        fields = common | {'target_token', 'target_text', 'target_start', 'target_end',
                           'before_strong', 'after_strong', 'proposed_strong', 'references', 'proof'}
        require((status == 'accepted' and action == 'add-strong' and row['reason'] == ARTICLE_RULE)
                or (status == 'review' and action == 'retain'
                    and row['reason'] == 'no-independent-article-corroboration'),
                'Invalid article audit decision')
        require(type(row.get('target_text')) is str and type(row.get('target_token')) is str
                and re.fullmatch(r'd\d{3,}', row['target_token']), 'Invalid article target fields')
        require(type(row.get('target_start')) is int and type(row.get('target_end')) is int
                and 0 <= row['target_start'] < row['target_end'], 'Invalid article target positions')
        require(row.get('before_strong') == [] and row.get('proposed_strong') == ['G3588']
                and row.get('after_strong') == (['G3588'] if status == 'accepted' else []),
                'Invalid article Strong delta')
    else:
        require(False, 'Unknown linguistic audit row kind')
    require(set(row) == fields, 'Unexpected or missing public linguistic audit fields')
    if 'references' in row:
        refs = row['references']
        require(type(refs) is dict and set(refs) == set(reference_labels)
                and all(type(value) is str and value in ARTICLE_REFERENCE_STATUSES for value in refs.values()),
                'Invalid public article reference status')
    if 'proof' in row:
        proof = row['proof']
        require(type(proof) is dict and type(proof.get('rule')) is str and proof['rule'] in ACCEPTED_RULES,
                'Invalid linguistic proof rule')
        article = proof['rule'] == ARTICLE_RULE
        proof_fields = ({'rule', 'source_article', 'source_head', 'source_left',
                         'head_strong', 'article_morph', 'head_morph'} if article else
                        {'rule', 'source_token', 'strong', 'morph', 'catalog_entry_sha256'}
                        if proof['rule'] == NAME_RULE else
                        {'rule', 'source_token', 'source_left', 'source_right', 'strong', 'morph'})
        require(set(proof) == proof_fields and
                all(type(value) is str or (key == 'source_left' and article and value is None)
                    for key, value in proof.items()), 'Unexpected or malformed public linguistic proof fields')
        require((kind != 'article-addition' or article) and
                (status != 'accepted' or proof['rule'] == row['reason']),
                'Linguistic proof and decision differ')


@dataclass
class ValidationResult:
    root: ET.Element
    audit: list[dict]
    summary: dict


def rule_identity():
    """Hash rules and semantic/XML dependencies, without machine-specific paths."""
    names = ('linguistic.py', 'linguistic_rules.py', 'linguistic_names.py', 'confirm.py', 'common.py',
             'importers.py', 'xmlio.py', 'project.py')
    hashes = {name: file_hash(importlib.import_module('.' + name[:-3], __package__).__file__) for name in names}
    data_files = {'rules/' + path.name: file_hash(path) for path in (CATALOG_PATH, SOURCES_PATH)}
    identity = {'implementation': hashes, 'data_files': data_files}
    return {'version': RULES_VERSION, 'sha256': digest(identity), **identity}


def _source_extras(path, profile):
    """Read extra original fields even before the common TSV importer is extended."""
    options = profile['options']; columns = options['columns']
    greek = options.get('profile') == 'tagnt'
    extra_columns = {'conjoined': columns.get('conjoined', 10 if greek else None),
                     'alternate': columns.get('alternate', 12 if greek else 9),
                     'editions_raw': columns.get('editions')}
    extras = {}
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        for lineno, row in enumerate(csv.reader(stream, delimiter='\t'), 1):
            if not row or not re.match(r'^[1-3]?[A-Za-z]+\.\d+\.\d+', row[0]):
                continue
            ref = row[columns['ref']].strip()
            require(ref not in extras, f'Duplicate STEP occurrence: {path.name}:{lineno}')
            data = {}
            for key, position in extra_columns.items():
                if position is not None:
                    require(position < len(row), f'{path.name}:{lineno}: missing {key}')
                    data[key] = row[position].strip()
            data['alternate'] = strongs(data.get('alternate', ''), options.get('prefix', 'G'))
            word = re.search(r'#([^=]+)', ref)
            data['word'] = word[1] if word else ''
            extras[ref] = data
    return extras


def reference_identity(profiles_path, source_root, nt_edition):
    """Cheap preflight identity, included in the build cache key before mutations."""
    require(nt_edition in {'WH', 'TR'}, 'Supported NT editions are WH and TR')
    source_root = Path(source_root).resolve()
    profiles_path = Path(profiles_path)
    profiles = json.loads(profiles_path.read_text(encoding='utf-8'))
    require(isinstance(profiles, list) and profiles, 'STEP profiles must be a nonempty list')
    files = []
    for profile in profiles:
        require(profile['options'].get('profile') in {'tagnt', 'tahot'}, 'Unsupported linguistic reference profile')
        for configured_path in profile['paths']:
            path = (source_root / configured_path).resolve()
            require(path.is_relative_to(source_root), 'STEP path escapes source root')
            files.append({'source': profile['id'], 'path': str(path.relative_to(source_root)),
                          'sha256': file_hash(path)})
    metadata = {'profile': SOURCE_PROFILE, 'selected_nt_edition': nt_edition,
                'profiles_sha256': file_hash(profiles_path), 'files': files}
    metadata['sha256'] = digest(metadata)
    return metadata


def release_settings(profiles_path, source_root, nt_edition):
    return {'method': METHOD, 'rule_identity': rule_identity(),
            'source_snapshot': reference_identity(profiles_path, source_root, nt_edition),
            'article_corroboration_required': True, 'prior_alignment_required': True}


def load_reference_occurrences(profiles_path, source_root, nt_edition):
    """Load actual word occurrences, filtered to WH/TR and labelled Hebrew L/Q.

    Returned metadata contains file IDs and hashes only, never local absolute paths.
    The build's normal source-lock verification can additionally check these files.
    """
    require(nt_edition in {'WH', 'TR'}, 'Supported NT editions are WH and TR')
    profiles_path = Path(profiles_path)
    source_root = Path(source_root).resolve()
    profiles = json.loads(profiles_path.read_text(encoding='utf-8'))
    require(isinstance(profiles, list) and profiles, 'STEP profiles must be a nonempty list')
    occurrences = defaultdict(list); files = []; seen = set()
    for profile in profiles:
        options = dict(profile['options'])
        require(options.get('profile') in {'tagnt', 'tahot'}, 'Unsupported linguistic reference profile')
        if options['profile'] == 'tagnt':
            options['edition'] = nt_edition
        for configured_path in profile['paths']:
            path = (source_root / configured_path).resolve()
            require(path.is_relative_to(source_root), 'STEP path escapes source root')
            extras = _source_extras(path, profile)
            files.append({'source': profile['id'], 'path': str(path.relative_to(source_root)),
                          'sha256': file_hash(path)})
            for row in import_reference_tsv(path, profile['id'], options):
                for token in row['tokens']:
                    key = (profile['id'], token['origin_id'])
                    require(key not in seen, f'Duplicate imported STEP occurrence: {key}')
                    seen.add(key)
                    token.update(extras[token['origin_id']])
                    occurrences[row['ref']].append(token)
    require(occurrences, 'No STEP source occurrences loaded')
    metadata = {'profile': SOURCE_PROFILE, 'selected_nt_edition': nt_edition,
                'profiles_sha256': file_hash(profiles_path), 'files': files}
    metadata['sha256'] = digest(metadata)
    return dict(occurrences), metadata


def _token_view(view):
    """Keep annotation spans: one German word is not automatically one source word."""
    tokens = [dict(token, strong=[], uncertain=False, anchor_eligible=False,
                   blocked=False, phrase_tokens=1) for token in view.tokens]
    hint_spans = set(); unsupported_hint = False
    hints = []
    for hint in view.hints:
        span, indices, reason = view.hint_span(hint)
        hints.append((hint, span, indices, reason))
        if span is not None:
            hint_spans.add(span.element)
        else:
            # An orphaned/structurally ambiguous marker must not make a nearby
            # assignment into a trusted anchor simply because its span is unknown.
            unsupported_hint = True
    for index, token in enumerate(tokens):
        overlaps = [span for span in view.spans
                    if span.start < token['end'] and token['start'] < span.end]
        containing = [span for span in overlaps
                      if span.start <= token['start'] and token['end'] <= span.end]
        token['strong'] = sorted({code for span in containing if span.valid for code in span.codes})
        token['uncertain'] = any(span.element in hint_spans for span in overlaps)
        token['blocked'] = any(not span.valid for span in overlaps) or len(containing) != len(overlaps)
        if len(overlaps) == 1:
            span = overlaps[0]
            covered = [t for t in tokens if t['start'] < span.end and t['end'] > span.start]
            token['phrase_tokens'] = len(covered)
            token['anchor_eligible'] = (not unsupported_hint and not token['uncertain']
                and not token['blocked'] and len(covered) == 1 and len(span.codes) == 1
                and span.valid and not span.element.get(PROVENANCE)
                and span.start <= token['start'] and token['end'] <= span.end)
        if not overlaps:
            token['anchor_eligible'] = False
    return tokens, hints


def _single_slot(view, token):
    if any(s.start < token['end'] and token['start'] < s.end for s in view.spans):
        return False
    for node, attr, lo, hi in slots(view.element):
        if lo <= token['start'] and token['end'] <= hi:
            owner = node if attr == 'text' else view.parents.get(node)
            while owner is not None:
                if tag(owner) in GRAMMAR or tag(owner) in EXCLUDED:
                    return False
                owner = view.parents.get(owner)
            return True
    return False


def _span_signature(element, remove_provenance=False):
    clone = copy.deepcopy(element); clone.tail = None
    if remove_provenance:
        clone.attrib.pop(PROVENANCE, None)
    return ET.tostring(clone, encoding='unicode')


def _corroborate_assignment(view, target_indices, reference_views, alignments, codes=('G3588',)):
    statuses = {}
    for label, reference in reference_views.items():
        statuses[label] = ('missing-reference-verse' if reference is None else
                           reference.confirm_span(target_indices, codes, alignments[label]))
    return statuses


def validate_tree(root, reference_occurrences, *, nt_edition='WH', source_metadata=None,
                  corroborating_roots=None, require_article_corroboration=True, verse_guards=None):
    """Return a changed copy plus a complete decision audit. Inputs remain immutable.

    Decisions use one frozen snapshot. Tags accepted by this stage remain ineligible
    as anchors on future invocations, so rerunning cannot bootstrap new approvals.
    """
    require(nt_edition in {'WH', 'TR'}, 'Supported NT editions are WH and TR')
    require(isinstance(reference_occurrences, dict), 'Reference occurrences must be a verse mapping')
    original_text = {ref: plain(v) for ref, v in zef_verses(root, True)}
    original_notes = _preserved_notes(root)
    verse_guards = verse_guards or {}
    corroborating_roots = corroborating_roots or {}
    name_catalog = load_name_catalog()
    require(set(corroborating_roots) <= {'elb-bk', 'elb-csv'}, 'Supported article references: elb-bk, elb-csv')
    reference_indexes = {label: _verse_index(tree) for label, tree in corroborating_roots.items()}
    corroboration_hashes = {label: hashlib.sha256(ET.tostring(tree, encoding='utf-8')).hexdigest()
                           for label, tree in corroborating_roots.items()}
    output = copy.deepcopy(root)
    all_hints = [node for node in output.iter() if tag(node) == 'NOTE' and node.get('ex') == HINT]
    hint_ids = {node: f'u{index:06}' for index, node in enumerate(all_hints, 1)}
    originals = {node: _span_signature(node) for node in output.iter() if tag(node) in GRAMMAR}
    approved_existing = set(); audit = []; handled = set(); added_elements = set()
    counts = Counter({'hints_before': len(all_hints), 'hints_removed': 0,
                      'article_tags_added': 0, 'hints_rejected': 0, 'article_candidates_retained': 0})
    for ref, verse in zef_verses(output):
        view = _Verse(verse, ref)
        tokens, hints = _token_view(view)
        reference_views = {label: _Verse(index[ref], ref) if ref in index else None
                           for label, index in reference_indexes.items()}
        alignments = {label: forced_alignment(view.tokens, reference.tokens)
                      for label, reference in reference_views.items() if reference is not None}
        source = reference_occurrences.get(ref, [])
        is_nt = BOOKS.index(ref.split('.')[0]) >= 39
        source_problem = verse_guards.get(ref) or _source_shape_problem(source, nt_edition, is_nt, ref)
        inherited_codes = {code for token in tokens for code in token['strong']}
        source_codes = {code for token in source for code in token.get('strong', [])}
        if len(inherited_codes) >= 3 and len(inherited_codes & source_codes) / len(inherited_codes) < 0.65:
            source_problem = source_problem or 'verse-inventory-mismatch'

        decisions = {d['token']: d for d in classify_uncertain(ref, view.text, tokens, source)}
        removals = []; additions = []; used_source_occurrences = set()
        for hint, span, indices, reason in hints:
            handled.add(hint)
            row = {'kind': 'uncertainty', 'hint_id': hint_ids[hint], 'ref': ref,
                   'status': 'review', 'action': 'retain', 'rule_version': RULES_VERSION}
            if span is not None:
                row.update(target_text=view.text[span.start:span.end],
                           target_strong=list(span.codes),
                           target_tokens=[tokens[i]['id'] for i in indices])
            reason = reason or source_problem
            if span is not None and span.element.get(PROVENANCE):
                reason = reason or 'already-reviewed-linguistic-annotation'
            if not reason and len(indices) != 1:
                reason = 'multiword-target-span'
            if not reason and len(span.codes) != 1:
                reason = 'multiple-target-strong-codes'
            if not reason:
                token = tokens[indices[0]]
                decision = decisions.get(token['id'])
                if decision and decision['status'] == 'review' and span.codes[0] in name_catalog:
                    name_references = _corroborate_assignment(view, indices, reference_views, alignments, span.codes)
                    decision = proper_name_decision(ref, tokens, indices[0], source, name_catalog,
                        nt_edition=nt_edition, reference_statuses=name_references)
                    if decision['reason'] == 'no-independent-word-level-name-corroboration':
                        row['references'] = name_references
                if decision is None:
                    reason = 'unsupported-target-annotation'
                else:
                    row.update(status=decision['status'], reason=decision['reason'])
                    if decision['status'] == 'accepted':
                        proof = decision['proof']
                        occurrence = proof.get('source_article', proof.get('source_token'))
                        corroboration = (_corroborate_assignment(view, indices, reference_views, alignments)
                                         if proof.get('source_article') else decision.get('references'))
                        if corroboration is not None:
                            row['references'] = corroboration
                        if (corroboration is not None and require_article_corroboration
                                and 'confirmed' not in corroboration.values()):
                            row.update(status='review', reason='no-independent-article-corroboration')
                        elif occurrence in used_source_occurrences:
                            row.update(status='review', reason='source-occurrence-already-used')
                        else:
                            used_source_occurrences.add(occurrence)
                            row.update(action='remove-hint', proof=proof)
                            removals.append((hint, span.element))
            if reason:
                row['reason'] = reason
            audit.append(row)
        # Compute additions from the same snapshot, before applying removals.
        if not source_problem:
            for index, token in enumerate(tokens):
                if token['strong'] or token['blocked'] or token['text'].casefold() not in ARTICLES:
                    continue
                proof = linked_article_proof(view.text, tokens, index, source)
                if not proof or not _single_slot(view, token):
                    continue
                if proof['source_article'] in used_source_occurrences:
                    continue
                corroboration = _corroborate_assignment(view, [index], reference_views, alignments)
                approved = not require_article_corroboration or 'confirmed' in corroboration.values()
                if approved:
                    used_source_occurrences.add(proof['source_article'])
                    additions.append(dict(token, strong=['G3588'], uncertain=False))
                else:
                    counts['article_candidates_retained'] += 1
                audit.append({'kind': 'article-addition', 'ref': ref,
                              'target_token': token['id'], 'target_text': token['text'],
                              'target_start': token['start'], 'target_end': token['end'],
                              'before_strong': [], 'after_strong': ['G3588'] if approved else [],
                              'proposed_strong': ['G3588'],
                              'status': 'accepted' if approved else 'review',
                              'action': 'add-strong' if approved else 'retain',
                              'reason': proof['rule'] if approved else 'no-independent-article-corroboration',
                              'references': corroboration,
                              'rule_version': RULES_VERSION, 'proof': proof})
        for hint, grammar in removals:
            require(not grammar.get(PROVENANCE), 'Previously validated annotation unexpectedly retains a hint')
            grammar.set(PROVENANCE, RULES_VERSION)
            approved_existing.add(grammar)
            _remove_preserving_tail(view.parents[hint], hint)
        old_elements = set(verse.iter())
        added = annotate(verse, additions, hints=False)
        require(added == len(additions), 'Article insertion did not match its approved token spans')
        for node in set(verse.iter()) - old_elements:
            require(tag(node) == 'gr', 'Unexpected node created during article insertion')
            node.set(PROVENANCE, RULES_VERSION)
            added_elements.add(node)
        counts['hints_removed'] += len(removals)
        counts['article_tags_added'] += added
    for hint in all_hints:
        if hint not in handled:
            audit.append({'kind': 'uncertainty', 'hint_id': hint_ids[hint], 'ref': None,
                          'status': 'review', 'action': 'retain',
                          'reason': 'outside-supported-verse-text', 'rule_version': RULES_VERSION})
    # Invariants deliberately include all original markup within existing gr tags.
    require(original_text == {ref: plain(v) for ref, v in zef_verses(output, True)},
            'Linguistic validation changed Bible text or captions')
    require(original_notes == _preserved_notes(output), 'Original note subtrees changed')
    for node, signature in originals.items():
        require(_span_signature(node, node in approved_existing) == signature,
                'Existing Strong annotation changed beyond approved provenance')
    remaining = sum(tag(n) == 'NOTE' and n.get('ex') == HINT for n in output.iter())
    require(remaining + counts['hints_removed'] == counts['hints_before'], 'Uncertainty balance failed')
    require(sum(r['kind'] == 'uncertainty' for r in audit) == counts['hints_before'],
            'Not every input uncertainty marker was audited exactly once')
    require(len(added_elements) == counts['article_tags_added'], 'New Strong tag count differs')
    audit.sort(key=lambda r: (0, r['hint_id']) if r['kind'] == 'uncertainty'
               else (1, BOOKS.index(r['ref'].split('.')[0]),
                     *map(int, r['ref'].split('.')[1:]), r['target_start']))
    for row in audit:
        _validate_audit_schema(row, corroborating_roots)
    summary = dict(counts)
    summary.update(method=METHOD, rule_identity=rule_identity(), selected_nt_edition=nt_edition,
                   hints_remaining=remaining,
                   decisions=dict(Counter(r.get('reason', r.get('proof', {}).get('rule')) for r in audit)),
                   text_preserved=True, original_notes_preserved=len(original_notes),
                   existing_strong_values_preserved=True, no_bootstrapping=True,
                   article_corroboration_required=require_article_corroboration,
                   article_reference_tree_hashes=corroboration_hashes,
                   prior_alignment_guard_count=len(verse_guards))
    if source_metadata is not None:
        summary['source_snapshot'] = source_metadata
    return ValidationResult(output, audit, summary)


def _write_audit(path, rows):
    path = Path(path)
    body = ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
                   for row in rows)
    if path.suffix != '.gz':
        atomic_text(path, body)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    try:
        with os.fdopen(handle, 'wb') as stream:
            with gzip.GzipFile(filename='', fileobj=stream, mode='wb', mtime=0) as zipped:
                zipped.write(body.encode('utf-8'))
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _load_alignment_guards(path, root):
    text = {ref: plain(verse) for ref, verse in zef_verses(root)}
    guards = {}; seen = set()
    opener = gzip.open if Path(path).suffix == '.gz' else open
    with opener(path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            ref = row.get('ref')
            require(ref in text and ref not in seen, 'Alignment verses differ from linguistic input')
            seen.add(ref)
            require(row.get('text') == text[ref], f'Alignment text differs at {ref}')
            if row.get('inventory_mismatch'):
                guards[ref] = 'prior-verse-inventory-mismatch'
    require(seen == set(text), 'Alignment must cover every linguistic input verse')
    return guards


def validate_files(input_path, output_path, *, source_profiles_path, source_root,
                   nt_edition='WH', audit_path=None, report_path=None, manifest_path=None,
                   corroborating_paths=None, require_article_corroboration=True, alignment_path=None,
                   output_identity=None):
    """Reproducible file wrapper suitable for the pipeline's 06-linguistic stage."""
    input_path = Path(input_path); output_path = Path(output_path)
    audit_path = Path(audit_path) if audit_path else output_path.with_suffix('.audit.jsonl.gz')
    report_path = Path(report_path) if report_path else output_path.with_suffix('.report.json')
    manifest_path = Path(manifest_path) if manifest_path else output_path.with_suffix('.manifest.json')
    outputs = [output_path, audit_path, report_path, manifest_path]
    require(len({p.resolve() for p in outputs}) == len(outputs), 'Linguistic output paths must differ')
    require(input_path.resolve() not in {p.resolve() for p in outputs}, 'Refusing to overwrite linguistic input')
    corroborating_paths = corroborating_paths or {}
    require(set(corroborating_paths) <= {'elb-bk', 'elb-csv'}, 'Supported article references: elb-bk, elb-csv')
    references, source_metadata = load_reference_occurrences(source_profiles_path, source_root, nt_edition)
    corroborating_roots = {label: parse_xml(path) for label, path in corroborating_paths.items()}
    protected = {Path(source_profiles_path).resolve()}
    protected.update(Path(path).resolve() for path in corroborating_paths.values())
    protected.update((Path(source_root) / row['path']).resolve() for row in source_metadata['files'])
    require(not protected.intersection(p.resolve() for p in outputs), 'Refusing to overwrite a reference input')
    tree = parse_xml(input_path)
    if alignment_path is None and (input_path.parent / 'alignment.jsonl.gz').exists():
        alignment_path = input_path.parent / 'alignment.jsonl.gz'
    verse_guards = _load_alignment_guards(alignment_path, tree) if alignment_path else {}
    if alignment_path:
        require(Path(alignment_path).resolve() not in {p.resolve() for p in outputs},
                'Refusing to overwrite alignment input')
    result = validate_tree(tree, references, nt_edition=nt_edition,
                           source_metadata=source_metadata, corroborating_roots=corroborating_roots,
                           require_article_corroboration=require_article_corroboration, verse_guards=verse_guards)
    if output_identity is not None:
        from .project import metadata
        metadata(result.root, output_identity[0], output_identity[1], '06-linguistic')
    write_xml(output_path, result.root)
    # Reparse the actual serialized artifact; report preservation, not merely tree intent.
    serialized = parse_xml(output_path)
    require({r: plain(v) for r, v in zef_verses(serialized, True)} ==
            {r: plain(v) for r, v in zef_verses(result.root, True)}, 'Serialized text differs')
    require(_preserved_notes(serialized) == _preserved_notes(result.root), 'Serialized notes differ')
    _write_audit(audit_path, result.audit)
    report = result.summary | {'input_sha256': file_hash(input_path), 'output_sha256': file_hash(output_path),
                               'audit_sha256': file_hash(audit_path)}
    write_json(report_path, report)
    manifest = {'schema': 1, 'phase': '06-linguistic', 'method': METHOD,
                'rule_identity': result.summary['rule_identity'],
                'input_sha256': report['input_sha256'], 'source_snapshot': source_metadata,
                'selected_nt_edition': nt_edition,
                'article_corroboration_required': require_article_corroboration,
                'alignment_sha256': file_hash(alignment_path) if alignment_path else None,
                'output_identity': list(output_identity) if output_identity is not None else None,
                'article_reference_hashes': {label: file_hash(path) for label, path in corroborating_paths.items()},
                'outputs': {'xml': file_hash(output_path), 'audit': file_hash(audit_path),
                            'report': file_hash(report_path)}}
    write_json(manifest_path, manifest)
    return result


def verify_transition(before, after, audit, source_occurrences, *, nt_edition='WH',
                      verse_guards=None, output_identity=None):
    """Replay only audited, source-proven deltas and compare the entire XML tree.

    Public verification can recheck STEP proofs and exact XML changes. The private
    reference comparison itself remains reproducible from its recorded snapshots.
    """
    verse_guards = verse_guards or {}
    for row in audit:
        _validate_audit_schema(row, {'elb-bk', 'elb-csv'})
    name_catalog = load_name_catalog()
    replay = copy.deepcopy(before)
    views = {ref: _Verse(verse, ref) for ref, verse in zef_verses(replay)}
    token_views = {ref: _token_view(view)[0] for ref, view in views.items()}
    markers = [node for node in replay.iter() if tag(node) == 'NOTE' and node.get('ex') == HINT]
    hint_ids = {f'u{number:06}': node for number, node in enumerate(markers, 1)}
    locations = {hint: (ref, span, indices, failure)
                 for ref, view in views.items() for hint, span, indices, failure in _token_view(view)[1]}
    hinted_rows = [row for row in audit if row.get('kind') == 'uncertainty']
    require(len(hinted_rows) == len(hint_ids) and {row.get('hint_id') for row in hinted_rows} == set(hint_ids),
            'Incomplete or duplicate linguistic uncertainty audit')
    require(all(row.get('kind') in {'uncertainty', 'article-addition'} for row in audit),
            'Unknown linguistic audit row kind')
    additions = defaultdict(list); removed = added = 0; used_occurrences = set(); seen_additions = set()

    def proof_for(ref, index, row, article, accepted=True):
        require(ref not in verse_guards, 'Accepted proof uses a guarded verse')
        tokens = token_views[ref]; view = views[ref]; source = source_occurrences.get(ref, [])
        require(not _source_shape_problem(source, nt_edition, BOOKS.index(ref.split('.')[0]) >= 39, ref),
                'Accepted proof has invalid source occurrence identity')
        available = {code for token in source for code in token.get('strong', [])}
        inherited = {code for token in tokens for code in token['strong']}
        require(len(inherited) < 3 or len(inherited & available) / len(inherited) >= 0.65,
                'Accepted proof uses a mismatched verse inventory')
        if row.get('proof', {}).get('rule') == NAME_RULE:
            decision = proper_name_decision(ref, tokens, index, source, name_catalog,
                nt_edition=nt_edition, reference_statuses=row.get('references', {}))
            proof = decision.get('proof') if decision['status'] == 'accepted' else None
        else:
            proof = (linked_article_proof(view.text, tokens, index, source) if article else
                     atomic_bridge_proof(view.text, tokens, index, source))
        require(proof is not None and row.get('proof') == proof, 'Linguistic proof differs from source occurrences')
        occurrence = (ref, proof.get('source_article', proof.get('source_token')))
        if accepted:
            require(occurrence not in used_occurrences, 'A source occurrence was accepted more than once')
            used_occurrences.add(occurrence)
        if accepted and (article or proof['rule'] == NAME_RULE):
            statuses = row.get('references', {})
            require(set(statuses) == {'elb-bk', 'elb-csv'} and 'confirmed' in statuses.values(),
                    'Article or proper name lacks independent corroboration')

    for row in audit:
        require(row.get('rule_version') == RULES_VERSION, 'Unknown linguistic audit rule version')
        action = row.get('action')
        if row['kind'] == 'uncertainty':
            hint = hint_ids[row['hint_id']]
            location = locations.get(hint)
            require(row.get('ref') == (location[0] if location else None), 'Hint audit verse mismatch')
            if location and location[1] is not None:
                ref, span, indices, failure = location
                require(row.get('target_text') == views[ref].text[span.start:span.end] and
                        row.get('target_strong') == list(span.codes) and
                        row.get('target_tokens') == [token_views[ref][i]['id'] for i in indices],
                        'Hint audit target differs from its original XML span')
            else:
                require(not {'target_text', 'target_strong', 'target_tokens'}.intersection(row),
                        'Unlocated hint audit contains an unrelated target')
            if action == 'retain':
                require(row.get('status') == 'review', 'Retained hint has invalid status')
                if row['reason'] in {'no-independent-article-corroboration',
                                     'no-independent-word-level-name-corroboration'}:
                    require('confirmed' not in row['references'].values(),
                            'Retained article hint claims successful corroboration')
                continue
            require(action == 'remove-hint' and row.get('status') == 'accepted' and location,
                    'Unapproved uncertainty-note removal')
            ref, span, indices, failure = location
            require(not failure and span is not None and len(indices) == len(span.codes) == 1,
                    'Approved uncertainty span is not atomic')
            require(not span.element.get(PROVENANCE), 'Previously reviewed span cannot be approved again')
            require(row.get('target_text') == views[ref].text[span.start:span.end] and
                    row.get('target_strong') == list(span.codes) and
                    row.get('target_tokens') == [token_views[ref][i]['id'] for i in indices],
                    'Approved hint audit span differs from XML')
            proof_for(ref, indices[0], row, span.codes == ('G3588',))
            span.element.set(PROVENANCE, RULES_VERSION)
            _remove_preserving_tail(views[ref].parents[hint], hint)
            removed += 1
        else:
            ref = row.get('ref'); require(ref in views, 'Unknown article-addition verse')
            token = next((t for t in token_views[ref] if t['id'] == row.get('target_token')), None)
            require(token is not None and not token['strong'] and _single_slot(views[ref], token),
                    'Article audit points to an occupied or invalid target span')
            require(row.get('target_text') == token['text'] and row.get('target_start') == token['start'] and
                    row.get('target_end') == token['end'] and row.get('before_strong') == [] and
                    row.get('proposed_strong') == ['G3588'], 'Article audit span differs from XML')
            key = (ref, token['id']);require(key not in seen_additions, 'Duplicate article audit token')
            seen_additions.add(key)
            if action == 'retain':
                require(row.get('status') == 'review' and row.get('after_strong') == [],
                        'Retained article claims an executed Strong change')
                require('confirmed' not in row['references'].values(),
                        'Retained article claims successful corroboration')
                proof_for(ref, token_views[ref].index(token), row, True, accepted=False)
                continue
            require(action == 'add-strong' and row.get('status') == 'accepted' and
                    row.get('after_strong') == ['G3588'], 'Unapproved Strong addition')
            proof_for(ref, token_views[ref].index(token), row, True)
            additions[ref].append(dict(token, strong=['G3588'], uncertain=False))
            added += 1
    for ref, proposed in additions.items():
        verse = views[ref].element; previous = set(verse.iter())
        require(annotate(verse, proposed, hints=False) == len(proposed), 'Audited Strong addition cannot be reproduced')
        for node in set(verse.iter()) - previous:
            require(tag(node) == 'gr', 'Unexpected audited addition element')
            node.set(PROVENANCE, RULES_VERSION)
    if output_identity is not None:
        from .project import metadata
        metadata(replay, output_identity[0], output_identity[1], '06-linguistic')

    def signature(root):
        # Structural indentation is not Bible text; mixed-content text is exact.
        root = copy.deepcopy(root)
        for element in root.iter():
            if tag(element) in {'XMLBIBLE', 'BIBLEBOOK', 'CHAPTER'}:
                if not (element.text or '').strip():element.text = None
                for child in element:
                    if not (child.tail or '').strip():child.tail = None
        return ET.tostring(root, encoding='unicode')

    require(signature(replay) == signature(after), 'XML contains changes outside the approved linguistic deltas')
    return {'hints_removed': removed, 'article_tags_added': added,
            'hints_before': len(markers), 'hints_remaining': len(markers) - removed}
