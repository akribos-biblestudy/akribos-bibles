#!/usr/bin/env python3
"""Append deterministic source-based linguistic validation to a confirmed export."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from akribos.linguistic import validate_files


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path,help='Confirmed 05-reference-confirmed.xml export')
    parser.add_argument('--output',type=Path,help='Defaults to 06-linguistic.xml next to input')
    parser.add_argument('--source-root',type=Path,default=ROOT)
    parser.add_argument('--profiles',type=Path,help='Defaults to source-root/config/step-profiles.json')
    parser.add_argument('--nt-edition',choices=('WH','TR'),required=True)
    parser.add_argument('--elb-bk',type=Path,help='Private BK corroboration snapshot')
    parser.add_argument('--elb-csv',type=Path,help='Private CSV corroboration snapshot')
    parser.add_argument('--alignment',type=Path,help='Original alignment audit; neighboring alignment.jsonl.gz is detected')
    args=parser.parse_args(argv)
    references={label:path for label,path in [('elb-bk',args.elb_bk),('elb-csv',args.elb_csv)] if path}
    if not references:
        parser.error('Provide --elb-bk or --elb-csv to corroborate article decisions')
    result=validate_files(args.input,args.output or args.input.parent/'06-linguistic.xml',
                         source_profiles_path=args.profiles or args.source_root/'config/step-profiles.json',
                         source_root=args.source_root,nt_edition=args.nt_edition,
                         corroborating_paths=references,alignment_path=args.alignment)
    print(json.dumps({key:result.summary[key] for key in ('hints_before','hints_removed',
                     'hints_remaining','hints_rejected','article_tags_added','article_candidates_retained',
                     'editorial_corrections','editorial_corrections_marked','editorial_corrections_inherited',
                     'editorial_hints_removed','editorial_not_applicable')},
                     ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())
