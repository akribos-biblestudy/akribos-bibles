"""Deterministic, complete public repository archive; private paths are excluded."""
from pathlib import Path
import argparse,json,sys,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from verify_repository import verify_repository
from akribos.common import require,file_hash

ROOT_FILES={'README.md','CHANGELOG.md','LICENSE','LICENSE-DATA.md','THIRD-PARTY-NOTICES.md','.gitignore','.gitattributes','bible.py','requirements.txt'}
PUBLIC_DIRS={'akribos','config','rules','sources','licenses','vendor','scripts','tests','docs','history','releases','comparisons'}
FORBIDDEN_REFERENCE_SHA256='cc1a633a0e7a95b118a0b61fc8bcfeeb07a1379856b6b32122071f50117316d5'


def package(output):
    report=verify_repository();files=[]
    for p in sorted(ROOT.rglob('*')):
        rel=p.relative_to(ROOT)
        if not p.is_file() or '__pycache__' in rel.parts or p.suffix in {'.pyc','.pyo'}:continue
        if not (str(rel) in ROOT_FILES or rel.parts[0] in PUBLIC_DIRS):continue
        require(not p.is_symlink(),'Do not package symlinks')
        require(p.stat().st_size<100*1024*1024,f'File exceeds GitHub limit: {rel}')
        require(file_hash(p)!=FORBIDDEN_REFERENCE_SHA256,'Private ELB BK reference found in public paths')
        require('word-differences.jsonl.gz'!=p.name,'Private word differences in public paths')
        files.append(p)
    output=Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:
            info=zipfile.ZipInfo('akribos-bible/'+str(p.relative_to(ROOT)),date_time=(2026,9,10,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,p.read_bytes())
    print(json.dumps({'output':str(output),'files':len(files),'bytes':output.stat().st_size,'sha256':file_hash(output),'verification':report},ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);package(p.parse_args().output)
