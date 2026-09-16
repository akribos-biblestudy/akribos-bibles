"""Confirm existing uncertain assignments against two independent references.

This module never transfers Strong identifiers or reference text. It only removes
the Akribos uncertainty NOTE after both references confirm the entire existing
assignment at an unambiguously aligned word span. The returned audit contains
target identifiers/assignments and decision categories, never reference content.
"""
from __future__ import annotations

import copy
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .common import BOOKS, file_hash, require, tokenize
from .importers import parse_xml, tag
from .xmlio import EXCLUDED, plain, strong_fingerprints, zef_verses

HINT = 'nl:akribosStrongUncertainty'
GRAMMAR = {'gr', 'GRAM', 'w'}
NORMALIZATION = 'NFC-lowercase-v1'
METHOD = 'two-reference-exact-strong-set-v1'
INPUT_PROFILE = 'zefania-word-spans-v1'
PLACEHOLDER = re.compile(r'\[\s*\?\s*\]')
REFERENCE_STATUSES = frozenset({
    'confirmed', 'missing-reference-source', 'missing-reference-verse',
    'uncertain-reference-verse', 'word-not-aligned', 'ambiguous-word-alignment',
    'noncontiguous-reference-span', 'reference-placeholder-in-span',
    'invalid-reference-strong-set', 'reference-annotation-crosses-span',
    'incomplete-reference-word-span', 'missing-reference-strong-tags',
    'different-strong-set',
})
TARGET_FAILURES = frozenset({
    'structured-uncertainty-note', 'no-preceding-strong-span',
    'text-between-assignment-and-hint', 'target-placeholder-in-span',
    'invalid-target-strong-set', 'nested-target-strong-spans',
    'incomplete-target-word-span',
})
AUDIT_FIELDS = frozenset({'ref', 'hint', 'target_token_ids', 'target_strong',
                          'status', 'reason', 'references'})


def verify_confirmation_transition(before, after, audit, *, output_identity=None):
    """Replay the exact public stage-05 delta without needing private sources.

    Every input hint must have one correctly located audit entry. A removal
    needs two recorded confirmations of the complete existing assignment. This
    validates those recorded decisions and their XML effects; reproducing the
    private comparison still requires the separately identified source files.
    """
    rows = {}
    reasons = REFERENCE_STATUSES | TARGET_FAILURES | {
        'both-references-confirm-complete-set', 'outside-supported-verse-text'}
    for row in audit:
        require(isinstance(row, dict) and set(row) == AUDIT_FIELDS,
                'Unexpected public confirmation audit fields')
        require((row['ref'] is None or isinstance(row['ref'], str)) and
                type(row['hint']) is int and row['hint'] > 0,
                'Invalid confirmation audit location')
        require(isinstance(row['target_token_ids'], list) and
                all(isinstance(value, str) for value in row['target_token_ids']) and
                isinstance(row['target_strong'], list) and
                all(isinstance(value, str) for value in row['target_strong']),
                'Invalid confirmation audit assignment')
        require(isinstance(row['status'], str) and row['status'] in {'confirmed', 'retained'} and
                isinstance(row['reason'], str) and row['reason'] in reasons,
                'Unknown confirmation audit decision')
        statuses = row['references']
        require(isinstance(statuses, dict) and
                set(statuses) == (set() if row['ref'] is None else {'elb-bk', 'elb-csv'}) and
                all(isinstance(value, str) and value in REFERENCE_STATUSES | {'target-not-eligible'}
                    for value in statuses.values()), 'Invalid confirmation reference statuses')
        key = (row['ref'], row['hint'])
        require(key not in rows, 'Duplicate confirmation audit location')
        rows[key] = row

    replay = copy.deepcopy(before)
    markers = [node for node in replay.iter() if tag(node) == 'NOTE' and node.get('ex') == HINT]
    require(len(rows) == len(markers), 'Incomplete reference-confirmation audit')
    processed = set()
    removed = 0
    # Keep verse views local: replaying a full Bible need not retain every token,
    # parent map and grammar span after its verse has been checked.
    for ref, element in zef_verses(replay):
        verse = _Verse(element, ref)
        decisions = []
        for number, hint in enumerate(verse.hints, 1):
            processed.add(hint)
            row = rows.pop((ref, number), None)
            require(row is not None, 'Confirmation audit does not identify an input hint')
            span, indices, failure = verse.hint_span(hint)
            require(row['target_token_ids'] == [verse.tokens[i]['id'] for i in indices] and
                    row['target_strong'] == (list(span.codes) if span else []),
                    'Confirmation audit assignment differs from input hint')
            statuses = row['references']
            if failure:
                require(row['status'] == 'retained' and row['reason'] == failure and
                        all(value == 'target-not-eligible' for value in statuses.values()),
                        'Ineligible confirmation hint was not retained')
            else:
                require(all(value in REFERENCE_STATUSES for value in statuses.values()),
                        'Eligible confirmation hint has invalid reference statuses')
                failures = [statuses[label] for label in ('elb-bk', 'elb-csv')
                            if statuses[label] != 'confirmed']
                if failures:
                    require(row['status'] == 'retained' and row['reason'] == failures[0],
                            'Confirmation decision disagrees with reference statuses')
                else:
                    require(row['status'] == 'confirmed' and
                            row['reason'] == 'both-references-confirm-complete-set',
                            'Confirmation removal lacks two recorded confirmations')
                    decisions.append((verse.parents[hint], hint))
        for parent, hint in decisions:
            _remove_preserving_tail(parent, hint)
            removed += 1

    for number, hint in enumerate(markers, 1):
        if hint in processed:
            continue
        row = rows.pop((None, number), None)
        require(row is not None and row['target_token_ids'] == [] and row['target_strong'] == [] and
                row['status'] == 'retained' and row['reason'] == 'outside-supported-verse-text',
                'Unsupported confirmation hint was not retained')
    require(not rows, 'Confirmation audit contains unknown input hints')
    if output_identity is not None:
        from .project import metadata
        metadata(replay, output_identity[0], output_identity[1], '05-reference-confirmed')

    def signature(root):
        root = copy.deepcopy(root)
        for element in root.iter():
            if tag(element) in {'XMLBIBLE', 'BIBLEBOOK', 'CHAPTER'}:
                if not (element.text or '').strip():
                    element.text = None
                for child in element:
                    if not (child.tail or '').strip():
                        child.tail = None
        return ET.tostring(root, encoding='unicode')

    require(signature(replay) == signature(after),
            'XML contains changes outside the approved confirmation hint removals')
    return {'hints_before': len(markers), 'hints_removed': removed,
            'hints_remaining': len(markers) - removed}


def word_key(word):
    # Do not casefold: that also merges German "Maße" and "Masse". Do not
    # lemmatize or substitute divine names: those are semantic comparisons.
    return unicodedata.normalize('NFC', word).lower()


def forced_alignment(target, reference):
    """Map only matches shared by EVERY maximum-length common subsequence.

    A chosen SequenceMatcher/LCS path can silently select the wrong occurrence
    of a repeated word. Here a token is eligible only if it cannot be skipped
    in any optimum AND all optimum paths match it to the same reference token.
    Punctuation is outside the tokenizer; spelling and word order are retained.
    """
    a = [word_key(t['text']) for t in target]
    b = [word_key(t['text']) for t in reference]
    n, m = len(a), len(b)
    prefix = [[0] * (m + 1) for _ in range(n + 1)]
    suffix = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n):
        for j in range(m):
            prefix[i + 1][j + 1] = (prefix[i][j] + 1 if a[i] == b[j]
                                     else max(prefix[i][j + 1], prefix[i + 1][j]))
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            suffix[i][j] = (suffix[i + 1][j + 1] + 1 if a[i] == b[j]
                             else max(suffix[i + 1][j], suffix[i][j + 1]))
    best = prefix[n][m]
    result = []
    for i in range(n):
        matches = [j for j in range(m)
                   if a[i] == b[j] and prefix[i][j] + 1 + suffix[i + 1][j + 1] == best]
        can_skip = any(prefix[i][j] + suffix[i + 1][j] == best for j in range(m + 1))
        if not matches:
            result.append((None, 'word-not-aligned'))
        elif can_skip or len(matches) != 1:
            result.append((None, 'ambiguous-word-alignment'))
        else:
            result.append((matches[0], 'aligned'))
    return result


def _complete_codes(element, prefix):
    """Reject malformed or wrong-testament members rather than dropping them."""
    raw = element.get('str', element.get('lemma', ''))
    pieces = [p for p in re.split(r'[\s/\\+,;\-]+', raw or '') if p]
    if not pieces:
        return (), False
    codes = set()
    for piece in pieces:
        piece = re.sub(r'^(?:strong|Strong|STRONG):', '', piece).strip('{}[]')
        # This comparison profile accepts classical dictionary numbers only.
        # STEP's broader display normalizer may reduce occurrence/sense suffixes;
        # doing that here would turn an unverified extension into exact evidence.
        match = re.fullmatch(r'([HG]?)(\d+)', piece)
        if not match or (match[1] or prefix) != prefix:
            return (), False
        if not 0 < int(match[2]) <= (8674 if prefix == 'H' else 5624):
            return (), False
        codes.add(prefix + str(int(match[2])))
    return tuple(sorted(codes)), True


@dataclass(frozen=True)
class _Span:
    element: ET.Element
    start: int
    end: int
    codes: tuple[str, ...]
    valid: bool


class _Verse:
    def __init__(self, element, ref):
        self.element = element
        self.text = plain(element)
        self.tokens = tokenize(self.text)
        self.placeholders = [(m.start(), m.end()) for m in PLACEHOLDER.finditer(self.text)]
        self.spans = []
        self.hints = []
        self.parents = {}
        prefix = 'H' if BOOKS.index(ref.split('.')[0]) < 39 else 'G'
        offset = 0

        def visit(node):
            nonlocal offset
            if tag(node) in EXCLUDED:
                if tag(node) == 'NOTE' and node.get('ex') == HINT:
                    self.hints.append(node)
                return
            start = offset
            offset += len(node.text or '')
            for child in node:
                self.parents[child] = node
                visit(child)
                offset += len(child.tail or '')
            if tag(node) in GRAMMAR:
                codes, valid = _complete_codes(node, prefix)
                self.spans.append(_Span(node, start, offset, codes, valid))

        visit(element)
        require(offset == len(self.text), 'Canonical verse offsets differ')
        self.by_element = {span.element: span for span in self.spans}

    def has_placeholder(self, start, end):
        return any(lo < end and hi > start for lo, hi in self.placeholders)

    def hint_span(self, hint):
        if len(hint):
            return None, [], 'structured-uncertainty-note'
        parent = self.parents[hint]
        index = list(parent).index(hint)
        if not index or tag(parent[index - 1]) not in GRAMMAR:
            return None, [], 'no-preceding-strong-span'
        grammar = parent[index - 1]
        if tokenize(grammar.tail or ''):
            return None, [], 'text-between-assignment-and-hint'
        span = self.by_element[grammar]
        if self.has_placeholder(span.start, span.end):
            return span, [], 'target-placeholder-in-span'
        if not span.valid or not span.codes:
            return span, [], 'invalid-target-strong-set'
        if any(tag(e) in GRAMMAR for e in list(grammar.iter())[1:]):
            return span, [], 'nested-target-strong-spans'
        ancestor = parent
        while ancestor is not None:
            if tag(ancestor) in GRAMMAR:
                return span, [], 'nested-target-strong-spans'
            ancestor = self.parents.get(ancestor)
        indices = [i for i, t in enumerate(self.tokens)
                   if t['start'] < span.end and t['end'] > span.start]
        if not indices or any(not (span.start <= self.tokens[i]['start']
                                   and self.tokens[i]['end'] <= span.end) for i in indices):
            return span, [], 'incomplete-target-word-span'
        return span, indices, None

    def confirm_span(self, target_indices, target_codes, alignment):
        # A reference carrying Akribos's own unresolved-assignment marker must
        # not turn another edition's candidate into a confirmed assignment.
        # Retain the whole verse as review evidence: malformed or displaced
        # hints cannot reliably delimit which adjacent span they qualify.
        if self.hints:
            return 'uncertain-reference-verse'
        matches = [alignment[i] for i in target_indices]
        for _, status in matches:
            if status != 'aligned':
                return status
        indices = [index for index, _ in matches]
        if indices != list(range(indices[0], indices[-1] + 1)):
            return 'noncontiguous-reference-span'
        # BK uses literal [?] for unrepresented source occurrences. The word
        # tokenizer omits punctuation, so explicitly reject such gaps rather
        # than treating the words on either side as one uninterrupted phrase.
        if self.has_placeholder(self.tokens[indices[0]]['start'], self.tokens[indices[-1]]['end']):
            return 'reference-placeholder-in-span'
        selected = set(indices)
        codes = set()
        covered = set()
        for span in self.spans:
            overlap = {i for i, t in enumerate(self.tokens)
                       if t['start'] < span.end and t['end'] > span.start}
            if not overlap & selected:
                continue
            if self.has_placeholder(span.start, span.end):
                return 'reference-placeholder-in-span'
            if not span.valid:
                return 'invalid-reference-strong-set'
            # A code attached to a longer phrase does not confirm one word of
            # that phrase. A full phrase may be split into several tagged words.
            if not overlap <= selected:
                return 'reference-annotation-crosses-span'
            if any(not (span.start <= self.tokens[i]['start']
                        and self.tokens[i]['end'] <= span.end) for i in overlap):
                return 'incomplete-reference-word-span'
            covered.update(overlap)
            codes.update(span.codes)
        if covered != selected:
            return 'missing-reference-strong-tags'
        if codes != set(target_codes):
            return 'different-strong-set'
        return 'confirmed'


def _preserved_notes(root):
    result = []
    for note in root.iter():
        if tag(note) not in {'NOTE', 'note'} or note.get('ex') == HINT:
            continue
        clone = copy.deepcopy(note)
        clone.tail = None
        result.append(ET.tostring(clone, encoding='unicode'))
    return result


def _remove_preserving_tail(parent, element):
    index = list(parent).index(element)
    if element.tail:
        if index:
            previous = parent[index - 1]
            previous.tail = (previous.tail or '') + element.tail
        else:
            parent.text = (parent.text or '') + element.tail
    parent.remove(element)


def _verse_index(root, *, include_captions=False):
    # zef_verses also rejects duplicates. Keep an explicit check at the index
    # boundary so a future iterator change cannot turn duplicates into silent
    # last-write-wins source selection.
    result = {}
    for ref, verse in zef_verses(root, include_captions=include_captions):
        require(ref not in result, f'Duplicate verse in confirmation input: {ref}')
        result[ref] = verse
    return result


def prepare_confirmation(version, elb_bk=None, elb_csv=None):
    """Validate a complete release request before any build files are created.

    Parsed references stay in memory. Persist only ``settings``; it deliberately
    contains hashes and profile names, without private filesystem paths.
    """
    requested = elb_bk is not None or elb_csv is not None
    if version == '1.4':
        require(False, 'Version 1.4 requires the separate language-validation stage, which is not available in this command yet')
    if version != '1.3':
        require(not requested, '--elb-bk/--elb-csv require --version 1.3')
        return None
    require(elb_bk is not None and elb_csv is not None,
            'Version 1.3 requires both --elb-bk and --elb-csv reference snapshots')
    paths = {'elb-bk': Path(elb_bk), 'elb-csv': Path(elb_csv)}
    require(paths['elb-bk'].resolve() != paths['elb-csv'].resolve(),
            'Two independent reference snapshots are required')
    hashes = {label: file_hash(path) for label, path in paths.items()}
    require(hashes['elb-bk'] != hashes['elb-csv'],
            'Reference snapshots have identical SHA-256 hashes; two independent sources are required')
    references = {label: parse_xml(path) for label, path in paths.items()}
    for label, tree in references.items():
        verses = _verse_index(tree)
        require(verses, f'No Bible verses found in {label}')
        require(any(tag(node) in GRAMMAR and (node.get('str') or node.get('lemma'))
                    for verse in verses.values() for node in verse.iter()),
                f'No Strong annotations found in {label}')
    return {'references': references, 'settings': {
        'method': METHOD, 'input_profile': INPUT_PROFILE, 'normalization': NORMALIZATION,
        'reference_sha256': hashes}}


@dataclass
class ConfirmationResult:
    root: ET.Element
    audit: list[dict]
    summary: dict


def confirm_uncertainty(target, elb_bk, elb_csv, *, in_place=False):
    """Review every hint and return transformed XML plus a publication-safe audit.

    Inputs are parsed Zefania roots. An absent reference is ``None`` and retains
    every affected hint. Input reference trees are never mutated. By default the
    target is copied. Verse IDs must agree; no implicit verse-number remapping.
    Public audit rows include only target span/code values and decision labels.
    """
    root = target if in_place else copy.deepcopy(target)
    before_text = {ref: plain(v) for ref, v in _verse_index(root, include_captions=True).items()}
    before_strongs = strong_fingerprints(root)
    before_notes = _preserved_notes(root)
    references = {'elb-bk': elb_bk, 'elb-csv': elb_csv}
    verse_maps = {label: (_verse_index(tree) if tree is not None else {})
                  for label, tree in references.items()}
    original_hints = [e for e in root.iter() if tag(e) == 'NOTE' and e.get('ex') == HINT]
    processed = set()
    audit = []
    reasons = Counter()
    reference_counts = {label: Counter() for label in references}
    removed = 0
    for ref, element in zef_verses(root):
        verse = _Verse(element, ref)
        if not verse.hints:
            continue
        source_verses = {}
        alignments = {}
        for label, mapping in verse_maps.items():
            if ref in mapping:
                source_verses[label] = _Verse(mapping[ref], ref)
                alignments[label] = forced_alignment(verse.tokens, source_verses[label].tokens)
        decisions = []
        for hint_number, hint in enumerate(verse.hints, 1):
            processed.add(hint)
            span, indices, failure = verse.hint_span(hint)
            row = {'ref': ref, 'hint': hint_number,
                   'target_token_ids': [verse.tokens[i]['id'] for i in indices],
                   'target_strong': list(span.codes) if span else [],
                   'status': 'retained', 'reason': failure, 'references': {}}
            for label in references:
                if failure:
                    status = 'target-not-eligible'
                elif references[label] is None:
                    status = 'missing-reference-source'
                elif label not in source_verses:
                    status = 'missing-reference-verse'
                else:
                    status = source_verses[label].confirm_span(indices, span.codes, alignments[label])
                row['references'][label] = status
                reference_counts[label][status] += 1
            if not failure:
                statuses = list(row['references'].values())
                if all(status == 'confirmed' for status in statuses):
                    row['status'] = 'confirmed'
                    row['reason'] = 'both-references-confirm-complete-set'
                    decisions.append((verse.parents[hint], hint))
                else:
                    # Keep all per-source failures in the audit; a stable first
                    # failure is the summary category when both fail differently.
                    row['reason'] = next(status for status in statuses if status != 'confirmed')
            audit.append(row)
            reasons[row['reason']] += 1
        # Analyse first, mutate afterwards; offsets and sibling indices therefore
        # always describe the input artifact, including multiple adjacent hints.
        for parent, hint in decisions:
            _remove_preserving_tail(parent, hint)
            removed += 1
    for number, hint in enumerate(original_hints, 1):
        if hint not in processed:
            audit.append({'ref': None, 'hint': number, 'target_token_ids': [],
                          'target_strong': [], 'status': 'retained',
                          'reason': 'outside-supported-verse-text', 'references': {}})
            reasons['outside-supported-verse-text'] += 1
    after_hints = sum(tag(e) == 'NOTE' and e.get('ex') == HINT for e in root.iter())
    require(len(audit) == len(original_hints), 'Incomplete uncertainty review audit')
    require(after_hints == len(original_hints) - removed, 'Unexpected uncertainty-note count')
    require(before_text == {ref: plain(v) for ref, v in zef_verses(root, include_captions=True)},
            'Uncertainty review changed Bible text')
    require(before_strongs == strong_fingerprints(root), 'Uncertainty review changed Strong tags')
    require(before_notes == _preserved_notes(root), 'Uncertainty review changed original notes')
    summary = {'method': METHOD, 'normalization': NORMALIZATION,
               'alignment': 'forced-matches-in-all-optimal-LCS-alignments',
               'hints_before': len(original_hints), 'hints_removed': removed, 'hints_remaining': after_hints,
               'decisions': dict(sorted(reasons.items())),
               'references': {label: dict(sorted(counts.items()))
                              for label, counts in reference_counts.items()},
               'new_strong_assignments': 0, 'changed_strong_assignments': 0,
               'public_audit': 'Target assignments and decisions only; no reference text or associations.'}
    return ConfirmationResult(root, audit, summary)


def confirm_files(target_path, elb_bk_path, elb_csv_path):
    """Read XML snapshots and add hashes; the caller owns writing/history/metadata."""
    paths = [Path(p) if p is not None else None for p in (target_path, elb_bk_path, elb_csv_path)]
    require(paths[0] is not None, 'A target input is required')
    require(all(p is None or p.resolve() != paths[0].resolve() for p in paths[1:]),
            'Reference snapshots must differ from the target')
    if paths[1] is not None and paths[2] is not None:
        require(paths[1].resolve() != paths[2].resolve(), 'Two independent reference snapshots are required')
    hashes = [file_hash(path) if path is not None else None for path in paths]
    if paths[1] is not None and paths[2] is not None:
        require(hashes[1] != hashes[2], 'Reference snapshots have identical SHA-256 hashes; two independent sources are required')
    trees = [parse_xml(path) if path is not None else None for path in paths]
    result = confirm_uncertainty(*trees)
    result.summary['input_sha256'] = hashes[0]
    result.summary['reference_sha256'] = {
        label: value for label, value in zip(('elb-bk', 'elb-csv'), hashes[1:])}
    return result
