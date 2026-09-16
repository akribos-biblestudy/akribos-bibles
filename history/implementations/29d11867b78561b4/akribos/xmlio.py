"""Mixed-content XML operations. Annotation/note subtrees are never flattened."""
from __future__ import annotations
import copy
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from .common import BOOKS, canonical_ref, require, strongs, tokenize, atomic_text
from .importers import parse_xml, tag

EXCLUDED = {'NOTE', 'XREF', 'REMARK', 'note', 'reference'}


def slots(element):
    """Yield canonical text slots and absolute Unicode-character offsets."""
    offset = 0
    def walk(e):
        nonlocal offset
        if tag(e) in EXCLUDED:
            return
        if e.text:
            yield e, 'text', offset, offset + len(e.text)
            offset += len(e.text)
        for c in e:
            yield from walk(c)
            if c.tail:
                yield c, 'tail', offset, offset + len(c.tail)
                offset += len(c.tail)
    yield from walk(element)


def plain(element):
    return ''.join(getattr(e, attr) for e, attr, _, _ in slots(element))


def zef_verses(root, include_captions=False):
    require(tag(root) == 'XMLBIBLE', 'Expected Zefania XMLBIBLE')
    seen = set()
    for b in root.findall('BIBLEBOOK'):
        number = int(b.get('bnumber', '0'))
        require(1 <= number <= 66, 'This profile supports the 66-book canon')
        for c in b.findall('CHAPTER'):
            for v in c:
                if tag(v) != 'VERS' and not (include_captions and tag(v) == 'CAPTION'):
                    continue
                ref = f"{BOOKS[number-1]}.{int(c.get('cnumber'))}.{int(v.get('vnumber', '0'))}"
                require(ref not in seen, f'Duplicate verse: {ref}')
                seen.add(ref)
                yield ref, v


def note_fingerprints(root):
    result = []
    for e in root.iter():
        if tag(e) in {'NOTE', 'note'}:
            clone = copy.deepcopy(e)
            clone.tail = None
            result.append(ET.tostring(clone, encoding='unicode'))
    return result


def strong_fingerprints(root):
    return [dict(e.attrib) for e in root.iter() if tag(e) in {'gr', 'GRAM', 'w'}]


def normalize_gr(root):
    def visit(e):
        if tag(e) in EXCLUDED: return
        if tag(e) == 'GRAM': e.tag = 'gr'
        for c in e: visit(c)
    visit(root)


def apply_edits(element, edits):
    """Non-overlapping replacements in original offsets; preserve all XML nodes.

    A word may cross a STYLE or NOTE boundary. Put its replacement at the first
    affected text slot, retaining all elements, their attributes and their order.
    NOTE.text and descendants are never visited. NOTE.tail is canonical text.
    """
    source = plain(element)
    ordered = sorted(edits, key=lambda e: (e['start'], e['end']))
    previous = 0
    for edit in ordered:
        require(previous <= edit['start'] < edit['end'] <= len(source), 'Overlapping/invalid edit')
        require(source[edit['start']:edit['end']] == edit['before'], 'Edit precondition failed')
        previous = edit['end']
    oldslots = list(slots(element))
    for e, attr, lo, hi in reversed(oldslots):
        text = getattr(e, attr)
        for edit in reversed(ordered):
            a, b = edit['start'], edit['end']
            if a >= hi or b <= lo:
                continue
            replacement = edit['after'] if lo <= a < hi else ''
            text = text[:max(0, a-lo)] + replacement + text[min(hi-lo, b-lo):]
        setattr(e, attr, text)
    expected = source
    for edit in reversed(ordered):
        expected = expected[:edit['start']] + edit['after'] + expected[edit['end']:]
    require(plain(element) == expected, 'Mixed-content edit verification failed')


def verse_tokens(v, ref):
    text = plain(v)
    tokens = tokenize(text)
    offset = 0
    spans = []
    def walk(e):
        nonlocal offset
        if tag(e) in EXCLUDED:
            return
        lo = offset
        offset += len(e.text or '')
        for c in e:
            walk(c)
            offset += len(c.tail or '')
        if tag(e) in {'gr', 'GRAM', 'w'}:
            prefix = 'H' if BOOKS.index(ref.split('.')[0]) < 39 else 'G'
            codes = strongs(e.get('str', e.get('lemma', '')), prefix)
            codes = [s for s in codes if 0 < int(s[1:]) <= (8674 if s[0] == 'H' else 5624)]
            spans.append((lo, offset, codes))
    walk(v)
    for t in tokens:
        t['strong'] = sorted({s for lo, hi, ss in spans if lo <= t['start'] and t['end'] <= hi for s in ss})
    return text, tokens


def annotate(v, tokens, hints=True):
    """Add word tags only in plain slots. Existing tags/notes stay unchanged."""
    parents = {c:p for p in v.iter() for c in p}
    assigned = 0
    for node, attr, lo, hi in reversed(list(slots(v))):
        # A tail belongs to its parent, never to the preceding note or gr.
        owner = node if attr == 'text' else parents[node]
        ancestor = owner
        inside_gr = False
        while ancestor is not None:
            if tag(ancestor) in {'gr', 'GRAM'}:
                inside_gr = True
            ancestor = parents.get(ancestor)
        if inside_gr:
            continue
        chosen = [t for t in tokens if t.get('strong') and lo <= t['start'] and t['end'] <= hi]
        if not chosen:
            continue
        original = getattr(node, attr)
        if attr == 'text':
            parent, index = node, 0
        else:
            parent, index = parents[node], list(parents[node]).index(node)+1
        setattr(node, attr, original[:chosen[0]['start']-lo])
        for i, t in enumerate(chosen):
            gr = ET.Element('gr', {'str':' '.join(s[1:] for s in t['strong'])})
            gr.text = original[t['start']-lo:t['end']-lo]
            parent.insert(index, gr); index += 1
            last = gr
            if hints and t.get('uncertain', t.get('method') in {'lexicon', 'concordance'}):
                hint = ET.Element('NOTE', {'type':'x-explanation', 'ex':'nl:akribosStrongUncertainty'})
                hint.text = 'Automatische Wortzuordnung; fachlich noch nicht bestätigt.'
                parent.insert(index, hint); index += 1
                last = hint
            end = chosen[i+1]['start']-lo if i+1 < len(chosen) else len(original)
            last.tail = original[t['end']-lo:end]
            assigned += 1
    return assigned


def write_xml(path, root):
    # Never indent mixed content: pretty printing can change the Bible text.
    # Only structural whitespace is normalized: one verse per line for Git.
    for e in root.iter():
        if tag(e) in {'XMLBIBLE', 'BIBLEBOOK', 'CHAPTER'}:
            if not (e.text or '').strip(): e.text = '\n'
            for child in e:
                if not (child.tail or '').strip(): child.tail = '\n'
    atomic_text(path, '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode') + '\n')


def import_osis(path):
    """OSIS container + milestone verses; retain inline notes and formatting.

    Deliberately fail on ambiguous ranges/mixed verse profiles. Export conversion
    cannot preserve every OSIS feature; notes preserve their text/inline markup
    as Zefania NOTE/STYLE, and raw source attributes remain in data-osis JSON.
    """
    import json
    source = parse_xml(path)
    original_note_count = sum(tag(e)=='note' for e in source.iter())
    allverses = [v for v in source.iter() if tag(v) == 'verse']
    container = [v for v in allverses if v.get('osisID') and not v.get('sID')]
    milestone = [v for v in allverses if v.get('sID')]
    require(not (container and milestone), 'Mixed OSIS verse profiles')
    rows = []
    if container:
        rows = [(canonical_ref(v.get('osisID')), copy.deepcopy(v)) for v in container]
    else:
        current = None
        active = None
        stack = []
        def append(text):
            if current is None or not text:
                return
            p = stack[-1] if stack else current
            if len(p): p[-1].tail = (p[-1].tail or '')+text
            else: p.text = (p.text or '')+text
        def visit(e):
            nonlocal current, active, stack
            if tag(e) == 'verse':
                if e.get('sID'):
                    require(current is None, 'Unclosed OSIS milestone')
                    active = canonical_ref(e.get('osisID') or e.get('sID'))
                    current = ET.Element('verse'); stack = []
                elif e.get('eID'):
                    require(active == canonical_ref(e.get('eID')), 'Mismatched OSIS milestone')
                    rows.append((active, current)); current = None; active = None; stack = []
                return
            clone = None
            if current is not None:
                clone = ET.SubElement(stack[-1] if stack else current, tag(e), e.attrib)
                stack.append(clone)
            append(e.text)
            for c in e:
                visit(c); append(c.tail)
            if clone is not None and stack and stack[-1] is clone:
                stack.pop()
        visit(source)
        require(current is None, 'Missing OSIS eID')
    require(rows, 'No OSIS verses')
    output = ET.Element('XMLBIBLE', {'biblename':'OSIS import', 'type':'x-bible'})
    ET.SubElement(output, 'INFORMATION')
    books, chapters, seen = {}, {}, set()
    for ref, v in rows:
        require(ref not in seen, f'Duplicate OSIS reference {ref}'); seen.add(ref)
        book, chapter, verse = ref.split('.')
        if book not in books: books[book] = ET.SubElement(output,'BIBLEBOOK',{'bnumber':str(BOOKS.index(book)+1),'bname':book})
        if (book,chapter) not in chapters: chapters[book,chapter] = ET.SubElement(books[book],'CHAPTER',{'cnumber':chapter})
        v.tag = 'VERS'; v.attrib = {'vnumber':verse}; v.tail = None
        for e in list(v.iter())[1:]:
            oldtag, attrs = tag(e), dict(e.attrib)
            if oldtag == 'w':
                codes = strongs(attrs.get('lemma',''), 'H' if BOOKS.index(book)<39 else 'G')
                e.tag='gr'; e.attrib={'str':' '.join(s[1:] for s in codes)}
                if attrs.get('morph'): e.set('data-osis-morph',attrs['morph'])
            elif oldtag == 'note':
                e.tag='NOTE'; e.attrib={'type':'x-studynote','data-osis':json.dumps(attrs,ensure_ascii=False,sort_keys=True)}
            elif oldtag in {'lb','br'}:
                e.tag='BR'
            else:
                e.tag='STYLE'; e.attrib={'data-osis-tag':oldtag,'data-osis':json.dumps(attrs,ensure_ascii=False,sort_keys=True)}
        chapters[book,chapter].append(v)
    require(sum(tag(e)=='NOTE' for e in output.iter())==original_note_count,
            'OSIS notes outside supported verse containers/milestones; import stopped to prevent note loss')
    return output
