"""Deterministic language editing; all changes use guarded character offsets."""
from __future__ import annotations
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from .common import require, file_hash, write_json, atomic_text
from .importers import parse_xml
from .xmlio import (plain, zef_verses, apply_edits, normalize_gr, note_fingerprints,
                    strong_fingerprints, write_xml)

WORD = re.compile(r'[^\W\d_]+', re.UNICODE)
ROOT = Path(__file__).resolve().parents[1]
NOUNS = {'weib':'Frau','weibe':'Frau','weibes':'Frau','weiber':'Frauen','weibern':'Frauen',
         'eheweib':'Ehefrau','eheweibe':'Ehefrau','eheweibes':'Ehefrau',
         'eheweiber':'Ehefrauen','eheweibern':'Ehefrauen'}
CONTRACTIONS = {'zum':'zur','beim':'bei der','vom':'von der','im':'in der',
                'ins':'in die','ans':'an die','aufs':'auf die','fürs':'für die','durchs':'durch die'}
ADJECTIVES = set('alt jung schön hässlich häßlich gut bös fremd ehebrecherisch klug weis'
                 ' zänkisch fromm verständig vernünftig unfruchtbar schwanger verstoßen'
                 ' verlassen geliebt gehasst gehaßt lieb tugendhaft lebendig tot rein unrein'
                 ' hebräisch ägyptisch israelitisch kanaanitisch midianitisch kuschitisch'
                 ' moabitisch ammonitisch hethitisch jerusalemisch störrisch beständig'
                 ' ander selbig eigen jedwed säugend erschlagen ermordet wacker gewiss'
                 ' tekoitisch wohlhabend hurerisch anmutig unleidlich betrübt kananäisch'
                 ' kanaanäisch verlobt samaritisch gläubig verheiratet ungläubig jüdisch'
                 ' los wild töricht zornig griechisch vertraut gottesfürchtig buhlerisch'.split())

DAT_PREPS={'mit','bei','zu','von','aus','nach','außer','gegenüber','entgegen','gemäß','seit'}
ACC_PREPS={'für','durch','gegen','ohne','um','wider'}
NOM_BEFORE={'spricht','sprach','redete','antwortete','gebot'}
FINITE_AFTER=set('ist war wird wurde hat hatte sprach spricht redet redete gebot gebietet'
                 ' kam kommt ging geht hörte hört sah sieht tat tut machte macht sandte sendet'
                 ' antwortete antwortet schlug schlägt errettete errettet rettet richtete richtet'
                 ' gedenkt gedachte segnete segnet gab gibt nahm nimmt ließ lässt verwarf verwirft'
                 ' erweckte erweckt erhob erhebt schuf schafft tötet tötete macht nimmt regiert'
                 ' behütet bewahrt lässt hört kennt weiß vermag wohnt thronte thront'
                 ' bildete pflanzte baute rief ruft schickte schickt blickte blickt schloss schließt'
                 ' roch riecht fuhr fährt zerstreute zerstreut erschien erscheint will wollte'
                 ' verhärtete verhärtet lebt lebte hilft half segne richte füge sei stehe sehe'
                 ' stand steht gelobt gelobte befahl befiehlt vernichtete vernichtet verhieß'
                 ' gereut geredet geboten geheißen befohlen gesegnet bestimmt gegeben'.split())
HUMAN_SUBJECTS=set('ich du er sie wir ihr mose david samuel salomo josua israel aaron '
                   'abraham isaak jakob abram saul elia elisa hiskia hanna man volk knecht männer'.split())
DAT_VERBS=re.compile(r'(?:dien|dank|vertrau|gehorch|folg|glaub|lobsing|sing|opfer|huldig|zujubel|jauchz)(?:e|en|n|et|t|te|ten|test|tet|st|est)?')
ACC_VERBS=re.compile(r'(?:fürcht|lob|preis|lieb|such|befrag|ehr|veracht|verlass|versuch|verspott|kenn|erkenn|rühm|hass|anruf|schau|schmäh|reiz)(?:e|en|n|et|t|te|ten|test|tet|ete|eten|etest|etet|st|est)?')
SUBORDINATORS={'dass','daß','weil','wenn','ob','damit','nachdem','bevor','wie','was','welches','welche','welchen','welchem','wo','womit','denen'}
SUBJECT_AUX={'hat','hatte','wird','wurde','war','ist','sei','sind','soll','sollte','möge','ließ','erschien','sandte','fiel','verwirrte','machte','half'}
IMPERATIVE_ADDRESS={'höre','erhöre','rette','hilf','gedenke','erwache','sieh','vergib','schaffe','bewahre','befreie','belebe','neige','laß','lass','wende','vernimm'}
FINITE_AFTER={word.casefold() for word in FINITE_AFTER}

# Attested third-person forms, including wishes ("der HERR gebe ...").
# Do not infer person from an -e/-t suffix: "ich lobe" / "ihr lobt" are objects.
SUBJECT_FORMS=set('suchte bestimmte führte wandte zog trieb streitet stürzte wies stieg'
    ' lasse erhebe gebe vergelte mache tue erweise räche bestätige schelte'
    ' legte vertilgte ergrimmte erhörte stritt stärkte verlieh offenbarte donnerte'
    ' salbte liebte erhellt schaffte vergalt erstattete erwies zeugte erforscht'
    ' befestigte demütigte wendete mehrte prüft zerbricht erschüttert erlöst'
    ' liebt löst öffnet baut hält hasst besaß lenkt zürnt erleuchtet leert tritt'
    ' streckt tröstet zieht erinnert streckte rechtet konnte zerstört betrübt'
    ' brüllt bestellte stellt merkte ward soll möge hätte'.split())
CASE_ADVERBS=r'(?:(?:auch|noch|nur|nicht|mehr|völlig|allein|wiederum|doch|stets)\s+)*'
DAT_OBJECT_FORMS=set('dienen dient dienet dienten gedient danken dankt danket dankte'
    ' vertrauen vertraut gehorchen gehorcht folgen folget folgte nachfolgen nachfolget'
    ' nachgefolgt nachwandeln nachzuwandeln glauben glaubt glaubet geglaubt'
    ' lobsingen singen singet opfern opfert opferten geopfert huldigen jauchzen'
    ' zujubeln darbringen darbringt darzubringen geben gebet gibt gegeben bringen opferte'
    ' geliehen leihen geloben gelobt heiligen heiligt geheiligt weihen geweiht'.split())
ACC_OBJECT_FORMS=set('fürchten fürchtet fürchtete gefürchtet loben lobt lobet lobten'
    ' preisen preist preiset priesen lieben liebt liebet suchen sucht suchet gesucht'
    ' befragen befragt befragte ehren ehrt verachten verachtet verlassen verlasst'
    ' verlasset verließen versuchen versucht versuchet verspotten kennen kennt'
    ' kannte kannten erkennen erkennt rühmen rühmt hassen hasst anrufen angerufen'
    ' bitten bittet gebeten anflehen angefleht anzuflehen anbeten anzubeten reizten'.split())


def contextual_name_case(left, right):
    """Additional explicit constructions; return None when case is ambiguous.

    Only inspect the surrounding clause, never a verb in the next sentence.
    Relative clauses and second-person addresses must remain distinguishable.
    """
    clause=re.split(r'[,;:.!?]',left)[-1].strip(' \t\n„“"»«').casefold()
    tail=re.split(r'[,;:.!?]',right)[0].strip().casefold()
    before=re.findall(r'[^\W\d_]+',clause)
    after=[spelling_key(m[0]) for m in WORD.finditer(tail)]
    # An existing title already carries the article ("der Herr Jehova").
    if re.search(r'\bHerrn\s+$',left):
        return 'HERRN','existing-oblique-title'
    if re.search(r'\bHerr\s*,?\s*$',left):
        return 'HERR','existing-title'
    if re.match(r'\s*,\s*der\s+du\b',right,re.I):
        return 'HERR','direct-address-relative'
    if re.match(r'\s*,\s*sei\b',right,re.I):
        return 'HERR','direct-address-sei'
    if re.search(r'\b(?:rede|sprich|rette|hilf|erhöre|höre|gedenke|erwache|vergib)\s*,?\s*$',left,re.I) or re.search(r'\b(?:stehe auf|kehre wieder)\s*,\s*$',left,re.I):
        return 'HERR','direct-address-imperative-phrase'
    if re.match(r'\s*(?:,\s*Gott\s+[^!;:.?]+|der Heerscharen)\s*!',right,re.I):
        return 'HERR','direct-address-title'
    if re.match(r'\s*,\s*Gott\s+[^,;:.!?]+,\s*(?:tue|höre|gedenke|rette)\b',right,re.I):
        return 'HERR','direct-address-title-imperative'
    # Psalm 24 answers a title question with two verbless nominative clauses.
    # Without the actual preceding question the same words may be an address.
    title_question=re.search(r'\bWer ist (?:er, dieser |dieser )König der Herrlichkeit\?\s*(.*)$',left,re.I)
    if title_question and (not title_question[1].strip() or
            re.fullmatch(r'Jehova,\s*stark und mächtig!\s*',title_question[1],re.I)):
        if re.match(r'\s*,\s*(?:stark und mächtig|mächtig im Kampf)!',right,re.I) or \
                re.match(r'\s+der Heerscharen,\s*er ist der König der Herrlichkeit\b',right,re.I):
            return 'der HERR','nominative-answer-to-title-question'
    if before and before[-1]=='ich' and re.match(r'\s*(?:,\s*[^,;:.!?]+,\s*)?bin\b',right,re.I):
        return 'der HERR','predicate-name-subordinate'
    if before and before[-1]=='du' and after[:1]==['bist']:
        return 'der HERR','predicate-name-subordinate'
    if re.search(r'\bes\s*$',clause) and after[:1] in (['reut'],['reute'],['gereut']):
        return 'den HERRN','accusative-impersonal-regret'
    if (before and before[-1] in {'gehört','gehören'}) or (after[:1]==['gehört'] and not (set(after[1:])&{'hat','hatte','habe','hätte'})):
        return 'dem HERRN','dative-belonging'
    if re.match(r'\s+(?:heilig\s+(?:sein|sei)|zum Preise|zu Hilfe|ein Gelübde)\b',right):
        return 'dem HERRN','dative-dedication'
    if re.match(r'\s+geheiligt\s+(?:waren|sind|worden)\b',right):
        return 'dem HERRN','dative-consecration'
    if re.match(r'\s+einen Altar zu bauen\b',right):
        return 'dem HERRN','dative-altar-infinitive'
    if re.match(r'\s+(?:die\s+)?(?:Ehre|Herrlichkeit)\s+geben\b',right):
        return 'dem HERRN','dative-give-honor'
    # Infinitive "um ... zu" does not make the name an accusative object.
    first_object=re.split(r'\bund\b',tail)[0]
    if (set(before)&(HUMAN_SUBJECTS|{'philister','welcher','sollt'}) or 'um' in before) and re.search(r'\b(?:\w*opfer\w*|altar|gelübde)\b',first_object) and re.search(r'\b(?:dar\w*|opfern|erstatte\w*|bauen|geben|bringen|tun|heben)\b',first_object):
        return 'dem HERRN','dative-offering-recipient'
    object_tail=re.sub(r'^'+CASE_ADVERBS+r'(?:zu\s+)?','',tail)
    object_word=spelling_key(object_tail.split()[0]) if object_tail else ''
    human_before=bool(set(before)&(HUMAN_SUBJECTS|{'man'}))
    if object_word in DAT_OBJECT_FORMS and (human_before or object_tail.startswith(('geliehen','nachgefolgt','nachzuwandeln')) or re.match(r'\s+zu\s+',right)):
        return 'dem HERRN','dative-object-after-subject'
    if object_word in ACC_OBJECT_FORMS and (human_before or re.match(r'\s+zu\s+',right)):
        return 'den HERRN','accusative-object-after-subject'
    if human_before and re.match(r'\s+für\s+(?:mich|dich|ihn|sie|uns|euch)\s+bitten\b',right):
        return 'den HERRN','accusative-intercession'
    if re.search(r'\b(?:bet\w*|flehte)\b',clause) and re.match(r'\s+an\b',right):
        return 'den HERRN','accusative-separable-anbeten'
    if re.search(r'\bwehklagt\w*\s*$',clause) and after[:1]==['nach']:
        return 'dem HERRN','dative-separable-nachwehklagen'
    if human_before and (set(before)&{'kannte','kannten','verließen','priesen','erzürntet','erzürnte','befragte','befragten','nannte'} or any(ACC_VERBS.fullmatch(w) for w in before)):
        return 'den HERRN','accusative-separated-verb'
    if human_before and (set(before)&{'sangen','singen','opfere','opferte','opfern'}) and not set(before)&{'anbeten','anzubeten'}:
        return 'dem HERRN','dative-separated-verb'
    if human_before and before[-1] in {'gebe','gibt','gab','geben','gaben'}:
        return 'dem HERRN','dative-give-recipient'
    if not human_before and re.search(r'\b(?:so\s+)?(?:tue|täte|fordere|vergelte|gebe|sei|mache|erweise|lasse|bestelle|spreche|wolle|möge)(?:\s+(?:es|mir|dir|ihm|uns|euch|ihnen|mich|dich|denn|nun|doch|heute))*\s*$',clause):
        return 'der HERR','subject-wish-inversion'
    if re.search(r'\b(?:hat|hatte|hätte|wird|wurde|ward|ließ|gab|sprach|antwortete|hilft|half|rief|rettete|schlug|führte|segnete|tötete|tat|enthüllte|treibt|zürnte|sonderte|leitete|donnerte|bringt|öffnete|begann|verwarf|kehrte|erzürnte)(?:\s+(?:mir|dir|ihm|uns|euch|ihnen|mich|dich|es|denn|nun|auch))*\s*$',clause) and not human_before:
        return 'der HERR','subject-inversion'
    if re.search(r'\bes\s+gereute\s*$',clause):
        return 'den HERRN','accusative-impersonal-regret'
    if after and after[0] in SUBJECT_FORMS and not human_before:
        return 'der HERR','subject-attested-finite-verb'
    # "die ... suchen" has a plural subject; the singular divine name is
    # its object. Singular "das ... kannte" is ambiguous without an antecedent.
    if before and before[-1] in {'die','das','welche','welches'} and object_word in ACC_OBJECT_FORMS:
        if before[-1] in {'die','welche'} and object_word.endswith('en'):
            return 'den HERRN','accusative-relative-plural'
        return None
    if re.search(r'\b(?:da|als|indem|bis|das|die|wohin|seitdem|soweit|wenn nicht)\s*$',clause) and not human_before and not (set(after[:3])&{'ich','du','wir','ihr'}):
        return 'der HERR','subject-relative-or-subordinate'
    # Nominative appositions only when the resumed clause identifies a subject.
    apposition=re.match(r'\s*,\s*(?:der|mein|dein|sein|ihr|unser|euer)\s+Gott\b[^,;:.!?]*,\s*(.*)',right,re.I)
    if apposition:
        resumed=[spelling_key(m[0]) for m in WORD.finditer(re.split(r'[,;:.!?]',apposition[1])[0])]
        if re.match(r'es sei\b',apposition[1],re.I) and any(w.startswith('dein') for w in resumed):
            return 'HERR','direct-address-God-apposition'
        if not human_before and (set(resumed[:4])&(FINITE_AFTER|SUBJECT_FORMS|{'er','versucht','versuchte'})) and not (set(resumed[:2])&{'ich','du','wir','ihr'}):
            return 'der HERR','subject-with-God-apposition'
    if clause in {'','und','aber','denn','und nun','siehe','und siehe'}:
        if re.match(r'\s*,\s*(?:der\s+(?!du\b)|dessen\b|vor dessen\b)',right,re.I):
            return 'der HERR','subject-with-relative-clause'
        if re.match(r'\s*[-–—]\s*es\b',right):
            return 'der HERR','subject-left-dislocation'
        if re.match(r'\s*,\s*er\s+(?:ist|wird)\b',right):
            return 'der HERR','subject-resumed-pronoun'
    if re.match(r'\s+der Heerscharen\s+(?:ist|war|lebt)\b',right):
        return 'der HERR','subject-Lord-of-hosts'
    return None


def divine_name(text, words, i):
    """Return replacement, explicit case rule, and optional review reason.

    Word order alone is not a general German case parser. Each accepted rule
    has a visible grammatical cue; unclassified occurrences stay in the queue.
    """
    token=words[i];w=token[0].lower()
    left=text[:token.start()];right=text[token.end():]
    previous=words[i-1][0].lower() if i and text[words[i-1].end():token.start()].isspace() else ''
    following=[spelling_key(m[0]) for m in words[i+1:i+7]]
    clause=re.split(r'[,;:.!?]',left)[-1].lower()
    recent=re.findall(r'[^\W\d_]+',clause)[-7:]
    replacement,reason='HERR','unresolved-case'
    review='Subjekt/Objekt/Anrede ohne eindeutiges Regelsignal; Artikel und Kasus prüfen.'
    if w=='jehovas':
        replacement='HERRN' if previous=='des' else 'des HERRN';reason='genitive';review=None
    elif previous in {'dem','den','des'}:
        replacement='HERRN';reason='existing-oblique-article';review=None
    elif previous=='der':
        replacement='HERR';reason='existing-nominative-article';review=None
    elif previous in DAT_PREPS:
        replacement='dem HERRN';reason='dative-preposition';review=None
    elif previous=='um' and (context_case:=contextual_name_case(left,right)) and context_case[0]=='dem HERRN':
        replacement,reason=context_case;review=None
    elif previous in ACC_PREPS:
        replacement='den HERRN';reason='accusative-preposition';review=None
    elif previous=='in':
        replacement='dem HERRN';reason='dative-in-Lord';review=None
    elif previous=='vor':
        # In the fixed Biblical phrase "vor Jehova", presence before God is
        # locative. Directional uses of "vor" outside this phrase are not changed.
        replacement='dem HERRN';reason='presence-before-Lord';review=None
    elif previous in {'auf','an','über'}:
        if previous=='an' and any(x in {'hängt','hängen','hing','hingen','hänget'} for x in recent):
            replacement='dem HERRN';reason='dative-haengen-an';review=None
        elif previous=='auf' and any(x in {'vertrauen','vertraue','vertraut','vertraute','vertrauet','hoffen','hoffe','hofft','harrt','harren','harrte','verlassen','verlässt'} for x in recent):
            replacement='den HERRN';reason='accusative-trust-in';review=None
        elif previous=='an' and any(x in {'glauben','glaube','glaubt','glaubte','glaubet','halten','hält','hielt'} for x in recent):
            replacement='den HERRN';reason='accusative-believe-in';review=None
        elif previous=='auf' and (any(x in {'richtet','richten','richte','gerichtet','harre','harret','harrten'} for x in recent) or re.match(r'\s*(?:,\s*[^,]+,)?\s*(?:harren|hoffen|vertrauen|vertröste|vertraut)\b',right,re.I)):
            replacement='den HERRN';reason='accusative-reliance-on';review=None
        elif previous=='an' and ('teil' in recent or 'glaubten' in recent):
            replacement='dem HERRN' if 'teil' in recent else 'den HERRN';reason='preposition-an-context';review=None
    # "dein Gott" names the God of the person being addressed; it does not
    # address God. Its inflection identifies the name's case even when a
    # second-person subject immediately precedes it ("bist du Jehova, deinem
    # Gott"). Other possessive phrases, e.g. "deinen Weg", remain addresses.
    elif re.match(r'\s*,\s*deinem\s+(?:Gott|Erlöser|Erbarmer|Herrn)\b',right,re.I):
        replacement='dem HERRN';reason='dative-second-person-title';review=None
    elif re.match(r'\s*,\s*deinen\s+(?:Gott|Erlöser|Erbarmer|Herrn)\b',right,re.I):
        replacement='den HERRN';reason='accusative-second-person-title';review=None
    elif re.match(r'\s*,\s*dein\s+(?:Gott|Erlöser|Erbarmer|Herr)\b',right,re.I):
        replacement='der HERR';reason='nominative-second-person-title';review=None
    # In a reporting clause, the following "du" belongs to the quotation:
    # "spricht Jehova, du wirst ...", not an address to the divine name.
    elif previous in NOM_BEFORE and not (set(recent[:-1])&HUMAN_SUBJECTS):
        replacement='der HERR';reason='subject-after-speech-verb';review=None
    elif re.search(r'\b(?:vergeltet\s+ihr|vergelten\s+wir)(?:\s+(?:es|also|so|nun|heute))*\s*$',clause,re.I):
        replacement='dem HERRN';reason='dative-vergelten-with-explicit-subject';review=None
    elif previous in {'o','ach'} or re.search(r'\bdu\s*,?\s*$',left,re.I):
        replacement='HERR';reason='direct-address';review=None
    elif re.search(r'\bich\s*,\s*$',left,re.I):
        replacement='der HERR';reason='first-person-apposition';review=None
    elif re.search(r'\b(?:name|namen)\s*$',left,re.I):
        replacement='HERR';reason='quoted-name';review=None
    elif re.match(r'\s*[,!]\s*(?:du|dein\w*|dich|dir)\b',right,re.I):
        replacement='HERR';reason='direct-address-pronoun';review=None
    elif re.search(r'\b(?:höre|erhöre|rette|hilf|gedenke|erwache|sieh|vergib|schaffe|bewahre|befreie)\s*,?\s*$',left,re.I):
        replacement='HERR';reason='direct-address-imperative';review=None
    elif re.match(r'\s*,',right) and set(following)&IMPERATIVE_ADDRESS:
        replacement='HERR';reason='direct-address-following-imperative';review=None
    elif re.match(r'\s*[,!?;.]?\s*$',right) and re.search(r'[,!?]\s*$',left):
        replacement='HERR';reason='terminal-direct-address';review=None
    elif re.match(r'\s*,\s*(?:meinem|deinem|seinem|unserem|eurem|ihrem|dem)\s+Gott\b',right,re.I):
        replacement='dem HERRN';reason='dative-apposition';review=None
    elif re.match(r'\s*,\s*(?:meinen|deinen|seinen|unseren|euren|ihren|den)\s+Gott\b',right,re.I):
        replacement='den HERRN';reason='accusative-apposition';review=None
    elif context_case:=contextual_name_case(left,right):
        replacement,reason=context_case;review=None
    elif previous and DAT_VERBS.fullmatch(previous):
        replacement='dem HERRN';reason='dative-verb';review=None
    elif previous in {'gebet','gib'}:
        replacement='dem HERRN';reason='dative-give-imperative';review=None
    elif any(x in {'baute','bauten','bauete','baueten'} for x in recent) and re.search(r'\beinen Altar\b',right[:140]):
        replacement='dem HERRN';reason='dative-altar-recipient';review=None
    elif previous in {'bat','baten','nannte','nannten'} or (previous in {'reute','reut'} and 'es' in recent):
        replacement='den HERRN';reason='accusative-attested-verb';review=None
    elif previous and ACC_VERBS.fullmatch(spelling_key(previous)):
        replacement='den HERRN';reason='accusative-verb';review=None
    elif previous in SUBJECT_AUX and not (set(recent[:-1])&HUMAN_SUBJECTS):
        replacement='der HERR';reason='subject-after-auxiliary';review=None
    elif previous in SUBORDINATORS and not (set(following[:3])&{'ich','du','wir'}) and (previous!='wie' or set(following)&FINITE_AFTER):
        replacement='der HERR';reason='subject-subordinate-clause';review=None
    elif following and following[0] in FINITE_AFTER:
        replacement='der HERR';reason='subject-before-finite-verb';review=None
    elif len(following)>1 and following[0]=='gott' and following[1] in FINITE_AFTER:
        replacement='der HERR';reason='subject-Lord-God';review=None
    elif following and following[0] in {'mir','dir','ihm','uns','euch','ihnen','sich','es','alles','selbst','allein','heute','wieder'} and set(following[1:4])&FINITE_AFTER:
        replacement='der HERR';reason='subject-with-intervening-object';review=None
    elif re.search(r'\b(?:ich bin|er ist|du bist|ihr seid|wir sind)\s*$',left,re.I):
        replacement='der HERR';reason='predicate-name';review=None
    elif following and any(ACC_VERBS.fullmatch(x) for x in following[:3]) and any(x in {'sollst','soll','sollen','will','wollen','werde','werden','muss','musst'} for x in recent):
        replacement='den HERRN';reason='object-before-infinitive';review=None
    elif following and any(DAT_VERBS.fullmatch(x) for x in following[:3]) and any(x in {'sollst','soll','sollen','will','wollen','werde','werden','muss','musst'} for x in recent):
        replacement='dem HERRN';reason='dative-before-infinitive';review=None
    if replacement.startswith(('des ','dem ','den ','der ')) and (i==0 or re.search(r'[.!?:]\s*[„“"»«]*\s*$',text[words[i-1].end():token.start()])):
        replacement=replacement[0].upper()+replacement[1:]
    return replacement,reason,review


def match_case(before, after):
    if before.isupper(): return after.upper()
    if before[:1].isupper(): return after[:1].upper()+after[1:]
    return after[:1].lower()+after[1:]


def rules(path=None):
    return json.loads(Path(path or ROOT/'rules/orthography.json').read_text(encoding='utf-8'))


def spelling_key(text):
    """Normalization for matching only; does not change source text."""
    return rules_cached().get(text.casefold(), text.casefold())


def rules_cached():
    if not hasattr(rules_cached, 'value'): rules_cached.value = rules()['words']
    return rules_cached.value


def gender_determiner(word, case):
    w = word.lower()
    if w in CONTRACTIONS: return CONTRACTIONS[w]
    if w in {'das','dem','des'}: return 'die' if case == 'na' else 'der'
    if w == 'alles': return 'alle' if case == 'na' else 'aller'
    for stem in ('ein','kein','mein','dein','sein','ihr','unser','unsr','euer','eur','dies','jen','jed','jeglich','jedwed','welch','solch','manch'):
        if w in {stem,stem+'es',stem+'em'}:
            if stem == 'eur': stem = 'eur'
            if stem == 'euer': stem = 'eur'
            return stem + ('e' if case == 'na' else 'er')
    return None


def plan_verse(text, edition, config):
    words = list(WORD.finditer(text))
    changes, reviews = {}, []
    def put(token, replacement, rule):
        before = token[0]
        if replacement == before: return
        old = changes.get(token.start())
        changes[token.start()] = {'start':token.start(),'end':token.end(),'before':before,
                                  'after':replacement,'rule':(old['rule']+'; ' if old else '')+rule}
    def current(token):
        return changes.get(token.start(), {}).get('after', token[0])
    for i, token in enumerate(words):
        w = token[0].lower()
        if edition in {'lut', 'luther'} and token[0] in {'HErr', 'HErrn', 'HErrs'}:
            put(token, token[0].upper(), 'name:Luther-divine-capitalization')
        if w in config['words']:
            put(token, match_case(token[0], config['words'][w]), 'orthography:wordlist')
        if w in config['review_words']:
            reviews.append({'start':token.start(),'word':token[0], 'kind':'spelling-context',
                            'reason':'Kontextabhängige Schreibung/modernes Homograph; unverändert prüfen.'})
        if edition == 'elb' and w in {'jehova','jehovas'}:
            replacement,case_rule,review=divine_name(text,words,i)
            put(token,replacement,'name:'+case_rule)
            if review:
                reviews.append({'start':token.start(),'word':token[0], 'kind':'divine-name-syntax','reason':review})
        if w not in NOUNS:
            continue
        # Common nouns are capitalized in German, including verse-initial data
        # from old sources that occasionally use lowercase.
        replacement = NOUNS[w]
        put(token, replacement if not token[0].isupper() else replacement.upper(), 'word:Weib-Frau')
        if w.endswith(('weiber','weibern')):
            continue
        case = 'dg' if w.endswith(('weibe','weibes')) else 'na'
        adjectives = []
        determiner = None
        for j in range(i-1, max(-1, i-6), -1):
            previous = words[j]
            following = words[j+1]
            if not text[previous.end():following.start()].isspace(): break
            old = previous[0].lower()
            if old in {'und','oder'} and adjectives:
                continue
            if old in {'solch','jeglich','eigen'} and j and words[j-1][0].lower() in {'ein','sein','mein','dein','ihr','kein'}:
                adjectives.append(previous)
                continue
            # "eines anderen Weib" can mean another man's wife, rather than
            # an adjective agreeing with Weib. Preserve that possessive group.
            if old in {'anderen','fremden','verstorbenen','nächsten','einen'} and w.endswith('weib'):
                break
            if old.endswith(('em','es')) and gender_determiner(old, 'dg') is not None:
                # "dieses Weib" is nominative/accusative; noun -es marks genitive.
                if old.endswith('em'): case='dg'
            updated = gender_determiner(old, case)
            if updated:
                put(previous, match_case(previous[0],updated), 'grammar:Frau-determiner')
                determiner = previous
                break
            stem = re.sub(r'(?:es|em|en|er|e)$','',old)
            if stem in ADJECTIVES or old in {'tugendsam','holdselig','unrein','samaritisch','eigen','jeglich','solch'}:
                adjectives.append(previous)
            else:
                break
        for adjective in adjectives:
            old = current(adjective)
            updated = old
            if case == 'na' and old.endswith(('es','er','em')): updated=old[:-2]+'e'
            elif case == 'dg' and old.endswith('em'): updated=old[:-2]+'er'
            elif old.lower() in {'tugendsam','holdselig','unrein','samaritisch','eigen','jeglich','solch'}:updated=old+('e' if case=='na' else 'er')
            put(adjective, updated, 'grammar:Frau-adjective')
        # Only an immediately following relative pronoun with a comma and an
        # explicit singular antecedent is rewritten. Longer agreement is reviewed.
        if i+1 < len(words) and re.fullmatch(r'\s*,\s*', text[token.end():words[i+1].start()]):
            relative = words[i+1]
            relmap={'das':'die','welches':'welche','dessen':'deren'}
            if relative[0].lower() in relmap:
                put(relative,match_case(relative[0],relmap[relative[0].lower()]),'grammar:Frau-relative')
        reviews.append({'start':token.start(),'word':token[0], 'kind':'gender-agreement',
                        'reason':'Nominalgruppe regelbasiert angepasst; längere Pronomenbezüge/Satzkongruenz prüfen.'})
    for old, new in config.get('phrases', {}).items():
        for found in re.finditer(r'(?<!\w)'+re.escape(old).replace(r'\ ',r'\s+')+r'(?!\w)', text, re.I):
            parts = [t for t in words if found.start() <= t.start() and t.end() <= found.end()]
            replacements = new.split()
            require(len(parts)==len(replacements), 'Phrase rules must preserve word count')
            for index,(token,replacement) in enumerate(zip(parts,replacements)):
                # The phrase table deliberately specifies internal capitalization.
                if index==0: replacement=match_case(token[0],replacement)
                put(token,replacement,'orthography:phrase')
    return sorted(changes.values(),key=lambda x:x['start']),reviews


def modernize(input_path, output_path, edition, rule_path=None, overrides_path=None,
              version='1.1', bible_id=None):
    input_path, output_path = Path(input_path), Path(output_path)
    require(input_path.resolve()!=output_path.resolve(),'Write a new version; do not overwrite the input')
    require(edition in {'elb','lut','luther','generic','none'},'Unsupported language profile')
    config = rules(rule_path)
    root = parse_xml(input_path)
    before_notes = note_fingerprints(root)
    before_strongs = strong_fingerprints(root)
    normalize_gr(root)
    overrides = json.loads(Path(overrides_path).read_text()) if overrides_path else {}
    verse_map = dict(zef_verses(root, include_captions=True))
    require(verse_map,'No supported Zefania verses found')
    require(set(overrides) <= set(verse_map),'Override references absent verses')
    audit, pending, offsets = [], [], []
    for ref, verse in verse_map.items():
        original = plain(verse)
        edits, reviews = plan_verse(original,edition,config) if edition != 'none' else ([], [])
        # Explicit editorial exceptions are position+text guarded. They override
        # overlapping automatic edits; never silently match a changed edition.
        for override in overrides.get(ref,[]):
            require(original[override['start']:override['end']]==override['before'],f'Override mismatch {ref}')
            require(bool(override.get('reason')),'Override needs a documented reason')
            edits=[e for e in edits if e['end']<=override['start'] or e['start']>=override['end']]
            edits.append({k:override[k] for k in ('start','end','before','after')} | {'rule':'editorial:'+override['reason']})
        edits.sort(key=lambda e:e['start'])
        delta=0
        for edit in edits:
            row={'ref':ref,**edit,'new_start':edit['start']+delta,'new_end':edit['start']+delta+len(edit['after'])}
            audit.append(row)
            delta+=len(edit['after'])-(edit['end']-edit['start'])
        apply_edits(verse,edits)
        modified=plain(verse)
        if edits:
            offsets.append({'ref':ref,'input_text_sha256':hashlib.sha256(original.encode()).hexdigest(),
                            'output_text_sha256':hashlib.sha256(modified.encode()).hexdigest(),
                            'edits':[{k:row[k] for k in ('start','end','new_start','new_end','before','after')} for row in audit[-len(edits):]]})
        pending.extend({'ref':ref,**r,'context_before':original,'context_after':modified} for r in reviews)
    require(note_fingerprints(root)==before_notes,'A note subtree changed')
    require(strong_fingerprints(root)==before_strongs,'Strong/morphology attributes changed')
    from .project import metadata
    metadata(root, bible_id or ('akribos.lut' if edition in {'lut','luther'} else 'akribos.'+edition), version, 'language')
    write_xml(output_path,root)
    # Verify the serialized file, not only the in-memory tree.
    check=parse_xml(output_path)
    require(note_fingerprints(check)==before_notes,'Serialized notes changed')
    require(strong_fingerprints(check)==before_strongs,'Serialized Strong attributes changed')
    for suffix,rows,fields in [('changes.csv',audit,['ref','start','end','new_start','new_end','before','after','rule']),
                               ('review.csv',pending,['ref','start','word','kind','reason','context_before','context_after'])]:
        path=output_path.with_suffix('.'+suffix)
        with path.open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    atomic_text(output_path.with_suffix('.offset-map.jsonl'), ''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in offsets))
    report={'edition':edition,'version':version,'input_sha256':file_hash(input_path),'output_sha256':file_hash(output_path),
            'rule_sha256':file_hash(rule_path or ROOT/'rules/orthography.json'),
            'implementation_sha256':{name:file_hash(ROOT/'akribos'/name) for name in ('modernize.py','xmlio.py','common.py','importers.py')},
            'overrides_sha256':file_hash(overrides_path) if overrides_path else None,
            'edits':len(audit),'changed_verses':len(offsets),'rules':dict(Counter(r['rule'] for r in audit)),
            'notes_preserved':len(before_notes),'strong_elements_preserved':len(before_strongs),
            'review_items':len(pending),'review_kinds':dict(Counter(r['kind'] for r in pending)),
            'preservation_checks':{'note_subtrees':True,'strong_attributes_and_order':True,'serialized_xml':True},
            'limits':['Deterministic partial spelling modernization; not a new translation or expert-verified edition.',
                      'Jehova/HERR uses explicit case/context rules; unclassified articles/case are queued for review.',
                      'Original study notes and their quotations retain source spelling.',
                      'Old external token offsets are obsolete; use offset-map.jsonl and re-tokenize.']}
    write_json(output_path.with_suffix('.report.json'),report)
    return report
