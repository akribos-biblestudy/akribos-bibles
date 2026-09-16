"""Verify complete original/history inventories and the public release profile."""
from pathlib import Path
import argparse,gzip,json,re,sys,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from akribos.common import file_hash,require,digest
from akribos.project import VERSION,EDITION_TITLES,check_sources,cached
from akribos.importers import parse_xml
from akribos.xmlio import zef_verses,plain


def verify_repository(version=VERSION):
    require(re.fullmatch(r'[0-9]+(?:\.[0-9]+){0,2}(?:-[a-z0-9]+)?',version),'Invalid version')
    sources=check_sources();expected={s['path'] for s in sources['sources']}
    actual={str(p.relative_to(ROOT)) for p in (ROOT/'sources/originals').rglob('*') if p.is_file()}
    require(expected==actual,'Unregistered/missing original; reference XML must stay under .local')
    runs=0
    for directory in ('history','comparisons'):
        for p in (ROOT/directory).rglob('manifest.json'):
            cached(p.parent);runs+=1
            m=json.loads(p.read_text(encoding='utf-8'))['implementation']
            snap=ROOT/'history/implementations'/digest(m)[:16]
            require((snap/'implementation.json').exists(),f'Missing source snapshot for {p}')
            for name,h in m.items():require(file_hash(snap/name)==h,f'Implementation snapshot changed: {snap/name}')
    compressed=0
    for p in (ROOT/"history").rglob("*.gz"):
        with gzip.open(p,"rb") as f:
            while f.read(1024*1024):pass
        compressed+=1
    results={}
    for bid in ('akribos.elb','akribos.lut'):
        p=ROOT/'releases'/(bid+'.xml');r=parse_xml(p)
        require(r.findtext('INFORMATION/identifier')==bid,'Wrong output identifier')
        require(r.get('revision')==version,'Wrong output version')
        require(r.findtext('INFORMATION/rights','').startswith(f'Version {version}. '),'Version absent from rights')
        short,title,original=EDITION_TITLES[bid]
        fields={'title':title,'description':f'mit Strongs (Akribos {version})',
                'short_title':short,'cover_title':short,'tab_title':short,
                'selection_title':title,'selection_subtitle':f'mit Strongs (Akribos {version})'}
        for field,value in fields.items():
            require(r.findtext('INFORMATION/'+field)==value,f'Wrong display metadata: {bid}/{field}')
        require(f'Originalausgabe: {original}.' in r.findtext('INFORMATION/rights',''),'Original edition absent from rights')
        require(not list(r.iter('GRAM')),'Uppercase GRAM in release')
        notes=sum(n.get('type')=='x-studynote' for n in r.iter('NOTE'))
        require(notes==(9481 if bid=='akribos.elb' else 0),'Unexpected loss/addition of original study notes')
        leftovers=0
        for ref,v in zef_verses(r):
            text=plain(v)
            if bid=='akribos.lut':leftovers+=len(re.findall(r'\bHErr(?:n|s)?\b',text))
            else:leftovers+=len(re.findall(r'\bJehova(?:s)?\b',text))
        require(leftovers==0,'Requested divine-name normalization incomplete')
        link=json.loads(p.with_suffix('.build.json').read_text(encoding='utf-8'))
        require(link['bible_id']==bid and link['version']==version,'Release manifest identity/version mismatch')
        require(file_hash(p)==link['sha256']==file_hash(ROOT/link['history']/'04-multisource.xml'),'Release/history mismatch')
        results[bid]={'sha256':file_hash(p),'original_studynotes':notes,'normalized_names':True}
    # Public comparison schema has no reference word/code columns.
    for p in (ROOT/'comparisons').rglob('verse-differences.csv'):
        require(p.read_text(encoding='utf-8').splitlines()[0]=='ref,categories','Unsafe public difference columns')
    kjv=ROOT/'releases/kjv1611.xml';r=parse_xml(kjv)
    link=json.loads(kjv.with_suffix('.build.json').read_text(encoding='utf-8'))
    require(link['source_id']=='kjv1611' and link['operation']=='syntax-repair-only','Wrong KJV operation')
    original=next(s for s in sources['sources'] if s['id']=='kjv1611')
    require(link['source_sha256']==original['sha256'],'Wrong KJV original hash')
    require(file_hash(kjv)==link['sha256']==file_hash(ROOT/link['history']/'bible.xml'),'KJV release/history mismatch')
    require(r.findtext('INFORMATION/identifier')==link['bible_id']=='bk_bible.kjv1611','Wrong KJV identifier')
    require(r.findtext('INFORMATION/rights')=='Public Domain','KJV original rights changed')
    require(not list(r.iter('STYLE')),'Unrepaired KJV STYLE tags')
    notes=sum(1 for _ in r.iter('NOTE'));verses=sum(1 for _ in r.iter('VERS'))
    require(notes==7716 and verses==31102,'KJV notes/verses missing')
    results['kjv1611']={'sha256':file_hash(kjv),'original_studynotes':notes,'verses':verses,'syntax_repaired':True}
    return {'version':version,'registered_originals':len(expected),'verified_history_runs':runs,'gzip_crc_checks':compressed,'releases':results}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',default=VERSION,help=f'Erwartete Version der aktuellen Ausgabedateien (Standard: {VERSION})')
    print(json.dumps(verify_repository(parser.parse_args().version),ensure_ascii=False,indent=2))
