"""Synthetic Hebrew occurrence-counterexamples; no private reference text."""
import copy
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from akribos.common import BOOKS, DataError, tokenize
from akribos.confirm import (HINT, SAFETY_PROFILE, ConfirmationSafetyEvidence,
                             confirm_uncertainty, load_confirmation_evidence,
                             verify_confirmation_transition, _remove_preserving_tail)
from akribos.project import jsonl_gz, line
from akribos.xmlio import plain


NOTE = f'<NOTE ex="{HINT}">Synthetic uncertain assignment</NOTE>'


def bible(fragment, ref='Gen.1.1'):
    book, chapter, verse = ref.split('.')
    return ET.fromstring(f'<XMLBIBLE><BIBLEBOOK bnumber="{BOOKS.index(book)+1}">'
                        f'<CHAPTER cnumber="{chapter}"><VERS vnumber="{verse}">'
                        + fragment + '</VERS></CHAPTER></BIBLEBOOK></XMLBIBLE>')


def occurrences(*codes, ref='Gen.1.1'):
    return [{'origin_id': f'{ref}#{index:02}=L', 'strong': list(values),
             'morph': 'synthetic', 'edition': 'L/Q'}
            for index, values in enumerate(codes, 1)]


class HebrewSafetyTests(unittest.TestCase):
    def check(self, fragment, source, *, ref='Gen.1.1', evidence=True):
        target = bible(fragment.replace('</gr>', '</gr>'+NOTE, 1), ref)
        reference = bible(fragment, ref)
        proof = (ConfirmationSafetyEvidence({ref: source}, frozenset(), 'WH', {})
                 if evidence else None)
        result = confirm_uncertainty(target, reference, reference, safety_evidence=proof)
        replay = verify_confirmation_transition(target, result.root, result.audit, safety_evidence=proof)
        self.assertEqual(result.summary['hints_removed'], replay['hints_removed'])
        self.assertEqual(plain(target.find('.//VERS')), plain(result.root.find('.//VERS')))
        self.assertEqual(result.summary['safety_profile'], SAFETY_PROFILE)
        return target, result, proof

    def test_exodus_indefinite_article_cannot_borrow_the_later_numeral(self):
        # Exod 33:5: the explicit one belongs to the following brief moment.
        ref = 'Exod.33.5'
        _, result, _ = self.check('<gr str="259">ein</gr> halsstarriges Volk; '
            '<gr str="259">einen</gr> Augenblick', occurrences(['H259'], ['H7281'], ref=ref), ref=ref)
        self.assertEqual(result.audit[0]['references'], {'elb-bk':'confirmed','elb-csv':'confirmed'})
        self.assertEqual(result.audit[0]['reason'], 'function-code-over-assigned-in-verse')
        self.assertEqual(result.summary['hints_removed'], 0)

    def test_genesis_conjunction_cannot_borrow_the_later_relative(self):
        ref = 'Gen.19.21'
        target, result, proof = self.check('<gr str="834">dass</gr> die Stadt bleibt, '
            'von <gr str="834">der</gr> du geredet hast', occurrences(['H834'], ref=ref), ref=ref)
        self.assertEqual(result.audit[0]['reason'], 'function-code-over-assigned-in-verse')
        forged = copy.deepcopy(result.audit)
        forged[0].update(status='confirmed', reason='both-references-confirm-complete-set')
        changed = copy.deepcopy(result.root); verse = changed.find('.//VERS')
        _remove_preserving_tail(verse, verse.find('NOTE'))
        with self.assertRaisesRegex(DataError, 'safety veto'):
            verify_confirmation_transition(target, changed, forged, safety_evidence=proof)

    def test_correct_numeral_and_relative_phrase_remain_confirmable(self):
        for fragment, source in [
            ('<gr str="259">einen</gr> Augenblick', occurrences(['H259'], ['H7281'])),
            ('<gr str="259">einen einzigen</gr> Augenblick', occurrences(['H259'])),
            ('die Stadt, <gr str="834">von der</gr> du geredet hast', occurrences(['H834'])),
            ('<gr str="259">einer</gr> und <gr str="259">einer</gr>', occurrences(['H259'], ['H259'])),
        ]:
            with self.subTest(fragment=fragment):
                _, result, _ = self.check(fragment, source)
                self.assertEqual(result.summary['hints_removed'], 1)

    def test_multicode_membership_counts_once_per_span_and_occurrence(self):
        _, result, _ = self.check('<gr str="259">einer</gr> und <gr str="259 376">Mann</gr>',
                                  occurrences(['H259', 'H376']))
        self.assertEqual(result.audit[0]['reason'], 'function-code-over-assigned-in-verse')
        _, result, _ = self.check('<gr str="259 376">ein Mann</gr>', occurrences(['H259', 'H376']))
        self.assertEqual(result.summary['hints_removed'], 1)
        _, result, _ = self.check('<gr str="259">einen</gr> Augenblick',
                                  occurrences(['H9002', 'H259', 'H9014']))
        self.assertEqual(result.summary['hints_removed'], 1)

    def test_no_expansion_to_other_hebrew_codes(self):
        _, result, _ = self.check('<gr str="3117">Tag</gr> und <gr str="3117">Tag</gr>', [], evidence=False)
        self.assertEqual(result.summary['hints_removed'], 1)

    def test_missing_hebrew_evidence_never_confirms(self):
        for code in ('259', '834'):
            _, result, _ = self.check(f'<gr str="{code}">Wort</gr>', [], evidence=False)
            self.assertEqual(result.audit[0]['reason'], 'missing-function-word-source-evidence')
            _, result, _ = self.check(f'<gr str="{code}">Wort</gr>', [])
            self.assertEqual(result.audit[0]['reason'], 'missing-function-word-source-verse')

    def test_l_cowitness_labels_are_one_occurrence_each(self):
        source = occurrences(['H259'], ['H259'])
        source[0]['origin_id'] = 'Gen.1.1#01=L(abh)'
        source[1]['origin_id'] = 'Gen.1.1#02=LAB(h)'
        _, result, _ = self.check('<gr str="259">einer</gr> und <gr str="259">einer</gr>', source)
        self.assertEqual(result.summary['hints_removed'], 1)
        _, result, _ = self.check('<gr str="259">einer</gr> und <gr str="259">einer</gr>', source[:1])
        self.assertEqual(result.audit[0]['reason'], 'function-code-over-assigned-in-verse')

    def test_q_alternatives_duplicate_or_reordered_positions_are_not_added(self):
        for ids in [
            ['Gen.1.1#01=L', 'Gen.1.1#01=Q(K)'],
            ['Gen.1.1#01=L', 'Gen.1.1#02=Q(k)'],
            ['Gen.1.1#01=L', 'Gen.1.1#01=LAB(h)'],
            ['Gen.1.1#02=L', 'Gen.1.1#01=L'],
            ['Gen.1.1#01a=L', 'Gen.1.1#02=L'],
            ['Gen.1.1#00=L', 'Gen.1.1#01=L'],
            ['Gen.1.1#01=L(+)', 'Gen.1.1#02=L'],
        ]:
            with self.subTest(ids=ids):
                source = occurrences(['H259'], ['H259'])
                for token, origin in zip(source, ids):token['origin_id'] = origin
                _, result, _ = self.check('<gr str="259">einer</gr> und <gr str="259">einer</gr>', source)
                self.assertEqual(result.audit[0]['reason'], 'hebrew-source-occurrence-count-unproved')
                self.assertEqual(result.summary['hints_removed'], 0)

    def test_even_an_unrelated_q_word_makes_count_evidence_ambiguous(self):
        source = occurrences(['H834'], ['H3117'])
        source[1]['origin_id'] = 'Gen.1.1#02=Q(K)'
        _, result, _ = self.check('<gr str="834">welcher</gr> Tag', source)
        self.assertEqual(result.audit[0]['reason'], 'hebrew-source-occurrence-count-unproved')

    def test_loader_keeps_actual_hebrew_codes_and_guards_numbering(self):
        target = bible('<gr str="259">einen</gr>'+NOTE+' Augenblick')
        reference = bible('<gr str="259">einen</gr> Augenblick')
        text = plain(target.find('.//VERS'))
        alignment = {'ref':'Gen.1.1', 'text':text, 'tokens':tokenize(text),
                     'step_profile':'L/Q', 'inventory_mismatch':False}
        with tempfile.TemporaryDirectory() as directory:
            src_path = Path(directory)/'source.jsonl.gz'; align_path = Path(directory)/'alignment.jsonl.gz'
            with jsonl_gz(align_path) as stream:line(stream, alignment)
            for origin, expected in [('Gen.1.1#01=LAB(h)', None),
                                     ('Gen.1.1#01=Q(K)', 'hebrew-source-occurrence-count-unproved'),
                                     ('Gen.1.1(1.2)#01=L', 'source-verse-numbering-unproved')]:
                with self.subTest(origin=origin):
                    source = occurrences(['H259']);source[0]['origin_id'] = origin
                    with jsonl_gz(src_path) as stream:line(stream, {'ref':'Gen.1.1', 'tokens':source})
                    proof = load_confirmation_evidence(target, src_path, align_path, nt_edition='WH')
                    self.assertEqual(proof.occurrences['Gen.1.1'][0]['strong'], ['H259'])
                    result = confirm_uncertainty(target, reference, reference, safety_evidence=proof)
                    verify_confirmation_transition(target, result.root, result.audit, safety_evidence=proof)
                    self.assertEqual(result.summary['hints_removed'], int(expected is None))
                    if expected:self.assertEqual(result.audit[0]['reason'], expected)


if __name__ == '__main__':unittest.main()
