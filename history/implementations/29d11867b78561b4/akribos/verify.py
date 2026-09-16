"""Independent, complete text reconstruction from an editor's CSV audit."""
import csv
from collections import defaultdict
from .common import require,file_hash
from .importers import parse_xml
from .xmlio import zef_verses,plain,note_fingerprints,strong_fingerprints


def verify(before,after,changes):
    a,b=parse_xml(before),parse_xml(after)
    require(note_fingerprints(a)==note_fingerprints(b),'Notes differ')
    require(strong_fingerprints(a)==strong_fingerprints(b),'Strong/morphology attributes differ')
    av,bv=dict(zef_verses(a,True)),dict(zef_verses(b,True))
    require(set(av)==set(bv),'Verse/caption inventory differs')
    edits=defaultdict(list)
    with open(changes,encoding='utf-8',newline='') as f:
        for row in csv.DictReader(f):edits[row['ref']].append(row)
    require(set(edits)<=set(av),'Unknown audit verse')
    total=0
    for ref,v in av.items():
        original=plain(v);expected=original;previous_end=0;delta=0
        ordered=sorted(edits.get(ref,[]),key=lambda r:int(r['start']))
        for row in ordered:
            start,end=int(row['start']),int(row['end'])
            require(previous_end<=start<end<=len(original),f'Overlapping/invalid audit {ref}')
            require(original[start:end]==row['before'],f'Audit source mismatch {ref}')
            require(int(row['new_start'])==start+delta,f'Audit destination offset mismatch {ref}')
            require(int(row['new_end'])==start+delta+len(row['after']),f'Audit destination end mismatch {ref}')
            delta+=len(row['after'])-(end-start);previous_end=end
        for row in reversed(ordered):
            start,end=int(row['start']),int(row['end'])
            expected=expected[:start]+row['after']+expected[end:]
        require(expected==plain(bv[ref]),f'Unlogged text change {ref}')
        total+=len(ordered)
    return {'passed':True,'verses_and_captions':len(av),'notes':len(note_fingerprints(a)),
            'strong_elements':len(strong_fingerprints(a)),'reconstructed_edits':total,
            'input_sha256':file_hash(before),'output_sha256':file_hash(after),
            'checks':['All note subtrees preserved','All Strong attributes/order preserved',
                      'Same verses/captions','Every output verse reconstructed exactly from CSV audit']}
