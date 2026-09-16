import copy
import csv
import gzip
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from akribos.common import DataError
from akribos.confirm import HINT
from akribos.linguistic import (PROVENANCE, load_reference_occurrences, validate_files,
                               validate_tree, verify_transition, _load_alignment_guards)
from akribos.xmlio import plain


def bible(fragment, book=40):
    return ET.fromstring(f'<XMLBIBLE><INFORMATION><rights>Original rights</rights></INFORMATION>'
        f'<BIBLEBOOK bnumber="{book}"><CHAPTER cnumber="1"><VERS vnumber="1">{fragment}'
        '</VERS></CHAPTER></BIBLEBOOK></XMLBIBLE>')


def hint(body='Automatische Zuordnung'):
    return f'<NOTE type="x-explanation" ex="{HINT}">{body}</NOTE>'


def occurrence(n, code, morph, conjoined='', ref='Matt.1.1', **extra):
    return {'origin_id': f'{ref}#{n:02}=NKO' if not code.startswith('H') else f'{ref}#{n:02}=L',
            'word':f'{n:02}', 'strong':[code], 'morph':morph, 'conjoined':conjoined,
            'edition':'WH' if code.startswith('G') else 'L/Q', **extra}


def article_source():
    return [occurrence(1,'G991','V-PAI-3S'), occurrence(2,'G3588','T-ASM','#02»03:G5207'),
            occurrence(3,'G5207','N-ASM')]


def article_target(marked=False):
    return bible('<gr str="991" custom="preserve">sieht</gr> '+
                 ('<gr str="3588" rmac="T">den</gr>'+hint() if marked else 'den')+
                 ' <gr str="5207">Sohn</gr>.')


def article_reference():
    return bible('<gr str="991">sieht</gr> <gr str="3588">den</gr> <gr str="5207">Sohn</gr>.')


def hints(root):return sum(n.get('ex')==HINT for n in root.iter('NOTE'))


class AuditSchemaTests(unittest.TestCase):
    def result(self, marked=False, corroborated=True):
        target = article_target(marked)
        reference = article_reference() if corroborated else bible('anderer Wortlaut')
        source = {'Matt.1.1': article_source()}
        result = validate_tree(target, source,
            corroborating_roots={'elb-bk':reference, 'elb-csv':copy.deepcopy(reference)})
        self.assertTrue(verify_transition(target, result.root, result.audit, source))
        return target, result, source

    def test_no_extra_fields_or_free_text_in_accepted_or_retained_rows(self):
        mutations = [
            lambda row: row.update(private_path='/tmp/private-reference.xml'),
            lambda row: row.update(private_reference_text='PRIVATE REFERENCE CONTENT'),
            lambda row: row.update(reason='PRIVATE REFERENCE CONTENT'),
            lambda row: row['references'].update({'elb-csv':'PRIVATE REFERENCE CONTENT'}),
            lambda row: row['references'].update({'private-reference':'confirmed'}),
            lambda row: row['references'].update({'elb-csv':{'text':'PRIVATE REFERENCE CONTENT'}}),
        ]
        for marked in (False, True):
            for corroborated in (False, True):
                target, result, source = self.result(marked, corroborated)
                for mutate in mutations:
                    with self.subTest(marked=marked, corroborated=corroborated, mutate=mutate):
                        rows=copy.deepcopy(result.audit);mutate(rows[0])
                        with self.assertRaises(DataError):verify_transition(target,result.root,rows,source)

    def test_retained_target_text_and_strong_fields_are_bound_to_own_xml(self):
        for marked in (False,True):
            target,result,source=self.result(marked,False)
            rows=copy.deepcopy(result.audit);rows[0]['target_text']='PRIVATE REFERENCE CONTENT'
            with self.assertRaises(DataError):verify_transition(target,result.root,rows,source)
            if marked:
                for key,value in [('target_strong',['G1']),('target_tokens',['d999'])]:
                    rows=copy.deepcopy(result.audit);rows[0][key]=value
                    with self.assertRaises(DataError):verify_transition(target,result.root,rows,source)

    def test_retained_article_proof_is_closed_and_checked_against_step(self):
        target,result,source=self.result(False,False)
        for mutate in [
            lambda proof: proof.update(private_reference_text='PRIVATE REFERENCE CONTENT'),
            lambda proof: proof.update(rule={'text':'PRIVATE REFERENCE CONTENT'}),
            lambda proof: proof.update(source_article='PRIVATE REFERENCE CONTENT'),
            lambda proof: proof.update(source_article='Matt.1.1#99=NKO'),
        ]:
            rows=copy.deepcopy(result.audit);mutate(rows[0]['proof'])
            with self.assertRaises(DataError):verify_transition(target,result.root,rows,source)

    def test_retained_hint_without_target_cannot_carry_added_text_fields(self):
        target=bible('Wort'+hint());source={'Matt.1.1':article_source()}
        result=validate_tree(target,source)
        rows=copy.deepcopy(result.audit)
        rows[0].update(target_text='PRIVATE REFERENCE CONTENT',target_strong=[],target_tokens=[])
        with self.assertRaisesRegex(DataError,'unrelated target'):
            verify_transition(target,result.root,rows,source)

    def test_free_text_guard_reason_cannot_be_published_by_file_phase(self):
        with self.assertRaises(DataError):
            validate_tree(article_target(True),{'Matt.1.1':article_source()},
                          verse_guards={'Matt.1.1':'PRIVATE REFERENCE CONTENT'})


class ProperNamePhaseTests(unittest.TestCase):
    def fixture(self, hebrew=False, corroborated=True):
        code,word,ref,book = ('H85','Abraham','Gen.1.1',1) if hebrew else ('G2424','Jesus','Matt.1.1',40)
        target=bible(f'<gr str="{code[1:]}" custom="preserve">{word}</gr>'+hint()+
                     '<NOTE type="x-studynote">Original <STYLE>Notiz</STYLE></NOTE> geht.',book)
        reference=bible(f'<gr str="{code[1:] if corroborated else "1"}">{word}</gr> geht.',book)
        different=bible(f'<gr str="1">{word}</gr> geht.',book)
        source={ref:[occurrence(1,code,'HNpm' if hebrew else 'N-NSM-P',ref=ref,
                               text='אַבְרָהָ֔ם' if hebrew else 'Ἰησοῦς',lemma='Ἰησοῦς')]}
        references={'elb-bk':reference,'elb-csv':different}
        return target,source,references

    def test_name_confirmation_preserves_tag_text_notes_and_is_idempotent(self):
        for hebrew in (False,True):
            with self.subTest(hebrew=hebrew):
                target,source,refs=self.fixture(hebrew);before=ET.tostring(target)
                result=validate_tree(target,source,corroborating_roots=refs)
                self.assertEqual(result.summary['hints_removed'],1)
                self.assertEqual(result.summary['article_tags_added'],0)
                self.assertEqual(result.audit[0]['proof']['rule'],'unique-proper-name-with-independent-reference')
                self.assertEqual(result.root.find('.//gr').get('custom'),'preserve')
                self.assertEqual(result.root.find('.//gr').get('str'),target.find('.//gr').get('str'))
                self.assertEqual(result.root.find('.//NOTE/STYLE').text,'Notiz')
                self.assertEqual(ET.tostring(target),before)
                verify_transition(target,result.root,result.audit,source)
                repeated=validate_tree(result.root,source,corroborating_roots=refs)
                self.assertEqual(ET.tostring(repeated.root),ET.tostring(result.root))
                self.assertEqual(repeated.summary['hints_removed'],0)

    def test_missing_precise_name_confirmation_is_retained_with_closed_statuses(self):
        target,source,refs=self.fixture(corroborated=False)
        result=validate_tree(target,source,corroborating_roots=refs)
        self.assertEqual(result.summary['hints_removed'],0)
        self.assertEqual(result.audit[0]['reason'],'no-independent-word-level-name-corroboration')
        verify_transition(target,result.root,result.audit,source)
        result.audit[0]['references']['elb-csv']='PRIVATE REFERENCE CONTENT'
        with self.assertRaises(DataError):verify_transition(target,result.root,result.audit,source)

    def test_name_proof_is_bound_to_catalog_source_and_reference(self):
        target,source,refs=self.fixture()
        result=validate_tree(target,source,corroborating_roots=refs)
        for mutation in [
            lambda row:row['proof'].update(catalog_entry_sha256='0'*64),
            lambda row:row['proof'].update(source_token='Matt.1.1#99=NKO'),
            lambda row:row['proof'].update(strong='G3972'),
            lambda row:row['proof'].update(morph='N-NSM'),
            lambda row:row['proof'].update(private_reference_text='PRIVATE REFERENCE CONTENT'),
            lambda row:row['references'].update({'elb-bk':'different-strong-set'}),
        ]:
            rows=copy.deepcopy(result.audit);mutation(rows[0])
            with self.assertRaises(DataError):verify_transition(target,result.root,rows,source)
        changed=copy.deepcopy(source);changed['Matt.1.1'][0]['lemma']='Παῦλος'
        with self.assertRaises(DataError):verify_transition(target,result.root,result.audit,changed)

    def test_name_rule_keeps_guards_and_cannot_add_an_unmarked_code(self):
        target,source,refs=self.fixture()
        for change in ('guard','provenance','unmarked'):
            current=copy.deepcopy(target);kwargs={}
            if change=='guard':kwargs['verse_guards']={'Matt.1.1':'prior-verse-inventory-mismatch'}
            elif change=='provenance':current.find('.//gr').set(PROVENANCE,'1.4.0')
            else:current.find('.//gr').attrib.pop('str')
            result=validate_tree(current,source,corroborating_roots=refs,**kwargs)
            self.assertEqual(result.summary['hints_removed'],0)
            self.assertEqual(result.summary['article_tags_added'],0)


class TreeTests(unittest.TestCase):
    def run_article(self, root=None, source=None, **kwargs):
        return validate_tree(root if root is not None else article_target(),
            {'Matt.1.1':source if source is not None else article_source()},
            corroborating_roots=kwargs.pop('corroborating_roots',{'elb-bk':article_reference()}), **kwargs)

    def test_addition_needs_occurrence_morphology_and_independent_reference(self):
        target=article_target(); before=ET.tostring(target)
        result=self.run_article(target)
        self.assertEqual(result.summary['article_tags_added'],1)
        self.assertEqual(ET.tostring(target),before)
        self.assertEqual(plain(result.root.find('.//VERS')),'sieht den Sohn.')
        article=result.root.find('.//gr[@str="3588"]')
        self.assertEqual(article.get(PROVENANCE),'1.4.0')
        self.assertEqual(result.audit[0]['references'],{'elb-bk':'confirmed'})
        self.assertEqual(result.root.find('.//gr[@str="991"]').get('custom'),'preserve')

    def test_missing_independent_article_reference_retains_candidate(self):
        result=self.run_article(corroborating_roots={})
        self.assertEqual(result.summary['article_tags_added'],0)
        self.assertEqual(result.audit[0]['reason'],'no-independent-article-corroboration')
        self.assertEqual(result.audit[0]['after_strong'],[])
        self.assertEqual(result.audit[0]['proposed_strong'],['G3588'])

    def test_disagreeing_reference_does_not_confirm_by_verse_inventory(self):
        reference=bible('<gr str="3588">sieht</gr> den <gr str="5207">Sohn</gr>.')
        result=self.run_article(corroborating_roots={'elb-csv':reference})
        self.assertEqual(result.summary['article_tags_added'],0)

    def test_uncertain_reference_article_cannot_confirm(self):
        reference=bible('<gr str="991">sieht</gr> <gr str="3588">den</gr>'+hint()+' <gr str="5207">Sohn</gr>.')
        result=self.run_article(corroborating_roots={'elb-bk':reference})
        self.assertEqual(result.summary['article_tags_added'],0)
        self.assertEqual(result.audit[0]['action'],'retain')
    def test_extended_or_malformed_reference_number_is_not_truncated(self):
        reference=bible('<gr str="991">sieht</gr> <gr str="3588a">den</gr> <gr str="5207">Sohn</gr>.')
        result=self.run_article(corroborating_roots={'elb-bk':reference})
        self.assertEqual(result.summary['article_tags_added'],0)
    def test_one_reference_is_sufficient_in_addition_to_grammatical_proof(self):
        result=self.run_article(corroborating_roots={'elb-bk':article_reference(), 'elb-csv':bible('unrelated')})
        self.assertEqual(result.summary['article_tags_added'],1)

    def test_broad_reference_span_is_not_a_word_confirmation(self):
        reference=bible('<gr str="991">sieht</gr> <gr str="3588">den Sohn</gr>.')
        result=self.run_article(corroborating_roots={'elb-bk':reference})
        self.assertEqual(result.summary['article_tags_added'],0)

    def test_existing_article_keeps_strong_and_original_attributes(self):
        result=self.run_article(article_target(True))
        self.assertEqual(result.summary['hints_removed'],1)
        article=result.root.find('.//gr[@str="3588"]')
        self.assertEqual(article.get('rmac'),'T')
        self.assertEqual(article.get('str'),'3588')
        self.assertEqual(hints(result.root),0)

    def test_article_hint_needs_independent_corroboration_too(self):
        result=self.run_article(article_target(True),corroborating_roots={})
        self.assertEqual(result.summary['hints_removed'],0)
        self.assertEqual(hints(result.root),1)

    def test_atomic_greek_conjunction_has_two_independent_anchors(self):
        target=bible('<gr str="3962">Vater</gr> <gr str="2532">und</gr>'+hint()+' <gr str="5207">Sohn</gr>')
        source=[occurrence(1,'G3962','N-NSM'), occurrence(2,'G2532','CONJ'), occurrence(3,'G5207','N-NSM')]
        result=validate_tree(target,{'Matt.1.1':source})
        self.assertEqual(result.summary['hints_removed'],1)
        self.assertIn('atomic-function',result.audit[0]['proof']['rule'])

    def test_atomic_hebrew_noun_checks_source_pos_and_translation_form(self):
        target=bible('<gr str="559">sprach</gr> <gr str="430">Gott</gr>'+hint()+' <gr str="216">Licht</gr>',book=1)
        source=[occurrence(1,'H559','HVqw3ms',ref='Gen.1.1'), occurrence(2,'H430','HNcmpa',ref='Gen.1.1'),
                occurrence(3,'H216','HNcbsa',ref='Gen.1.1')]
        result=validate_tree(target,{'Gen.1.1':source})
        self.assertEqual(result.summary['hints_removed'],1)
        source[1]['morph']='HVqp3ms'
        self.assertEqual(validate_tree(target,{'Gen.1.1':source}).summary['hints_removed'],0)

    def test_multiword_original_span_cannot_supply_independent_anchor(self):
        target=bible('<gr str="991">er sieht</gr> den <gr str="5207">Sohn</gr>.')
        reference=bible('er <gr str="991">sieht</gr> <gr str="3588">den</gr> <gr str="5207">Sohn</gr>.')
        result=self.run_article(target,corroborating_roots={'elb-bk':reference})
        self.assertEqual(result.summary['article_tags_added'],0)

    def test_original_notes_styles_and_tails_are_immutable(self):
        target=article_target(True)
        article=target.find('.//gr[@str="3588"]')
        article.text='d'; ET.SubElement(article,'STYLE',{'css':'bold'}).text='en'
        note=ET.SubElement(target.find('.//VERS'),'NOTE',{'type':'x-studynote'})
        note.text='Original ';ET.SubElement(note,'STYLE').text='Notiz';note.tail=' Ende'
        before_note=ET.tostring(note)
        result=self.run_article(target)
        self.assertEqual(result.summary['hints_removed'],1)
        self.assertEqual(ET.tostring(result.root.find('.//NOTE')),before_note)
        self.assertEqual(result.root.find('.//gr[@str="3588"]/STYLE').text,'en')

    def test_every_hint_is_audited_including_notes_and_captions(self):
        target=article_target(True)
        verse=target.find('.//VERS')
        verse.append(ET.fromstring('<NOTE type="x-studynote">Original'+hint()+'</NOTE>'))
        chapter=target.find('.//CHAPTER'); caption=ET.SubElement(chapter,'CAPTION',{'vnumber':'0'})
        caption.append(ET.fromstring(hint()))
        result=self.run_article(target)
        self.assertEqual(result.summary['hints_before'],3)
        self.assertEqual(len([a for a in result.audit if a['kind']=='uncertainty']),3)
        self.assertEqual(result.summary['hints_remaining'],2)

    def test_structured_or_orphaned_hint_is_preserved(self):
        for fragment in ('<gr str="3588">den</gr>'+hint('<STYLE>Text</STYLE>'), 'den'+hint()):
            result=validate_tree(bible(fragment),{'Matt.1.1':article_source()})
            self.assertEqual(result.summary['hints_removed'],0)
            self.assertEqual(result.summary['hints_remaining'],1)

    def test_malformed_or_wrong_testament_codes_cannot_become_anchors(self):
        for code in ('991 unknown','991 H991','991 99999'):
            target=article_target();target.find('.//gr').set('str',code)
            self.assertEqual(self.run_article(target).summary['article_tags_added'],0)

    def test_article_crossing_markup_slots_is_not_restructured(self):
        target=bible('<gr str="991">sieht</gr> d<STYLE>en</STYLE> <gr str="5207">Sohn</gr>.')
        result=self.run_article(target)
        self.assertEqual(result.summary['article_tags_added'],0)
        self.assertEqual(ET.tostring(target),ET.tostring(result.root))

    def test_repeated_run_is_idempotent_and_provenance_does_not_become_anchor(self):
        first=self.run_article(article_target(True))
        second=self.run_article(first.root)
        self.assertEqual(ET.tostring(first.root),ET.tostring(second.root))
        self.assertEqual(second.summary['hints_removed'],0)
        third=self.run_article(article_target())
        fourth=self.run_article(third.root)
        self.assertEqual(ET.tostring(third.root),ET.tostring(fourth.root))
        self.assertEqual(fourth.summary['article_tags_added'],0)

    def test_preexisting_linguistic_provenance_cannot_supply_anchor(self):
        target=article_target();target.find('.//gr[@str="991"]').set(PROVENANCE,'1.4.0')
        self.assertEqual(self.run_article(target).summary['article_tags_added'],0)

    def test_1_3_confirmed_annotation_without_hint_is_an_anchor(self):
        self.assertEqual(self.run_article(article_target()).summary['article_tags_added'],1)

    def test_no_same_pass_bootstrapping(self):
        target=bible('<gr str="3962">Vater</gr> <gr str="2532">und</gr>'+hint()+
                     ' <gr str="5207">Sohn</gr> <gr str="2228">oder</gr>'+hint()+' <gr str="2316">Gott</gr>')
        source=[occurrence(1,'G3962','N-NSM'),occurrence(2,'G2532','CONJ'),occurrence(3,'G5207','N-NSM'),
                occurrence(4,'G2228','CONJ'),occurrence(5,'G2316','N-NSM')]
        result=validate_tree(target,{'Matt.1.1':source})
        # Both proofs have independently trusted noun anchors, so both may pass;
        # neither proof cites the other conjunction as a new anchor.
        self.assertEqual(result.summary['hints_removed'],2)
        for row in result.audit:
            self.assertNotIn(row['proof']['source_left'],{source[1]['origin_id'],source[3]['origin_id']})
            self.assertNotIn(row['proof']['source_right'],{source[1]['origin_id'],source[3]['origin_id']})

    def test_prior_inventory_guard_blocks_both_hints_and_additions(self):
        for marked in (True,False):
            result=self.run_article(article_target(marked),verse_guards={'Matt.1.1':'prior-verse-inventory-mismatch'})
            self.assertEqual(result.summary['hints_removed'],0)
            self.assertEqual(result.summary['article_tags_added'],0)

    def test_wrong_source_verse_cannot_supply_proof(self):
        source=article_source();source[0]['origin_id']='Matt.1.2#01=NKO'
        result=self.run_article(article_target(True),source)
        self.assertEqual(result.audit[0]['reason'],'source-occurrence-belongs-to-other-verse')
        self.assertEqual(result.summary['hints_removed'],0)

    def test_wrong_edition_and_duplicate_occurrence_are_protected(self):
        for wrong in ('edition','duplicate'):
            source=article_source()
            if wrong=='edition':source[1]['edition']='TR'
            else:source[1]['origin_id']=source[0]['origin_id']
            self.assertEqual(self.run_article(article_target(True),source).summary['hints_removed'],0)

    def test_absent_code_is_missing_evidence_and_preserved_for_review(self):
        target=bible('<gr str="999">Fremd</gr>'+hint())
        result=validate_tree(target,{'Matt.1.1':article_source()})
        self.assertEqual(result.audit[0]['status'],'review')
        self.assertEqual(result.audit[0]['reason'],'code-absent-in-selected-source')
        self.assertEqual(result.summary['hints_rejected'],0)
        self.assertEqual(hints(result.root),1)
        self.assertEqual(result.root.find('.//gr').get('str'),'999')
        self.assertEqual(ET.tostring(result.root),ET.tostring(target))
        verify_transition(target,result.root,result.audit,{'Matt.1.1':article_source()})
        result.audit[0]['status']='reject'
        with self.assertRaisesRegex(DataError,'Invalid retained uncertainty decision'):
            verify_transition(target,result.root,result.audit,{'Matt.1.1':article_source()})

    def test_duplicate_target_verse_fails_before_changes(self):
        target=article_target();chapter=target.find('.//CHAPTER');chapter.append(copy.deepcopy(chapter[0]))
        before=ET.tostring(target)
        with self.assertRaisesRegex(DataError,'Duplicate verse'):self.run_article(target)
        self.assertEqual(ET.tostring(target),before)

    def test_audit_contains_no_private_reference_content(self):
        reference=article_reference();reference.find('.//INFORMATION').text='Privater Referenzmarker'
        result=self.run_article(corroborating_roots={'elb-bk':reference})
        self.assertNotIn('Privater Referenzmarker',json.dumps(result.audit))
        self.assertNotIn('Privater Referenzmarker',json.dumps(result.summary))


class FileTests(unittest.TestCase):
    def fixture(self, folder):
        folder=Path(folder)
        profile={'id':'tagnt','paths':['greek.tsv'],'options':{'profile':'tagnt','prefix':'G','edition':'WH',
          'columns':{'ref':0,'text':1,'gloss':2,'strong':11,'combined':3,'lemma':4,'editions':5,'variants':6}}}
        config=folder/'profiles.json';config.write_text(json.dumps([profile]))
        rows=[]
        for source in article_source():
            row=['']*17;row[0]=source['origin_id'];row[1]='Greek';row[2]='gloss'
            row[3]=source['strong'][0]+'='+source['morph'];row[4]='lemma=gloss';row[5]='WH+TR'
            row[10]=source['conjoined'];row[11]=source['strong'][0];rows.append(row)
        with (folder/'greek.tsv').open('w',newline='') as stream:csv.writer(stream,delimiter='\t').writerows(rows)
        inp=folder/'input.xml';inp.write_bytes(ET.tostring(article_target(True)))
        peer=folder/'peer.xml';peer.write_bytes(ET.tostring(article_reference()))
        return inp,config,peer

    def test_files_are_reproducible_gzip_manifest_and_sources_immutable(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);inp,config,peer=self.fixture(folder)
            originals={p:p.read_bytes() for p in (inp,config,peer,folder/'greek.tsv')}
            outputs=[]
            for name in ('a','b'):
                out=folder/name/'06-linguistic.xml'
                result=validate_files(inp,out,source_profiles_path=config,source_root=folder,
                                      corroborating_paths={'elb-bk':peer})
                self.assertEqual(result.summary['hints_removed'],1)
                outputs.append({p.suffix+p.name:p.read_bytes() for p in out.parent.iterdir()})
            self.assertEqual(outputs[0],outputs[1])
            self.assertEqual(originals,{p:p.read_bytes() for p in originals})
            manifest=json.loads((folder/'a/06-linguistic.manifest.json').read_text())
            self.assertTrue(manifest['rule_identity']['sha256'])
            self.assertNotIn(str(folder),json.dumps(manifest))
            with gzip.open(folder/'a/06-linguistic.audit.jsonl.gz','rt') as stream:
                self.assertEqual(json.loads(stream.readline())['action'],'remove-hint')

    def test_no_output_may_overwrite_any_input(self):
        with tempfile.TemporaryDirectory() as folder:
            inp,config,peer=self.fixture(folder)
            for output in (inp,config,peer,Path(folder)/'greek.tsv'):
                with self.assertRaises(DataError):
                    validate_files(inp,output,source_profiles_path=config,source_root=folder,
                                   corroborating_paths={'elb-bk':peer})

    def test_alignment_guard_is_loaded_automatically_and_hashed(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);inp,config,peer=self.fixture(folder)
            with gzip.open(folder/'alignment.jsonl.gz','wt') as stream:
                stream.write(json.dumps({'ref':'Matt.1.1','text':'sieht den Sohn.','inventory_mismatch':True})+'\n')
            result=validate_files(inp,folder/'out.xml',source_profiles_path=config,source_root=folder,
                                  corroborating_paths={'elb-bk':peer})
            self.assertEqual(result.summary['hints_removed'],0)
            self.assertEqual(result.audit[0]['reason'],'prior-verse-inventory-mismatch')
            self.assertTrue(json.loads((folder/'out.manifest.json').read_text())['alignment_sha256'])

    def test_alignment_must_match_complete_target_text(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'alignment.jsonl';path.write_text(json.dumps({'ref':'Matt.1.1','text':'different'})+'\n')
            with self.assertRaisesRegex(DataError,'Alignment text differs'):_load_alignment_guards(path,article_target())
            path.write_text('')
            with self.assertRaisesRegex(DataError,'every linguistic input verse'):_load_alignment_guards(path,article_target())

    def test_absolute_profile_path_is_normalized_out_of_public_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            inp,config,peer=self.fixture(folder)
            profiles=json.loads(config.read_text());profiles[0]['paths']=[str(Path(folder)/'greek.tsv')]
            config.write_text(json.dumps(profiles))
            _,meta=load_reference_occurrences(config,folder,'WH')
            self.assertEqual(meta['files'][0]['path'],'greek.tsv')
            self.assertNotIn(folder,json.dumps(meta))

    def test_reference_source_paths_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as folder:
            inp,config,peer=self.fixture(folder)
            profiles=json.loads(config.read_text());profiles[0]['paths']=['../elsewhere.tsv']
            config.write_text(json.dumps(profiles))
            with self.assertRaisesRegex(DataError,'escapes source root'):load_reference_occurrences(config,folder,'WH')


if __name__=='__main__':unittest.main()
