import contextlib
import copy
import csv
import gzip
import io
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import bible
from akribos.common import DataError,file_hash,write_json
from akribos.importers import parse_xml
from akribos.linguistic import PROVENANCE,rule_identity
from akribos.pipeline import build,publish
from akribos.project import cached,jsonl_gz,line
from akribos.xmlio import write_xml,plain
from scripts.verify_repository import verify_release_history


def tree(fragment,title='fixture'):
    return ET.fromstring('<XMLBIBLE><INFORMATION><title>'+title+'</title></INFORMATION>'
        '<BIBLEBOOK bnumber="40"><CHAPTER cnumber="1"><VERS vnumber="1">'+fragment+
        '</VERS></CHAPTER></BIBLEBOOK></XMLBIBLE>')


class LinguisticBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);(self.root/'config').mkdir()
        (self.root/'rules').mkdir()
        for path in ('rules/proper-name-catalog.json','rules/proper-name-sources.json'):
            (self.root/path).write_bytes((Path(__file__).resolve().parents[1]/path).read_bytes())
        self.bk=self.root/'private-bk.xml';self.csv=self.root/'private-csv.xml'
        for path,title in ((self.bk,'BK fixture'),(self.csv,'CSV fixture')):
            write_xml(path,tree('<gr str="991">sieht</gr> <gr str="3588">den</gr> <gr str="5207">Sohn</gr>.',title))
        self.edits={}
        for edition in ('elb','elb1905','lut','schlachter1951'):
            folder=self.root/'prepared'/edition;folder.mkdir(parents=True)
            fragment=('sieht den Sohn<NOTE type="x-studynote">Original <STYLE>Notiz</STYLE></NOTE>.'
                      if edition=='elb' else 'sieht den <gr str="5207">Sohn</gr>.')
            write_xml(folder/'01-language.xml',tree(fragment))
            write_json(folder/'manifest.json',{'settings':{'bible_id':'akribos.elb'}})
            self.edits[edition]=folder
        profile={'id':'tagnt','paths':['greek.tsv'],'options':{'profile':'tagnt','prefix':'G','edition':'WH',
          'columns':{'ref':0,'text':1,'gloss':2,'strong':11,'combined':3,'lemma':4,'editions':5,'variants':6,
                     'conjoined':10,'alternate':12}}}
        write_json(self.root/'config/step-profiles.json',[profile])
        rows=[]
        for n,code,morph,link in ((1,'G991','V-PAI-3S',''),(2,'G3588','T-ASM','#02»03:G5207'),(3,'G5207','N-ASM','')):
            row=['']*17;row[0]=f'Matt.1.1#{n:02}=NKO';row[1]='Greek';row[2]='gloss'
            row[3]=code+'='+morph;row[4]='lemma=gloss';row[5]='WH+TR';row[10]=link;row[11]=code;rows.append(row)
        with (self.root/'greek.tsv').open('w',newline='') as stream:csv.writer(stream,delimiter='\t').writerows(rows)

    @contextlib.contextmanager
    def pipeline(self):
        def edit(edition,*args,**kwargs):return self.edits[edition]
        def additions(tokens,*args,**kwargs):
            for token in tokens:
                if token['text']=='sieht':token.update(strong=['G991'],method='lexicon',uncertain=True,sources=['fixture'])
        with contextlib.ExitStack() as stack:
            for module in ('akribos.pipeline','akribos.project','scripts.verify_repository'):
                stack.enter_context(patch(module+'.ROOT',self.root))
            identity=rule_identity()
            implementation={'akribos/'+name:sha for name,sha in identity['implementation'].items()} | identity['data_files']
            stack.enter_context(patch('akribos.project.code_identity',return_value=implementation))
            stack.enter_context(patch('akribos.pipeline.check_sources'))
            stack.enter_context(patch('akribos.pipeline.edit',side_effect=edit))
            stack.enter_context(patch('akribos.pipeline.prepare_kjv',return_value=self.edits['elb1905']/'01-language.xml'))
            stack.enter_context(patch('akribos.pipeline.reference_inventory',return_value={'Matt.1.1':{'G991','G3588','G5207'}}))
            stack.enter_context(patch('akribos.pipeline.lexicons',return_value=({},{})))
            stack.enter_context(patch('akribos.pipeline.learn',return_value=({},{})))
            addition=stack.enter_context(patch('akribos.pipeline.additional_fill',side_effect=additions))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            yield addition

    def run_build(self,**kwargs):
        return build(edition='elb',version='1.4',elb_bk=self.bk,elb_csv=self.csv,**kwargs)

    def link(self):
        path=self.root/'releases/akribos.elb.xml'
        return path,json.loads(path.with_suffix('.build.json').read_text())

    def test_full_chain_new_13_anchor_cache_and_byte_identical_rebuild(self):
        input_bytes={path:path.read_bytes() for path in (self.bk,self.csv,self.root/'greek.tsv')}
        with self.pipeline() as addition:
            destination=self.run_build();release,link=self.link()
            fourth=parse_xml(destination/'04-multisource.xml');fifth=parse_xml(destination/'05-reference-confirmed.xml')
            sixth=parse_xml(release)
            self.assertEqual(len(fourth.findall('.//NOTE')),2)
            self.assertEqual(len(fifth.findall('.//NOTE')),1)
            self.assertIsNone(fifth.find('.//gr[@str="3588"]'))
            self.assertIsNotNone(sixth.find('.//gr[@str="3588"]'))
            # The left anchor was uncertain before 05 and becomes usable only after 05.
            self.assertIsNone(fifth.find('.//gr[@str="991"]').get(PROVENANCE))
            self.assertEqual(sixth.find('.//gr[@str="3588"]').get(PROVENANCE),'1.4.0')
            self.assertEqual(sixth.find('.//NOTE/STYLE').text,'Notiz')
            self.assertEqual(plain(fourth.find('.//VERS')),plain(sixth.find('.//VERS')))
            self.assertEqual(sixth.get('revision'),'1.4')
            self.assertEqual(sixth.findtext('INFORMATION/selection_subtitle'),'mit Strongs (Akribos 1.4)')
            self.assertTrue(sixth.findtext('INFORMATION/rights').startswith('Version 1.4.'))
            self.assertEqual(link['artifact'],'06-linguistic.xml')
            self.assertEqual(verify_release_history(release,link,'1.4'),'06-linguistic.xml')
            manifest=json.loads((destination/'manifest.json').read_text())
            settings=manifest['settings']['linguistic_validation']
            self.assertTrue(settings['article_corroboration_required'])
            self.assertTrue(settings['prior_alignment_required'])
            self.assertIn('sha256',settings['rule_identity'])
            self.assertNotIn(str(self.root),json.dumps(manifest))
            original={p.name:p.read_bytes() for p in destination.iterdir()};calls=addition.call_count
            self.assertEqual(self.run_build(),destination)
            self.assertEqual(addition.call_count,calls)
            self.assertEqual(self.run_build(rebuild=True),destination)
            self.assertGreater(addition.call_count,calls)
            self.assertEqual(original,{p.name:p.read_bytes() for p in destination.iterdir()})
        self.assertEqual(input_bytes,{p:p.read_bytes() for p in input_bytes})

    def test_reference_or_step_hash_change_creates_new_immutable_run(self):
        with self.pipeline():
            original_run=self.run_build();original={p.name:p.read_bytes() for p in original_run.iterdir()}
            self.csv.write_text(self.csv.read_text().replace('CSV fixture','CSV updated fixture'))
            reference_run=self.run_build()
            self.assertNotEqual(original_run,reference_run)
            step=self.root/'greek.tsv';step.write_text(step.read_text().replace('gloss','new gloss'))
            source_run=self.run_build()
            self.assertNotEqual(reference_run,source_run)
            self.assertEqual(original,{p.name:p.read_bytes() for p in original_run.iterdir()})

    def test_missing_private_sources_fail_before_any_build_mutation(self):
        for kwargs in ({},{'elb_bk':self.bk},{'elb_bk':self.bk,'elb_csv':self.bk}):
            with self.subTest(kwargs=kwargs),patch('akribos.pipeline.edit') as editor,patch('akribos.pipeline.check_sources') as checker:
                with self.assertRaises(DataError):build(version='1.4',**kwargs)
                editor.assert_not_called();checker.assert_not_called()
        self.assertFalse((self.root/'history').exists())
        self.assertFalse((self.root/'releases').exists())

    def test_publish_rejects_wrong_phase_for_14_and_wrong_version_for_06(self):
        with patch('akribos.pipeline.ROOT',self.root):
            for version,artifact in (('1.4','04-multisource.xml'),('1.4','05-reference-confirmed.xml'),
                                     ('1.3','06-linguistic.xml'),('1.2','06-linguistic.xml')):
                with self.assertRaises(DataError):publish(self.edits['elb'],'akribos.elb',version,artifact=artifact)
        self.assertFalse((self.root/'releases').exists())

    def test_cli_14_requires_both_sources_before_snapshot(self):
        with patch.object(sys,'argv',['bible.py','build','--version','1.4','--elb-bk',str(self.bk)]),\
             patch('scripts.snapshots.snapshot_current') as snapshot,patch('akribos.pipeline.build') as builder,\
             contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):bible.main()
            snapshot.assert_not_called();builder.assert_not_called()

    def test_cli_14_forwards_refs_and_has_no_corroboration_bypass(self):
        with patch.object(sys,'argv',['bible.py','build','--edition','elb','--version','1.4',
                                     '--elb-bk',str(self.bk),'--elb-csv',str(self.csv),'--rebuild']),\
             patch('scripts.snapshots.snapshot_current'),patch('akribos.pipeline.build') as builder,\
             patch('akribos.project.export_kjv'),contextlib.redirect_stdout(io.StringIO()):
            bible.main()
            self.assertEqual(builder.call_args.kwargs['version'],'1.4')
            self.assertNotIn('require_article_corroboration',builder.call_args.kwargs)
            self.assertTrue(builder.call_args.kwargs['rebuild'])
        with patch.object(sys,'argv',['bible.py','build','--version','1.4','--no-article-corroboration']),\
             contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):bible.main()

    def test_verifier_rejects_corroboration_or_alignment_guard_disabled(self):
        with self.pipeline():
            destination=self.run_build();release,link=self.link()
            path=destination/'manifest.json';original=path.read_bytes()
            for key in ('article_corroboration_required','prior_alignment_required'):
                manifest=json.loads(original);manifest['settings']['linguistic_validation'][key]=False
                write_json(path,manifest)
                with self.assertRaises(DataError):verify_release_history(release,link,'1.4')
            path.write_bytes(original)

    def test_verifier_rejects_unlogged_strong_changes_even_if_file_hashes_are_updated(self):
        with self.pipeline():
            destination=self.run_build();release,link=self.link()
            stage=destination/'06-linguistic.xml';root=parse_xml(stage)
            root.find('.//gr[@str="5207"]').set('str','3962')
            write_xml(stage,root);release.write_bytes(stage.read_bytes());link['sha256']=file_hash(stage)
            report_path=destination/'06-linguistic.report.json';report=json.loads(report_path.read_text())
            report['output_sha256']=file_hash(stage);write_json(report_path,report)
            manifest_path=destination/'06-linguistic.manifest.json';phase=json.loads(manifest_path.read_text())
            phase['outputs']['xml']=file_hash(stage);phase['outputs']['report']=file_hash(report_path);write_json(manifest_path,phase)
            with self.assertRaisesRegex(DataError,'outside the approved linguistic deltas'):
                verify_release_history(release,link,'1.4')

    def test_verifier_rejects_private_audit_payload_even_with_recomputed_hashes(self):
        with self.pipeline():
            destination=self.run_build();release,link=self.link()
            audit_path=destination/'06-linguistic.audit.jsonl.gz'
            with gzip.open(audit_path,'rt',encoding='utf-8') as stream:
                original_rows=[json.loads(value) for value in stream]
            for mutate in [
                lambda row:row.update(private_path='/tmp/private-csv-reference.xml'),
                lambda row:row.update(private_reference_text='PRIVATE REFERENCE CONTENT'),
                lambda row:row['references'].update({'elb-csv':'PRIVATE REFERENCE CONTENT'}),
                lambda row:row['proof'].update(private_reference_text='PRIVATE REFERENCE CONTENT'),
            ]:
                rows=copy.deepcopy(original_rows);mutate(rows[0])
                with jsonl_gz(audit_path) as stream:
                    for row in rows:line(stream,row)
                report_path=destination/'06-linguistic.report.json';report=json.loads(report_path.read_text())
                report['audit_sha256']=file_hash(audit_path);write_json(report_path,report)
                phase_path=destination/'06-linguistic.manifest.json';phase=json.loads(phase_path.read_text())
                phase['outputs']['audit']=file_hash(audit_path)
                phase['outputs']['report']=file_hash(report_path);write_json(phase_path,phase)
                manifest_path=destination/'manifest.json';manifest=json.loads(manifest_path.read_text())
                manifest['files']={str(path.relative_to(destination)):file_hash(path)
                                  for path in destination.rglob('*') if path.is_file() and path!=manifest_path}
                write_json(manifest_path,manifest)
                self.assertTrue(cached(destination))
                with self.assertRaisesRegex(DataError,'public .* (audit fields|reference status|proof fields)'):
                    verify_release_history(release,link,'1.4')

    def test_verifier_requires_the_archived_proper_name_catalog(self):
        with self.pipeline():
            destination=self.run_build();release,link=self.link()
            catalog=self.root/'rules/proper-name-catalog.json'
            original=catalog.read_bytes();catalog.write_bytes(original+b'\n')
            with self.assertRaisesRegex(DataError,'Proper-name catalog differs'):
                verify_release_history(release,link,'1.4')


if __name__=='__main__':unittest.main()
