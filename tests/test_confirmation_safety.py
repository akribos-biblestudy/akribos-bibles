import copy
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from akribos.common import DataError, file_hash, tokenize
from akribos.confirm import (HINT, ConfirmationSafetyEvidence, confirm_uncertainty,
                             load_confirmation_evidence, verify_confirmation_transition,
                             _remove_preserving_tail)
from akribos.project import jsonl_gz, line
from akribos.xmlio import plain


NOTE = f'<NOTE ex="{HINT}">Uncertain synthetic assignment</NOTE>'


def bible(fragment):
    return ET.fromstring('<XMLBIBLE><INFORMATION/><BIBLEBOOK bnumber="43">'
                        '<CHAPTER cnumber="1"><VERS vnumber="1">'+fragment+
                        '</VERS></CHAPTER></BIBLEBOOK></XMLBIBLE>')


def occurrences(*rows):
    return [{'origin_id': f'John.1.1#{index:02}=NKO', 'strong': codes,
             'morph': morph, 'edition': 'WH'}
            for index, (codes, morph) in enumerate(rows, 1)]


class FunctionSafetyTests(unittest.TestCase):
    def check(self, fragment, source, *, reference=None, csv_reference=None, evidence=True, guarded=False):
        target = bible(fragment.replace('</gr>', '</gr>'+NOTE, 1))
        reference = fragment if reference is None else reference
        bk = bible(reference); csv = bible(reference if csv_reference is None else csv_reference)
        proof = (ConfirmationSafetyEvidence({'John.1.1': source},
                 frozenset({'John.1.1'} if guarded else ()), 'WH', {}) if evidence else None)
        result = confirm_uncertainty(target, bk, csv, safety_evidence=proof)
        counts = verify_confirmation_transition(target, result.root, result.audit, safety_evidence=proof)
        self.assertEqual(counts['hints_removed'], result.summary['hints_removed'])
        self.assertEqual(plain(target.find('.//VERS')), plain(result.root.find('.//VERS')))
        return target, result, proof

    def test_article_requires_actual_immediate_reference_neighbour(self):
        source = occurrences((['G3588'], 'T-NSN'))
        _, result, _ = self.check('<gr str="3588">das</gr> Lamm', source)
        self.assertEqual(result.summary['hints_removed'], 1)
        _, result, _ = self.check('<gr str="3588">das</gr> ist Gottes Lamm', source,
                                  reference='<gr str="3588">das</gr> Lamm Gottes')
        self.assertEqual(result.audit[0]['reason'], 'article-right-context-not-forced-adjacent')
        self.assertEqual(result.summary['hints_removed'], 0)

    def test_both_references_must_prove_article_neighbour(self):
        _, result, _ = self.check('<gr str="3588">das</gr> Lamm', occurrences((['G3588'], 'T-NSN')),
                                  csv_reference='<gr str="3588">das</gr> schöne Lamm')
        self.assertEqual(result.audit[0]['references']['elb-bk'], 'confirmed')
        self.assertEqual(result.audit[0]['references']['elb-csv'], 'article-right-context-not-forced-adjacent')
        self.assertEqual(result.summary['hints_removed'], 0)

    def test_article_boundaries_ambiguity_and_end_retain(self):
        source = occurrences((['G3588'], 'T-NSN'))
        for target, reference, reason in [
            ('<gr str="3588">das</gr> Lamm', '<gr str="3588">das</gr>, Lamm', 'article-reference-context-boundary'),
            ('<gr str="3588">das</gr>, Lamm', None, 'article-target-context-boundary'),
            ('<gr str="3588">das</gr> Lamm', '<gr str="3588">das</gr> Lamm Lamm', 'article-right-context-not-forced-adjacent'),
            ('<gr str="3588">das</gr>', None, 'article-without-right-context'),
            ('<gr str="3588">das Lamm</gr>', None, 'article-multiword-context-unproved'),
        ]:
            with self.subTest(reason=reason):
                _, result, _ = self.check(target, source, reference=reference)
                self.assertEqual(result.audit[0]['reason'], reason)
                self.assertEqual(result.summary['hints_removed'], 0)

    def test_multicode_article_still_needs_context(self):
        source = occurrences((['G1722'], 'PREP'), (['G3588'], 'T-DSM'))
        _, good, _ = self.check('<gr str="1722 3588">im</gr> Tempel', source)
        self.assertEqual(good.summary['hints_removed'], 1)
        _, bad, _ = self.check('<gr str="1722 3588">im</gr> Tempel', source,
                               reference='<gr str="1722 3588">im</gr> Hause')
        self.assertEqual(bad.summary['hints_removed'], 0)

    def test_public_replay_rechecks_article_target_context(self):
        for fragment in ('<gr str="3588">das</gr>', '<gr str="3588">das Lamm</gr>',
                         '<gr str="3588">das</gr>, Lamm'):
            with self.subTest(fragment=fragment):
                target, result, evidence = self.check(fragment, occurrences((['G3588'], 'T-NSN')))
                rows = copy.deepcopy(result.audit)
                rows[0].update(status='confirmed', reason='both-references-confirm-complete-set',
                               references={'elb-bk':'confirmed','elb-csv':'confirmed'})
                changed = copy.deepcopy(result.root);verse = changed.find('.//VERS')
                _remove_preserving_tail(verse, verse.find('NOTE'))
                with self.assertRaisesRegex(DataError, 'Article target context'):
                    verify_confirmation_transition(target, changed, rows, safety_evidence=evidence)

    def test_identical_reference_errors_do_not_confirm_infinitival_zu(self):
        target, result, proof = self.check('<gr str="4314">zu</gr> <gr str="470">antworten</gr>',
                           occurrences((['G4314'], 'PREP'), (['G470'], 'V-APN')))
        self.assertEqual(result.audit[0]['references'], {'elb-bk': 'confirmed', 'elb-csv': 'confirmed'})
        self.assertEqual(result.audit[0]['reason'], 'preposition-on-possible-infinitival-zu')
        self.assertEqual(result.summary['hints_removed'], 0)
        forged = copy.deepcopy(result.audit)
        forged[0].update(status='confirmed', reason='both-references-confirm-complete-set')
        with self.assertRaisesRegex(DataError, 'safety veto'):
            verify_confirmation_transition(target, result.root, forged, safety_evidence=proof)

    def test_lowercase_possessive_nominalization_and_unlinked_word_are_not_verb_proofs(self):
        for fragment, source in [
            ('<gr str="4314">zu</gr> <gr str="846">ihren</gr> Kindern',
             occurrences((['G4314'], 'PREP'), (['G846'], 'P-3GP'))),
            ('<gr str="4314">zu</gr> <gr str="470">Antworten</gr>',
             occurrences((['G4314'], 'PREP'), (['G470'], 'V-APN'))),
            ('<gr str="4314">zu</gr> sagen', occurrences((['G4314'], 'PREP'))),
        ]:
            with self.subTest(fragment=fragment):
                _, result, _ = self.check(fragment, source)
                self.assertEqual(result.summary['hints_removed'], 1)

    def test_overassignment_counts_every_span_including_composite_codes(self):
        for fragment, source in [
            ('<gr str="1537">zu</gr> mir setze dich <gr str="1537">zu</gr> meiner Rechten',
             occurrences((['G1537'], 'PREP'))),
            ('<gr str="4314">zu</gr> ihnen <gr str="4314 470 5023">darauf</gr>',
             occurrences((['G4314'], 'PREP'))),
            ('<gr str="3588">das</gr> Lamm <gr str="3588">der</gr> Stadt',
             occurrences((['G3588'], 'T-NSN'))),
            ('<gr str="1437 3739">wer</gr> hört <gr str="3739">welcher</gr> spricht',
             occurrences((['G1437'], 'COND'), (['G3739'], 'R-NSM'))),
        ]:
            with self.subTest(fragment=fragment):
                _, result, _ = self.check(fragment, source)
                self.assertEqual(result.audit[0]['reason'], 'function-code-over-assigned-in-verse')
                self.assertEqual(result.summary['hints_removed'], 0)

    def test_one_phrase_counts_once_and_source_multicode_occurrence_counts_once(self):
        _, result, _ = self.check('<gr str="4314">darauf hin</gr>',
                                  occurrences((['G4314', 'G470'], 'PREP')))
        self.assertEqual(result.summary['hints_removed'], 1)

    def test_three_target_pronoun_spans_need_more_than_one_actual_occurrence(self):
        _, result, _ = self.check(
            '<gr str="3165">Ich</gr> stehe wo <gr str="3165">ich</gr> gerichtet werde '
            'und <gr str="3165">ich</gr> nichts tat', occurrences((['G3165'], 'P-1AS')))
        self.assertEqual(result.audit[0]['reason'], 'function-code-over-assigned-in-verse')
        self.assertEqual(result.summary['hints_removed'], 0)

    def test_greek_accusative_infinitive_subject_can_translate_german_ich(self):
        _, result, _ = self.check('<gr str="3165">ich</gr> soll gerichtet werden',
                                  occurrences((['G3165'], 'P-1AS')))
        self.assertEqual(result.summary['hints_removed'], 1)

    def test_epi_count_includes_a_composite_noun_span(self):
        _, result, _ = self.check(
            '<gr str="1909">mit</gr> dem <gr str="1909 2563">Rohr</gr> '
            '<gr str="1909">auf</gr> zwölftausend', occurrences((['G1909'], 'PREP')))
        self.assertEqual(result.audit[0]['reason'], 'function-code-over-assigned-in-verse')
        self.assertEqual(result.summary['hints_removed'], 0)

    def test_two_real_preposition_occurrences_allow_two_target_spans(self):
        _, result, _ = self.check('<gr str="1909">auf</gr> Erden und <gr str="1909">auf</gr> dem Meer',
                                  occurrences((['G1909'], 'PREP'), (['G1909'], 'PREP')))
        self.assertEqual(result.summary['hints_removed'], 1)
        _, result, _ = self.check('<gr str="4314">zu</gr> ihm <gr str="4314">zu</gr> ihr',
                                  occurrences((['G4314'], 'PREP'), (['G4314'], 'PREP')))
        self.assertEqual(result.summary['hints_removed'], 1)

    def test_missing_source_evidence_and_prior_alignment_guard_retain(self):
        for options, reason in [
            ({'evidence': False}, 'missing-function-word-source-evidence'),
            ({}, 'missing-function-word-source-verse'),
            ({'guarded': True}, 'prior-verse-inventory-mismatch'),
        ]:
            with self.subTest(reason=reason):
                source = occurrences((['G4314'], 'PREP')) if options else []
                _, result, _ = self.check('<gr str="4314">zu</gr> ihm', source, **options)
                self.assertEqual(result.audit[0]['reason'], reason)
                self.assertEqual(result.summary['hints_removed'], 0)

    def test_isolated_es_cannot_receive_conjunction_code_even_when_references_agree(self):
        for fragment, removed in [
            ('<gr str="3754">es</gr> sei der Gärtner', 0),
            ('<gr str="846 3754">es</gr> sei der Gärtner', 0),
            ('<gr str="3754">dass</gr> er kommt', 1),
            ('<gr str="846">es</gr> kommt', 1),
            ('<gr str="3754">es sei</gr> der Gärtner', 1),
        ]:
            with self.subTest(fragment=fragment):
                _, result, _ = self.check(fragment, [], evidence=False)
                self.assertEqual(result.summary['hints_removed'], removed)
                if not removed:
                    self.assertEqual(result.audit[0]['reason'], 'conjunction-on-isolated-german-es')
                    self.assertEqual(result.audit[0]['references'], {'elb-bk':'confirmed','elb-csv':'confirmed'})

    def test_replay_rejects_unknown_veto_text_and_nonarticle_context_status(self):
        target, result, proof = self.check('<gr str="4314">zu</gr> ihm', [])
        for change in [
            {'reason': 'PRIVATE REFERENCE WORDS'},
            {'reason': 'article-without-right-context',
             'references': {'elb-bk': 'article-without-right-context', 'elb-csv': 'confirmed'}},
        ]:
            rows = copy.deepcopy(result.audit);rows[0].update(change)
            with self.assertRaises(DataError):
                verify_confirmation_transition(target, result.root, rows, safety_evidence=proof)


class SafetyEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = bible('<gr str="4314">zu</gr> ihm')
        text = plain(self.target.find('.//VERS'))
        self.alignment = {'ref': 'John.1.1', 'text': text, 'tokens': tokenize(text),
                          'step_profile': 'WH', 'inventory_mismatch': False}
        self.source = {'ref': 'John.1.1', 'tokens': occurrences((['G4314'], 'PREP'))}
        self.paths = [self.root/'source.jsonl.gz', self.root/'alignment.jsonl.gz']

    def load(self, sources=None, alignments=None):
        for path, rows in zip(self.paths, (sources if sources is not None else [self.source],
                                          alignments if alignments is not None else [self.alignment])):
            with jsonl_gz(path) as stream:
                for row in rows:line(stream, row)
        return load_confirmation_evidence(self.target, *self.paths, nt_edition='WH')

    def test_existing_artifacts_are_hashed_and_no_reference_words_are_retained(self):
        self.source['tokens'][0].update(text='SOURCE WORD', gloss='SOURCE GLOSS')
        evidence = self.load()
        self.assertEqual(evidence.sha256, {'source_occurrences': file_hash(self.paths[0]),
                                          'alignment': file_hash(self.paths[1])})
        self.assertNotIn('SOURCE WORD', json.dumps(evidence.occurrences))
        self.assertNotIn('SOURCE GLOSS', json.dumps(evidence.occurrences))

    def test_missing_or_duplicate_alignment_verses_fail(self):
        for rows in ([], [self.alignment, self.alignment]):
            with self.subTest(rows=len(rows)), self.assertRaises(DataError):self.load(alignments=rows)

    def test_alignment_text_positions_profile_and_guard_must_match(self):
        original = copy.deepcopy(self.alignment)
        for change in ({'text': 'anderer Text'}, {'step_profile': 'TR'}, {'inventory_mismatch': 'false'}):
            self.alignment = original | change
            with self.subTest(change=change), self.assertRaises(DataError):self.load()
        self.alignment = copy.deepcopy(original);self.alignment['tokens'][0]['start'] = 1
        with self.assertRaises(DataError):self.load()

    def test_duplicate_occurrence_or_wrong_source_verse_and_edition_fail(self):
        original = copy.deepcopy(self.source)
        for change in ({'origin_id': 'John.1.2#01=NKO'}, {'edition': 'TR'}):
            self.source = copy.deepcopy(original);self.source['tokens'][0].update(change)
            with self.subTest(change=change), self.assertRaises(DataError):self.load()
        self.source = copy.deepcopy(original);self.source['tokens'].append(copy.deepcopy(self.source['tokens'][0]))
        with self.assertRaises(DataError):self.load()
        self.source = copy.deepcopy(original)
        with self.assertRaises(DataError):self.load(sources=[self.source, self.source])

    def test_source_numbering_alternatives_are_preserved_as_a_veto(self):
        for origin in ('John.1.1(1.2)#01=NKO', 'John.1.1[1.2]#01=NKO', 'John.1.1{1.2}#01=NKO'):
            with self.subTest(origin=origin):
                self.source['tokens'][0]['origin_id'] = origin
                evidence = self.load()
                self.assertEqual(evidence.source_guarded_verses, frozenset({'John.1.1'}))
                target = bible('<gr str="4314">zu</gr>'+NOTE+' ihm')
                result = confirm_uncertainty(target, self.target, self.target, safety_evidence=evidence)
                self.assertEqual(result.audit[0]['reason'], 'source-verse-numbering-unproved')
                self.assertEqual(result.summary['hints_removed'], 0)


if __name__ == '__main__':unittest.main()
