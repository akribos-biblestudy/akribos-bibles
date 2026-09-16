#!/usr/bin/env python3
"""Reproducible language, Strong, KJV repair and reference comparison commands."""
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.local/python'))
from akribos.common import DataError
from akribos.project import VERSION


def main():
    parser=argparse.ArgumentParser(description='Akribos: Originale → Sprachfassung → Strong-Aufbereitung; separater Referenzvergleich')
    sub=parser.add_subparsers(dest='command',required=True)
    for name in ('edit','build'):
        p=sub.add_parser(name)
        p.add_argument('--edition',choices=['elb','lut','all','custom'],default='all')
        p.add_argument('--version',default=VERSION,help=f'Ausgabeversion (Standard: {VERSION}); lädt keinen historischen Code')
        p.add_argument('--input',type=Path,help='Eigene Zefania- oder OSIS-Datei; Ergebnisse bleiben .local/')
        p.add_argument('--id',dest='bible_id',help='Stabile Ausgabe-ID für eigene Texte')
        p.add_argument('--profile',choices=['elb','lut','generic','none'])
        p.add_argument('--overrides',type=Path,help='Positionsgesicherte redaktionelle Ausnahmen als JSON')
        p.add_argument('--rebuild',action='store_true',help='Erneut berechnen und Bytegleichheit des vorhandenen Laufs prüfen')
        if name=='build':p.add_argument('--nt-edition',choices=['WH','TR'])
    p=sub.add_parser('repair-kjv',help='Syntaxreparierte KJV als importierbare XML-Datei exportieren')
    p.add_argument('--rebuild',action='store_true',help='Reparatur neu ausführen und Bytegleichheit prüfen')
    p=sub.add_parser('compare')
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--label',default='reference')
    p.add_argument('--verse-map',type=Path,help='JSON: eigene Vers-ID → Referenz-Vers-ID')
    p.add_argument('--public-index',action='store_true',help='Öffentlichen Versindex ohne fremde Wörter/Strong-Werte hinzufügen')
    p.add_argument('--rebuild',action='store_true')
    args=vars(parser.parse_args());cmd=args.pop('command')
    from scripts.snapshots import snapshot_current
    snapshot_current()
    try:
        if cmd=='repair-kjv':
            from akribos.project import export_kjv
            print(export_kjv(**args));return
        if cmd=='compare':
            from akribos.compare import compare
            args['input_path']=args.pop('input');args['reference_path']=args.pop('reference')
            print(compare(**args));return
        if args['input']:
            if args['edition']!='custom' or not args['bible_id']:parser.error('--input benötigt --edition custom und --id')
            if args['bible_id'] in {'akribos.elb','akribos.lut'}:parser.error('Für eigene Texte eine eigene ID wählen')
        elif args['edition']=='custom':parser.error('--edition custom benötigt --input')
        elif args['bible_id']:parser.error('--id ist nur für eigene Texte verfügbar; ELB/LUT-IDs sind fest')
        from akribos.pipeline import edit,build
        args['input_path']=args.pop('input')
        editions=['elb','lut'] if args['edition']=='all' else [args['edition']]
        for edition in editions:
            args['edition']=edition
            print((build if cmd=='build' else edit)(**args))
        if cmd=='build' and not args['input_path']:
            from akribos.project import export_kjv
            print(export_kjv(rebuild=args['rebuild']))
    except (DataError,FileNotFoundError) as exc:
        parser.exit(2,f'Fehler: {exc}\n')

if __name__=='__main__':main()
