from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Literal
import json
from pathlib import Path
from pymongo.collection import Collection
from pymongo import MongoClient

Difficulty = Literal["easy", "hard"]

@dataclass
class ScoringMap:
    # map[raw] = {'hard': int, 'easy': int}
    map: Dict[int, Dict[Difficulty, int]]

    def scaled(self, raw: int, difficulty: Difficulty) -> int:
        if raw < 0:
            raw = 0
        if raw not in self.map:
            # clamp to nearest available key
            lo = min(self.map.keys())
            hi = max(self.map.keys())
            raw = min(max(raw, lo), hi)
        return int(self.map[raw][difficulty])

@dataclass
class ScoringMaps:
    # keys: 'Math', 'Reading and Writing'
    maps: Dict[str, ScoringMap]

    @classmethod
    def from_file(cls, path: Path) -> "ScoringMaps":
        data = json.loads(Path(path).read_text())
        m: Dict[str, Dict[int, Dict[str, int]]] = {}
        for entry in data:
            key = entry["key"]  # 'Math' or 'Reading and Writing'
            raw_map = {}
            for row in entry["map"]:
                raw_map[int(row["raw"])] = {"hard": int(row["hard"]), "easy": int(row["easy"])}
            m[key] = ScoringMap(raw_map)
        return cls(maps=m)

    @classmethod
    def from_mongo(cls, client: MongoClient, db_name: str) -> "ScoringMaps":
        col: Collection = client[db_name]["sat_scoring"]
        docs = list(col.find({}))
        m: Dict[str, Dict[int, Dict[str, int]]] = {}
        for entry in docs:
            key = entry["key"]
            raw_map = {}
            for row in entry["map"]:
                raw_map[int(row["raw"])] = {"hard": int(row["hard"]), "easy": int(row["easy"])}
            m[key] = ScoringMap(raw_map)
        return cls(maps=m)

    def get(self, subject_key: str) -> ScoringMap:
        return self.maps[subject_key]
