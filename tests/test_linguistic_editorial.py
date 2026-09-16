"""Fixed public 1.2 excerpts: tests remain stable when release files advance."""
import copy
import contextlib
import gzip
import io
import json
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

from akribos import linguistic_editorial as editorial
from akribos.common import DataError, canonical_ref, digest, file_hash
from akribos.confirm import HINT, _Verse, _preserved_notes, _remove_preserving_tail
from akribos.importers import parse_xml
from akribos.linguistic import (RULES_VERSION, load_reference_occurrences, validate_tree,
                               validate_files, verify_transition, _span_signature)
from akribos.xmlio import plain, zef_verses

ROOT = Path(__file__).resolve().parents[1]


class EditorialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = editorial.load_catalog()
        cls.roots = {bid:parse_xml(ROOT/'tests/fixtures'/f'{bid}.editorial-input-1.2.xml')
                     for bid in ('akribos.elb','akribos.lut')}
        cls.metadata = {'files':[{'path':path,'sha256':sha}
                                for path,sha in cls.catalog['source_files'].items()]}

    def input(self, bid='akribos.elb'):
        return copy.deepcopy(self.roots[bid]), {r['ref']:copy.deepcopy(r['source_projection'])
            for r in self.catalog['rules'] if r['bible_id']==bid}

    def validate(self, root, source, nt='WH', metadata=None):
        return validate_tree(root,source,nt_edition=nt,
                             source_metadata=self.metadata if metadata is None else metadata)

    def replay(self, root, result, source, nt='WH', metadata=None):
        return verify_transition(root,result.root,result.audit,source,nt_edition=nt,
                                 source_metadata=self.metadata if metadata is None else metadata)

    def test_all_reviewed_edits_and_only_these_change(self):
        counts=[]
        for bid,nt in [('akribos.elb','WH'),('akribos.lut','TR')]:
            root,source=self.input(bid);before=ET.tostring(root)
            result=self.validate(root,source,nt);counts.append(result.summary)
            self.assertEqual(before,ET.tostring(root),'Caller input was mutated')
            self.assertEqual({r:plain(v) for r,v in zef_verses(root)},
                             {r:plain(v) for r,v in zef_verses(result.root)})
            self.assertEqual(_preserved_notes(root),_preserved_notes(result.root))
            expected={(r['ref'],r['token']):r for r in self.catalog['rules'] if r['bible_id']==bid}
            old={r:_Verse(v,r) for r,v in zef_verses(root)}
            new={r:_Verse(v,r) for r,v in zef_verses(result.root)}
            for ref,view in old.items():
                for span in view.spans:
                    changed=next((r for (rr,_),r in expected.items() if rr==ref and
                                  (r['target_start'],r['target_end'])==(span.start,span.end)),None)
                    same=[s for s in new[ref].spans if (s.start,s.end)==(span.start,span.end)]
                    if changed and not changed['after_strong']:
                        self.assertEqual(same,[])
                    elif changed:
                        self.assertEqual(list(same[0].codes),changed['after_strong'])
                        clone=copy.deepcopy(same[0].element)
                        clone.set('str',span.element.get('str'))
                        clone.attrib.pop('data-akribos-linguistic')
                        clone.attrib.pop(editorial.PROVENANCE)
                        self.assertEqual(_span_signature(span.element),_span_signature(clone))
                    else:
                        self.assertEqual(len(same),1)
                        self.assertEqual(_span_signature(span.element),_span_signature(same[0].element))
            replay=self.replay(root,result,source,nt)
            for key,value in replay.items():self.assertEqual(result.summary[key],value)
            self.assertEqual(result.summary['article_tags_added'],0)
            self.assertTrue(result.summary['unlisted_strong_values_preserved'])
            self.assertFalse(result.summary['existing_strong_values_preserved'])
        self.assertEqual(sum(x['editorial_corrections'] for x in counts),41)
        self.assertEqual(sum(x['editorial_corrections_marked'] for x in counts),24)
        self.assertEqual(sum(x['editorial_corrections_inherited'] for x in counts),17)
        self.assertEqual(sum(x['editorial_hints_removed'] for x in counts),24)

    def test_idempotent_and_no_post_correction_bootstrap(self):
        for bid,nt in [('akribos.elb','WH'),('akribos.lut','TR')]:
            root,source=self.input(bid);first=self.validate(root,source,nt)
            second=self.validate(first.root,source,nt)
            self.assertEqual(ET.tostring(first.root),ET.tostring(second.root))
            self.assertEqual(second.summary['editorial_corrections'],0)
            self.assertEqual(second.summary['hints_removed'],0)
            self.assertFalse(any(r['kind']=='article-addition' for r in second.audit))
            self.replay(first.root,second,source,nt)

    def test_hint_removed_in_prior_reference_phase_still_allows_exact_correction(self):
        root,source=self.input()
        for ref,verse in zef_verses(root):
            view=_Verse(verse,ref)
            for hint in view.hints:_remove_preserving_tail(view.parents[hint],hint)
        result=self.validate(root,source)
        self.assertEqual(result.summary['editorial_corrections'],18)
        self.assertEqual(result.summary['editorial_hints_removed'],0)
        self.assertEqual(result.summary['hints_removed'],0)
        self.replay(root,result,source)

    def test_wrong_target_edition_and_source_identity_never_change_codes(self):
        for nt,metadata,reason in [('TR',self.metadata,'wrong-target-edition'),
             ('WH',{},'source-file-identity-mismatch'),
             ('WH',{'files':[dict(row,sha256='0'*64) for row in self.metadata['files']]},'source-file-identity-mismatch')]:
            root,source=self.input();result=self.validate(root,source,nt,metadata)
            self.assertEqual(ET.tostring(root),ET.tostring(result.root))
            self.assertTrue(all(r['reason']==reason for r in result.audit if r['kind']=='editorial-correction'))
            self.replay(root,result,source,nt,metadata)

    def test_exact_target_token_span_text_and_codes_are_required(self):
        def target(root):
            verse=dict(zef_verses(root))['Matt.22.44'];view=_Verse(verse,'Matt.22.44')
            return next(s.element for s in view.spans if s.start==17)
        for mutate,reason in [
            (lambda root:target(root).set('str','4314'),'target-strong-set-mismatch'),
            (lambda root:target(root).set('custom','new'),'target-span-hash-mismatch'),
            (lambda root:setattr(target(root),'text','bei'),'target-text-hash-mismatch'),
            (lambda root:target(root).set('str','1537 4314'),'target-strong-set-mismatch')]:
            root,source=self.input();mutate(root);before=_span_signature(target(root))
            result=self.validate(root,source)
            row=next(r for r in result.audit if r.get('rule_id')=='akribos.elb:Matt.22.44:d004')
            self.assertEqual(row['reason'],reason);self.assertEqual(row['status'],'not-applicable')
            self.assertEqual(before,_span_signature(target(result.root)))
            self.replay(root,result,source)
        root,source=self.input();view=_Verse(dict(zef_verses(root))['Matt.22.44'],'Matt.22.44')
        rule=next(r for r in self.catalog['rules'] if r['id']=='akribos.elb:Matt.22.44:d004')
        for key,value in [('token','d005'),('target_start',18),('target_word','bei')]:
            changed=dict(rule);changed[key]=value
            row,_,_=editorial.decide(changed,view,source[rule['ref']],nt_edition='WH',
                source_metadata=self.metadata,source_files=self.catalog['source_files'],hint_ids={},rule_version=RULES_VERSION)
            self.assertEqual(row['reason'],'target-token-mismatch')

    def test_actual_selected_source_projection_is_required(self):
        root,source=self.input();source['Matt.22.44'][0]['lemma']='different'
        result=self.validate(root,source)
        row=next(r for r in result.audit if r.get('rule_id')=='akribos.elb:Matt.22.44:d004')
        self.assertEqual(row['reason'],'source-projection-mismatch')
        self.assertEqual(row['before_strong'],row['after_strong'])
        self.replay(root,result,source)

    def test_missing_verse_is_explicitly_not_applicable(self):
        root,source=self.input();root.remove(root.find('BIBLEBOOK'))
        result=self.validate(root,source)
        self.assertTrue(any(r['reason']=='missing-target-verse' for r in result.audit))
        self.replay(root,result,source)

    def test_unlisted_bible_identifier_has_no_editorial_rules(self):
        root,source=self.input();root.find('INFORMATION/identifier').text='other.bible'
        result=self.validate(root,source)
        self.assertFalse(any(r['kind']=='editorial-correction' for r in result.audit))

    def test_excluded_ambiguous_cases_stay_outside_catalog(self):
        ids={r['id'] for r in self.catalog['rules']}
        self.assertNotIn('akribos.elb:Acts.1.2:d003',ids)
        self.assertNotIn('akribos.elb:Acts.25.10:d019',ids)
        root,source=self.input('akribos.lut');result=self.validate(root,source,'TR')
        before=_Verse(dict(zef_verses(root))['John.1.29'],'John.1.29')
        after=_Verse(dict(zef_verses(result.root))['John.1.29'],'John.1.29')
        das=next(t for t in before.tokens if t['text']=='das')
        self.assertTrue(any(s.start==das['start'] and s.codes==('G3588',) for s in after.spans))

    def test_composite_reed_span_keeps_its_correct_noun_code(self):
        root,source=self.input('akribos.lut');result=self.validate(root,source,'TR')
        row=next(r for r in result.audit if r.get('rule_id')=='akribos.lut:Rev.21.16:d022')
        self.assertEqual(row['before_strong'],['G1909','G2563'])
        self.assertEqual(row['after_strong'],['G2563'])
        view=_Verse(dict(zef_verses(result.root))['Rev.21.16'],'Rev.21.16')
        token=next(t for t in view.tokens if t['id']=='d022')
        span=next(s for s in view.spans if s.start==token['start'])
        self.assertEqual(token['text'],'Rohr');self.assertEqual(span.codes,('G2563',))
        self.replay(root,result,source,'TR')

    def test_hebrew_edits_preserve_the_actual_number_and_relative_phrase(self):
        for bid,nt in [('akribos.elb','WH'),('akribos.lut','TR')]:
            root,source=self.input(bid);result=self.validate(root,source,nt)
            for ref,code in [('Gen.19.21','H834'),('Exod.33.5','H259')]:
                before=_Verse(dict(zef_verses(root))[ref],ref)
                after=_Verse(dict(zef_verses(result.root))[ref],ref)
                before_count=sum(code in s.codes for s in before.spans)
                self.assertGreaterEqual(before_count,1)
                kept=[s for s in after.spans if code in s.codes]
                self.assertEqual(len(kept),before_count-1)
                row=next(r for r in result.audit if r['kind']=='editorial-correction' and r['ref']==ref)
                self.assertTrue(all(s.start>row['target_end'] for s in kept))
                self.assertEqual(set(row['proof']['source_file_hashes']),editorial.OT_FILES)
                self.assertEqual(row['after_strong'],[])
            self.replay(root,result,source,nt)

    def test_hebrew_correction_requires_actual_tahot_identity_and_witness(self):
        root,source=self.input()
        only_ot={'files':[r for r in self.metadata['files'] if r['path'] in editorial.OT_FILES]}
        result=self.validate(root,source,metadata=only_ot)
        self.assertEqual(result.summary['editorial_corrections'],2)
        self.replay(root,result,source,metadata=only_ot)
        no_ot={'files':[r for r in self.metadata['files'] if r['path'] in editorial.NT_FILES]}
        result=self.validate(root,source,metadata=no_ot)
        self.assertEqual(result.summary['editorial_corrections'],16)
        for change in ({'edition':'other'}, {'origin_id':'Gen.19.21#01=Q'}):
            changed=copy.deepcopy(source);changed['Gen.19.21'][0].update(change)
            result=self.validate(root,changed)
            row=next(r for r in result.audit if r.get('rule_id')=='akribos.elb:Gen.19.21:d015')
            self.assertEqual(row['reason'],'source-projection-mismatch')
            self.assertEqual(row['before_strong'],row['after_strong'])
            self.replay(root,result,changed)

    def test_phase_cli_reports_editorial_changes_separately(self):
        from scripts.validate_linguistic import main
        root,source=self.input('akribos.lut');result=self.validate(root,source,'TR')
        stream=io.StringIO()
        with patch('scripts.validate_linguistic.validate_files',return_value=result),contextlib.redirect_stdout(stream):
            self.assertEqual(main(['input.xml','--nt-edition','TR','--elb-bk','private.xml']),0)
        report=json.loads(stream.getvalue())
        self.assertEqual(report['editorial_corrections'],23)
        self.assertEqual(report['editorial_corrections_marked'],9)
        self.assertEqual(report['editorial_corrections_inherited'],14)
        self.assertEqual(report['editorial_hints_removed'],9)

    def test_real_file_phase_hashes_metadata_and_rebuild_are_reproducible(self):
        # Real pinned files exercise source selection and the identity gate.
        profiles_data=[dict(p,paths=[path for path in p['paths'] if path in self.catalog['source_files']])
                       for p in json.loads((ROOT/'config/step-profiles.json').read_text())]
        input_path=ROOT/'tests/fixtures/akribos.elb.editorial-input-1.2.xml'
        input_hash=file_hash(input_path)
        with tempfile.TemporaryDirectory() as directory:
            temp=Path(directory);profiles=temp/'profiles.json';profiles.write_text(json.dumps(profiles_data))
            output=temp/'06-linguistic.xml'
            result=validate_files(input_path,output,source_profiles_path=profiles,source_root=ROOT,
                                  output_identity=('akribos.elb','1.4'))
            self.assertEqual(result.summary['editorial_corrections'],18)
            self.assertEqual(parse_xml(output).get('revision'),'1.4')
            self.assertEqual(result.summary['article_tags_added'],0)
            phase=json.loads(output.with_suffix('.manifest.json').read_text())
            report=json.loads(output.with_suffix('.report.json').read_text())
            self.assertEqual(phase['outputs']['xml'],file_hash(output))
            self.assertEqual(report['output_sha256'],file_hash(output))
            self.assertIn('rules/editorial-strong-corrections.json',phase['rule_identity']['data_files'])
            snapshot={p.name:p.read_bytes() for p in temp.iterdir()}
            validate_files(input_path,output,source_profiles_path=profiles,source_root=ROOT,
                           output_identity=('akribos.elb','1.4'))
            self.assertEqual(snapshot,{p.name:p.read_bytes() for p in temp.iterdir()})
            source,metadata=load_reference_occurrences(profiles,ROOT,'WH')
            with gzip.open(output.with_suffix('.audit.jsonl.gz'),'rt',encoding='utf-8') as stream:
                audit=[json.loads(line) for line in stream]
            verify_transition(parse_xml(input_path),parse_xml(output),audit,source,
                              source_metadata=metadata,output_identity=('akribos.elb','1.4'))
        self.assertEqual(file_hash(input_path),input_hash)

    def test_audit_replay_rejects_changed_target_proof_or_private_fields(self):
        root,source=self.input();result=self.validate(root,source)
        mutations=[lambda row:row.update(after_strong=['G991']),lambda row:row.update(before_strong=['G991']),
            lambda row:row.update(annotation_origin='inherited'),lambda row:row.update(hint_id=None),
            lambda row:row.update(target_text='private peer text'),lambda row:row.update(private_path='/secret'),
            lambda row:row['proof'].update(source_projection_sha256='0'*64),
            lambda row:row['proof'].update(rule_sha256='0'*64),
            lambda row:row['proof'].update(private_reference_text='secret'),
            lambda row:row.update(action={}),lambda row:row.update(rule_id=[])]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                tampered=copy.deepcopy(result);row=next(r for r in tampered.audit if r['kind']=='editorial-correction' and r['hint_id'] is not None)
                mutate(row)
                # There are no trusted audit/output hashes in this replay: an
                # attacker recomputing all outer checksums still faces the proof.
                with self.assertRaises(DataError):self.replay(root,tampered,source)
        tampered=copy.deepcopy(result);tampered.audit=[r for r in tampered.audit if r['kind']!='editorial-correction']
        with self.assertRaises(DataError):self.replay(root,tampered,source)
        tampered=copy.deepcopy(result);tampered.audit.append(next(r for r in tampered.audit if r['kind']=='editorial-correction'))
        with self.assertRaises(DataError):self.replay(root,tampered,source)

    def test_unwrap_preserves_mixed_content_and_note_tails(self):
        root=ET.fromstring('<VERS>before <gr str="1537">z<STYLE>u</STYLE></gr><NOTE ex="x">hint</NOTE> after</VERS>')
        grammar=root[0];hint=root[1]
        editorial.apply({'status':'applied','action':'unwrap-strong-span'},grammar,hint,
                        {grammar:root,hint:root},RULES_VERSION)
        self.assertEqual(ET.tostring(root,encoding='unicode'),'<VERS>before z<STYLE>u</STYLE> after</VERS>')

    def test_catalog_projection_matches_pinned_original_step_rows(self):
        profiles_data=[dict(p,paths=[path for path in p['paths'] if path in self.catalog['source_files']])
                       for p in json.loads((ROOT/'config/step-profiles.json').read_text())]
        wanted={r['ref'] for r in self.catalog['rules']}
        with tempfile.TemporaryDirectory() as directory:
            temporary=Path(directory)
            for relative,sha in self.catalog['source_files'].items():
                self.assertEqual(file_hash(ROOT/relative),sha)
                target=temporary/relative;target.parent.mkdir(parents=True,exist_ok=True)
                with (ROOT/relative).open(encoding='utf-8-sig') as stream,target.open('w',encoding='utf-8') as out:
                    for line in stream:
                        first=line.split('\t',1)[0]
                        if re.match(r'^[1-3]?[A-Za-z]+\.\d+\.\d+#',first) and canonical_ref(first.split('#')[0]) in wanted:out.write(line)
            profiles=temporary/'profiles.json';profiles.write_text(json.dumps(profiles_data))
            for nt in ('WH','TR'):
                source,_=load_reference_occurrences(profiles,temporary,nt)
                for rule in self.catalog['rules']:
                    if rule['nt_edition']!=nt:continue
                    projection=[{k:t.get(k) for k in editorial.SOURCE_FIELDS} for t in source[rule['ref']]]
                    self.assertEqual(projection,rule['source_projection'])
                    self.assertEqual(digest(projection),rule['binding']['source_projection_sha256'])
