"""Parse privately cached csv-bibel.de chapter HTML as comparison-only Zefania.

No network requests are made here. Only the observed chapter DOM profile is
accepted. Parenthetical, approximate and text-variant annotations remain plain
text, so they cannot confirm an existing Strong assignment. Source HTML/XML
belongs outside the public repository.
"""
from __future__ import annotations

import copy
import argparse
import base64
import gzip
import hashlib
import io
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

# Public book index observed on csv-bibel.de, 2026-09-16. Its chapter
# numbering has Joel 1-4 and Malachi 1-3; do not substitute an English index.
CSV_CHAPTER_COUNTS = (
    50, 40, 27, 36, 34, 24, 21, 4, 31, 24, 22, 25, 29, 36, 10, 13, 10, 42,
    150, 31, 12, 8, 66, 52, 5, 48, 12, 14, 4, 9, 1, 4, 7, 3, 3, 3, 2, 14, 3,
    28, 16, 24, 21, 28, 16, 16, 13, 6, 6, 4, 4, 5, 3, 6, 4, 3, 1, 13, 5,
    5, 3, 5, 1, 1, 1, 22,
)


class CSVReferenceError(ValueError):
    """The cached page does not satisfy the explicit reference profile."""


@dataclass
class _Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list = field(default_factory=list)

    @property
    def classes(self):
        return set(self.attrs.get('class', '').split())

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, _Node):
                yield from child.walk()

    def text(self):
        return ''.join(child.text() if isinstance(child, _Node) else child
                       for child in self.children)


class _DOM(HTMLParser):
    VOID = frozenset('area base br col embed hr img input link meta param source track wbr'.split())

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node('document')
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def _need(condition, message):
    if not condition:
        raise CSVReferenceError(message)


def _source_url(url):
    parsed = urlsplit(url)
    _need(parsed.scheme == 'https' and parsed.netloc in {'www.csv-bibel.de', 'csv-bibel.de'}
          and parsed.path.startswith('/bibel/') and not parsed.query and not parsed.fragment,
          'Expected an HTTPS csv-bibel.de chapter URL')
    return url


def _root(urls):
    root = ET.Element('XMLBIBLE', {'biblename': 'Elberfelder Übersetzung (Edition CSV Hückeswagen)',
                                 'type': 'x-bible'})
    info = ET.SubElement(root, 'INFORMATION')
    for key, value in {
        'title': 'Elberfelder Übersetzung (Edition CSV Hückeswagen)',
        'identifier': 'reference.elb-csv',
        'creator': 'Christliche Schriftenverbreitung e.V.',
        'language': 'ger',
        'rights': '© Christliche Schriftenverbreitung e.V.',
        'source': '\n'.join(sorted(set(urls))),
        'description': 'Private Vergleichsreferenz aus zwischengespeicherten Kapitelseiten; '
                       'keine Weiterveröffentlichung des Referenztextes.',
    }.items():
        ET.SubElement(info, key).text = value
    return root


def _append_text(parent, text):
    if len(parent):
        parent[-1].tail = (parent[-1].tail or '') + text
    else:
        parent.text = (parent.text or '') + text


def _hidden(node):
    return bool(node.classes & {'strong-no', 'footnote', 'cp-none', 'text-variant'}) \
        or node.tag in {'script', 'style', 'button'}


def _word_text(node):
    if _hidden(node):
        return ''
    if node.tag == 'br':
        return ' '
    return ''.join(_word_text(child) if isinstance(child, _Node) else child
                   for child in node.children)


def _code_set(raw):
    if not re.fullmatch(r'[HG]\d+(?::\d+)?(?:\+[HG]\d+(?::\d+)?)*', raw):
        return None
    def canonical(part):
        number, separator, sense = part[1:].partition(':')
        return part[0] + str(int(number)) + (separator + str(int(sense)) if separator else '')
    return tuple(sorted({canonical(part) for part in raw.split('+')}))


def _annotation(node, book, chapter, verse):
    """Return an exact full set, or None for explicitly qualified annotations."""
    nested = list(node.walk())
    _need(sum('strong-link' in n.classes for n in nested) == 1,
          'Nested Strong links are unsupported')
    labels = [n for n in nested if 'strong-no' in n.classes]
    _need(len(labels) == 1, 'Each Strong link needs exactly one visible Strong label')
    position = node.attrs.get('data-position', '')
    parts = position.split('@')
    _need(len(parts) == 4 and re.fullmatch(r'\d{7,8}', parts[1]) is not None
          and re.fullmatch(r'-?\d+', parts[2]) is not None
          and re.fullmatch(r'\d+', parts[3]) is not None,
          'Unrecognized Strong data-position')
    _need(int(parts[1]) == book * 1000000 + chapter * 1000 + verse,
          'Strong annotation belongs to another verse')
    prefix = 'H' if book < 40 else 'G'
    position_codes = _code_set(parts[0])
    _need(position_codes is not None, 'Malformed complete Strong set in data-position')
    classes = [c[7:] for c in node.classes if c.startswith('strong-') and c != 'strong-link']
    _need(classes and all(re.fullmatch(r'[HG]\d+(?:-\d+)?', c) for c in classes),
          'Malformed Strong classes')
    class_codes = _code_set('+'.join(c.replace('-', ':') for c in classes))
    shared_group = position_codes != class_codes and set(position_codes) < set(class_codes)
    _need(position_codes == class_codes or shared_group, 'Strong classes and data-position disagree')
    _need(all(c.startswith(prefix) for c in position_codes), 'Strong testament prefix differs')
    label = labels[0].text().strip()
    # The website uses parentheses for components of translated phrases, ~ for
    # qualified alignment and text-variant for readings such as NA/TR. Do not
    # turn any of those into unconditional evidence.
    if shared_group or int(parts[2]) <= 0 or any('text-variant' in n.classes for n in nested) \
            or any(char in label for char in ('(', ')', '~')):
        return None
    label_codes = _code_set(label)
    if label_codes is None:
        return None
    _need(label_codes == position_codes, 'Visible label and complete Strong set disagree')
    if any(':' in c for c in position_codes):
        return None
    # Extended CSV identifiers are not silently truncated to standard Strongs.
    if any(not 0 < int(c[1:]) <= (8674 if prefix == 'H' else 5624) for c in position_codes):
        return None
    return position_codes


def _render(node, parent, book, chapter, verse, variant_state, *, suppress_annotations=False):
    if _hidden(node):
        return
    opening = 'bible-brackets-open' in node.classes
    closing = 'bible-brackets-close' in node.classes
    if opening or closing:
        _need(opening != closing, 'Ambiguous variant bracket marker')
        _need(_word_text(node) == ('⌜' if opening else '⌝'), 'Unknown variant bracket text')
        if opening:
            _need(not variant_state['open'], 'Nested variant bracket range')
            variant_state['open'] = True
        else:
            _need(variant_state['open'], 'Variant bracket closes without opening')
            variant_state['open'] = False
        _append_text(parent, _word_text(node))
        return
    if node.tag == 'br':
        _append_text(parent, ' ')
        return
    if 'strong-link' in node.classes:
        codes = _annotation(node, book, chapter, verse)
        text = _word_text(node)
        _need(bool(text.strip()) or codes is None, 'Empty Strong word span')
        has_brackets = any(n.classes & {'bible-brackets-open', 'bible-brackets-close'}
                           for n in node.walk())
        _need(has_brackets or not any(c in text for c in '⌜⌝'),
              'Unclassified variant bracket in Strong word')
        if codes and not variant_state['open'] and not has_brackets and not suppress_annotations:
            ET.SubElement(parent, 'gr', {'str': ' '.join(codes)}).text = text
        else:
            # Traverse even an untagged link: a bracket inside it can open or
            # close a range extending across later sibling/container elements.
            for child in node.children:
                if isinstance(child, _Node):
                    _render(child, parent, book, chapter, verse, variant_state, suppress_annotations=True)
                else:
                    _need(not any(c in child for c in '⌜⌝'), 'Unclassified variant bracket in verse')
                    _append_text(parent, child)
        return
    # Unknown markup inside the text is preserved as text, never interpreted
    # as an annotation. Supplied words (<small>) remain present but untagged.
    for child in node.children:
        if isinstance(child, _Node):
            _render(child, parent, book, chapter, verse, variant_state,
                    suppress_annotations=suppress_annotations)
        else:
            _need(not any(c in child for c in '⌜⌝'), 'Unclassified variant bracket in verse')
            _append_text(parent, child)


def parse_chapter_html(html, *, source_url, book, chapter):
    """Parse a cached chapter; every profile error includes chapter and URL."""
    try:
        return _parse_chapter_html(html, source_url=source_url, book=book, chapter=chapter)
    except (CSVReferenceError, ValueError, TypeError) as error:
        raise CSVReferenceError(f'{book}.{chapter} ({source_url}): {error}') from error


def _parse_chapter_html(html, *, source_url, book, chapter):
    """Parse one cached chapter into Zefania; fail on mismatched/duplicate IDs.

    ``book`` is the Zefania book number (1–66), ``chapter`` the expected chapter.
    They are checked against the page container, verse buttons and annotations.
    The caller controls fetching, robots pacing and private cache storage.
    """
    _source_url(source_url)
    _need(isinstance(book, int) and 1 <= book <= 66 and isinstance(chapter, int)
          and 1 <= chapter <= 150, 'Invalid expected book/chapter')
    parser = _DOM()
    parser.feed(html)
    parser.close()
    nodes = list(parser.root.walk())
    views = [n for n in nodes if {'bible-view', 'bible-chapter-view'} <= n.classes]
    _need(len(views) == 1, 'Expected exactly one Bible chapter view')
    view = views[0]
    _need({c for c in view.classes if c.startswith('bible-book-')} == {f'bible-book-{book}'},
          'Chapter view book does not match expected book')
    for node in nodes:
        if node.tag == 'meta' and node.attrs.get('name') == 'og:url':
            _need(node.attrs.get('content') == source_url, 'Page canonical URL differs')
    def verse_nodes(node, inside_verse=False):
        if 'bible-verse' in node.classes:
            if not inside_verse:
                yield node
                inside_verse = True
            else:
                # Poetry/quotations can contain anonymous bible-verse spans
                # within the named outer verse (observed in Genesis 25:23).
                _need(not node.attrs.get('name'), 'Nested named verse is unsupported')
        for child in node.children:
            if isinstance(child, _Node):
                yield from verse_nodes(child, inside_verse)

    verses = list(verse_nodes(view))
    _need(bool(verses), 'No verse nodes in chapter page')
    root = _root([source_url])
    out_book = ET.SubElement(root, 'BIBLEBOOK', {'bnumber': str(book)})
    out_chapter = ET.SubElement(out_book, 'CHAPTER', {'cnumber': str(chapter)})
    seen = set()
    out = None
    vno = None
    variant_state = {'open': False}
    for verse in verses:
        name = verse.attrs.get('name')
        buttons = [n for n in verse.walk() if n.tag == 'button' and 'btn-verse-no' in n.classes]
        if name is not None:
            _need(not variant_state['open'], 'Unclosed variant bracket range in verse')
            number = re.fullmatch(r'v([1-9]\d*)', name)
            _need(number is not None, 'Missing or malformed verse ID')
            vno = int(number[1])
            _need(vno not in seen, 'Duplicate verse ID')
            seen.add(vno)
            _need(len(buttons) == 1, 'Expected one reference button per verse')
            button = buttons[0]
            reference = re.search(r'\s(\d+),(\d+)$', button.attrs.get('data-reference', ''))
            _need(reference is not None and (int(reference[1]), int(reference[2])) == (chapter, vno)
                  and button.attrs.get('data-url') == source_url + f'#v{vno}',
                  'Verse button reference differs from expected chapter/verse')
            out = ET.SubElement(out_chapter, 'VERS', {'vnumber': str(vno)})
        else:
            # Genesis 25:23 and other poetic quotations continue one verse in
            # a separate anonymous block. Do not infer identity from position
            # alone: every annotation must explicitly name the preceding verse.
            _need(out is not None and not buttons, 'Anonymous verse without preceding named verse')
            positions = [n.attrs.get('data-position', '').split('@')
                         for n in verse.walk() if 'strong-link' in n.classes]
            _need(positions and all(len(p) == 4 and re.fullmatch(r'\d{7,8}', p[1])
                                   and int(p[1]) == book * 1000000 + chapter * 1000 + vno
                                   for p in positions),
                  'Continuation Strong positions do not identify the preceding verse')
            _append_text(out, ' ')
        texts = [n for n in verse.walk() if 'bible-verse-text' in n.classes]
        _need(len(texts) == 1, 'Expected exactly one text span per verse')
        _render(texts[0], out, book, chapter, vno, variant_state)
        if not ''.join(out.itertext()).strip():
            # Some numbered verses have no main-text reading in this edition
            # (observed in Mark 15:28). Its textual variant is only a footnote;
            # importing that note as verse text would change the witness.
            _need(name is not None and not variant_state['open']
                  and any('footnote' in n.classes and n.attrs.get('data-footnote')
                          for n in texts[0].walk())
                  and not any('strong-link' in n.classes for n in texts[0].walk()),
                  'Empty verse text without an explicit note-only verse')
            out_chapter.remove(out)
            out = None
    _need(not variant_state['open'], 'Unclosed variant bracket range in verse')
    _need(len(out_chapter) > 0, 'No main-text verses in chapter page')
    return root


def merge_reference_chapters(chapters):
    """Combine parsed private references, refusing duplicated chapter/verse IDs."""
    sources, verses = set(), {}
    for root in chapters:
        _need(root.tag == 'XMLBIBLE' and root.findtext('INFORMATION/identifier') == 'reference.elb-csv',
              'Expected a parsed CSV reference chapter')
        sources.update((root.findtext('INFORMATION/source') or '').splitlines())
        for book in root.findall('BIBLEBOOK'):
            for chapter in book.findall('CHAPTER'):
                key = (int(book.get('bnumber')), int(chapter.get('cnumber')))
                _need(key not in verses, 'Duplicate reference chapter')
                values = chapter.findall('VERS')
                _need(len({v.get('vnumber') for v in values}) == len(values), 'Duplicate reference verse')
                verses[key] = values
    _need(bool(verses), 'No reference chapters supplied')
    root = _root(sources)
    books = {}
    for (bno, cno), values in sorted(verses.items()):
        if bno not in books:
            books[bno] = ET.SubElement(root, 'BIBLEBOOK', {'bnumber': str(bno)})
        chapter = ET.SubElement(books[bno], 'CHAPTER', {'cnumber': str(cno)})
        for verse in sorted(values, key=lambda v: int(v.get('vnumber'))):
            chapter.append(copy.deepcopy(verse))
    return root


def require_complete_reference(root):
    """Require every chapter in the publisher's index, without inventing verses."""
    expected = {(book, chapter) for book, count in enumerate(CSV_CHAPTER_COUNTS, 1)
                for chapter in range(1, count + 1)}
    actual = [(int(book.get('bnumber')), int(chapter.get('cnumber')))
              for book in root.findall('BIBLEBOOK') for chapter in book.findall('CHAPTER')]
    _need(len(actual) == len(set(actual)), 'Duplicate reference chapter')
    missing, extra = expected - set(actual), set(actual) - expected
    _need(not missing and not extra,
          f'Incomplete CSV reference: {len(missing)} missing chapters, {len(extra)} unexpected chapters; '
          f'first missing={sorted(missing)[:5]}, first unexpected={sorted(extra)[:5]}')


def cache_to_reference(cache_dir, *, require_complete=False):
    """Verify exported browser-cache chunks and return XML with fixed provenance.

    Expected records contain key, book, chapter, url, retrieved_at, sha256 and
    html_gzip_base64. The hash covers the original decompressed UTF-8 bytes.
    Neither the current time nor local filesystem names enter the output.
    """
    paths = sorted(Path(cache_dir).glob('chunk*.json'))
    _need(bool(paths), 'No chunk*.json browser cache files found')
    chapters, manifest = [], []
    seen_keys, seen_hashes = set(), set()
    for path in paths:
        records = json.loads(path.read_text(encoding='utf-8'))
        _need(isinstance(records, list), 'Cache chunk must contain an array of records')
        for record in records:
            _need(isinstance(record, dict), 'Cache entry must be an object')
            context = f"{record.get('key', '?')} ({record.get('url', '?')})"
            def check(condition, message):
                _need(condition, f'{context}: {message}')
            check({'key', 'book', 'chapter', 'url', 'retrieved_at', 'sha256', 'html_gzip_base64'} <= record.keys(),
                  'Cache entry is missing required provenance')
            book, chapter = record['book'], record['chapter']
            check(type(book) is int and type(chapter) is int, 'Cache book/chapter must be integers')
            key = f'{book:02}.{chapter:03}'
            check(record['key'] == key, 'Cache key differs from book/chapter')
            check(key not in seen_keys, 'Duplicate cached chapter')
            seen_keys.add(key)
            digest = record['sha256']
            check(isinstance(digest, str) and re.fullmatch(r'[0-9a-f]{64}', digest),
                  'Malformed cached HTML SHA256')
            check(digest not in seen_hashes, 'Same cached HTML content assigned to multiple chapters')
            seen_hashes.add(digest)
            try:
                packed = base64.b64decode(record['html_gzip_base64'], validate=True)
                with gzip.GzipFile(fileobj=io.BytesIO(packed)) as stream:
                    raw = stream.read(16 * 1024 * 1024 + 1)
                html = raw.decode('utf-8')
            except (ValueError, OSError, EOFError, TypeError) as error:
                raise CSVReferenceError(f'{context}: Invalid cached HTML encoding: {error}') from error
            check(len(raw) <= 16 * 1024 * 1024, 'Chapter HTML exceeds parser size limit')
            check(hashlib.sha256(raw).hexdigest() == digest, 'Cached HTML SHA256 mismatch')
            chapters.append(parse_chapter_html(html, source_url=record['url'], book=book, chapter=chapter))
            check(isinstance(record['retrieved_at'], str) and bool(record['retrieved_at']),
                  'Cache retrieval timestamp is missing')
            manifest.append({k: record[k] for k in ('key', 'book', 'chapter', 'url', 'retrieved_at', 'sha256')})
    root = merge_reference_chapters(chapters)
    if require_complete:
        require_complete_reference(root)
    manifest.sort(key=lambda item: item['key'])
    serialized = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    info = root.find('INFORMATION')
    ET.SubElement(info, 'reference_cache_manifest').text = serialized
    ET.SubElement(info, 'reference_cache_sha256').text = hashlib.sha256(serialized.encode('utf-8')).hexdigest()
    return root


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-complete', action='store_true',
                        help='Require all 1,189 chapters in the CSV publisher book index')
    args = parser.parse_args(argv)
    root = cache_to_reference(args.cache_dir, require_complete=args.require_complete)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = ET.tostring(root, encoding='utf-8', xml_declaration=True) + b'\n'
    temporary = args.output.with_name(args.output.name + '.tmp')
    temporary.write_bytes(payload)
    temporary.replace(args.output)
    print(json.dumps({'chapters': len(root.findall('.//CHAPTER')),
                      'verses': len(root.findall('.//VERS')),
                      'sha256': hashlib.sha256(payload).hexdigest()}, sort_keys=True))


if __name__ == '__main__':
    main()
