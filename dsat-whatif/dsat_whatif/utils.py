from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def to_csv(df: pd.DataFrame, path: Path):
    df.to_csv(path, index=False)

def to_json(obj, path: Path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def pick(d: dict, keys):
    return {k: d.get(k) for k in keys}
