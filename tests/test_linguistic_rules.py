import unittest
from akribos.linguistic_rules import linked_article_proof,classify_uncertain,atomic_bridge_proof

def german(words):
    result=[];offset=0
    for i,(w,codes,uncertain) in enumerate(words):
        result.append({'id':f'd{i+1:03}','text':w,'strong':codes,'start':offset,'end':offset+len(w),'uncertain':uncertain})
        offset+=len(w)+1
    return ' '.join(w[0] for w in words),result

def source(word,code,morph,conjoined=''):
    return {'word':f'{word:02}','strong':[code],'morph':morph,'conjoined':conjoined,'origin_id':f'John.1.1#{word:02}=NKO'}

class ArticleTests(unittest.TestCase):
    def setUp(self):
        self.text,self.tokens=german([('sieht',['G991'],False),('den',[],False),('Sohn',['G5207'],False)])
        self.source=[source(1,'G991','V-PAI-3S'),source(2,'G3588','T-ASM','#02»03:G5207'),source(3,'G5207','N-ASM')]
    def test_confirmed_left_anchor_and_explicit_head_link(self):
        self.assertIsNotNone(linked_article_proof(self.text,self.tokens,1,self.source))
    def test_initial_article_in_both_languages(self):
        text,tokens=german([('Der',[],False),('Sohn',['G5207'],False)])
        self.assertIsNotNone(linked_article_proof(text,tokens,0,self.source[1:]))
    def test_supplied_article_no_link(self):
        self.source[1]['conjoined']=''
        self.assertIsNone(linked_article_proof(self.text,self.tokens,1,self.source))
    def test_article_elsewhere_in_verse_is_insufficient(self):
        self.source.insert(1,source(8,'G2532','CONJ'))
        self.assertIsNone(linked_article_proof(self.text,self.tokens,1,self.source))
    def test_repeated_head_word_is_ambiguous(self):
        self.source.append(source(8,'G5207','N-ASM'))
        self.assertIsNone(linked_article_proof(self.text,self.tokens,1,self.source))
    def test_uncertain_head_is_not_proof(self):
        self.tokens[2]['uncertain']=True
        self.assertIsNone(linked_article_proof(self.text,self.tokens,1,self.source))
    def test_relative_pronoun_before_proper_name(self):
        text,tokens=german([('den',[],False),('Jesus',['G2424'],False),('liebte',['G25'],False)])
        refs=[source(1,'G3739','R-ASM'),source(2,'G25','V-IAI-3S'),source(3,'G3588','T-NSM','#03»04:G2424'),source(4,'G2424','N-NSM-P')]
        self.assertIsNone(linked_article_proof(text,tokens,0,refs))
    def test_matthew_1_6_die_urias_is_not_a_determiner(self):
        text,tokens=german([('der',['G3588'],False),('die',[],False),('Urias',['G3774'],False)])
        refs=[source(15,'G3588','T-GSF','#15'),source(17,'G3588','T-GSM','#17»18:G3774'),source(18,'G3774','N-GSM-P')]
        self.assertIsNone(linked_article_proof(text,tokens,1,refs))
    def test_clause_boundary_does_not_create_anchor(self):
        text=self.text.replace('sieht ','sieht,')
        self.assertIsNone(linked_article_proof(text,self.tokens,1,self.source))
    def test_greek_head_case_gender_number_must_match_article(self):
        self.source[1]['morph']='T-NSF'
        self.assertIsNone(linked_article_proof(self.text,self.tokens,1,self.source))
    def test_german_gender_need_not_equal_greek_gender(self):
        text,tokens=german([('Das',[],False),('Wort',['G3056'],False)])
        refs=[source(1,'G3588','T-NSM','#01»02:G3056'),source(2,'G3056','N-NSM')]
        self.assertIsNotNone(linked_article_proof(text,tokens,0,refs))
    def test_hebrew_3588_is_not_an_article(self):
        self.source[1]['strong']=['H3588']
        self.assertIsNone(linked_article_proof(self.text,self.tokens,1,self.source))
    def test_selected_edition_moved_words_not_assumed_contiguous(self):
        self.source[1]['editions_raw']='NA28+WH moved 2: TR'
        self.assertIsNone(linked_article_proof(self.text,self.tokens,1,self.source))
    def test_every_uncertain_token_gets_a_disposition(self):
        for t in self.tokens:t['uncertain']=True
        self.tokens[1]['strong']=['G3588']
        decision=classify_uncertain('John.1.1',self.text,self.tokens,self.source)
        self.assertEqual(len(decision),3)
        self.assertEqual({x['status'] for x in decision},{'review'})
    def test_alternate_inflected_strong_is_not_rejected(self):
        text,tokens=german([('war',['G2258'],True)])
        refs=[source(1,'G1510','V-IAI-3S')|{'alternate':['G2258']}]
        self.assertEqual(classify_uncertain('John.1.1',text,tokens,refs)[0]['reason'],'alternate-strong-encoding')
    def test_reference_mismatch_preserves_review(self):
        self.tokens[1]|={'strong':['G3588'],'uncertain':True}
        result=classify_uncertain('John.1.1',self.text,self.tokens,self.source,True)
        self.assertEqual(result[0]['status'],'review')
    def test_unknown_source_absence_is_not_approval(self):
        text,tokens=german([('Wort',['G3056'],True)])
        self.assertEqual(classify_uncertain('John.1.1',text,tokens,[])[0]['status'],'review')

class ExtendedTests(unittest.TestCase):
    def test_real_luther_matthew_8_10_das_jesus_demonstrative(self):
        text,tokens=german([('Da',['G1161'],False),('das',[],False),('Jesus',['G2424'],False),('hörte',['G191'],False)])
        refs=[source(1,'G1161','CONJ'),source(2,'G3588','T-NSM','#02»03:G2424'),source(3,'G2424','N-NSM-P'),source(4,'G191','V-AAP-NSM')]
        self.assertIsNone(linked_article_proof(text,tokens,1,refs))
    def test_das_gott_is_not_german_determiner(self):
        text,tokens=german([('Da',['G1161'],False),('das',[],False),('Gott',['G2316'],False)])
        refs=[source(1,'G1161','CONJ'),source(2,'G3588','T-NSM','#02»03:G2316'),source(3,'G2316','N-NSM-T')]
        self.assertIsNone(linked_article_proof(text,tokens,1,refs))
    def test_unlisted_german_noun_needs_review(self):
        text,tokens=german([('die',[],False),('Taube',['G4058'],False)])
        refs=[source(1,'G3588','T-NSF','#01»02:G4058'),source(2,'G4058','N-NSF')]
        self.assertIsNone(linked_article_proof(text,tokens,0,refs))
    def test_romans_12_3_nach_dem_is_a_multitoken_conjunction(self):
        text,tokens=german([('nach',['G5613'],False),('dem',[],False),('Gott',['G2316'],False)])
        refs=[source(1,'G5613','ADV'),source(2,'G3588','T-NSM','#02»03:G2316'),source(3,'G2316','N-NSM-T')]
        self.assertIsNone(linked_article_proof(text,tokens,1,refs))
    def test_actual_preposition_before_german_article_is_not_blocked(self):
        text,tokens=german([('in',['G1722'],False),('dem',[],False),('Sohn',['G5207'],False)])
        refs=[source(1,'G1722','PREP'),source(2,'G3588','T-DSM','#02»03:G5207'),source(3,'G5207','N-DSM')]
        self.assertIsNotNone(linked_article_proof(text,tokens,1,refs))
    def test_pronominal_left_anchor_is_not_determination_evidence(self):
        text,tokens=german([('ihm',['G846'],False),('der',[],False),('Sohn',['G5207'],False)])
        refs=[source(1,'G846','P-3DSM'),source(2,'G3588','T-NSM','#02»03:G5207'),source(3,'G5207','N-NSM')]
        self.assertIsNone(linked_article_proof(text,tokens,1,refs))
    def test_german_source_number_mismatch_is_not_approved(self):
        text,tokens=german([('Die',[],False),('Götter',['G2316'],False)])
        refs=[source(1,'G3588','T-NSM','#01»02:G2316'),source(2,'G2316','N-NSM')]
        self.assertIsNone(linked_article_proof(text,tokens,0,refs))
    def test_versification_marker_needs_reference_review(self):
        text,tokens=german([('Christo',['G5547'],True)])
        refs=[source(1,'G5547','N-DSM-T')|{'origin_id':'Gal.2.19[2.20]#10=NKO'}]
        d=classify_uncertain('Gal.2.19',text,tokens,refs)[0]
        self.assertEqual(d['status'],'review')
        self.assertEqual(d['reason'],'source-order-or-versification-variation')
    def test_code_in_multicode_span_is_not_unique(self):
        text,tokens=german([('Der',[],False),('Sohn',['G5207'],False),('Kind',['G5207','G3813'],False)])
        refs=[source(1,'G3588','T-NSM','#01»02:G5207'),source(2,'G5207','N-NSM')]
        self.assertIsNone(linked_article_proof(text,tokens,0,refs))
    def test_actual_selected_edition_movement_marker(self):
        text,tokens=german([('Der',[],False),('Sohn',['G5207'],False)])
        refs=[source(1,'G3588','T-NSM','#01»02:G5207')|{'editions_raw':'NA28+WH+TR»1','edition':'TR'},source(2,'G5207','N-NSM')]
        self.assertIsNone(linked_article_proof(text,tokens,0,refs))
    def test_movement_of_unselected_edition_is_not_a_rejection(self):
        text,tokens=german([('Der',[],False),('Sohn',['G5207'],False)])
        refs=[source(1,'G3588','T-NSM','#01»02:G5207')|{'editions_raw':'NA28+WH+TR»1','edition':'WH'},source(2,'G5207','N-NSM')]
        self.assertIsNotNone(linked_article_proof(text,tokens,0,refs))
    def test_atomic_greek_conjunction_between_independent_anchors(self):
        text,tokens=german([('Vater',['G3962'],False),('und',['G2532'],True),('Sohn',['G5207'],False)])
        refs=[source(1,'G3962','N-NSM'),source(2,'G2532','CONJ'),source(3,'G5207','N-NSM')]
        self.assertIsNotNone(atomic_bridge_proof(text,tokens,1,refs))
        self.assertEqual(classify_uncertain('John.1.1',text,tokens,refs)[0]['status'],'accepted')
    def test_same_verse_presence_without_adjacent_anchors_insufficient(self):
        text,tokens=german([('Vater',['G3962'],False),('und',['G2532'],True),('Sohn',['G5207'],False)])
        refs=[source(1,'G3962','N-NSM'),source(2,'G2532','CONJ'),source(3,'G3588','T-NSM'),source(4,'G5207','N-NSM')]
        self.assertIsNone(atomic_bridge_proof(text,tokens,1,refs))
    def test_greek_negation_must_have_negation_morphology(self):
        text,tokens=german([('Vater',['G3962'],False),('nicht',['G3756'],True),('Sohn',['G5207'],False)])
        refs=[source(1,'G3962','N-NSM'),source(2,'G3756','PRT-N'),source(3,'G5207','N-NSM')]
        self.assertIsNotNone(atomic_bridge_proof(text,tokens,1,refs))
        refs[1]['morph']='ADV'
        self.assertIsNone(atomic_bridge_proof(text,tokens,1,refs))
    def test_hebrew_atomic_noun_with_actual_source_pos(self):
        text,tokens=german([('sprach',['H559'],False),('Gott',['H430'],True),('Licht',['H216'],False)])
        refs=[source(1,'H559','HVqw3ms'),source(2,'H430','HNcmpa'),source(3,'H216','HNcbsa')]
        self.assertIsNotNone(atomic_bridge_proof(text,tokens,1,refs))
        refs[1]['morph']='HVqp3ms'
        self.assertIsNone(atomic_bridge_proof(text,tokens,1,refs))
    def test_hebrew_prefix_composite_is_protected(self):
        text,tokens=german([('Vater',['H1'],False),('nicht',['H3808'],True),('Sohn',['H1121'],False)])
        refs=[source(1,'H1','HNcmsa'),source(2,'H3808','HC/Tn')|{'strong':['H9002','H3808']},source(3,'H1121','HNcmsa')]
        self.assertIsNone(atomic_bridge_proof(text,tokens,1,refs))
    def test_phrase_assignment_is_protected(self):
        text,tokens=german([('Vater',['G3962'],False),('und',['G2532'],True),('Sohn',['G5207'],False)])
        tokens[1]['phrase_tokens']=2
        refs=[source(1,'G3962','N-NSM'),source(2,'G2532','CONJ'),source(3,'G5207','N-NSM')]
        self.assertIsNone(atomic_bridge_proof(text,tokens,1,refs))
    def test_hebrew_yahweh_requires_uppercase_rendering(self):
        text,tokens=german([('sprach',['H559'],False),('HERR',['H3068'],True),('Mose',['H4872'],False)])
        refs=[source(1,'H559','HVqw3ms'),source(2,'H3068','HNpt'),source(3,'H4872','HNpms')]
        self.assertIsNotNone(atomic_bridge_proof(text,tokens,1,refs))
        tokens[1]['text']='Herr'
        self.assertIsNone(atomic_bridge_proof(text,tokens,1,refs))

if __name__=='__main__':unittest.main()
