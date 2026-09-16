"""Verify complete original/history inventories and the public release profile."""
from pathlib import Path
import argparse,gzip,json,re,sys,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from akribos.common import file_hash,require,digest
from akribos.project import VERSION,EDITION_TITLES,check_sources,cached,original_notes
from akribos.importers import parse_xml
from akribos.xmlio import zef_verses,plain,strong_fingerprints
from akribos.confirm import (METHOD,INPUT_PROFILE,NORMALIZATION,SAFETY_PROFILE,
                             verify_confirmation_transition,load_confirmation_evidence)
from akribos.linguistic import (METHOD as LINGUISTIC_METHOD,RULES_VERSION,load_reference_occurrences,
                                verify_transition,_load_alignment_guards)


def verify_release_history(path,link,version):
    """Validate optional stage selection while preserving historical stage-04 links."""
    artifact=link.get('artifact','04-multisource.xml')
    expected={'1.3':'05-reference-confirmed.xml','1.4':'06-linguistic.xml'}.get(version,'04-multisource.xml')
    require(artifact==expected,f'Version {version} must publish {expected}')
    history=(ROOT/link['history']).resolve()
    require(history.is_relative_to(ROOT.resolve()),'Release history escapes repository')
    require(file_hash(path)==link['sha256']==file_hash(history/artifact),'Release/history mismatch')
    if artifact=='04-multisource.xml':return artifact
    manifest=json.loads((history/'manifest.json').read_text(encoding='utf-8'))
    settings=manifest['settings'].get('reference_confirmation',{})
    hashes=settings.get('reference_sha256',{})
    require(set(hashes)=={'elb-bk','elb-csv'} and all(re.fullmatch(r'[a-f0-9]{64}',value) for value in hashes.values()),
            'Missing reference identities for confirmed release')
    require(len(set(hashes.values()))==2,'Confirmed release uses identical references')
    require(settings.get('method')==METHOD and settings.get('input_profile')==INPUT_PROFILE and
            settings.get('normalization')==NORMALIZATION and settings.get('safety_profile')==SAFETY_PROFILE,
            'Unknown reference-confirmation profile')
    report=json.loads((history/'05-reference-confirmed.report.json').read_text(encoding='utf-8'))
    require(report.get('reference_sha256')==hashes,'Confirmation reference hashes differ from manifest')
    require(report.get('sha256')==file_hash(history/'05-reference-confirmed.xml') and report.get('input_sha256')==file_hash(history/'04-multisource.xml'),
            'Confirmation report input/output mismatch')
    before=parse_xml(history/'04-multisource.xml');after=parse_xml(history/'05-reference-confirmed.xml')
    nt_edition=manifest['settings'].get('nt_edition')
    evidence=load_confirmation_evidence(before,history/'source-occurrences.jsonl.gz',
                                        history/'alignment.jsonl.gz',nt_edition=nt_edition)
    require(report.get('safety_profile')==SAFETY_PROFILE and report.get('selected_nt_edition')==nt_edition and
            report.get('safety_evidence_sha256')==evidence.sha256,'Confirmation safety evidence identity differs')
    require({ref:plain(v) for ref,v in zef_verses(before,True)}=={ref:plain(v) for ref,v in zef_verses(after,True)},
            'Confirmation changed Bible text')
    require(strong_fingerprints(before)==strong_fingerprints(after),'Confirmation changed Strong attributes')
    require(original_notes(before)==original_notes(after),'Confirmation changed original notes')
    hints=lambda tree:sum(note.get('ex')=='nl:akribosStrongUncertainty' for note in tree.iter('NOTE'))
    require(report.get('hints_before')==hints(before) and report.get('hints_remaining')==hints(after) and
            report.get('hints_removed')==hints(before)-hints(after),'Confirmation hint counts differ')
    with gzip.open(history/'05-reference-confirmed.audit.jsonl.gz','rt',encoding='utf-8') as stream:
        rows=[json.loads(line) for line in stream]
    counts=verify_confirmation_transition(before,after,rows,output_identity=(link['bible_id'],version),
                                          safety_evidence=evidence)
    require(all(report.get(key)==value for key,value in counts.items()),'Confirmation audit totals differ')
    if artifact=='06-linguistic.xml':verify_linguistic_history(history,manifest,link)
    return artifact


def verify_linguistic_history(history,manifest,link):
    """Verify phase identities, all hints, proofs and the exact allowed XML delta."""
    phase=json.loads((history/'06-linguistic.manifest.json').read_text(encoding='utf-8'))
    report=json.loads((history/'06-linguistic.report.json').read_text(encoding='utf-8'))
    settings=manifest['settings'].get('linguistic_validation',{})
    require(settings.get('method')==phase.get('method')==report.get('method')==LINGUISTIC_METHOD,
            'Unknown or missing linguistic validation method')
    require(phase.get('schema')==1 and phase.get('phase')=='06-linguistic','Invalid linguistic phase manifest')
    require(settings.get('article_corroboration_required') is True and
            phase.get('article_corroboration_required') is True and
            report.get('article_corroboration_required') is True,'Release disabled independent article corroboration')
    require(settings.get('prior_alignment_required') is True,'Release omitted original alignment guards')
    rules=settings.get('rule_identity',{})
    require(rules==phase.get('rule_identity')==report.get('rule_identity') and rules.get('version')==RULES_VERSION,
            'Linguistic rule identities differ')
    implementation=rules.get('implementation',{})
    require(set(implementation)=={'linguistic.py','linguistic_rules.py','confirm.py','common.py',
                                 'importers.py','xmlio.py','project.py'},'Missing linguistic rule dependencies')
    require(rules.get('sha256')==digest(implementation),'Linguistic rule digest differs')
    require(all(manifest['implementation'].get('akribos/'+name)==sha for name,sha in implementation.items()),
            'Linguistic rules differ from archived build implementation')
    source_snapshot=settings.get('source_snapshot')
    require(source_snapshot==phase.get('source_snapshot')==report.get('source_snapshot'),
            'Linguistic source snapshots differ')
    nt_edition=manifest['settings'].get('nt_edition')
    require(nt_edition in {'WH','TR'} and phase.get('selected_nt_edition')==nt_edition and
            report.get('selected_nt_edition')==nt_edition,'Linguistic NT edition mismatch')
    references,snapshot=load_reference_occurrences(ROOT/'config/step-profiles.json',ROOT,nt_edition)
    require(snapshot==source_snapshot,'Linguistic source inputs changed')
    hashes=manifest['settings']['reference_confirmation']['reference_sha256']
    require(phase.get('article_reference_hashes')==hashes,'Article comparison inputs differ from phase 05')
    require(set(report.get('article_reference_tree_hashes',{}))==set(hashes),'Missing article comparison identities')
    require(phase.get('output_identity')==[link['bible_id'],'1.4'],'Wrong linguistic output identity')
    before_path=history/'05-reference-confirmed.xml';after_path=history/'06-linguistic.xml'
    audit_path=history/'06-linguistic.audit.jsonl.gz';report_path=history/'06-linguistic.report.json'
    require(phase.get('outputs')=={'xml':file_hash(after_path),'audit':file_hash(audit_path),'report':file_hash(report_path)},
            'Linguistic output hashes differ')
    require(phase.get('input_sha256')==report.get('input_sha256')==file_hash(before_path),
            'Linguistic input hash mismatch')
    require(report.get('output_sha256')==file_hash(after_path)==link['sha256'] and
            report.get('audit_sha256')==file_hash(audit_path),'Linguistic report hashes differ')
    require(phase.get('alignment_sha256')==file_hash(history/'alignment.jsonl.gz'),'Linguistic alignment hash mismatch')
    before=parse_xml(before_path);after=parse_xml(after_path)
    guards=_load_alignment_guards(history/'alignment.jsonl.gz',before)
    require(report.get('prior_alignment_guard_count')==len(guards),'Linguistic alignment guard count differs')
    with gzip.open(audit_path,'rt',encoding='utf-8') as stream:rows=[json.loads(line) for line in stream]
    counts=verify_transition(before,after,rows,references,nt_edition=nt_edition,
                             verse_guards=guards,output_identity=(link['bible_id'],'1.4'))
    require(all(report.get(key)==value for key,value in counts.items()),'Linguistic audit balance differs')
    require(report.get('article_candidates_retained')==sum(r['kind']=='article-addition' and r['action']=='retain' for r in rows),
            'Linguistic retained article count differs')
    require(report.get('hints_rejected')==sum(r['kind']=='uncertainty' and r['status']=='reject' for r in rows),
            'Linguistic rejected hint count differs')
    require(report.get('text_preserved') is True and report.get('existing_strong_values_preserved') is True and
            report.get('no_bootstrapping') is True,'Missing linguistic preservation assertions')
    require(report.get('original_notes_preserved')==len(original_notes(before))==len(original_notes(after)),
            'Linguistic original note count differs')


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
        verify_release_history(p,link,version)
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
