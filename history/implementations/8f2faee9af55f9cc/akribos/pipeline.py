"""Language first, primary annotations second, then lexical and multi-source additions."""
from __future__ import annotations
import copy, json, re, shutil
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from .common import require, file_hash, write_json, digest
from .project import (ROOT,VERSION,source,check_sources,identity,workspace,finalize,cached,
    metadata,load_input,stats,original_notes,prepare_kjv,jsonl_gz,line,csv_write)
from .modernize import modernize
from .xmlio import zef_verses,verse_tokens,annotate,plain,write_xml,strong_fingerprints
from .importers import parse_xml
from .verify import verify
from .lexical import key,lexicons,reference_inventory,learn,STOP
from .confirm import prepare_confirmation,confirm_uncertainty,load_confirmation_evidence
from .linguistic import release_settings,validate_files


def edit(edition='elb',version=VERSION,input_path=None,bible_id=None,overrides=None,rebuild=False,profile=None):
    check_sources()
    custom=input_path is not None
    sid={'elb':'elb1932','lut':'luther1912','elb1905':'elb1905','schlachter1951':'schlachter1951'}.get(edition,edition)
    p=Path(input_path).resolve() if custom else ROOT/source(sid)['path']
    bid=bible_id or {'elb':'akribos.elb','lut':'akribos.lut'}.get(edition,'donor.'+edition)
    require(re.fullmatch(r'[a-z0-9][a-z0-9._-]*',bid),'Use a lowercase stable Bible ID')
    require(re.fullmatch(r'[0-9]+(?:\.[0-9]+){0,2}(?:-[a-z0-9]+)?',version),'Invalid version')
    profile=profile or ('elb' if edition in {'elb','elb1905'} else 'lut' if edition=='lut' else 'generic')
    settings={'edition':edition,'bible_id':bid,'version':version,'input_sha256':file_hash(p),
              'profile':profile,'overrides_sha256':file_hash(overrides) if overrides else None}
    run=identity('edit',settings)
    base=ROOT/('.local/custom-history' if custom else 'history')
    dest=base/'edit'/bid/version/run
    if cached(dest) and not rebuild:return dest
    work=workspace('edit',run)
    tree=load_input(p);write_xml(work/'00-import.xml',tree)
    print(f'edit {bid} -> {dest.relative_to(ROOT)}',flush=True)
    modernize(work/'00-import.xml',work/'01-language.xml',profile,
              overrides_path=overrides,version=version,bible_id=bid)
    write_json(work/'verification.json',verify(work/'00-import.xml',work/'01-language.xml',work/'01-language.changes.csv'))
    write_json(work/'coverage.json',stats(parse_xml(work/'01-language.xml')))
    return finalize(work,dest,settings)


def compact_rows(path):
    r=load_input(path);rows={}
    for ref,v in zef_verses(r):
        _,tokens=verse_tokens(v,ref)
        rows[ref]=[(t['text'],tuple(t['strong'])) for t in tokens]
    return rows


def transfer(tokens,donor,sid,inventory=None,min_block=1,method='baseline-transfer'):
    a=[key(t['text']) for t in tokens];b=[key(t[0]) for t in donor]
    for block in SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks():
        if block.size<min_block:continue
        for k in range(block.size):
            t=tokens[block.a+k];codes=donor[block.b+k][1]
            if t['strong'] or not codes:continue
            if inventory is not None and not set(codes)<=inventory:continue
            t.update(strong=list(codes),method=method,sources=[sid],source_token_index=block.b+k,
                     matching_block_words=block.size,uncertain=method!='baseline-transfer')


def lexical_fill(tokens,inv,lex,review,ref):
    keys=[key(t['text'],True) for t in tokens]
    # Long phrase first. Ambiguity is never resolved just by choosing the first entry.
    for n in range(5,0,-1):
        for i in range(len(tokens)-n+1):
            part=tokens[i:i+n]
            if any(t['strong'] for t in part):continue
            candidates={c:s for c,s in lex.get(tuple(keys[i:i+n]),{}).items() if c in inv}
            if len(candidates)==1:
                c,sids=next(iter(candidates.items()))
                for t in part:t.update(strong=[c],method='lexicon',sources=sorted(sids)+['STEP'],uncertain=True,phrase_tokens=n)
            elif candidates:
                review.append({'ref':ref,'token':part[0]['id'],'kind':'lexicon-ambiguity','candidates':sorted(candidates)})


def additional_fill(tokens,ref,inv,donors,primary,index,origins,lex,review):
    for sid,rows in donors.items():
        if sid!=primary:transfer(tokens,rows.get(ref,[]),sid,inv,2,'other-translation')
    # Single content-word agreement within this very verse, including inflectional differences.
    verse_candidates=defaultdict(lambda:defaultdict(set))
    for sid,rows in donors.items():
        if sid==primary:continue
        for text,codes in rows.get(ref,[]):
            if len(codes)==1 and codes[0] in inv:
                verse_candidates[key(text,True)][codes[0]].add(sid)
    for t in tokens:
        if t['strong']:continue
        k=key(t['text'],True)
        if k in STOP or len(k)<3:continue
        vc=verse_candidates.get(k,{})
        if len(vc)==1:
            code,sids=next(iter(vc.items()))
            if len(sids)>=2 or code in lex.get((k,),{}):
                t.update(strong=[code],method='verse-consensus',sources=sorted(sids)+['STEP'],uncertain=True)
                continue
        candidates={c:n for c,n in index.get(k,{}).items() if c in inv}
        if len(candidates)==1:
            code,count=next(iter(candidates.items()));total=sum(index[k].values());sids=origins[k,code]
            if count>=3 and (count/total>=0.70 or len(sids)>=2):
                t.update(strong=[code],method='concordance',sources=sorted(sids)+['STEP'],
                         observed_count=count,observed_share=round(count/total,6),uncertain=True)
        elif candidates:review.append({'ref':ref,'token':t['id'],'kind':'concordance-ambiguity','candidates':sorted(candidates)})


def reference_confirmation_stage(work,bid,version,confirmation,nt_edition):
    """Write stage 05 and a deterministic audit without copying reference data."""
    require(version in {'1.3','1.4'} and confirmation is not None,'Stage 05 requires a complete version 1.3/1.4 request')
    input_path=work/'04-multisource.xml'
    target=parse_xml(input_path)
    sources=confirmation['references']
    evidence=load_confirmation_evidence(target,work/'source-occurrences.jsonl.gz',
                                        work/'alignment.jsonl.gz',nt_edition=nt_edition)
    result=confirm_uncertainty(target,sources['elb-bk'],sources['elb-csv'],safety_evidence=evidence)
    stage='05-reference-confirmed'
    metadata(result.root,bid,version,stage)
    output=work/(stage+'.xml');write_xml(output,result.root)
    serialized=parse_xml(output)
    require({ref:plain(v) for ref,v in zef_verses(target,True)}==
            {ref:plain(v) for ref,v in zef_verses(serialized,True)},'Serialized confirmation changed Bible text')
    require(strong_fingerprints(target)==strong_fingerprints(serialized),'Serialized confirmation changed Strong attributes')
    require(original_notes(target)==original_notes(serialized),'Serialized confirmation changed original notes')
    with jsonl_gz(work/(stage+'.audit.jsonl.gz')) as audit:
        for row in result.audit:line(audit,row)
    report=result.summary|confirmation['settings']|stats(serialized)|{
        'input_sha256':file_hash(input_path),'sha256':file_hash(output),
        'safety_evidence_sha256':evidence.sha256,'selected_nt_edition':nt_edition,
        'original_notes_preserved':len(original_notes(target)),'text_preserved':True,
        'strong_attributes_preserved':True}
    write_json(work/(stage+'.report.json'),report)
    return report


def linguistic_validation_stage(work,bid,version,confirmation,nt_edition,settings,elb_bk,elb_csv):
    require(version=='1.4' and confirmation is not None,'Stage 06 requires a complete version 1.4 request')
    stage='06-linguistic'
    validate_files(work/'05-reference-confirmed.xml',work/(stage+'.xml'),
        source_profiles_path=ROOT/'config/step-profiles.json',source_root=ROOT,nt_edition=nt_edition,
        corroborating_paths={'elb-bk':elb_bk,'elb-csv':elb_csv},
        require_article_corroboration=True,alignment_path=work/'alignment.jsonl.gz',
        output_identity=(bid,version))
    phase=json.loads((work/(stage+'.manifest.json')).read_text(encoding='utf-8'))
    require(phase['article_reference_hashes']==confirmation['settings']['reference_sha256'],
            'Private article references changed during the build')
    require(phase['source_snapshot']==settings['source_snapshot'] and phase['rule_identity']==settings['rule_identity'],
            'Linguistic sources or rules changed during the build')
    report=json.loads((work/(stage+'.report.json')).read_text(encoding='utf-8'))
    return report|stats(parse_xml(work/(stage+'.xml')))|{'sha256':phase['outputs']['xml']}


def build(edition='elb',version=VERSION,input_path=None,bible_id=None,overrides=None,rebuild=False,profile=None,nt_edition=None,
          elb_bk=None,elb_csv=None):
    # This must precede edit(), workspace creation and all release mutations.
    confirmation=prepare_confirmation(version,elb_bk,elb_csv)
    artifact=('06-linguistic.xml' if version=='1.4' else
              '05-reference-confirmed.xml' if confirmation else '04-multisource.xml')
    nt_edition=nt_edition or ('TR' if edition=='lut' else 'WH')
    require(nt_edition in {'WH','TR'},'Supported NT profiles: WH, TR')
    linguistic=release_settings(ROOT/'config/step-profiles.json',ROOT,nt_edition) if version=='1.4' else None
    check_sources()
    edited=edit(edition,version,input_path,bible_id,overrides,rebuild,profile)
    em=json.loads((edited/'manifest.json').read_text(encoding='utf-8'))['settings']
    bid=em['bible_id']
    donor_paths={}
    for sid,ed in [('elb1905','elb1905'),('luther1912','lut'),('schlachter1951','schlachter1951')]:
        donor_paths[sid]=edit(ed,version,rebuild=False)/'01-language.xml'
    kjv_path=prepare_kjv()
    settings={'bible_id':bid,'version':version,'edition':edition,'edited_sha256':file_hash(edited/'01-language.xml'),
              'nt_edition':nt_edition,'donors':{s:file_hash(p) for s,p in donor_paths.items()},'kjv_prepared_sha256':file_hash(kjv_path),
              'primary':'elb1905' if edition=='elb' else 'luther1912' if edition=='lut' else None,
              'language_history':str(edited.relative_to(ROOT))}
    if confirmation:settings['reference_confirmation']=confirmation['settings']
    if linguistic:settings['linguistic_validation']=linguistic
    run=identity('build',settings)
    dest=ROOT/('.local/custom-history' if input_path else 'history')/'build'/bid/version/run
    if cached(dest) and not rebuild:
        publish(dest,bid,version,bool(input_path),artifact=artifact);return dest
    work=workspace('build',run)
    print(f'build {bid}: loading German witnesses, STEP and lexicons ({nt_edition})',flush=True)
    donors={sid:compact_rows(p) for sid,p in donor_paths.items()}
    kjv=compact_rows(kjv_path)
    inv=reference_inventory(work,nt_edition);lex,lemmas=lexicons(work);index,origins=learn(donors)
    template=load_input(edited/'01-language.xml');notes_before=original_notes(template)
    trees={name:copy.deepcopy(template) for name in ['02-baseline','03-lexicon','04-multisource']}
    verse_maps={n:dict(zef_verses(t)) for n,t in trees.items()}
    counts={n:Counter() for n in trees};review=[];primary=settings['primary']
    with jsonl_gz(work/'alignment.jsonl.gz') as audit, jsonl_gz(work/'unassigned-source.jsonl.gz') as unassigned:
        for ref,v in zef_verses(template):
            text,tokens=verse_tokens(v,ref)
            for t in tokens:
                if t['strong']:t.update(method='inherited',sources=[primary or 'custom-original'],uncertain=False)
            if primary and edition=='elb':transfer(tokens,donors[primary].get(ref,[]),primary)
            inherited={c for t in tokens for c in t['strong']}
            available=inv.get(ref,set())
            mismatch=len(inherited)>=3 and len(inherited & available)/len(inherited)<0.65
            if mismatch:review.append({'ref':ref,'kind':'verse-inventory-mismatch','inherited_codes':sorted(inherited),'step_codes':sorted(available)})
            for stage in trees:
                if stage=='03-lexicon' and not mismatch:lexical_fill(tokens,available,lex,review,ref)
                if stage=='04-multisource' and not mismatch:additional_fill(tokens,ref,available,donors,primary,index,origins,lex,review)
                annotate(verse_maps[stage][ref],tokens,hints=stage!='02-baseline')
                _,actual=verse_tokens(verse_maps[stage][ref],ref)
                for t,a in zip(tokens,actual):
                    if t['strong']!=a['strong']:
                        review.append({'ref':ref,'token':t['id'],'kind':'cross-markup-word-skipped','proposed':t['strong']})
                        t['strong']=a['strong'];t['method']='unassigned'
                    if t['strong']:counts[stage][t.get('method','inherited')]+=1
            kjv_codes={c for _,codes in kjv.get(ref,[]) for c in codes}
            assigned={c for t in tokens for c in t['strong']}
            for t in tokens:
                if t['strong']:
                    t['kjv_same_verse_support']=[c for c in t['strong'] if c in kjv_codes]
                    t['lemma_candidates']={c:lemmas[c] for c in t['strong'] if lemmas.get(c)}
                    t['source_occurrences_ref']=ref
            line(audit,{'ref':ref,'text':text,'tokens':tokens,'step_profile':nt_edition if ref.split('.')[0] in 'Matt Mark Luke John Acts Rom 1Cor 2Cor Gal Eph Phil Col 1Thess 2Thess 1Tim 2Tim Titus Phlm Heb Jas 1Pet 2Pet 1John 2John 3John Jude Rev'.split() else 'L/Q',
                        'kjv_inventory_agreement':sorted(available & kjv_codes),'inventory_mismatch':mismatch})
            missing=sorted(available-assigned)
            if missing:line(unassigned,{'ref':ref,'unassigned_strong':missing,'note':'Dictionary entries, not a count of unaligned word occurrences. No visible verse-end note.'})
    reports={}
    for stage,tree in trees.items():
        require(original_notes(tree)==notes_before,'Original note subtree changed')
        # Verify text inventory without rebuilding the verse map for each verse.
        before={r:plain(v) for r,v in zef_verses(template,True)}
        after={r:plain(v) for r,v in zef_verses(tree,True)}
        require(before==after,'Strong enrichment changed Bible text or captions')
        metadata(tree,bid,version,stage)
        path=work/(stage+'.xml');write_xml(path,tree)
        check=parse_xml(path);require(original_notes(check)==notes_before,'Serialized note preservation failed')
        reports[stage]=stats(check)|{'sha256':file_hash(path),'methods':dict(counts[stage]),'original_notes_preserved':len(notes_before),'text_preserved':True}
        write_json(work/(stage+'.report.json'),reports[stage])
    with jsonl_gz(work/'review.jsonl.gz') as f:
        for row in review:line(f,row)
    # Release the enrichment trees/indexes before loading the next full-Bible stages.
    del template,trees,verse_maps,tree,check,donors,kjv,inv,lex,lemmas,index,origins,before,after
    if confirmation:
        reports['05-reference-confirmed']=reference_confirmation_stage(work,bid,version,confirmation,nt_edition)
    if linguistic:
        # Phase 06 reparses private snapshots and checks their hashes against stage 05.
        del confirmation['references']
        reports['06-linguistic']=linguistic_validation_stage(work,bid,version,confirmation,
                                                           nt_edition,linguistic,elb_bk,elb_csv)
    write_json(work/'report.json',{'bible_id':bid,'version':version,'stages':reports,'review_items':len(review),
        'warning':('Source-linked linguistic rules review every remaining uncertainty; only independently corroborated articles are added.' if linguistic else
                   'Coverage is not accuracy. Reference confirmation removes matching uncertainty notes; it never transfers Strong assignments.' if confirmation else
                   'Coverage is not accuracy. Reference verse numbers provisionally aligned. Existing annotations retained; new candidates require review. No BK input used.'),
        'step_edition':nt_edition,'language_history':str(edited.relative_to(ROOT))})
    finalize(work,dest,settings);publish(dest,bid,version,bool(input_path),artifact=artifact)
    print(bid,reports[artifact.removesuffix('.xml')],flush=True)
    return dest


def publish(dest,bid,version,custom=False,artifact='04-multisource.xml'):
    # Public filenames stay stable; Git commits/tags identify editorial releases.
    # Immutable run directories still retain all build inputs and intermediate files.
    expected={'1.3':'05-reference-confirmed.xml','1.4':'06-linguistic.xml'}.get(version,'04-multisource.xml')
    require(artifact==expected,f'Version {version} requires the {expected} artifact')
    out=ROOT/('.local/custom-releases' if custom else 'releases')
    if custom:out=out/version
    out.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(dest/artifact,out/(bid+'.xml'))
    link={'history':str(dest.relative_to(ROOT)),'bible_id':bid,'version':version,'sha256':file_hash(out/(bid+'.xml'))}
    if artifact!='04-multisource.xml':link['artifact']=artifact
    write_json(out/(bid+'.build.json'),link)
