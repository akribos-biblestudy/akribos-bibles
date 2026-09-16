"""Offline German lemmatization and explicitly sourced lexical candidates."""
from __future__ import annotations
from collections import Counter, defaultdict
from functools import lru_cache
import json, re
from .common import tokenize, strongs
from .project import ROOT, source, jsonl_gz, line, write_json
from .importers import parse_xml, import_reference_tsv
from .modernize import spelling_key
from .kautz import load_kautz

STOP=set('der die das den dem des ein eine einer eines einem einen und oder aber denn dass daß'
         ' ich du er sie es wir ihr ihnen ihm ihn mich dich sich uns euch mein dein sein'
         ' in an auf aus bei von zu vor nach mit um für als wie so da dort hier nicht'
         ' ist sind war waren wird werden sei seiet seid bin bist habe hat haben hätte'
         ' hatte hatten alle alles auch noch nur nun schon wenn wer was wo zu'.split())

@lru_cache(maxsize=200000)
def key(text, lemma=False):
    text=spelling_key(text)
    if text in {'jehova','jehovas','herrn'}:text='herr'
    if text in {'weib','weibe','weibes'}:text='frau'
    if text in {'weiber','weibern'}:text='frauen'
    if lemma:
        import simplemma
        text=simplemma.lemmatize(text,lang='de').casefold()
    return text


def phrase_key(text):return tuple(key(t['text'],True) for t in tokenize(text))


def lexicons(out):
    index=defaultdict(lambda:defaultdict(set)); lemmas={}
    def add(phrase,code,sid):
        k=phrase_key(phrase)
        if 1<=len(k)<=5 and (len(k)>1 or (k[0] not in STOP and len(k[0])>=3)):
            index[k][code].add(sid)
    kautz=load_kautz(ROOT/source('kautz')['path'],source('kautz'))
    for f in kautz['forms']:add(f['de'],f['strong'],'kautz')
    for code,e in kautz['entries'].items():lemmas[code]=e['lemma']
    counts={'kautz':kautz['statistics']}
    del kautz
    root=parse_xml(ROOT/source('hebrew-de')['path'])
    ns={'x':'http://openscriptures.github.com/morphhb/namespace'}
    heb=0
    for e in root.findall('x:entry',ns):
        code=e.get('id','')
        if not re.fullmatch(r'H\d+',code) or not 0<int(code[1:])<=8674:continue
        word=e.find('x:w',ns)
        if word is not None:lemmas[code]=''.join(word.itertext())
        for tr in e.findall('x:translation',ns):
            if tr.get('{http://www.w3.org/XML/1998/namespace}lang')!='de':continue
            for d in tr.findall('.//x:def',ns):
                for phrase in re.split(r'[,;/]', ''.join(d.itertext())):
                    phrase=re.sub(r'\([^)]*\)','',phrase).strip(' .:')
                    phrase=re.sub(r'^(?:der|die|das|ein|eine)\s+','',phrase)
                    if re.fullmatch(r'[A-Za-zÄÖÜäöüß’\- ]+',phrase) and len(phrase.split())<=4:
                        add(phrase,code,'hebrew-de-machine');heb+=1
    for row in json.loads((ROOT/'rules/de-strong.seed.json').read_text(encoding='utf-8')):
        add(row['de'],row['strong'],'akribos-seed')
    counts['hebrew_heading_phrases']=heb;counts['indexed_phrases']=len(index)
    with jsonl_gz(out/'lexical-index.jsonl.gz') as f:
        for k,v in sorted(index.items()):
            line(f,{'de_lemmas':k,'candidates':{c:sorted(s) for c,s in sorted(v.items())}})
    write_json(out/'lexicon-report.json',counts)
    # German lookup derivatives retain Kautz and Hebrew source terms; licenses remain applicable.
    return index,lemmas


def reference_inventory(out, nt_edition):
    inv=defaultdict(set)
    profiles=json.loads((ROOT/'config/step-profiles.json').read_text(encoding='utf-8'))
    with jsonl_gz(out/'source-occurrences.jsonl.gz') as f:
        for profile in profiles:
            options=dict(profile['options'])
            if options['profile']=='tagnt':options['edition']=nt_edition
            for path in profile['paths']:
                for row in import_reference_tsv(ROOT/path,profile['id'],options):
                    for t in row['tokens']:
                        inv[row['ref']].update(s for s in t['strong'] if 0<int(s[1:])<=(8674 if s[0]=='H' else 5624))
                    line(f,row)
    return inv


def learn(donors):
    index=defaultdict(Counter);origins=defaultdict(set)
    for sid,rows in donors.items():
        for row in rows.values():
            for text,codes in row:
                k=key(text,True)
                if k in STOP or len(k)<3 or len(codes)!=1:continue
                index[k][codes[0]]+=1;origins[k,codes[0]].add(sid)
    return index,origins
