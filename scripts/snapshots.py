"""Keep the computational implementation for every historical build, even before Git init."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from akribos.common import digest,file_hash,require,write_json
from akribos.project import code_identity


def save(mapping,blobs=None):
    out=ROOT/'history/implementations'/digest(mapping)[:16]
    for name,sha in mapping.items():
        data=(blobs or {}).get(name)
        if data is None:data=(ROOT/name).read_bytes()
        require(hashlib.sha256(data).hexdigest()==sha,f'Implementation source missing for {name} ({sha})')
        path=out/name
        if path.exists():require(path.read_bytes()==data,f'Implementation snapshot changed: {path}')
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    write_json(out/'implementation.json',mapping)
    return out


def snapshot_current():return save(code_identity())

if __name__=='__main__':print(snapshot_current())
