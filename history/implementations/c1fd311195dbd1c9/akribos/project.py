"""Registered source snapshots, deterministic history and metadata."""
from __future__ import annotations
import copy, csv, gzip, io, json, re, shutil, tempfile
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
import xml.etree.ElementTree as ET
from .common import digest, require, file_hash, write_json, atomic_text
from .importers import parse_xml, tag
from .xmlio import write_xml, zef_verses, verse_tokens, note_fingerprints, import_osis, normalize_gr

ROOT = Path(__file__).resolve().parents[1]
VERSION = '1.1'
EDITION_TITLES = {
    'akribos.elb': ('ELB', 'Elberfelder 1932', 'Unrevidierte Elberfelder Übersetzung von 1932'),
    'akribos.lut': ('LUT', 'Luther 1912', 'Luther-Bibel von 1912 (in neuer Rechtschreibung)'),
}


def manifest():
    return json.loads((ROOT/'config/sources.lock.json').read_text(encoding='utf-8'))


def check_sources():
    m = manifest()
    for s in m['sources']:
        p = (ROOT/s['path']).resolve()
        require(p.is_relative_to(ROOT), 'Source path escapes repository')
        require(p.is_file() and file_hash(p) == s['sha256'], f'Original missing or changed: {p}')
    return m


def source(sid):
    return next(s for s in manifest()['sources'] if s['id'] == sid)


def code_identity():
    return {str(p.relative_to(ROOT)): file_hash(p) for folder in ('akribos','rules','config')
            for p in sorted((ROOT/folder).rglob('*')) if p.suffix in {'.py','.json'}} | {'requirements.txt':file_hash(ROOT/'requirements.txt')}


def identity(kind, settings):
    return digest({'kind':kind,'settings':settings,'implementation':code_identity()})[:16]


def finalize(work, dest, settings):
    """Never overwrite a previous run; a rerun must be byte-identical."""
    files = {str(p.relative_to(work)): file_hash(p) for p in sorted(work.rglob('*')) if p.is_file()}
    write_json(work/'manifest.json', {'settings':settings,'implementation':code_identity(),'files':files})
    if dest.exists():
        expected = {str(p.relative_to(dest)):file_hash(p) for p in dest.rglob('*') if p.is_file()}
        actual = {str(p.relative_to(work)):file_hash(p) for p in work.rglob('*') if p.is_file()}
        require(expected == actual, f'Reproducibility failure; existing run kept: {dest}')
        shutil.rmtree(work)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(work),str(dest))
    return dest


def cached(dest):
    p = dest/'manifest.json'
    if not p.exists(): return False
    data = json.loads(p.read_text(encoding='utf-8'))
    actual = {str(x.relative_to(dest)) for x in dest.rglob('*') if x.is_file()}-{'manifest.json'}
    require(actual == set(data['files']),f'History file inventory changed: {dest}')
    for name,h in data['files'].items():
        require(file_hash(dest/name)==h,f'History file modified: {dest/name}')
    return True


def workspace(kind, run):
    base=ROOT/'.local/work';base.mkdir(parents=True,exist_ok=True)
    # Temporary paths are never part of artifact content or identities. Isolated
    # work dirs let interrupted jobs be inspected without blocking a clean rerun.
    return Path(tempfile.mkdtemp(prefix=f'{kind}-{run}-',dir=base))


def metadata(root, bible_id, version, stage, text_rights=None):
    info = root.find('INFORMATION')
    if info is None: info=ET.SubElement(root,'INFORMATION')
    edition = EDITION_TITLES.get(bible_id)
    title = edition[1] if edition else f'{bible_id} – Version {version}'
    subtitle = f'mit Strongs (Akribos {version})'
    if text_rights is None:
        text_rights = 'Bibelgrundtext und historische Original-Studynotes: Public Domain laut Quellenangaben.' if bible_id in {'akribos.elb','akribos.lut'} else 'Rechte am Bibeltext und an den Originalnotizen: siehe bereitgestellte Originalquelle; keine Public-Domain-Erklärung.'
    rights = f'Version {version}. {text_rights} Neue schutzfähige Strong-Aufbereitung und Redaktion: Copyright © 2026 Akribos, CC BY 4.0, https://creativecommons.org/licenses/by/4.0/. Übernommene Quellen behalten ihre Rechte: ELB1905/Luther1912/Schlachter1951/KJV laut PD-Angaben; STEP Bible und Open Scriptures CC BY 4.0; hebräisch-deutsche Ergänzungen AGPLv3; Kautz-Lexikon Copyright Gerhard Kautz, Veröffentlichung der Originaldatei mit Genehmigung. Keine ausschließlichen Rechte an Strong-Nummern oder gemeinfreien Texten.'
    if edition:
        rights += f' Originalausgabe: {edition[2]}. Akribos bearbeitet diese Ausgabe sprachlich und ergänzt Strong-Zuordnungen; es handelt sich nicht um eine eigene Übersetzung.'
    values = {'title':title, 'identifier':bible_id,'creator':'Akribos (Sprachbearbeitung und Strong-Aufbereitung)',
              'language':'deu','format':'Zefania XML / Akribos gr profile', 'rights':rights,
              'description':subtitle if edition else f'Akribos Version {version}; Verarbeitungsstufe {stage}. Regelbasiert bearbeitet; automatische Strong-Zuordnungen, keine gemessene Fehlerfreiheit. Original-Studynotes erhalten. Lemma/Morphologie und Prüfaufgaben in Begleitdateien.',
              'contributors':'STEP Bible (www.STEPBible.org), based on work at Tyndale House Cambridge; Gerhard Kautz; Open Scriptures Hebrew Bible; Jens Grabner / J. Barkowsky / TOLEDOT; Quellenregister siehe sources.lock.json.'}
    if edition:
        # Explicit Akribos display fields keep cover/tab labels separate from the
        # original edition's name and the versioned selection subtitle.
        values.update(short_title=edition[0], cover_title=edition[0], tab_title=edition[0],
                      selection_title=title, selection_subtitle=subtitle)
    for key,value in values.items():
        e=info.find(key)
        if e is None:e=ET.SubElement(info,key)
        e.text=value
    root.set('biblename',values['title']); root.set('revision',version)


def load_input(path):
    r=parse_xml(path)
    if tag(r)!='XMLBIBLE': r=import_osis(path)
    normalize_gr(r)
    for v in r.iter('VERS'):
        if v.get('vnumber')=='0': v.tag='CAPTION';v.attrib={'vref':'1'}
    return r


def stats(root):
    total=tagged=verses=0
    for ref,v in zef_verses(root):
        if ref.endswith('.0'):continue
        _,tokens=verse_tokens(v,ref)
        total+=len(tokens);tagged+=sum(bool(t['strong']) for t in tokens);verses+=1
    return {'verses':verses,'words':total,'tagged_words':tagged,
            'word_coverage_percent':round(100*tagged/total,4) if total else 0,
            'studynotes':sum(e.get('type')=='x-studynote' for e in root.iter('NOTE')),
            'word_hints':sum(e.get('ex')=='nl:akribosStrongUncertainty' for e in root.iter('NOTE'))}


def original_notes(root):
    check=ET.Element('CHECK')
    for e in root.iter('NOTE'):
        if e.get('ex')!='nl:akribosStrongUncertainty':check.append(copy.deepcopy(e))
    return note_fingerprints(check)


@contextmanager
def jsonl_gz(path):
    with open(path,'wb') as raw:
        with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as gz:
            with io.TextIOWrapper(gz,encoding='utf-8',newline='\n') as f:yield f


def line(f,obj):
    f.write(json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n')


def csv_write(path, rows, fields):
    with open(path,'w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)


def prepare_kjv(rebuild=False):
    """Pinned donor only: discard decorative STYLE tags, retain all text/gr/note tags.

    Source STYLE/gr crossings are not well-formed XML. This is NOT a generic
    recovering XML parser. Original bytes remain in sources/originals.
    """
    s=source('kjv1611');p=ROOT/s['path']
    require(file_hash(p)==s['sha256'],'Changed KJV snapshot')
    settings={'source':s,'repair':'remove-STYLE-only-and-escape-bare-ampersands-v1'}
    run=identity('prepare-kjv',settings);dest=ROOT/'history/prepared/kjv1611'/run
    if cached(dest) and not rebuild:return dest/'bible.xml'
    work=workspace('prepare-kjv',run)
    raw=p.read_text(encoding='utf-8-sig')
    edits=[]
    pattern=re.compile(r'</?STYLE\b[^>]*>|&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)')
    def replace(m):
        after='&amp;' if m[0]=='&' else ''
        edits.append({'start':m.start(),'end':m.end(),'before':m[0],'after':after});return after
    fixed=pattern.sub(replace,raw)
    require(re.findall(r'<gr\b[^>]*>',raw)==re.findall(r'<gr\b[^>]*>',fixed),'KJV Strong attributes changed')
    # NOTE payload text and all non-STYLE tags survive literally (apart from ampersand escaping).
    root=ET.fromstring(fixed)
    require(len(list(root.iter('NOTE')))==len(re.findall(r'<NOTE\b',raw)),'KJV notes lost')
    atomic_text(work/'bible.xml',fixed)
    with jsonl_gz(work/'repairs.jsonl.gz') as f:
        for e in edits:line(f,e)
    write_json(work/'report.json',{'repair_count':len(edits),'discarded_markup':'STYLE tags in derivative KJV donor copy only; original archived intact','notes_retained':len(list(root.iter('NOTE'))),'gr_start_tags_unchanged':True,'stats':stats(root)})
    finalize(work,dest,settings);return dest/'bible.xml'


def export_kjv(rebuild=False):
    """Export the syntax-repaired source with its original metadata and Strong tags."""
    prepared=prepare_kjv(rebuild=rebuild)
    output=ROOT/'releases/kjv1611.xml'
    output.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(prepared,output)
    root=parse_xml(output)
    write_json(output.with_suffix('.build.json'),{
        'source_id':'kjv1611','source_sha256':source('kjv1611')['sha256'],
        'bible_id':root.findtext('INFORMATION/identifier'),
        'history':str(prepared.parent.relative_to(ROOT)),
        'sha256':file_hash(output),'operation':'syntax-repair-only',
    })
    return output
