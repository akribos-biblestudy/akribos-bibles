"""Install the exact bundled dependency offline, without touching system Python."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,'-m','pip','install','--no-index','--find-links',str(root/'vendor'),
               '--require-hashes','--target',str(root/'.local/python'),'-r',str(root/'requirements.txt')],check=True)
