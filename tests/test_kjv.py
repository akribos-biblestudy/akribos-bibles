import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from akribos.common import file_hash
from akribos.project import export_kjv


class KjvExportTests(unittest.TestCase):
    def test_repair_export_preserves_source_words_strongs_notes_and_metadata(self):
        raw='''<XMLBIBLE revision="201909"><INFORMATION><identifier>bk_bible.kjv1611</identifier><rights>Public Domain</rights></INFORMATION><BIBLEBOOK bnumber="1"><CHAPTER cnumber="1"><VERS vnumber="1"><STYLE css="x"><gr str="430-853">God</STYLE></gr> &amp; man & woman.<NOTE type="x-studynote">Original note.</NOTE></VERS></CHAPTER></BIBLEBOOK></XMLBIBLE>'''
        with self.assertRaises(ET.ParseError):ET.fromstring(raw)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);original=root/'original.xml';original.write_text(raw)
            source={'id':'kjv1611','path':'original.xml','sha256':file_hash(original)}
            with patch('akribos.project.ROOT',root),patch('akribos.project.source',return_value=source),patch('akribos.project.code_identity',return_value={}):
                output=export_kjv();first=output.read_bytes()
                output.write_text('damaged export')
                self.assertEqual(export_kjv().read_bytes(),first)
                self.assertEqual(export_kjv(rebuild=True).read_bytes(),first)
            self.assertEqual(original.read_text(),raw)
            parsed=ET.fromstring(first)
            self.assertEqual(parsed.findtext('INFORMATION/identifier'),'bk_bible.kjv1611')
            self.assertEqual(parsed.findtext('INFORMATION/rights'),'Public Domain')
            self.assertEqual(parsed.get('revision'),'201909')
            self.assertEqual(parsed.find('.//gr').attrib,{'str':'430-853'})
            self.assertEqual(parsed.find('.//gr').text,'God')
            self.assertEqual(parsed.find('.//gr').tail,' & man & woman.')
            self.assertEqual(parsed.findtext('.//NOTE'),'Original note.')
            link=json.loads(output.with_suffix('.build.json').read_text())
            self.assertEqual(link['sha256'],file_hash(output))
            self.assertEqual(link['source_sha256'],source['sha256'])
            with gzip.open(root/link['history']/'repairs.jsonl.gz','rt') as f:
                edits=[json.loads(row) for row in f]
            reconstructed=raw
            for edit in reversed(edits):
                self.assertEqual(raw[edit['start']:edit['end']],edit['before'])
                reconstructed=reconstructed[:edit['start']]+edit['after']+reconstructed[edit['end']:]
            self.assertEqual(reconstructed.encode(),first)


if __name__=='__main__':unittest.main()
