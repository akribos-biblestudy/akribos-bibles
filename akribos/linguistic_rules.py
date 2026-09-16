"""Conservative occurrence-based rules; these functions never mutate input tokens.

Input tokens use the existing alignment JSON token shape; source tokens additionally
need word (TAGNT raw ref # component), conjoined, morph, and optional editions_raw.
Greek source lists MUST already be filtered to the chosen NT textual edition.
"""
import re
from .common import canonical_ref

ARTICLES=frozenset('der die das den dem des'.split())

# Explicit German noun paradigms; Greek gender is NOT German gender.
# Values are allowed (Strong, German gender, German number) triples.
GERMAN_HEADS={}
def _head(code,gender,number,forms):
    for form in forms.split():GERMAN_HEADS.setdefault(form,set()).add((code,gender,number))
for _args in [
 ('G2316','M','S','gott gottes'), ('G2316','M','P','götter göttern'),
 ('G3056','N','S','wort worte wortes'), ('G3056','N','P','worte worten wörter wörtern'),
 ('G5207','M','S','sohn sohnes sohns sohne'), ('G5207','M','P','söhne söhnen'),
 ('G3962','M','S','vater vaters'), ('G3962','M','P','väter vätern'),
 ('G2962','M','S','herr herrn'), ('G2962','M','P','herren'),
 ('G935','M','S','könig königs könige'), ('G935','M','P','könige königen'),
 ('G4172','F','S','stadt'), ('G4172','F','P','städte städten'),
 ('G1093','F','S','erde erden'), ('G740','N','S','brot brotes brots brote'),
 ('G740','N','P','brote broten'), ('G2281','N','S','meer meeres meere'),
 ('G2281','N','P','meere meeren'), ('G444','M','S','mensch menschen'),
 ('G444','M','P','menschen'), ('G2992','N','S','volk volkes volke'),
 ('G2992','N','P','völker völkern'), ('G26','F','S','liebe'),
 ('G4102','M','S','glaube glaubens glauben'), ('G1680','F','S','hoffnung'),
 ('G932','N','S','reich reiches reiche'), ('G932','N','P','reiche reichen'),
 ('G2222','N','S','leben lebens'),
 # Additional explicit German paradigms; lexical evidence: rules/greek-article-heads.evidence.json.
 ('G4151', 'M', 'S', 'geist geistes geists geiste'),
 ('G4151', 'M', 'P', 'geister geistern'),
 ('G2250', 'M', 'S', 'tag tages tags tage'),
 ('G2250', 'M', 'P', 'tage tagen'),
 ('G3571', 'F', 'S', 'nacht'),
 ('G3571', 'F', 'P', 'nächte nächten'),
 ('G32', 'M', 'S', 'engel engels'),
 ('G32', 'M', 'P', 'engel engeln'),
 ('G3772', 'M', 'S', 'himmel himmels'),
 ('G3772', 'M', 'P', 'himmel himmeln'),
 ('G2288', 'M', 'S', 'tod todes tods tode'),
 ('G2288', 'M', 'P', 'tode toden'),
 ('G2889', 'F', 'S', 'welt'),
 ('G2889', 'F', 'P', 'welten'),
 ('G266', 'F', 'S', 'sünde'),
 ('G266', 'F', 'P', 'sünden'),
 ('G5485', 'F', 'S', 'gnade'),
 ('G5485', 'F', 'P', 'gnaden'),
 ('G3101', 'M', 'S', 'jünger jüngers'),
 ('G3101', 'M', 'P', 'jünger jüngern'),
 ('G652', 'M', 'S', 'apostel apostels'),
 ('G652', 'M', 'P', 'apostel aposteln'),
 ('G80', 'M', 'S', 'bruder bruders'),
 ('G80', 'M', 'P', 'brüder brüdern'),
 ('G1135', 'F', 'S', 'frau'),
 ('G1135', 'F', 'P', 'frauen'),
 ('G5043', 'N', 'S', 'kind kindes kinds kinde'),
 ('G5043', 'N', 'P', 'kinder kindern'),
 ('G1411', 'F', 'S', 'macht'),
 ('G1411', 'F', 'P', 'mächte mächten'),
 ('G1411', 'F', 'S', 'kraft'),
 ('G1411', 'F', 'P', 'kräfte kräften'),
 ('G1391', 'F', 'S', 'herrlichkeit'),
 ('G1391', 'F', 'P', 'herrlichkeiten'),
 ('G225', 'F', 'S', 'wahrheit'),
 ('G225', 'F', 'P', 'wahrheiten'),
 ('G3551', 'N', 'S', 'gesetz gesetzes gesetze'),
 ('G3551', 'N', 'P', 'gesetze gesetzen'),
 ('G4983', 'M', 'S', 'leib leibes leibs leibe'),
 ('G4983', 'M', 'P', 'leiber leibern'),
 ('G4983', 'M', 'S', 'körper körpers'),
 ('G4983', 'M', 'P', 'körper körpern'),
 ('G129', 'N', 'S', 'blut blutes bluts blute'),
 ('G4561', 'N', 'S', 'fleisch fleisches fleischs fleische'),
 ('G5590', 'F', 'S', 'seele'),
 ('G5590', 'F', 'P', 'seelen'),
 ('G2588', 'N', 'S', 'herz herzens herzen'),
 ('G2588', 'N', 'P', 'herzen'),
 ('G3788', 'N', 'S', 'auge auges'),
 ('G3788', 'N', 'P', 'augen'),
 ('G5495', 'F', 'S', 'hand'),
 ('G5495', 'F', 'P', 'hände händen'),
 ('G4228', 'M', 'S', 'fuß fußes fuße'),
 ('G4228', 'M', 'P', 'füße füßen'),
 ('G4750', 'M', 'S', 'mund mundes munds munde'),
 ('G4750', 'M', 'P', 'münder mündern'),
 ('G3775', 'N', 'S', 'ohr ohres ohrs ohre'),
 ('G3775', 'N', 'P', 'ohren'),
 ('G3624', 'N', 'S', 'haus hauses hause'),
 ('G3624', 'N', 'P', 'häuser häusern'),
 ('G3485', 'M', 'S', 'tempel tempels'),
 ('G3485', 'M', 'P', 'tempel tempeln'),
 ('G4335', 'N', 'S', 'gebet gebetes gebets gebete'),
 ('G4335', 'N', 'P', 'gebete gebeten'),
 ('G2307', 'M', 'S', 'wille willens willen'),
 ('G2307', 'M', 'P', 'willen'),
 ('G5457', 'N', 'S', 'licht lichtes lichts lichte'),
 ('G5457', 'N', 'P', 'lichter lichtern'),
 ('G4655', 'F', 'S', 'finsternis'),
 ('G4655', 'F', 'P', 'finsternisse finsternissen'),
 ('G2440', 'N', 'S', 'kleid kleides kleids kleide'),
 ('G2440', 'N', 'P', 'kleider kleidern'),
 ('G4166', 'M', 'S', 'hirte hirten'),
 ('G4166', 'M', 'P', 'hirten'),
 ('G3144', 'M', 'S', 'zeuge zeugen'),
 ('G3144', 'M', 'P', 'zeugen'),
 ('G749', 'M', 'S', 'hohepriester hohepriesters hohenpriester hohenpriesters'),
 ('G749', 'M', 'P', 'hohepriester hohenpriester hohepriestern hohenpriestern'),
 ('G1401', 'M', 'S', 'knecht knechtes knechts knechte'),
 ('G1401', 'M', 'P', 'knechte knechten'),
 ('G1401', 'M', 'S', 'sklave sklaven'),
 ('G1401', 'M', 'P', 'sklaven'),
]:_head(*_args)
GERMAN_PREPOSITIONS=set('an auf aus außer bei bis durch für gegen hinter in mit nach neben ohne seit statt trotz über um unter von vor wegen wider zu zwischen'.split())

ARTICLE_FORMS={('M','S'):set('der den dem des'.split()),
 ('F','S'):set('die der'.split()),('N','S'):set('das dem des'.split()),
 ('M','P'):set('die der den'.split()),('F','P'):set('die der den'.split()),
 ('N','P'):set('die der den'.split())}

def selected_verse_has_movement(source):
    for s in source:
        if re.search(r'[\[({]',s.get('origin_id','').split('#')[0]):return True
        raw=s.get('editions_raw','')
        edition=s.get('edition')
        if 'moved' in raw:return True  # older exports
        if edition:
            if re.search(r'(?:^|[^A-Za-z0-9])'+re.escape(edition)+r'[«»]',raw):return True
        elif '«' in raw or '»' in raw:return True
    return False

# Atomic lexemes only; composites and repeated phrases never enter this rule.
ATOMIC={
 'G2532':({'und'},{'CONJ'}), 'G2228':({'oder'},{'CONJ'}),
 'G235':({'sondern'},{'CONJ'}), 'G1161':({'aber'},{'CONJ'}),
 'G1063':({'denn'},{'CONJ'}), 'G3754':({'dass','daß'},{'CONJ'}),
 'G3756':({'nicht'},{'PRT-N'}), 'G3361':({'nicht'},{'PRT-N'}),
 'G3761':({'weder','noch'},{'CONJ-N'}), 'G3777':({'weder','noch'},{'CONJ-N'}),
 'H3808':({'nicht'},{'HTn'}), 'H408':({'nicht'},{'HTn'}),
 'H3588':({'denn','weil','dass','daß'},{'HTc'}), 'H176':({'oder'},{'HC'}),
 'H1571':({'auch'},{'HD'}), 'H413':({'zu'},{'HR'}),
 'H4480':({'von','aus'},{'HR'}), 'H5921':({'auf','über'},{'HR'}),
}
HEBREW_NOUNS={
 'H430':set('gott gottes götter göttern'.split()),
 'H1121':set('sohn sohns sohnes sohne söhne söhnen'.split()),
 'H1':set('vater vaters väter vätern'.split()),
 'H1697':set('wort wortes worte worten wörter wörtern sache sachen'.split()),
 'H776':set('erde erden land landes lande länder ländern'.split()),
 'H8064':set('himmel himmels himmeln'.split()),
 'H4428':set('könig königs könige königen'.split()),
}


def unique_anchor(tokens,index,source):
    t=tokens[index]
    if t.get('uncertain') or not t.get('anchor_eligible',True) or len(t.get('strong',[]))!=1:return None
    code=t['strong'][0]
    if sum(code in x.get('strong',[]) for x in tokens)!=1:return None
    hits=[j for j,s in enumerate(source) if code in s.get('strong',[])]
    return hits[0] if len(hits)==1 and source[hits[0]].get('strong')==[code] else None


def linked_article_proof(text,tokens,index,source):
    """Accept a strict local translation pattern, not German word identity alone.

    Pattern: same unique confirmed left anchor + article + unique confirmed noun,
    contiguous in both languages; alternatively article+noun begin both verses.
    Explicit STEP article→head link and Greek morph agreement are mandatory.
    German/Greek case and gender can differ, so they are never compared directly.
    """
    current=tokens[index]
    if selected_verse_has_movement(source):return None
    if current['text'].casefold() not in ARTICLES or current.get('blocked',False):return None
    if current.get('strong') not in ([],['G3588']):return None
    if index+1>=len(tokens):return None
    hi=unique_anchor(tokens,index+1,source)
    if hi is None or hi==0:return None
    head=tokens[index+1];source_head=source[hi];article=source[hi-1]
    # 'Da das Jesus hörte' has a German object pronoun, not an article of Jesus.
    # Require a known German noun form and its German gender/number paradigm.
    if not head['text'][:1].isupper():return None
    if any(part.startswith('P') for part in source_head.get('morph','').split('-')[2:]):return None
    senses=GERMAN_HEADS.get(head['text'].casefold(),set())
    if not any(code==head['strong'][0] and number==source_head.get('morph','')[3:4]
               and current['text'].casefold() in ARTICLE_FORMS[gender,number]
               for code,gender,number in senses):return None
    if text[current['end']:head['start']].strip():return None
    if article.get('strong')!=['G3588']:return None
    if not re.fullmatch(r'T-[NGDAV][SPD][MFN]',article.get('morph','')):return None
    if not re.fullmatch(r'N-[NGDAV][SPD][MFN](?:-[A-Z]+)?',source_head.get('morph','')):return None
    if article['morph'][2:5]!=source_head['morph'][2:5]:return None
    code=head['strong'][0]
    links=re.findall(r'[»«](\d+):G0*(\d+)',article.get('conjoined',''))
    if (source_head.get('word',''),code[1:]) not in links:return None
    # No speculative interpretation of displaced order within textual editions.
    if any('moved' in s.get('editions_raw','') for s in (article,source_head)):return None
    if index==0:
        if hi!=1 or text[:current['start']].strip(' \t\n\"„“‚‘\''):return None
        left=None
    else:
        left=unique_anchor(tokens,index-1,source)
        if left is None or left!=hi-2:return None
        left_morph=source[left].get('morph','')
        if tokens[index-1]['text'].casefold() in GERMAN_PREPOSITIONS and left_morph!='PREP':return None
        if re.match(r'^(?:P|R|D|I|X)-',left_morph):return None
        if text[tokens[index-1]['end']:current['start']].strip():return None
        if 'moved' in source[left].get('editions_raw',''):return None
    return {'rule':'greek-article-linked-noun-with-left-anchor',
            'source_article':article['origin_id'],'source_head':source_head['origin_id'],
            'source_left':None if left is None else source[left]['origin_id'],
            'head_strong':code,'article_morph':article['morph'],'head_morph':source_head['morph']}


def atomic_bridge_proof(text,tokens,index,source):
    """Unique content/function word between two independently trusted anchors.

    Confirms an existing candidate only. Explicit semantic whitelist + exact
    source POS + two-sided occurrence alignment are all required. No H900x,
    suffixes, multiword expressions, or newly inferred anchors are consumed.
    """
    if index==0 or index+1>=len(tokens) or selected_verse_has_movement(source):return None
    token=tokens[index]
    if token.get('blocked',False) or len(token.get('strong',[]))!=1 or token.get('phrase_tokens',1)!=1:return None
    code=token['strong'][0];word=token['text'].casefold()
    if sum(code in t.get('strong',[]) for t in tokens)!=1:return None
    positions=[j for j,s in enumerate(source) if code in s.get('strong',[])]
    if len(positions)!=1:return None
    pos=positions[0];s=source[pos]
    if s.get('strong')!=[code]:return None
    if pos==0 or pos+1>=len(source):return None
    left=unique_anchor(tokens,index-1,source);right=unique_anchor(tokens,index+1,source)
    if left!=pos-1 or right!=pos+1:return None
    if text[tokens[index-1]['end']:token['start']].strip():return None
    if text[token['end']:tokens[index+1]['start']].strip():return None
    morph=s.get('morph','')
    if code in ATOMIC:
        forms,morphs=ATOMIC[code]
        if word not in forms or morph not in morphs:return None
        rule='atomic-function-word-between-confirmed-anchors'
    elif code in HEBREW_NOUNS:
        if word not in HEBREW_NOUNS[code] or not token['text'][:1].isupper():return None
        if not re.fullmatch(r'HN[cgp][mfbc][spd][acd]',morph):return None
        rule='hebrew-atomic-noun-between-confirmed-anchors'
    elif code=='H3068':
        if token['text'] not in {'HERR','HERRN'} or morph!='HNpt':return None
        rule='hebrew-divine-name-between-confirmed-anchors'
    else:return None
    return {'rule':rule,'source_token':s['origin_id'],'source_left':source[left]['origin_id'],
            'source_right':source[right]['origin_id'],'strong':code,'morph':morph}


def classify_uncertain(ref,text,tokens,source,inventory_mismatch=False):
    """Account for every uncertain assignment without inferring lexical errors.

    A source inventory proves availability, never the translation alignment.
    Absence of a code is missing evidence, not a proven lexical contradiction:
    sources can encode a lemma and its inflected forms under different numbers.
    Existing spans may share one Strong across several German words, so repeated
    German tags are a review category, not a count-based automatic rejection.
    """
    out=[]
    inventory={c for s in source for c in s.get('strong',[])}
    aliases={c for s in source for c in s.get('alternate',[])}
    used_articles=set()
    for i,t in enumerate(tokens):
        if not t.get('uncertain') or not t.get('strong'):continue
        row={'ref':ref,'token':t['id'],'before':t['strong'],'text':t['text']}
        if inventory_mismatch:status,reason='review','verse-reference-mismatch'
        elif not source:status,reason='review','missing-reference-verse'
        elif selected_verse_has_movement(source):status,reason='review','source-order-or-versification-variation'
        elif not set(t['strong'])<=inventory:
            status,reason='review',('alternate-strong-encoding' if set(t['strong'])<=(inventory|aliases)
                                    else 'code-absent-in-selected-source')
        elif (proof:=linked_article_proof(text,tokens,i,source)) and proof['source_article'] not in used_articles:
            status,reason='accepted',proof['rule'];row['proof']=proof
            used_articles.add(proof['source_article'])
        elif (proof:=atomic_bridge_proof(text,tokens,i,source)):
            status,reason='accepted',proof['rule'];row['proof']=proof
        elif len(t['strong'])>1:status,reason='review','multi-code-translation-span'
        elif sum(t['strong'][0] in s.get('strong',[]) for s in source)>1:status,reason='review','repeated-source-lexeme'
        elif sum(t['strong'][0] in x.get('strong',[]) for x in tokens)>1:status,reason='review','shared-german-translation-span'
        else:status,reason='review','alignment-needs-semantic-evidence'
        out.append(row|{'status':status,'reason':reason})
    return out


def _source_shape_problem(source, nt_edition, is_nt, expected_ref):
    """Malformed/mixed fixtures and unsupported source mixtures cannot be evidence."""
    seen = set()
    for token in source:
        origin = token.get('origin_id')
        if not origin or origin in seen:
            return 'duplicate-or-missing-source-occurrence-id'
        seen.add(origin)
        match = re.match(r'^([1-3]?[A-Za-z]+\.\d+\.\d+)', origin)
        if not match:
            return 'invalid-source-verse-reference'
        try:
            actual_ref = canonical_ref(match[1])
        except ValueError:
            return 'invalid-source-verse-reference'
        if actual_ref != expected_ref:
            return 'source-occurrence-belongs-to-other-verse'
        edition = token.get('edition')
        if is_nt and edition not in (None, '', nt_edition):
            return 'wrong-selected-nt-edition'
        if not is_nt and '=' in origin and not origin.split('=', 1)[1].startswith(('L', 'Q')):
            return 'unsupported-hebrew-witness'
    return None
