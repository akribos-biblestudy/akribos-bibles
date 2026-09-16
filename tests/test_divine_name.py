"""Grammatical regressions using the actual ELB source, including counterexamples."""
import sys
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from akribos.importers import parse_xml
from akribos.modernize import modernize, plan_verse, rules
from akribos.verify import verify
from akribos.xmlio import apply_edits, note_fingerprints, plain, strong_fingerprints, zef_verses


def name_edits(text):
    edits, reviews = plan_verse(text, 'elb', rules())
    return [e['after'] for e in edits if e['before'] in {'Jehova', 'Jehovas'}], reviews


class DivineNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verses = {ref: plain(v) for ref, v in zef_verses(
            parse_xml(ROOT / 'sources/originals/elb1932.xml'), True)}

    def test_reported_and_related_samuel_verses(self):
        expected = {
            '1Sam.17.37': ['Der HERR', 'der HERR'],
            '1Sam.20.12': ['HERR'],
            '1Sam.20.13': ['der HERR', 'der HERR'],
            '1Sam.20.16': ['der HERR'],
            '1Sam.20.42': ['des HERRN', 'Der HERR'],
            '1Sam.1.3': ['den HERRN', 'des HERRN'],
            '1Sam.1.11': ['HERR', 'dem HERRN'],
            '1Sam.1.21': ['dem HERRN'],
            '1Sam.1.28': ['dem HERRN', 'dem HERRN', 'den HERRN'],
            '1Sam.2.10': ['Der HERR', 'Der HERR'],
            '1Sam.2.12': ['den HERRN'],
            '1Sam.2.20': ['Der HERR', 'dem HERRN'],
            '1Sam.3.4': ['der HERR'],
            '1Sam.3.7': ['den HERRN', 'des HERRN'],
            '1Sam.3.9': ['HERR'],
            '1Sam.6.17': ['dem HERRN'],
            '1Sam.7.2': ['dem HERRN'],
            '1Sam.7.3': ['dem HERRN', 'den HERRN'],
            '1Sam.7.5': ['den HERRN'],
            '1Sam.7.12': ['der HERR'],
            '1Sam.9.17': ['der HERR'],
            '1Sam.10.22': ['den HERRN', 'der HERR'],
            '1Sam.12.14': ['den HERRN', 'des HERRN', 'dem HERRN'],
            '1Sam.12.16': ['der HERR'],
            '1Sam.13.12': ['den HERRN'],
            '1Sam.14.35': ['dem HERRN', 'dem HERRN'],
            '1Sam.15.35': ['den HERRN'],
            '1Sam.16.2': ['der HERR', 'dem HERRN'],
            '1Sam.16.5': ['dem HERRN'],
            '1Sam.23.4': ['den HERRN', 'der HERR'],
            '1Sam.23.10': ['HERR'],
            '1Sam.23.11': ['HERR', 'der HERR'],
            '1Sam.24.7': ['Der HERR', 'des HERRN', 'des HERRN'],
            '1Sam.24.13': ['Der HERR', 'der HERR'],
            '1Sam.24.16': ['der HERR'],
            '1Sam.24.19': ['der HERR'],
            '1Sam.25.38': ['der HERR'],
            '1Sam.26.10': ['der HERR', 'der HERR'],
            '1Sam.26.11': ['Der HERR', 'des HERRN'],
            '1Sam.28.16': ['der HERR'],
        }
        for ref, names in expected.items():
            with self.subTest(ref=ref):
                actual, reviews = name_edits(self.verses[ref])
                self.assertEqual(actual, names)
                self.assertFalse([r for r in reviews if r['kind'] == 'divine-name-syntax'])

    def test_same_constructions_in_other_books(self):
        expected = {
            'Gen.24.7': ['Der HERR'],
            'Gen.24.40': ['Der HERR'],
            'Gen.29.33': ['der HERR'],  # gehört hat = heard, not belongs
            'Exod.3.16': ['Der HERR'],
            'Exod.7.5': ['der HERR'],
            'Exod.9.29': ['dem HERRN', 'dem HERRN'],
            'Exod.14.31': ['der HERR', 'den HERRN', 'den HERRN'],
            'Lev.23.8': ['dem HERRN'],
            'Num.6.25': ['Der HERR'],
            'Num.6.26': ['Der HERR'],
            'Deut.1.6': ['Der HERR'],
            'Deut.12.4': ['Dem HERRN'],
            'Josh.14.9': ['dem HERRN'],
            'Ruth.1.9': ['Der HERR'],
            '2Sam.15.7': ['dem HERRN'],
            '1Chr.16.10': ['den HERRN'],
            '1Chr.21.17': ['HERR'],
            '2Chr.35.3': ['dem HERRN', 'dem HERRN'],
            'Ps.34.11': ['den HERRN'],
            'Ps.41.5': ['HERR'],
            'Ps.105.3': ['den HERRN'],
            'Ps.118.4': ['den HERRN'],
            'Isa.1.28': ['den HERRN'],
            'Isa.42.12': ['dem HERRN'],
            'Ezek.37.13': ['der HERR'],
            'Zeph.1.6': ['dem HERRN', 'den HERRN'],
            'Mal.3.16': ['den HERRN', 'der HERR', 'den HERRN'],
        }
        for ref, names in expected.items():
            with self.subTest(ref=ref):
                self.assertEqual(name_edits(self.verses[ref])[0], names)

    def test_addresses_and_relative_clauses(self):
        cases = {
            'Jehova, der mich errettet hat, er wird helfen.': 'Der HERR, der mich errettet hat, er wird helfen.',
            'Jehova, der du mich errettet hast, hilf mir!': 'HERR, der du mich errettet hast, hilf mir!',
            'Ich lobe Jehova, der mich errettet hat.': 'Ich lobe den HERRN, der mich errettet hat.',
            'Und David sprach: „Jehova, der mich errettet hat, er wird helfen.“': 'Und David sprach: „Der HERR, der mich errettet hat, er wird helfen.“',
            'Jehova, Gott Israels!': 'HERR, Gott Israels!',
            'Ich sprach: Jehova, sei mir gnädig!': 'Ich sprach: HERR, sei mir gnädig!',
            'Rede, Jehova, denn dein Knecht hört.': 'Rede, HERR, denn dein Knecht hört.',
            'Jehova, mein Gott, es sei deine Hand mit mir.': 'HERR, mein Gott, es sei deine Hand mit mir.',
            'Jehova, unser Gott, hat geholfen.': 'Der HERR, unser Gott, hat geholfen.',
            'Jehova, unser Gott, sei mit uns!': 'Der HERR, unser Gott, sei mit uns!',
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                v = ET.Element('VERS'); v.text = text
                edits, _ = plan_verse(text, 'elb', rules())
                apply_edits(v, edits)
                self.assertEqual(plain(v), expected)

    def test_objects_and_sentence_boundaries(self):
        cases = {
            'Ich will Jehova ein Opfer darbringen.': ['dem HERRN'],
            'Ich gebe Jehova die Ehre.': ['dem HERRN'],
            'Er kam, um Jehova zu opfern.': ['dem HERRN'],
            'Er kam, um Jehova anzubeten und ihm zu opfern.': ['den HERRN'],
            'Ich habe Jehova nicht angefleht.': ['den HERRN'],
            'Wir haben Jehova verlassen.': ['den HERRN'],
            'Das Land gehört Jehova.': ['dem HERRN'],
            'Weil Jehova gehört hat, hilft er.': ['der HERR'],
            'das Volk, das Jehova gemacht hatte': ['der HERR'],
            'die Jehova suchen': ['den HERRN'],
            'Der Herr Jehova sprach.': ['HERR'],
            'des Herrn Jehova': ['HERRN'],
            'dem Jehova': ['HERRN'],
            'der Jehova': ['HERR'],
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(name_edits(text)[0], expected)
        # A verb after ':' belongs to the quotation, not to its addressee.
        self.assertEqual(name_edits('Sie befragten wiederum Jehova: Wird er kommen?')[0], ['den HERRN'])

    def test_ambiguous_singular_relative_clause_remains_reviewable(self):
        for text in ('das Jehova kannte', 'sie hat Jehova erwählt', 'Jehova, vielleicht morgen.'):
            with self.subTest(text=text):
                _, reviews = name_edits(text)
                self.assertTrue(any(r['kind'] == 'divine-name-syntax' for r in reviews))

    def test_second_person_divine_titles_have_their_own_case(self):
        expected = {
            'Deut.5.12': ['der HERR'],
            'Deut.5.15': ['der HERR', 'der HERR'],
            'Deut.6.13': ['Den HERRN'],
            'Deut.7.6': ['dem HERRN', 'der HERR'],
            'Deut.10.12': ['der HERR', 'den HERRN', 'dem HERRN'],
            'Deut.30.1': ['der HERR'],
            'Deut.32.6': ['dem HERRN'],
            '1Sam.12.19': ['den HERRN'],
            'Isa.48.17': ['der HERR', 'der HERR'],
            'Isa.51.22': ['der HERR'],
            'Hos.13.4': ['der HERR'],
        }
        for ref, names in expected.items():
            with self.subTest(ref=ref):
                actual, reviews = name_edits(self.verses[ref])
                self.assertEqual(actual, names)
                self.assertFalse([r for r in reviews if r['kind'] == 'divine-name-syntax'])

    def test_reported_speech_does_not_turn_the_speaker_into_an_addressee(self):
        for ref in ('Exod.5.1', 'Exod.9.1', 'Exod.9.13', 'Isa.49.18', 'Jer.15.6', 'Jer.51.25'):
            with self.subTest(ref=ref):
                self.assertEqual(name_edits(self.verses[ref])[0],
                                 ['der HERR'] * (2 if ref in {'Exod.9.1', 'Exod.9.13'} else 1))

    def test_actual_addresses_and_title_boundaries_remain_distinct(self):
        for text, expected in {
            'Lehre mich, Jehova, deinen Weg.': ['HERR'],
            'Jehova, dein Name währt ewiglich.': ['HERR'],
            'Jehova, dein Ohr neige zu mir.': ['HERR'],
            'Vergib, Jehova, deinem Volke!': ['HERR'],
            'Jehova, du bist mein Gott.': ['HERR'],
            'Ich sprach: Jehova, du weißt es.': ['HERR'],
            'Jehova, mein Gott, hilf mir!': ['HERR'],
            'Jehova, dein Gott, hilft dir.': ['Der HERR'],
            'So vergelte Jehova mir.': ['der HERR'],
        }.items():
            with self.subTest(text=text):
                self.assertEqual(name_edits(text)[0], expected)

    def test_psalm_title_question_has_nominative_answers(self):
        self.assertEqual(name_edits(self.verses['Ps.24.8'])[0], ['Der HERR', 'Der HERR'])
        self.assertEqual(name_edits(self.verses['Ps.24.10'])[0], ['Der HERR'])
        for text in ('Jehova, stark und mächtig!', 'O Jehova, mächtig im Kampf!'):
            with self.subTest(text=text):
                self.assertEqual(name_edits(text)[0], ['HERR'])

    def test_all_samuel_name_occurrences_classified(self):
        for ref, text in self.verses.items():
            if ref.startswith('1Sam.'):
                with self.subTest(ref=ref):
                    _, reviews = name_edits(text)
                    self.assertFalse([r for r in reviews if r['kind'] == 'divine-name-syntax'])

    def test_file_pipeline_preserves_markup_notes_and_audit(self):
        xml = '<XMLBIBLE><BIBLEBOOK bnumber="9"><CHAPTER cnumber="17"><VERS vnumber="37">Und David sprach: <gr str="3068"><STYLE>Je</STYLE>hova</gr><NOTE type="x-studynote">Jehova bleibt hier erhalten.</NOTE>, der mich errettet hat, er wird helfen.</VERS></CHAPTER></BIBLEBOOK></XMLBIBLE>'
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory)/'source.xml', Path(directory)/'language.xml'
            source.write_text(xml, encoding='utf-8')
            report = modernize(source, output, 'elb')
            before, after = parse_xml(source), parse_xml(output)
            self.assertEqual(plain(after.find('.//VERS')), 'Und David sprach: Der HERR, der mich errettet hat, er wird helfen.')
            self.assertEqual(note_fingerprints(before), note_fingerprints(after))
            self.assertEqual(strong_fingerprints(before), strong_fingerprints(after))
            self.assertEqual(report['review_kinds'].get('divine-name-syntax', 0), 0)
            verify(source, output, output.with_suffix('.changes.csv'))


if __name__ == '__main__':
    unittest.main()
