import copy
import itertools
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from akribos.common import DataError, tokenize
from akribos.confirm import HINT, confirm_files, confirm_uncertainty, forced_alignment, word_key
from akribos.xmlio import plain, strong_fingerprints


def bible(fragment, book=1, verse=1):
    return ET.fromstring(f'<XMLBIBLE><INFORMATION/><BIBLEBOOK bnumber="{book}">'
                         f'<CHAPTER cnumber="1"><VERS vnumber="{verse}">{fragment}'
                         '</VERS></CHAPTER></BIBLEBOOK></XMLBIBLE>')


def hint(text='Automatische Wortzuordnung; fachlich noch nicht bestätigt.'):
    return f'<NOTE type="x-explanation" ex="{HINT}">{text}</NOTE>'


def count_hints(root):
    return sum(e.get('ex') == HINT for e in root.iter('NOTE'))


class ConfirmationTests(unittest.TestCase):
    def check(self, target_fragment, bk_fragment, csv_fragment=None):
        target = bible(target_fragment)
        bk = bible(bk_fragment) if bk_fragment is not None else None
        csv = bible(csv_fragment if csv_fragment is not None else bk_fragment) if bk_fragment is not None else None
        return confirm_uncertainty(target, bk, csv)

    def test_both_sources_confirm_without_changing_inputs(self):
        target = bible('<gr str="430">Gott</gr>' + hint() + ' sprach.')
        reference = bible('<gr str="430">Gott</gr> sprach.')
        original_target = ET.tostring(target)
        original_reference = ET.tostring(reference)
        result = confirm_uncertainty(target, reference, copy.deepcopy(reference))
        self.assertEqual(result.summary['hints_removed'], 1)
        self.assertEqual(count_hints(result.root), 0)
        self.assertEqual(plain(result.root.find('.//VERS')), 'Gott sprach.')
        self.assertEqual(ET.tostring(target), original_target)
        self.assertEqual(ET.tostring(reference), original_reference)
        self.assertEqual(strong_fingerprints(result.root), strong_fingerprints(target))

    def test_reference_disagreement_retains_hint(self):
        result = self.check('<gr str="430">Gott</gr>' + hint(),
                            '<gr str="430">Gott</gr>', '<gr str="410">Gott</gr>')
        self.assertEqual(count_hints(result.root), 1)
        self.assertEqual(result.audit[0]['references'], {'elb-bk': 'confirmed', 'elb-csv': 'different-strong-set'})

    def test_inventory_membership_does_not_confirm_other_word(self):
        result = self.check('<gr str="430">Gott</gr>' + hint() + ' ist mächtig',
                            '<gr str="410">Gott</gr> ist <gr str="430">mächtig</gr>')
        self.assertEqual(result.summary['hints_removed'], 0)

    def test_partial_multi_strong_set_retains_hint(self):
        result = self.check('<gr str="430 410">Gott</gr>' + hint(), '<gr str="430">Gott</gr>')
        self.assertEqual(result.audit[0]['reason'], 'different-strong-set')

    def test_exact_multi_strong_set_ignores_list_order(self):
        result = self.check('<gr str="430 410">Gott</gr>' + hint(), '<gr str="410-430">Gott</gr>')
        self.assertEqual(result.summary['hints_removed'], 1)

    def test_ambiguous_repeated_target_word_retains_both_hints(self):
        result = self.check('<gr str="430">Gott</gr>' + hint() + ' <gr str="430">Gott</gr>' + hint(),
                            '<gr str="430">Gott</gr>')
        self.assertEqual(result.summary['hints_remaining'], 2)
        self.assertTrue(all(r['reason'] == 'ambiguous-word-alignment' for r in result.audit))

    def test_ambiguous_repeated_reference_word_retains_hint(self):
        result = self.check('<gr str="430">Gott</gr>' + hint(), '<gr str="430">Gott</gr> <gr str="430">Gott</gr>')
        self.assertEqual(result.audit[0]['reason'], 'ambiguous-word-alignment')

    def test_context_can_disambiguate_repeated_words(self):
        fragment = 'Ein <gr str="430">Gott</gr> und sein <gr str="410">Gott</gr>'
        target = fragment.replace('>Gott</gr>', '>Gott</gr>' + hint())
        result = self.check(target, fragment)
        self.assertEqual(result.summary['hints_removed'], 2)

    def test_phrase_can_be_confirmed_by_same_phrase_or_fully_tagged_split(self):
        result = self.check('<gr str="430 1254">Gott schuf</gr>' + hint(),
                            '<gr str="430 1254">Gott schuf</gr>',
                            '<gr str="430">Gott</gr> <gr str="1254">schuf</gr>')
        self.assertEqual(result.summary['hints_removed'], 1)

    def test_phrase_cannot_be_partly_untagged(self):
        result = self.check('<gr str="430 1254">Gott schuf</gr>' + hint(),
                            '<gr str="430 1254">Gott</gr> schuf')
        self.assertEqual(result.audit[0]['reason'], 'missing-reference-strong-tags')

    def test_longer_reference_phrase_cannot_confirm_individual_word(self):
        result = self.check('<gr str="430">Gott</gr>' + hint() + ' sprach',
                            '<gr str="430">Gott sprach</gr>')
        self.assertEqual(result.audit[0]['reason'], 'reference-annotation-crosses-span')

    def test_noncontiguous_reference_match_cannot_confirm_phrase(self):
        result = self.check('<gr str="430 1254">Gott schuf</gr>' + hint(),
                            '<gr str="430">Gott</gr> allein <gr str="1254">schuf</gr>')
        self.assertEqual(result.audit[0]['reason'], 'noncontiguous-reference-span')

    def test_placeholder_strong_is_not_a_word_confirmation(self):
        result = self.check('<gr str="430">Gott</gr>' + hint(), '<gr str="430">[?]</gr>')
        self.assertEqual(result.audit[0]['reason'], 'word-not-aligned')
        self.assertEqual(result.summary['hints_removed'], 0)

    def test_placeholder_gap_cannot_disappear_during_phrase_alignment(self):
        result = self.check('<gr str="430 1254">Gott schuf</gr>' + hint(),
                            '<gr str="430">Gott</gr> <gr str="853">[?]</gr> <gr str="1254">schuf</gr>')
        self.assertEqual(result.audit[0]['reason'], 'reference-placeholder-in-span')
        self.assertEqual(result.summary['hints_removed'], 0)

    def test_placeholder_in_annotation_prevents_confirmation(self):
        result = self.check('<gr str="430">Gott</gr>' + hint(), '<gr str="430">Gott [?]</gr>')
        self.assertEqual(result.audit[0]['reason'], 'reference-placeholder-in-span')
        result = self.check('<gr str="430">Gott [?]</gr>' + hint(), '<gr str="430">Gott</gr>')
        self.assertEqual(result.audit[0]['reason'], 'target-placeholder-in-span')

    def test_duplicate_verse_ids_fail_in_target_and_either_reference(self):
        for duplicate_in in range(3):
            with self.subTest(duplicate_in=duplicate_in):
                roots = [bible('<gr str="430">Gott</gr>' + hint()),
                         bible('<gr str="430">Gott</gr>'), bible('<gr str="430">Gott</gr>')]
                chapter = roots[duplicate_in].find('.//CHAPTER')
                chapter.append(copy.deepcopy(chapter[0]))
                before = [ET.tostring(root) for root in roots]
                with self.assertRaisesRegex(DataError, 'Duplicate verse'):
                    confirm_uncertainty(*roots, in_place=True)
                self.assertEqual(before, [ET.tostring(root) for root in roots])

    def test_missing_source_and_verse_retain_hint(self):
        target = bible('<gr str="430">Gott</gr>' + hint())
        for reference, reason in ((None, 'missing-reference-source'),
                                  (bible('<gr str="430">Gott</gr>', verse=2), 'missing-reference-verse')):
            with self.subTest(reason=reason):
                result = confirm_uncertainty(target, bible('<gr str="430">Gott</gr>'), reference)
                self.assertEqual(result.audit[0]['reason'], reason)
                self.assertEqual(count_hints(result.root), 1)

    def test_nested_styles_tails_and_original_notes_are_preserved(self):
        target = bible('Am <STYLE css="bold"><gr str="430" rmac="N">G<STYLE>ot</STYLE>t'
                       '<NOTE type="x-studynote">Original <STYLE>Notiz</STYLE></NOTE></gr>'
                       + hint() + ',</STYLE> sprach <gr str="559">er</gr>' + hint() + '!'
                       '<NOTE ex="other">Weitere Notiz</NOTE> Ende.')
        reference = bible('Am <gr str="430">Gott</gr>, sprach <gr str="559">er</gr>! Ende.')
        before = plain(target.find('.//VERS'))
        result = confirm_uncertainty(target, reference, copy.deepcopy(reference))
        self.assertEqual(result.summary['hints_removed'], 2)
        self.assertEqual(plain(result.root.find('.//VERS')), before)
        notes = list(result.root.iter('NOTE'))
        self.assertEqual(len(notes), 2)
        self.assertEqual(notes[0].find('STYLE').text, 'Notiz')
        self.assertEqual(notes[1].tail, ' Ende.')

    def test_public_audit_does_not_copy_reference_content_or_assignments(self):
        result = self.check('<gr str="430">Gott</gr>' + hint(),
                            '<gr str="410">Gott</gr> <gr str="8667">Referenzgeheimnis</gr>')
        serialized = json.dumps({'audit': result.audit, 'summary': result.summary}, ensure_ascii=False)
        self.assertNotIn('Referenzgeheimnis', serialized)
        self.assertNotIn('410', serialized)
        self.assertNotIn('8667', serialized)
        self.assertIn('H430', serialized)

    def test_only_designated_hint_removed(self):
        result = self.check('<gr str="430">Gott</gr>' + hint()
                            + '<NOTE ex="other">Automatische Zuordnung</NOTE>.', '<gr str="430">Gott</gr>.')
        self.assertEqual(len(list(result.root.iter('NOTE'))), 1)
        self.assertEqual(result.root.find('.//NOTE').get('ex'), 'other')

    def test_hint_without_clear_assignment_is_retained_and_audited(self):
        result = self.check('Gott' + hint(), '<gr str="430">Gott</gr>')
        self.assertEqual(result.audit[0]['reason'], 'no-preceding-strong-span')
        result = self.check('<gr str="430">Gott</gr> sprach' + hint(), '<gr str="430">Gott</gr> sprach')
        self.assertEqual(result.audit[0]['reason'], 'text-between-assignment-and-hint')

    def test_malformed_codes_cannot_be_silently_dropped(self):
        for invalid in ('430 unknown', '430 99999', '430 G430'):
            with self.subTest(invalid=invalid):
                result = self.check('<gr str="430">Gott</gr>' + hint(), f'<gr str="{invalid}">Gott</gr>')
                self.assertEqual(result.audit[0]['reason'], 'invalid-reference-strong-set')

    def test_suffixes_cannot_turn_into_classical_strong_confirmation(self):
        for raw in ('H430unknown', 'H430_uncertain', 'H430a', 'H430_A', 'H430 H410a'):
            with self.subTest(raw=raw):
                result = self.check('<gr str="430">Gott</gr>' + hint(), f'<gr str="{raw}">Gott</gr>')
                self.assertEqual(result.summary['hints_removed'], 0)
                self.assertEqual(result.audit[0]['reason'], 'invalid-reference-strong-set')
        result = self.check('<gr str="H430a">Gott</gr>' + hint(), '<gr str="430">Gott</gr>')
        self.assertEqual(result.audit[0]['reason'], 'invalid-target-strong-set')

    def test_uncertain_reference_cannot_confirm_another_candidate(self):
        target = '<gr str="430">Gott</gr>' + hint()
        for reference in ('<gr str="430">Gott</gr>' + hint(),
                          '<STYLE><gr str="430">Gott</gr>' + hint() + '</STYLE>',
                          '<gr str="430">Gott</gr> sagte' + hint()):
            with self.subTest(reference=reference):
                result = self.check(target, '<gr str="430">Gott</gr>', reference)
                self.assertEqual(result.summary['hints_removed'], 0)
                self.assertEqual(result.audit[0]['references']['elb-csv'], 'uncertain-reference-verse')

    def test_known_uncertainty_elsewhere_in_reference_verse_retains_hint(self):
        result = self.check('<gr str="430">Gott</gr>' + hint() + ' sprach',
                            '<gr str="430">Gott</gr> <gr str="559">sprach</gr>' + hint())
        self.assertEqual(result.summary['hints_removed'], 0)
        self.assertEqual(result.audit[0]['reason'], 'uncertain-reference-verse')

    def test_nested_original_note_hint_remains_untouched_and_audited(self):
        target = bible('<gr str="430">Gott</gr><NOTE type="x-studynote">Original' + hint() + '</NOTE>')
        reference = bible('<gr str="430">Gott</gr>')
        before = ET.tostring(target)
        result = confirm_uncertainty(target, reference, copy.deepcopy(reference))
        self.assertEqual(result.audit[0]['reason'], 'outside-supported-verse-text')
        self.assertEqual(ET.tostring(result.root), before)

    def test_structured_hint_cannot_remove_other_data(self):
        target = '<gr str="430">Gott</gr>' + hint('<STYLE>Eigene Struktur</STYLE>')
        result = self.check(target, '<gr str="430">Gott</gr>')
        self.assertEqual(result.audit[0]['reason'], 'structured-uncertainty-note')
        self.assertEqual(count_hints(result.root), 1)

    def test_nested_target_assignments_cannot_hide_other_codes(self):
        for fragment in ('<gr str="410"><gr str="430">Gott</gr>' + hint() + '</gr>',
                         '<gr str="430"><gr str="410">Gott</gr></gr>' + hint()):
            with self.subTest(fragment=fragment):
                result = self.check(fragment, '<gr str="430">Gott</gr>')
                self.assertEqual(result.audit[0]['reason'], 'nested-target-strong-spans')

    def test_whole_word_boundaries_required(self):
        result = self.check('<gr str="430">G</gr>ott' + hint(), '<gr str="430">Gott</gr>')
        self.assertEqual(result.audit[0]['reason'], 'text-between-assignment-and-hint')
        result = self.check('<gr str="430">Gott</gr>' + hint(), '<gr str="430">Go</gr>tt')
        self.assertEqual(result.audit[0]['reason'], 'incomplete-reference-word-span')

    def test_normalization_does_not_merge_different_german_words(self):
        self.assertEqual(word_key('GOTT'), 'gott')
        self.assertEqual(word_key('A\u0308hre'), word_key('Ähre'))
        self.assertNotEqual(word_key('Maße'), word_key('Masse'))
        result = self.check('<gr str="430">Maße</gr>' + hint(), '<gr str="430">Masse</gr>')
        self.assertEqual(result.audit[0]['reason'], 'word-not-aligned')

    def test_repeated_run_is_idempotent_and_summary_deterministic(self):
        target = bible('<gr str="430">Gott</gr>' + hint())
        reference = bible('<gr str="430">Gott</gr>')
        first = confirm_uncertainty(target, reference, copy.deepcopy(reference))
        again = confirm_uncertainty(target, reference, copy.deepcopy(reference))
        second = confirm_uncertainty(first.root, reference, copy.deepcopy(reference))
        self.assertEqual(first.audit, again.audit)
        self.assertEqual(first.summary, again.summary)
        self.assertEqual(ET.tostring(first.root), ET.tostring(second.root))
        self.assertEqual(second.summary['hints_before'], 0)

    def test_new_testament_prefix(self):
        target = bible('<gr str="3588">der</gr>' + hint(), book=40)
        reference = bible('<gr str="3588">der</gr>', book=40)
        result = confirm_uncertainty(target, reference, copy.deepcopy(reference))
        self.assertEqual(result.audit[0]['target_strong'], ['G3588'])
        self.assertEqual(result.summary['hints_removed'], 1)

    def test_path_wrapper_hashes_sources_but_never_changes_them(self):
        with tempfile.TemporaryDirectory() as folder:
            target, bk, csv = [Path(folder) / name for name in ('target.xml', 'bk.xml', 'csv.xml')]
            target.write_bytes(ET.tostring(bible('<gr str="430">Gott</gr>' + hint())))
            for path, label in ((bk, 'BK source fixture'), (csv, 'CSV source fixture')):
                reference = bible('<gr str="430">Gott</gr>')
                ET.SubElement(reference.find('INFORMATION'), 'title').text = label
                path.write_bytes(ET.tostring(reference))
            before = {p: p.read_bytes() for p in (target, bk, csv)}
            result = confirm_files(target, bk, csv)
            self.assertEqual(result.summary['hints_removed'], 1)
            self.assertEqual(len(result.summary['reference_sha256']['elb-bk']), 64)
            self.assertEqual(before, {p: p.read_bytes() for p in before})
            with self.assertRaises(DataError):
                confirm_files(target, bk, bk)

    def test_different_reference_paths_with_identical_hashes_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            target, bk, csv = [Path(folder) / name for name in ('target.xml', 'bk.xml', 'csv.xml')]
            target.write_bytes(ET.tostring(bible('<gr str="430">Gott</gr>' + hint())))
            for path in (bk, csv):
                path.write_bytes(ET.tostring(bible('<gr str="430">Gott</gr>')))
            before = {p: p.read_bytes() for p in (target, bk, csv)}
            with self.assertRaisesRegex(DataError, 'identical SHA-256'):
                confirm_files(target, bk, csv)
            self.assertEqual(before, {p: p.read_bytes() for p in before})


class ForcedAlignmentTests(unittest.TestCase):
    def test_forced_matches_agree_with_all_enumerated_lcs_paths(self):
        # Independent exhaustive oracle for short repeated-word sequences.
        words = [tuple(p) for n in range(4) for p in itertools.product(('a', 'b'), repeat=n)]
        for a, b in itertools.product(words, repeat=2):
            possibilities = []
            for length in range(min(len(a), len(b)) + 1):
                for aa in itertools.combinations(range(len(a)), length):
                    for bb in itertools.combinations(range(len(b)), length):
                        if tuple(a[i] for i in aa) == tuple(b[j] for j in bb):
                            possibilities.append(tuple(zip(aa, bb)))
            longest = max(map(len, possibilities))
            best = [dict(pairs) for pairs in possibilities if len(pairs) == longest]
            actual = forced_alignment(tokenize(' '.join(a)), tokenize(' '.join(b)))
            for i in range(len(a)):
                candidates = {path.get(i) for path in best}
                expected = next(iter(candidates)) if len(candidates) == 1 and None not in candidates else None
                self.assertEqual(actual[i][0], expected, (a, b, i))


if __name__ == '__main__':
    unittest.main()
