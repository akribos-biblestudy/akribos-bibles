import contextlib
import copy
import gzip
import io
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

import bible
from akribos.common import DataError,file_hash,write_json
from akribos.confirm import prepare_confirmation
from akribos.importers import parse_xml
from akribos.pipeline import build,publish
from akribos.xmlio import plain,strong_fingerprints,write_xml
from scripts.verify_repository import verify_release_history


def tree(fragment,title='fixture'):
    return ET.fromstring('<XMLBIBLE><INFORMATION><title>'+title+'</title></INFORMATION>'
                         '<BIBLEBOOK bnumber="1"><CHAPTER cnumber="1"><VERS vnumber="1">'
                         +fragment+'</VERS></CHAPTER></BIBLEBOOK></XMLBIBLE>')


class ConfirmationBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.bk=self.root/'private-bk.xml';self.csv=self.root/'private-csv.xml'
        for path,title in ((self.bk,'BK fixture'),(self.csv,'CSV fixture')):
            write_xml(path,tree('<gr str="430">Gott</gr> <gr str="1254">schuf</gr>.',title))
        self.edits={}
        for edition in ('elb','elb1905','lut','schlachter1951'):
            folder=self.root/'prepared'/edition;folder.mkdir(parents=True)
            fragment=('Gott<NOTE type="x-studynote">Original <STYLE>Notiz</STYLE></NOTE> schuf.' if edition=='elb'
                      else '<gr str="430">Gott</gr> schuf.')
            write_xml(folder/'01-language.xml',tree(fragment))
            write_json(folder/'manifest.json',{'settings':{'bible_id':'akribos.elb'}})
            self.edits[edition]=folder

    @contextlib.contextmanager
    def pipeline(self):
        def edit(edition,*args,**kwargs):return self.edits[edition]
        def additions(tokens,*args,**kwargs):
            for token in tokens:
                if token['text']=='schuf':
                    token.update(strong=['H1254'],method='lexicon',uncertain=True,sources=['fixture'])
        with contextlib.ExitStack() as stack:
            for module in ('akribos.pipeline','akribos.project','scripts.verify_repository'):
                stack.enter_context(patch(module+'.ROOT',self.root))
            stack.enter_context(patch('akribos.project.code_identity',return_value={'fixture':'synthetic-implementation'}))
            stack.enter_context(patch('akribos.pipeline.check_sources'))
            stack.enter_context(patch('akribos.pipeline.edit',side_effect=edit))
            stack.enter_context(patch('akribos.pipeline.prepare_kjv',return_value=self.edits['elb1905']/'01-language.xml'))
            stack.enter_context(patch('akribos.pipeline.reference_inventory',return_value={'Gen.1.1':{'H430','H1254'}}))
            stack.enter_context(patch('akribos.pipeline.lexicons',return_value=({},{})))
            stack.enter_context(patch('akribos.pipeline.learn',return_value=({},{})))
            addition=stack.enter_context(patch('akribos.pipeline.additional_fill',side_effect=additions))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            yield addition

    def run_build(self,**kwargs):
        return build(edition='elb',version='1.3',elb_bk=self.bk,elb_csv=self.csv,**kwargs)

    def test_complete_build_stage_cache_and_byte_identical_rebuild(self):
        with self.pipeline() as addition:
            destination=self.run_build()
            release=self.root/'releases/akribos.elb.xml'
            before=parse_xml(destination/'04-multisource.xml');after=parse_xml(release)
            self.assertEqual(after.get('revision'),'1.3')
            self.assertEqual(plain(before.find('.//VERS')),plain(after.find('.//VERS')))
            self.assertEqual(strong_fingerprints(before),strong_fingerprints(after))
            self.assertEqual(len(before.findall('.//NOTE')),2)
            self.assertEqual(len(after.findall('.//NOTE')),1)
            self.assertEqual(after.find('.//NOTE/STYLE').text,'Notiz')
            manifest=json.loads((destination/'manifest.json').read_text())
            reference_settings=manifest['settings']['reference_confirmation']
            self.assertNotIn(str(self.root),json.dumps(reference_settings))
            self.assertEqual(reference_settings['reference_sha256'],{'elb-bk':file_hash(self.bk),'elb-csv':file_hash(self.csv)})
            link=json.loads(release.with_suffix('.build.json').read_text())
            self.assertEqual(link['artifact'],'05-reference-confirmed.xml')
            self.assertEqual(verify_release_history(release,link,'1.3'),'05-reference-confirmed.xml')
            with gzip.open(destination/'05-reference-confirmed.audit.jsonl.gz','rt') as stream:
                audit=[json.loads(line) for line in stream]
            self.assertEqual(len(audit),1)
            self.assertEqual(audit[0]['status'],'confirmed')
            original={p.name:p.read_bytes() for p in destination.iterdir()}
            calls=addition.call_count
            self.assertEqual(self.run_build(),destination)
            self.assertEqual(addition.call_count,calls)
            self.assertEqual(self.run_build(rebuild=True),destination)
            self.assertGreater(addition.call_count,calls)
            self.assertEqual(original,{p.name:p.read_bytes() for p in destination.iterdir()})

    def test_reference_hash_change_creates_new_run_and_preserves_old(self):
        with self.pipeline():
            first=self.run_build()
            original={p.name:p.read_bytes() for p in first.iterdir()}
            reference=parse_xml(self.csv)
            reference.find('INFORMATION/title').text='CSV second fixture'
            write_xml(self.csv,reference)
            second=self.run_build()
            self.assertNotEqual(first,second)
            self.assertEqual(original,{p.name:p.read_bytes() for p in first.iterdir()})

    def test_version_12_keeps_stage04_and_legacy_link(self):
        with self.pipeline():
            destination=build(edition='elb',version='1.2')
            release=self.root/'releases/akribos.elb.xml'
            link=json.loads(release.with_suffix('.build.json').read_text())
            self.assertNotIn('artifact',link)
            self.assertFalse((destination/'05-reference-confirmed.xml').exists())
            self.assertNotIn('reference_confirmation',json.loads((destination/'manifest.json').read_text())['settings'])
            self.assertEqual(file_hash(release),file_hash(destination/'04-multisource.xml'))
            self.assertEqual(verify_release_history(release,link,'1.2'),'04-multisource.xml')

    def test_invalid_reference_inputs_fail_before_build_mutation(self):
        cases=({}, {'elb_bk':self.bk}, {'elb_bk':self.bk,'elb_csv':self.bk},
               {'elb_bk':self.bk,'elb_csv':self.root/'absent.xml'})
        for arguments in cases:
            with self.subTest(arguments=arguments),patch('akribos.pipeline.edit') as edit,patch('akribos.pipeline.check_sources') as check:
                with self.assertRaises((DataError,FileNotFoundError)):
                    build(version='1.3',**arguments)
                edit.assert_not_called();check.assert_not_called()
        self.assertFalse((self.root/'history').exists())
        self.assertFalse((self.root/'releases').exists())

    def test_publish_cannot_label_unconfirmed_stage_as_13(self):
        with patch('akribos.pipeline.ROOT',self.root):
            for artifact in ('04-multisource.xml','../04-multisource.xml'):
                with self.assertRaises(DataError):publish(self.edits['elb'],'akribos.elb','1.3',artifact=artifact)
        self.assertFalse((self.root/'releases').exists())

    def test_verifier_rejects_missing_stage_and_duplicate_source_hashes(self):
        with self.pipeline():
            destination=self.run_build()
            release=self.root/'releases/akribos.elb.xml'
            link=json.loads(release.with_suffix('.build.json').read_text())
            invalid=dict(link);invalid.pop('artifact')
            with self.assertRaises(DataError):verify_release_history(release,invalid,'1.3')
            manifest=json.loads((destination/'manifest.json').read_text())
            hashes=manifest['settings']['reference_confirmation']['reference_sha256']
            hashes['elb-csv']=hashes['elb-bk']
            write_json(destination/'manifest.json',manifest)
            with self.assertRaisesRegex(DataError,'identical references'):
                verify_release_history(release,link,'1.3')

    def test_prepare_rejects_duplicate_verses_and_wrong_profile(self):
        invalid=parse_xml(self.csv);chapter=invalid.find('.//CHAPTER');chapter.append(copy.deepcopy(chapter[0]))
        write_xml(self.csv,invalid)
        with self.assertRaisesRegex(DataError,'Duplicate verse'):prepare_confirmation('1.3',self.bk,self.csv)
        self.csv.write_text('<HTML>no Bible</HTML>')
        with self.assertRaisesRegex(DataError,'Zefania'):prepare_confirmation('1.3',self.bk,self.csv)
        self.csv.write_text('<XMLBIBLE><INFORMATION/></XMLBIBLE>')
        with self.assertRaisesRegex(DataError,'No Bible verses'):prepare_confirmation('1.3',self.bk,self.csv)

    def test_cli_rejects_missing_source_before_snapshot_or_build(self):
        with patch.object(sys,'argv',['bible.py','build','--version','1.3','--elb-bk',str(self.bk)]),\
                patch('scripts.snapshots.snapshot_current') as snapshot,patch('akribos.pipeline.build') as builder,\
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as failure:bible.main()
            self.assertEqual(failure.exception.code,2)
            snapshot.assert_not_called();builder.assert_not_called()

    def test_cli_validates_xml_before_snapshot(self):
        self.csv.write_text('<XMLBIBLE>broken')
        with patch.object(sys,'argv',['bible.py','build','--version','1.3','--elb-bk',str(self.bk),'--elb-csv',str(self.csv)]),\
                patch('scripts.snapshots.snapshot_current') as snapshot,patch('akribos.pipeline.build') as builder,\
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as failure:bible.main()
            self.assertEqual(failure.exception.code,2)
            snapshot.assert_not_called();builder.assert_not_called()

    def test_cli_forwards_two_references_only_after_validation(self):
        with patch.object(sys,'argv',['bible.py','build','--edition','elb','--version','1.3',
                                      '--elb-bk',str(self.bk),'--elb-csv',str(self.csv),'--rebuild']),\
                patch('scripts.snapshots.snapshot_current') as snapshot,patch('akribos.pipeline.build') as builder,\
                patch('akribos.project.export_kjv'),contextlib.redirect_stdout(io.StringIO()):
            bible.main()
            snapshot.assert_called_once()
            builder.assert_called_once()
            self.assertEqual(builder.call_args.kwargs['elb_bk'],self.bk)
            self.assertEqual(builder.call_args.kwargs['elb_csv'],self.csv)
            self.assertTrue(builder.call_args.kwargs['rebuild'])

    def test_reference_options_cannot_change_version12_or_claim_version14(self):
        with self.assertRaises(DataError):prepare_confirmation('1.2',self.bk,self.csv)
        with self.assertRaisesRegex(DataError,'separate language-validation stage'):
            prepare_confirmation('1.4',self.bk,self.csv)


if __name__=='__main__':unittest.main()
