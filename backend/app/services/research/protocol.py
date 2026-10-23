"""Capture exact offline runner implementation without private matter data."""
import hashlib
import json
import platform
import os
import subprocess
import zipfile
from datetime import datetime,timezone
from importlib.metadata import version,PackageNotFoundError
from app.config import BACKEND_DIR

def snapshot(out,command):
    files=[p for folder in ("app","scripts") for p in (BACKEND_DIR/folder).rglob("*.py")]
    hashes={str(p.relative_to(BACKEND_DIR)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    packages={}
    for name in ("scikit-learn","numpy","pydantic","sentence-transformers","transformers","torch"):
        try: packages[name]=version(name)
        except PackageNotFoundError:packages[name]=None
    with zipfile.ZipFile(out/"source_snapshot.zip","x",zipfile.ZIP_DEFLATED) as archive:
        for p in files: archive.write(p,str(p.relative_to(BACKEND_DIR)))
    try: revision=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    except (OSError,subprocess.SubprocessError):revision=None
    (out/"environment.json").write_text(json.dumps({"capturedAt":datetime.now(timezone.utc).isoformat(),
        "gitRevision":revision,"hardware":{"platform":platform.platform(),"processor":platform.processor(),"logicalCPUs":os.cpu_count(),"peakMemory":"not measured"},
        "command":command,"python":platform.python_version(),"packages":packages,"sourceHashes":hashes,
        "modelHashes":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (BACKEND_DIR/"artifacts").glob("*.joblib")}},indent=2),encoding="utf-8")
