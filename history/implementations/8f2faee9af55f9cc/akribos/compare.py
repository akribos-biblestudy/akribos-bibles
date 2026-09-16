"""Read-only comparison. No reference data enters the builder or public word patches."""
from __future__ import annotations
import json, re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from .common import file_hash, require, write_json, ref_key
from .project import ROOT,identity,workspace,finalize,cached,load_input,stats,jsonl_gz,line,csv_write
from .xmlio import zef_verses,verse_tokens
from .lexical import key


def compare(input_path,reference_path,label='reference',rebuild=False,public_index=False,verse_map=None):
    a,b=Path(input_path).resolve(),Path(reference_path).resolve()
    require(a!=b,'Choose two distinct input files')
    require(re.fullmatch(r'[A-Za-z0-9_.-]+',label),'Label must be a simple filename component')
    target,reference=load_input(a),load_input(b)
    bid=target.findtext('INFORMATION/identifier') or 'bible'
    require(re.fullmatch(r'[A-Za-z0-9_.-]+',bid),'Unsafe Bible identifier')
    mapping=json.loads(Path(verse_map).read_text(encoding='utf-8')) if verse_map else {}
    require(isinstance(mapping,dict) and all(isinstance(k,str) and isinstance(v,str) for k,v in mapping.items()),'Verse map must map target refs to reference refs')
    settings={'input_sha256':file_hash(a),'reference_sha256':file_hash(b),'bible_id':bid,'label':label,
              'verse_map':mapping,'public_verse_index':public_index}
    run=identity('compare',settings)
    public=ROOT/'comparisons'/label/bid/run
    private=ROOT/'.local/comparisons'/label/bid/run
    if cached(public) and cached(private) and not rebuild:return public
    work=workspace('compare-public',run);detail=workspace('compare-private',run)
    av=dict(zef_verses(target));bv=dict(zef_verses(reference))
    require(set(mapping)<=set(av),'Verse map contains unknown target verses')
    mapped=[mapping.get(ref,ref) for ref in av]
    require(len(set(mapped))==len(mapped),'Many-to-one verse mappings require a custom versification profile')
    require(set(mapping.values())<=set(bv),'Verse map points to missing reference verse')
    totals=Counter();books=defaultdict(Counter);public_rows=[]
    with jsonl_gz(detail/'word-differences.jsonl.gz') as f:
        for ref in sorted(av,key=ref_key):
            other_ref=mapping.get(ref,ref);counts=Counter();kinds=set()
            _,at=verse_tokens(av[ref],ref)
            if other_ref not in bv:
                totals['verses_missing_in_reference']+=1
                public_rows.append({'ref':ref,'categories':'missing-reference-verse'})
                line(f,{'ref':ref,'kind':'missing-reference-verse'});continue
            _,bt=verse_tokens(bv[other_ref],other_ref)
            counts['common_verses']=1
            akeys=[key(t['text']) for t in at];bkeys=[key(t['text']) for t in bt]
            for op,i,j,k,l in SequenceMatcher(None,akeys,bkeys,autojunk=False).get_opcodes():
                if op!='equal':
                    kinds.add('text-or-tokenization')
                    counts['target_unmatched_words']+=j-i;counts['reference_unmatched_words']+=l-k
                    line(f,{'ref':ref,'reference_ref':other_ref,'kind':op,'target':at[i:j],'reference':bt[k:l]})
                    continue
                for t,u in zip(at[i:j],bt[k:l]):
                    counts['aligned_words']+=1
                    x,y=set(t['strong']),set(u['strong'])
                    if x and y:
                        counts['both_tagged_words']+=1
                        kind='identical-strong-set' if x==y else 'different-strong-set'
                    elif y:kind='only-reference-tagged'
                    elif x:kind='only-target-tagged'
                    else:kind='neither-tagged'
                    counts[kind]+=1
                    if kind in {'different-strong-set','only-reference-tagged','only-target-tagged'}:
                        kinds.add(kind)
                        line(f,{'ref':ref,'reference_ref':other_ref,'kind':kind,'target':t,'reference':u})
            totals.update(counts);books[ref.split('.')[0]].update(counts)
            if kinds:public_rows.append({'ref':ref,'categories':';'.join(sorted(kinds))})
    missing_ref=sorted(set(bv)-set(mapped),key=ref_key)
    totals['verses_missing_in_target']=len(missing_ref)
    for ref in missing_ref:public_rows.append({'ref':ref,'categories':'missing-target-verse'})
    ownstats,refstats=stats(target),stats(reference)
    report={'bible_id':bid,'reference_label':label,'input_sha256':settings['input_sha256'],'reference_sha256':settings['reference_sha256'],
            'target_coverage':ownstats,'reference_coverage':refstats,'comparison':dict(totals),
            'identical_sets_percent_of_both_tagged_aligned_words':round(100*totals['identical-strong-set']/totals['both_tagged_words'],4) if totals['both_tagged_words'] else None,
            'aligned_percent_of_target_words':round(100*totals['aligned_words']/ownstats['words'],4) if ownstats['words'] else None,
            'verses_with_differences':len(public_rows),'public_index_included':public_index,
            'method':'SequenceMatcher on explicit spelling-normalized word tokens; notes/headings excluded. Same verse identifiers unless supplied mapping. Strong sets, not semantic accuracy. Counts may be affected by source segmentation or versification.',
            'public_scope':'Only aggregate metrics and optional verse references/categories. No reference text, Strong values, token positions or reconstructive patches.',
            'reference_is_not_training_data':True}
    write_json(work/'summary.json',report)
    fields=['book']+sorted({k for row in books.values() for k in row})
    csv_write(work/'books.csv',[{'book':b,**books[b]} for b in books],fields)
    if public_index:csv_write(work/'verse-differences.csv',public_rows,['ref','categories'])
    csv_write(detail/'verse-differences.csv',public_rows,['ref','categories'])
    write_json(detail/'summary.json',report)
    (work/'README.md').write_text(f'''# Vergleich {bid} / {label}\n\nEigene Wortabdeckung: **{ownstats['word_coverage_percent']} %**.\nReferenz-Wortabdeckung: **{refstats['word_coverage_percent']} %**.\nIdentische Strong-Mengen unter beidseitig kodierten, wortgleich zugeordneten Tokens: **{report['identical_sets_percent_of_both_tagged_aligned_words']} %**.\n\nDiese Quote misst Übereinstimmung, keine fachliche Richtigkeit. Referenzdateien können Fehler, andere Verszählung und eine andere Urtextgrundlage haben.\n\n`summary.json` und `books.csv` enthalten aggregierte Messungen. Der optionale Versindex nennt nur Stellen und Abweichungsarten. Vollständige Wort-/Strong-Differenzen bleiben unter `.local/comparisons/` und gehören nicht ins öffentliche Repo. Der Vergleich verändert keine Bibeldatei und wird nicht als Anreicherungsquelle eingelesen.\n''',encoding='utf-8')
    finalize(detail,private,settings);finalize(work,public,settings)
    print(f'compare {bid}: own={ownstats["word_coverage_percent"]}%, reference={refstats["word_coverage_percent"]}%, agreement={report["identical_sets_percent_of_both_tagged_aligned_words"]}%',flush=True)
    return public
