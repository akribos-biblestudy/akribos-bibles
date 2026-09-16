"""Synthetic DOM fixtures; no publisher reference text is committed here."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from akribos.csv_reference import (
    CSVReferenceError, cache_to_reference, main, merge_reference_chapters, parse_chapter_html,
)


URL = 'https://www.csv-bibel.de/bibel/example-1'


def link(text='Beispiel', codes='G1519+G3588', *, bcv='40001001', occurrence=1,
         label=None, extra=''):
    classes = ' '.join('strong-' + code.replace(':', '-') for code in codes.split('+'))
    return (f'<a class="strong-link {classes}" data-position="{codes}@{bcv}@{occurrence}@1">'
            f'{text}<span class="strong-no cp-option"> {label if label is not None else codes}'
            f'{extra}</span></a>')


def verse(content, number=1, *, chapter=1, url=URL):
    return (f'<span class="bible-verse vb-verse" name="v{number}">'
            f'<span><button class="btn-verse-no" data-reference="Example {chapter},{number}" '
            f'data-url="{url}#v{number}">{number}</button></span>'
            f'<span class="bible-verse-text vb-verse-text">{content}</span></span>')


def page(content, *, book=40, url=URL):
    return (f'<html><head><meta name="og:url" content="{url}"></head><body>'
            '<h1>Excluded chapter heading</h1>'
            f'<div class="bible-view bible-chapter-view bible-book-{book}">{content}</div>'
            '<p>Excluded copyright footer</p></body></html>')


def parse(content, *, book=40, chapter=1):
    return parse_chapter_html(page(content, book=book), source_url=URL, book=book, chapter=chapter)


def cache_record(html, *, book=40, chapter=1):
    raw = html.encode('utf-8')
    return {'key': f'{book:02}.{chapter:03}', 'book': book, 'chapter': chapter,
            'url': URL, 'retrieved_at': '2026-01-02T03:04:05Z',
            'sha256': hashlib.sha256(raw).hexdigest(),
            'html_gzip_base64': base64.b64encode(gzip.compress(raw, mtime=0)).decode('ascii')}


class CSVReferenceTests(unittest.TestCase):
    def test_complete_multi_code_set_and_word_text(self):
        root = parse(verse('Ein ' + link() + '.'))
        result = root.find('.//VERS')
        self.assertEqual(''.join(result.itertext()), 'Ein Beispiel.')
        self.assertEqual(result.find('gr').get('str'), 'G1519 G3588')
        self.assertEqual(result.find('gr').text, 'Beispiel')

    def test_notes_labels_and_layout_do_not_become_verse_words(self):
        root = parse(verse('Ein <small class="cp-unwrap">freies</small> ' +
                           link('H<span class="format-herr">ERR</span>') +
                           '<sup class="footnote" data-footnote="Private note">a</sup>' +
                           '<span class="cp-none">Hidden reference</span>.<br>Ende'))
        self.assertEqual(''.join(root.find('.//VERS').itertext()), 'Ein freies HERR. Ende')
        self.assertEqual(len(root.findall('.//gr')), 1)

    def test_hebrew_seven_digit_verse_id_and_zero_padded_codes(self):
        root = parse(verse(link(codes='H0430', bcv='1001001', label='H430')), book=1)
        self.assertEqual(root.find('.//gr').get('str'), 'H430')

    def test_parenthetical_components_never_confirm(self):
        root = parse(verse(link(label='(G1519+G3588)', occurrence=-1)))
        self.assertEqual(root.findall('.//gr'), [])
        self.assertEqual(''.join(root.find('.//VERS').itertext()), 'Beispiel')

    def test_approximation_never_confirms_even_positive_position(self):
        root = parse(verse(link(label='~G1519+G3588')))
        self.assertEqual(root.findall('.//gr'), [])

    def test_negative_position_never_confirms_even_plain_label(self):
        self.assertEqual(parse(verse(link(occurrence=-1))).findall('.//gr'), [])

    def test_text_variant_never_confirms(self):
        root = parse(verse(link(extra='<span class="text-variant">TR</span>')))
        self.assertEqual(root.findall('.//gr'), [])
        self.assertEqual(''.join(root.find('.//VERS').itertext()), 'Beispiel')

    def test_variant_range_crosses_separate_nobr_containers(self):
        fragment = (link('Davor', 'G1') + ' <nobr><span class="bible-brackets-open">⌜</span>' +
                    link('Erstes', 'G2') + '</nobr> <nobr>' + link('Zweites', 'G3') +
                    '<span class="bible-brackets-close">⌝</span></nobr> ' + link('Danach', 'G4'))
        root = parse(verse(fragment))
        self.assertEqual([(n.text, n.get('str')) for n in root.findall('.//gr')],
                         [('Davor', 'G1'), ('Danach', 'G4')])
        self.assertEqual(''.join(root.find('.//VERS').itertext()), 'Davor ⌜Erstes Zweites⌝ Danach')

    def test_variant_bracket_inside_link_also_disables_whole_annotation(self):
        fragment = link('<span class="bible-brackets-open">⌜</span>Erstes', 'G2') + ' ' + \
            link('Zweites<span class="bible-brackets-close">⌝</span>', 'G3') + ' ' + link('Danach', 'G4')
        root = parse(verse(fragment))
        self.assertEqual([n.text for n in root.findall('.//gr')], ['Danach'])
        self.assertEqual(''.join(root.find('.//VERS').itertext()), '⌜Erstes Zweites⌝ Danach')

    def test_unbalanced_nested_and_unclassified_variant_ranges_fail(self):
        for content in ('<span class="bible-brackets-open">⌜</span>' + link(),
                        link() + '<span class="bible-brackets-close">⌝</span>',
                        '<span class="bible-brackets-open">⌜</span>' * 2 + link(),
                        '⌜' + link() + '⌝', link('⌜Beispiel⌝')):
            with self.subTest(content=content), self.assertRaises(CSVReferenceError):
                parse(verse(content))

    def test_footnote_variant_brackets_do_not_affect_verse_range(self):
        fragment = ('<sup class="footnote"><span class="bible-brackets-open">⌜</span>'
                    'Fußnotenvariante</sup>' + link())
        root = parse(verse(fragment))
        self.assertEqual(len(root.findall('.//gr')), 1)
        self.assertEqual(''.join(root.find('.//VERS').itertext()), 'Beispiel')

    def test_lexical_subdivision_is_not_silently_dropped(self):
        root = parse(verse(link(codes='H3651:1+H5921', bcv='1001001')), book=1)
        self.assertEqual(root.findall('.//gr'), [])
        self.assertEqual(''.join(root.find('.//VERS').itertext()), 'Beispiel')

    def test_extended_identifiers_leave_entire_set_untagged(self):
        root = parse(verse(link(codes='G1519+G6000')))
        self.assertEqual(root.findall('.//gr'), [])

    def test_inconsistent_codes_fail_instead_of_taking_intersection(self):
        content = link().replace('strong-G3588', 'strong-G3739')
        with self.assertRaisesRegex(CSVReferenceError, 'disagree'):
            parse(verse(content))

    def test_visible_plain_set_must_match_attributes(self):
        with self.assertRaisesRegex(CSVReferenceError, 'disagree'):
            parse(verse(link(label='G1519')))

    def test_wrong_testament_rejected(self):
        with self.assertRaisesRegex(CSVReferenceError, 'prefix'):
            parse(verse(link(codes='H430')))

    def test_annotation_verse_identity_checked(self):
        with self.assertRaisesRegex(CSVReferenceError, 'another verse'):
            parse(verse(link(bcv='40001002')))

    def test_page_and_verse_identities_checked(self):
        with self.assertRaisesRegex(CSVReferenceError, 'reference differs'):
            parse(verse(link(), chapter=2))
        with self.assertRaisesRegex(CSVReferenceError, 'book'):
            parse_chapter_html(page(verse(link())), source_url=URL, book=41, chapter=1)
        with self.assertRaisesRegex(CSVReferenceError, 'canonical URL'):
            parse_chapter_html(page(verse(link()), url=URL+'-wrong'), source_url=URL, book=40, chapter=1)

    def test_duplicate_verse_fails(self):
        with self.assertRaisesRegex(CSVReferenceError, 'Duplicate verse'):
            parse(verse(link()) + verse(link()))

    def test_anonymous_poetry_continuation_uses_verified_previous_verse(self):
        continuation = ('<p><span class="bible-verse"><span class="bible-verse-text">' +
                        link('Fortsetzung', 'G2') + '</span></span></p>')
        root = parse(verse(link('Anfang', 'G1')) + continuation)
        self.assertEqual(len(root.findall('.//VERS')), 1)
        self.assertEqual(''.join(root.find('.//VERS').itertext()), 'Anfang Fortsetzung')
        self.assertEqual([n.get('str') for n in root.findall('.//gr')], ['G1', 'G2'])
        with self.assertRaisesRegex(CSVReferenceError, 'preceding verse'):
            parse(verse(link()) + continuation.replace('40001001', '40001002'))
        with self.assertRaisesRegex(CSVReferenceError, 'preceding named verse'):
            parse(continuation)

    def test_continuation_without_explicit_identity_fails(self):
        continuation = '<span class="bible-verse"><span class="bible-verse-text">Wort</span></span>'
        with self.assertRaisesRegex(CSVReferenceError, 'preceding verse'):
            parse(verse(link()) + continuation)

    def test_shared_group_links_and_empty_star_markers_remain_untagged(self):
        primary = link('Mehrdeutig', 'G1').replace('strong-G1', 'strong-G1 strong-G2')
        secondary = link('', 'G2', label='/G2').replace('strong-G2', 'strong-G1 strong-G2')
        marker = link('', 'G3', label='*G3')
        root = parse(verse(primary + secondary + marker + ' ' + link('Danach', 'G4')))
        self.assertEqual(''.join(root.find('.//VERS').itertext()), 'Mehrdeutig Danach')
        self.assertEqual([n.get('str') for n in root.findall('.//gr')], ['G4'])

    def test_profile_failure_always_identifies_chapter_and_source_url(self):
        with self.assertRaises(CSVReferenceError) as error:
            parse('<span class="bible-verse" name="bad"></span>')
        self.assertIn('40.1', str(error.exception))
        self.assertIn(URL, str(error.exception))

    def test_empty_challenge_or_unrelated_page_fails(self):
        with self.assertRaisesRegex(CSVReferenceError, 'chapter view'):
            parse_chapter_html('<html><p>Access challenge</p></html>', source_url=URL, book=40, chapter=1)
        with self.assertRaisesRegex(CSVReferenceError, 'No verse'):
            parse('')

    def test_strong_links_need_labels_and_positions(self):
        with self.assertRaisesRegex(CSVReferenceError, 'label'):
            parse(verse('<a class="strong-link strong-G1" data-position="G1@40001001@1@1">Wort</a>'))
        with self.assertRaisesRegex(CSVReferenceError, 'data-position'):
            parse(verse(link().replace('40001001@1@1', 'bad')))

    def test_nested_annotations_are_rejected(self):
        with self.assertRaisesRegex(CSVReferenceError, 'Nested Strong'):
            parse(verse(link(text=link())))

    def test_merge_orders_chapters_and_preserves_inputs(self):
        first = parse(verse(link()))
        second = parse(verse(link(bcv='40002001'), chapter=2), chapter=2)
        before = ET.tostring(first)
        merged = merge_reference_chapters([second, first])
        self.assertEqual([c.get('cnumber') for c in merged.findall('.//CHAPTER')], ['1', '2'])
        self.assertEqual(ET.tostring(first), before)
        self.assertIn('Christliche Schriftenverbreitung', merged.findtext('INFORMATION/rights'))
        self.assertEqual(merged.findtext('INFORMATION/source'), URL)

    def test_merge_refuses_same_chapter_twice(self):
        root = parse(verse(link()))
        with self.assertRaisesRegex(CSVReferenceError, 'Duplicate reference chapter'):
            merge_reference_chapters([root, root])

    def test_cache_hash_checked_and_output_reproducible(self):
        record = cache_record(page(verse(link())))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'chunk-0000.json'
            path.write_text(json.dumps([record]))
            first = cache_to_reference(directory)
            self.assertEqual(ET.tostring(first), ET.tostring(cache_to_reference(directory)))
            manifest = json.loads(first.findtext('INFORMATION/reference_cache_manifest'))
            self.assertEqual(manifest[0]['sha256'], record['sha256'])
            self.assertNotIn('html_gzip_base64', manifest[0])
            record['sha256'] = '0' * 64
            path.write_text(json.dumps([record]))
            with self.assertRaisesRegex(CSVReferenceError, 'SHA256 mismatch'):
                cache_to_reference(directory)

    def test_duplicate_cache_chapter_fails(self):
        record = cache_record(page(verse(link())))
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'chunk-0.json').write_text(json.dumps([record, record]))
            with self.assertRaisesRegex(CSVReferenceError, 'Duplicate cached chapter'):
                cache_to_reference(directory)

    def test_cli_writes_importable_private_xml(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'chunk-0.json').write_text(json.dumps([cache_record(page(verse(link())))]))
            output = root / 'private' / 'reference.xml'
            main(['--cache-dir', directory, '--output', str(output)])
            parsed = ET.parse(output).getroot()
            self.assertEqual(parsed.tag, 'XMLBIBLE')
            self.assertEqual(len(parsed.findall('.//VERS')), 1)


if __name__ == '__main__':
    unittest.main()
