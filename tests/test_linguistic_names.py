from pathlib import Path
import copy
import csv
import hashlib
import json
import re
import sys
import unittest
import xml.etree.ElementTree as ET

from akribos.linguistic_names import proper_name_decision, load_name_catalog
from akribos.kautz import definition_lines, FAMILY

CATALOG = load_name_catalog()


class ProperNameEvidenceTests(unittest.TestCase):
    def test_catalog_entries_match_original_lexica_and_step_rows(self):
        root=Path(__file__).resolve().parents[1]
        kautz={int(e.get('strongs')):e for e in ET.parse(root/'sources/originals/stronggreek_de_kautz.xml').getroot().iter('entry')}
        greek={int(e.get('strongs')):e for e in ET.parse(root/'sources/originals/strongsgreek.xml').getroot().iter('entry')}
        hebrew={e.get('id'):e for e in ET.parse(root/'sources/originals/hebrewstrong.xml').getroot() if e.get('id')}
        wanted={(row['evidence']['step_lemma_evidence']['source'],row['evidence']['step_lemma_evidence']['origin_id'])
                for row in CATALOG.values()}
        step={}
        for source in {p for p,_ in wanted}:
            with (root/source).open(encoding='utf-8-sig') as stream:
                for row in csv.reader(stream,delimiter='\t'):
                    if row and (source,row[0]) in wanted:step[source,row[0]]=row
        for code,row in CATALOG.items():
            with self.subTest(code=code):
                evidence=row['evidence'];entry=kautz[evidence['greek_entry']]
                self.assertEqual(hashlib.sha256(ET.tostring(entry)).hexdigest(),evidence['german_entry_sha256'])
                self.assertEqual(hashlib.sha256(ET.tostring(greek[evidence['greek_entry']])).hexdigest(),evidence['greek_entry_sha256'])
                self.assertIn('N.pr.',''.join(entry.find('strongs_derivation').itertext()))
                lines=definition_lines(entry.find('strongs_def'))
                for heading in evidence['definition_headings']:
                    index=heading['line']-1
                    self.assertEqual(lines[index],heading['heading'])
                    self.assertFalse(any(FAMILY.search(line) for line in lines[:index+1]))
                at=evidence['step_lemma_evidence'];source=step[at['source'],at['origin_id']]
                self.assertEqual(hashlib.sha256('\t'.join(source).encode()).hexdigest(),at['row_sha256'])
                if code.startswith('G'):
                    self.assertIn(source[4].split('=',1)[0],row['source_lemmas'])
                else:
                    self.assertEqual(hashlib.sha256(ET.tostring(hebrew[code])).hexdigest(),evidence['hebrew_entry_sha256'])
                    self.assertTrue(any(e.get('language')=='HEBREW' and e.get('strongs')==code[1:]
                                        for e in entry.find('strongs_derivation').iter('strongsref')))


class ProperNameTests(unittest.TestCase):
    def setUp(self):
        self.ref = 'Gen.17.5'
        self.tokens = [{'id': 'd001', 'text': 'Abraham', 'strong': ['H85'],
                        'uncertain': True, 'phrase_tokens': 1}]
        self.source = [{'origin_id': 'Gen.17.5#09=L', 'strong': ['H85'],
                        'morph': 'HNpm', 'text': 'אַבְרָהָ֔ם'}]
        self.references = {'elb-bk': 'confirmed'}

    def result(self, **kwargs):
        return proper_name_decision(self.ref, self.tokens, 0, self.source, CATALOG,
                                    nt_edition='WH', reference_statuses=self.references, **kwargs)

    def test_real_pointed_hebrew_name_with_precise_reference(self):
        self.assertEqual(self.result()['status'], 'accepted')

    def test_source_lemma_letters_cannot_change(self):
        self.source[0]['text'] = 'אַבְרָם'  # Abram is H87, not Abraham H85.
        self.assertEqual(self.result()['reason'], 'hebrew-name-surface-not-confirmed')

    def test_german_abram_is_not_abraham(self):
        self.tokens[0]['text'] = 'Abram'
        self.assertEqual(self.result()['reason'], 'german-name-form-not-confirmed')

    def test_german_name_must_occur_once_even_without_another_tag(self):
        self.tokens.append({'text': 'Abrahams', 'strong': []})
        self.assertEqual(self.result()['reason'], 'repeated-german-name-family')

    def test_another_composite_target_span_also_counts(self):
        self.tokens.append({'text': 'ihm', 'strong': ['H85', 'H413']})
        self.assertEqual(self.result()['reason'], 'repeated-target-code-including-composite-spans')

    def test_another_composite_source_span_also_counts(self):
        self.source.append({'origin_id': 'Gen.17.5#12=L', 'strong': ['H9002', 'H85'],
                            'morph': 'HC/Npm', 'text': 'וְ/אַבְרָהָם'})
        self.assertEqual(self.result()['reason'], 'source-name-occurrence-not-unique')

    def test_source_prefix_is_not_split_or_silently_dropped(self):
        self.source[0].update(strong=['H9002', 'H85'], morph='HC/Npm', text='וְ/אַבְרָהָם')
        self.assertEqual(self.result()['reason'], 'source-name-is-composite')

    def test_source_compound_punctuation_is_not_silently_removed(self):
        self.source[0]['text'] = 'אַבְרָהָם־'
        self.assertEqual(self.result()['reason'], 'hebrew-compound-surface')

    def test_common_noun_morphology_does_not_prove_a_name(self):
        self.source[0]['morph'] = 'HNcmsa'
        self.assertEqual(self.result()['reason'], 'not-hebrew-proper-name-morphology')

    def test_no_new_code_assignment_or_nonuncertain_hint(self):
        self.tokens[0]['strong'] = []
        self.assertEqual(self.result()['reason'], 'not-single-existing-uncertain-name-span')
        self.tokens[0].update(strong=['H85'], uncertain=False)
        self.assertEqual(self.result()['reason'], 'not-single-existing-uncertain-name-span')

    def test_phrase_multi_code_and_blocked_candidates_fail(self):
        original = copy.deepcopy(self.tokens[0])
        for change in [{'phrase_tokens': 2}, {'strong': ['H85', 'H413']}, {'blocked': True}]:
            self.tokens[0] = original | change
            self.assertEqual(self.result()['reason'], 'not-single-existing-uncertain-name-span')

    def test_independent_reference_is_mandatory_not_verse_inventory(self):
        for status in ['missing-reference-verse', 'different-strong-set', 'ambiguous-word-alignment',
                       'reference-span-uncertain', 'missing-reference-strong-tags']:
            self.references = {'elb-bk': status}
            self.assertEqual(self.result()['reason'], 'no-independent-word-level-name-corroboration')
        self.references = {'own-inventory': 'confirmed'}
        self.assertEqual(self.result()['reason'], 'no-independent-word-level-name-corroboration')

    def test_one_actual_independent_reference_is_enough(self):
        self.references = {'elb-bk': 'different-strong-set', 'elb-csv': 'confirmed'}
        self.assertEqual(self.result()['status'], 'accepted')

    def test_verse_and_witness_guards(self):
        self.assertEqual(self.result(verse_guard='inventory_mismatch')['reason'], 'prior-verse-alignment-guard')
        for origin, reason in [('Gen.17.6#09=L', 'source-occurrence-belongs-to-other-verse'),
                               ('Gen.17.5#09=S', 'unsupported-hebrew-witness'),
                               ('Gen.17.5[17.6]#09=L', 'source-order-or-versification-variation')]:
            self.source[0]['origin_id'] = origin
            self.assertEqual(self.result()['reason'], reason)

    def test_inventory_mismatch_guard_remains_active(self):
        self.tokens += [{'text': 'a', 'strong': ['H1']}, {'text': 'b', 'strong': ['H1121']}]
        self.assertEqual(self.result()['reason'], 'verse-inventory-mismatch')

    def test_herr_adonai_and_jesus_joshua_are_not_normalized(self):
        for code, word in [('H3068', 'HERR'), ('H136', 'HERR')]:
            self.tokens[0].update(strong=[code], text=word)
            self.source[0].update(strong=[code], morph='HNpt', text='יהוה')
            self.assertEqual(self.result()['reason'], 'name-code-outside-explicit-catalog')
        self.ref = 'Matt.1.1'
        self.tokens[0].update(strong=['G2424'], text='Josua')
        self.source = [{'origin_id': 'Mat.1.1#03=NKO', 'strong': ['G2424'],
                        'lemma': 'Ἰησοῦς', 'morph': 'N-GSM-P', 'edition': 'WH'}]
        self.assertEqual(self.result()['reason'], 'german-name-form-not-confirmed')

    def test_greek_historical_name_form_and_exact_source_lemma(self):
        self.ref = 'Matt.1.1'
        self.tokens[0].update(strong=['G2424'], text='Jesu')
        self.source = [{'origin_id': 'Mat.1.1#03=NKO', 'strong': ['G2424'],
                        'lemma': 'Ἰησοῦς', 'morph': 'N-GSM-P', 'edition': 'WH'}]
        self.assertEqual(self.result()['status'], 'accepted')
        self.source[0]['lemma'] = 'Ἰησοῦς, Παῦλος'
        self.assertEqual(self.result()['reason'], 'source-name-lemma-not-confirmed')

    def test_greek_pronoun_and_title_morphologies_are_not_names(self):
        self.ref = 'Matt.1.1'
        self.tokens[0].update(strong=['G2424'], text='Jesu')
        self.source = [{'origin_id': 'Mat.1.1#03=NKO', 'strong': ['G2424'],
                        'lemma': 'Ἰησοῦς', 'morph': 'N-GSM-P', 'edition': 'WH'}]
        for morph in ['P-3GSM', 'N-GSM-T', 'N-GSM', 'N-GPM-P']:
            self.source[0]['morph'] = morph
            self.assertEqual(self.result()['reason'], 'not-greek-personal-proper-name-morphology')

    def test_selected_greek_edition_and_movement(self):
        self.ref = 'Matt.1.1'
        self.tokens[0].update(strong=['G2424'], text='Jesus')
        self.source = [{'origin_id': 'Mat.1.1#03=NKO', 'strong': ['G2424'],
                        'lemma': 'Ἰησοῦς', 'morph': 'N-GSM-P', 'edition': 'TR'}]
        self.assertEqual(self.result()['reason'], 'wrong-selected-nt-edition')
        self.source[0].update(edition='WH', editions_raw='WH»1')
        self.assertEqual(self.result()['reason'], 'source-order-or-versification-variation')

    def test_rule_never_mutates_inputs(self):
        before = copy.deepcopy((self.tokens, self.source, CATALOG, self.references))
        self.result()
        self.assertEqual((self.tokens, self.source, CATALOG, self.references), before)


if __name__ == '__main__':
    unittest.main()
