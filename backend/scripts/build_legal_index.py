"""One-time legal index build; --lexical-only is an explicit degraded mode."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.services.legal.index import build

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--lexical-only',action='store_true',help='Skip embeddings; report lexical-only mode')
    arguments=parser.parse_args()
    print(json.dumps(build(semantic=not arguments.lexical_only),indent=2))
