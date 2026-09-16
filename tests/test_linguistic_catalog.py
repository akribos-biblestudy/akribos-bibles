"""German article-head paradigms and their checked original lexicon evidence."""
from pathlib import Path
import copy
import hashlib
import json
import unittest
import xml.etree.ElementTree as ET

from akribos.kautz import definition_lines, FAMILY
from akribos import linguistic_rules as rules

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = json.loads((ROOT / 'rules/greek-article-heads.evidence.json').read_text())
CATALOG = EVIDENCE['entries']


def phrase(article, noun, code, greek_gender='M', number='S'):
    text = f'{article} {noun}'
    tokens = [
        {'id': 'd001', 'text': article, 'strong': [], 'start': 0, 'end': len(article)},
        {'id': 'd002', 'text': noun, 'strong': [code],
         'start': len(article) + 1, 'end': len(text)},
    ]
    source = [
        {'origin_id': 'John.1.1#01=NKO', 'word': '01', 'strong': ['G3588'],
         'morph': f'T-N{number}{greek_gender}', 'conjoined': f'#01»02:{code}'},
        {'origin_id': 'John.1.1#02=NKO', 'word': '02', 'strong': [code],
         'morph': f'N-N{number}{greek_gender}'},
    ]
    return text, tokens, source


class CatalogTests(unittest.TestCase):
    def check(self, expected, article, noun, code, gender, number='S'):
        text, tokens, source = phrase(article, noun, code, gender, number)
        actual = rules.linked_article_proof(text, tokens, 0, source)
        self.assertEqual(actual is not None, expected)

    def test_german_gender_is_not_inferred_from_greek(self):
        for args in [('Der', 'Geist', 'G4151', 'N'), ('Der', 'Tag', 'G2250', 'F'),
                     ('Das', 'Gesetz', 'G3551', 'M'), ('Der', 'Leib', 'G4983', 'N'),
                     ('Die', 'Welt', 'G2889', 'M'), ('Das', 'Gebet', 'G4335', 'F')]:
            with self.subTest(args=args):
                self.check(True, *args)

    def test_german_pronoun_before_incompatible_noun_is_not_article(self):
        for args in [('Das', 'Geist', 'G4151', 'N'), ('Die', 'Tag', 'G2250', 'F'),
                     ('Der', 'Gesetz', 'G3551', 'M'), ('Das', 'Leib', 'G4983', 'N')]:
            with self.subTest(args=args):
                self.check(False, *args)

    def test_ambiguous_german_forms_need_matching_source_number(self):
        self.check(True, 'Der', 'Engel', 'G32', 'M', 'S')
        self.check(True, 'Die', 'Engel', 'G32', 'M', 'P')
        self.check(False, 'Die', 'Engel', 'G32', 'M', 'S')
        self.check(True, 'Die', 'Apostel', 'G652', 'M', 'P')
        self.check(False, 'Dem', 'Apostel', 'G652', 'M', 'P')
        self.check(True, 'Die', 'Tage', 'G2250', 'F', 'P')
        self.check(False, 'Die', 'Tage', 'G2250', 'F', 'S')

    def test_unlisted_compound_cannot_inherit_base_noun(self):
        self.check(False, 'Der', 'Menschensohn', 'G5207', 'M')
        self.check(False, 'Der', 'Geistesmensch', 'G444', 'M')
        self.check(True, 'Der', 'Hohepriester', 'G749', 'M')

    def test_guards_still_protect_extended_heads(self):
        text, tokens, source = phrase('Der', 'Geist', 'G4151', 'N')
        for mutate in [
            lambda t, s: t[1].update(uncertain=True),
            lambda t, s: t[1].update(anchor_eligible=False),
            lambda t, s: s[0].update(conjoined=''),
            lambda t, s: s[0].update(morph='T-NSM'),
            lambda t, s: s[0].update(edition='WH', editions_raw='WH»1'),
            lambda t, s: s.append(copy.deepcopy(s[1])),
        ]:
            ts, ss = copy.deepcopy(tokens), copy.deepcopy(source)
            mutate(ts, ss)
            self.assertIsNone(rules.linked_article_proof(text, ts, 0, ss))

    def test_evidenced_paradigms_are_installed_without_replacing_existing_forms(self):
        for row in CATALOG:
            for number, field in [('S', 'singular_forms'), ('P', 'plural_forms')]:
                for form in row[field]:
                    with self.subTest(form=form, strong=row['strong'], number=number):
                        self.assertIn((row['strong'], row['german_gender'], number), rules.GERMAN_HEADS[form])
        self.assertIn(('G3056', 'N', 'S'), rules.GERMAN_HEADS['wort'])
        self.assertIn(('G2316', 'M', 'S'), rules.GERMAN_HEADS['gott'])

    def test_all_lexical_associations_have_original_entry_evidence(self):
        source = ROOT / EVIDENCE['lexicon_path']
        metadata = EVIDENCE
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), metadata['lexicon_sha256'])
        entries = {int(e.get('strongs')): e for e in ET.parse(source).getroot().iter('entry')}
        for row in CATALOG:
            with self.subTest(lemma=row['german_lemma']):
                evidence = row['lexicon_evidence']
                entry = entries[evidence['strong_entry']]
                self.assertEqual(row['strong'], f"G{evidence['strong_entry']}")
                self.assertEqual(hashlib.sha256(ET.tostring(entry, encoding='us-ascii')).hexdigest(),
                                 evidence['entry_sha256'])
                lines = definition_lines(entry.find('strongs_def'))
                at = evidence['definition_line'] - 1
                self.assertFalse(any(FAMILY.search(line) for line in lines[:at + 1]))
                self.assertIn(evidence['matched_term'].casefold(), lines[at].casefold())



if __name__ == '__main__':
    unittest.main()
