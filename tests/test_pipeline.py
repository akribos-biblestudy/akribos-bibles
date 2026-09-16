import copy, gzip, json, sys, tempfile, unittest
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'.local/python'))
from akribos.common import strongs,DataError
from akribos.modernize import plan_verse,rules
from akribos.xmlio import apply_edits,plain,verse_tokens,annotate,note_fingerprints,write_xml,import_osis
from akribos.project import metadata,jsonl_gz,line,load_input
from akribos.pipeline import transfer,lexical_fill,additional_fill
from akribos.importers import parse_xml
from akribos.lexical import key


def bible(verse):
    return ET.fromstring('<XMLBIBLE><INFORMATION/><BIBLEBOOK bnumber="1"><CHAPTER cnumber="1"><VERS vnumber="1">'+verse+'</VERS></CHAPTER></BIBLEBOOK></XMLBIBLE>')


def edited(text,edition='elb'):
    v=ET.Element('VERS');v.text=text
    edits,reviews=plan_verse(text,edition,rules());apply_edits(v,edits)
    return plain(v),reviews

class PipelineTests(unittest.TestCase):
    def test_strong_lists_and_extended_codes(self):
        self.assertEqual(strongs('1254-853 01254','H'),['H1254','H853'])
        self.assertEqual(strongs('strong:G0976 G2424G H0430_A'),['G976','G2424','H430'])
    def test_name_case(self):
        self.assertEqual(edited('sie versammelten sich zu Jehova')[0],'sie versammelten sich zu dem HERRN')
        self.assertEqual(edited('Jehova sprach.')[0],'Der HERR sprach.')
        self.assertEqual(edited('das Wort Jehovas')[0],'das Wort des HERRN')
    def test_luther_capitalization_not_human_herr(self):
        self.assertEqual(edited('HErr und HErrn; der Herr und dem Herrn.','lut')[0],'HERR und HERRN; der Herr und dem Herrn.')
    def test_gender(self):
        self.assertEqual(edited('das alte Weib')[0],'die alte Frau')
        self.assertEqual(edited('mit dem alten Weibe')[0],'mit der alten Frau')
        self.assertEqual(edited('ein schönes Weib, das singt')[0],'eine schöne Frau, die singt')
    def test_spelling_not_global_sz_replacement(self):
        self.assertEqual(edited('daß er muß, heißt nicht Straße.')[0],'dass er muss, heißt nicht Straße.')
    def test_notes_survive_edits_and_annotation(self):
        r=bible('zu <gr str="3068">Jehova</gr><NOTE type="x-studynote">Jehova: <STYLE css="font-weight:bold">Original</STYLE></NOTE> sprach.')
        v=r.find('.//VERS');before=note_fingerprints(r)
        changes,_=plan_verse(plain(v),'elb',rules());apply_edits(v,changes)
        text,toks=verse_tokens(v,'Gen.1.1')
        toks[-1].update(strong=['H559'],method='lexicon',uncertain=True)
        annotate(v,toks)
        self.assertEqual(note_fingerprints(r)[:1],before)
        self.assertEqual(plain(v),'zu dem HERRN sprach.')
        self.assertEqual(v[-1].get('ex'),'nl:akribosStrongUncertainty')
        self.assertEqual(v[-2].text,'sprach')
    def test_cross_style_word(self):
        r=bible('das W<STYLE>ei</STYLE>b<NOTE type="x-studynote">Weib</NOTE> kam')
        v=r.find('.//VERS');before=note_fingerprints(r)
        edits,_=plan_verse(plain(v),'elb',rules());apply_edits(v,edits)
        self.assertEqual(plain(v),'die Frau kam');self.assertEqual(note_fingerprints(r),before)
    def test_original_attributes_preserved(self):
        r=bible('<gr str="430" rmac="N">Gott</gr> schuf')
        v=r.find('.//VERS');_,tokens=verse_tokens(v,'Gen.1.1');tokens[1].update(strong=['H1254'])
        annotate(v,tokens);self.assertEqual(v[0].attrib,{'str':'430','rmac':'N'})
        self.assertEqual(len(v.findall('gr')),2)
    def test_ambiguous_lexicon_stays_unassigned(self):
        t=[{'id':'d001','text':'Licht','strong':[]}];review=[]
        lexical_fill(t,{'H216','H3974'},{('licht',):{'H216':{'test'},'H3974':{'test'}}},review,'Gen.1.1')
        self.assertEqual(t[0]['strong'],[]);self.assertEqual(review[0]['kind'],'lexicon-ambiguity')
    def test_lexicon_requires_verse_inventory(self):
        t=[{'id':'d001','text':'Licht','strong':[]}]
        lexical_fill(t,{'H430'},{('licht',):{'H216':{'test'}}},[],'Gen.1.1')
        self.assertEqual(t[0]['strong'],[])
    def test_primary_never_overwrites(self):
        t=[{'text':'Gott','strong':['H430']}]
        transfer(t,[('Gott',('H410',))],'test');self.assertEqual(t[0]['strong'],['H430'])
    def test_lemma_inflection(self):
        self.assertEqual(key('Frauen',True),key('Frau',True))
        self.assertEqual(key('ging',True),key('gehen',True))
    def test_metadata_ids_version_rights(self):
        for bid,short,title in [('akribos.elb','ELB','Elberfelder 1932'),('akribos.lut','LUT','Luther 1912')]:
            r=bible('Text');ET.SubElement(r.find('INFORMATION'),'source').text='Originalquelle'
            for version in ('1.2','2.3.4'):
                metadata(r,bid,version,'language');metadata(r,bid,version,'04-multisource')
                self.assertEqual(r.findtext('INFORMATION/identifier'),bid)
                self.assertEqual(r.findtext('INFORMATION/title'),title)
                self.assertEqual(r.findtext('INFORMATION/cover_title'),short)
                self.assertEqual(r.findtext('INFORMATION/tab_title'),short)
                self.assertEqual(r.findtext('INFORMATION/selection_title'),title)
                self.assertEqual(r.findtext('INFORMATION/selection_subtitle'),f'mit Strongs (Akribos {version})')
                self.assertEqual(r.get('revision'),version)
                rights=r.findtext('INFORMATION/rights')
                self.assertTrue(rights.startswith(f'Version {version}. Bibelgrundtext'))
                self.assertIn('Originalausgabe:',rights)
                self.assertIn('nicht um eine eigene Übersetzung',rights)
                self.assertEqual(len(r.findall('INFORMATION/selection_subtitle')),1)
                self.assertEqual(r.findtext('INFORMATION/source'),'Originalquelle')
        r=bible('Text');metadata(r,'akribos.custom','1.1','language')
        self.assertIn('keine Public-Domain-Erklärung',r.findtext('INFORMATION/rights'))
    def test_publishing_replaces_current_release_and_preserves_history(self):
        from unittest.mock import patch
        from akribos.pipeline import publish
        from akribos.common import file_hash
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);old=root/'history/old';new=root/'history/new'
            for folder,text in ((old,'original 1.1'),(new,'corrected 1.2')):
                folder.mkdir(parents=True);(folder/'04-multisource.xml').write_text(text)
            with patch('akribos.pipeline.ROOT',root):
                publish(old,'akribos.elb','1.1')
                publish(new,'akribos.elb','1.2')
                publish(old,'akribos.custom','1.1',custom=True)
            output=root/'releases/akribos.elb.xml'
            self.assertEqual(output.read_text(),'corrected 1.2')
            self.assertEqual((old/'04-multisource.xml').read_text(),'original 1.1')
            self.assertEqual((new/'04-multisource.xml').read_text(),'corrected 1.2')
            link=json.loads(output.with_suffix('.build.json').read_text())
            self.assertEqual(link,{'history':'history/new','bible_id':'akribos.elb','version':'1.2','sha256':file_hash(output)})
            self.assertFalse((root/'releases/1.2').exists())
            self.assertFalse((root/'releases/akribos.custom.xml').exists())
            self.assertTrue((root/'.local/custom-releases/1.1/akribos.custom.xml').exists())
    def test_serialization_does_not_add_verse_whitespace(self):
        r=bible('ein<STYLE> Wort</STYLE><NOTE>Notiz</NOTE>!');v=r.find('.//VERS');before=plain(v)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.xml';write_xml(p,r)
            self.assertEqual(plain(parse_xml(p).find('.//VERS')),before)
    def test_deterministic_compressed_audit(self):
        with tempfile.TemporaryDirectory() as d:
            a,b=Path(d)/'a.gz',Path(d)/'b.gz'
            for p in (a,b):
                with jsonl_gz(p) as f:line(f,{'text':'größer'})
            self.assertEqual(a.read_bytes(),b.read_bytes())
    def test_xml_external_entities_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.xml';p.write_text('<!DOCTYPE x [<!ENTITY a SYSTEM "file:///etc/passwd">]><x>&a;</x>')
            with self.assertRaises(DataError):parse_xml(p)
    def test_osis_container_notes_and_strong(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.xml';p.write_text('<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace"><osisText><div><chapter><verse osisID="Gen.1.1">Im <w lemma="strong:H7225">Anfang</w><note>Hinweis <hi>Original</hi></note>.</verse></chapter></div></osisText></osis>')
            r=import_osis(p);v=r.find('.//VERS')
            self.assertEqual(plain(v),'Im Anfang.');self.assertEqual(verse_tokens(v,'Gen.1.1')[1][-1]['strong'],['H7225'])
            self.assertEqual(''.join(r.find('.//NOTE').itertext()),'Hinweis Original')
    def test_note_grammar_tag_is_untouched(self):
        from akribos.xmlio import normalize_gr
        r=bible('<GRAM str="430">Gott</GRAM><NOTE><GRAM str="216">Licht</GRAM></NOTE>')
        before=note_fingerprints(r);normalize_gr(r)
        self.assertEqual(r.find('.//VERS')[0].tag,'gr')
        self.assertEqual(note_fingerprints(r),before)
    def test_comparison_denominators_and_public_privacy(self):
        from unittest.mock import patch
        from akribos.compare import compare
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);a=p/'a.xml';b=p/'b.xml'
            ar=bible('<gr str="430">Gott</gr> schuf Licht');metadata(ar,'akribos.test','1.1','test');write_xml(a,ar)
            br=bible('<gr str="430">Gott</gr> <gr str="1254">schuf</gr> <gr str="216-3974">Licht</gr>');write_xml(b,br)
            original_a,original_b=a.read_bytes(),b.read_bytes()
            with patch('akribos.compare.ROOT',p):out=compare(a,b,'synthetic',public_index=True)
            report=json.loads((out/'summary.json').read_text())
            self.assertEqual(report['target_coverage']['word_coverage_percent'],33.3333)
            self.assertEqual(report['reference_coverage']['word_coverage_percent'],100)
            self.assertEqual(report['comparison']['only-reference-tagged'],2)
            self.assertEqual(report['comparison']['identical-strong-set'],1)
            public=(out/'verse-differences.csv').read_text()
            self.assertNotIn('1254',public);self.assertNotIn('Licht',public)
            self.assertEqual(a.read_bytes(),original_a);self.assertEqual(b.read_bytes(),original_b)
    def test_osis_milestone(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.xml';p.write_text('<osis><osisText><div><chapter><p><verse sID="Gen.1.1"/>Ein <w lemma="strong:H430">Gott</w><note>Note</note>.<verse eID="Gen.1.1"/></p></chapter></div></osisText></osis>')
            r=import_osis(p);self.assertEqual(plain(r.find('.//VERS')),'Ein Gott.')
            self.assertEqual(r.find('.//NOTE').text,'Note')

if __name__=='__main__':unittest.main()
