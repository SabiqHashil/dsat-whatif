from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal, Tuple
import json
from pathlib import Path
from pymongo import MongoClient
from pymongo.collection import Collection

ModuleTag = Literal["module1", "module2"]
DiffTag = Literal["easy", "hard"]

@dataclass
class Question:
    question_id: str
    section: str            # original field (Static / hard / easy)
    module: ModuleTag       # derived: module1 or module2
    module2_diff: Optional[DiffTag]  # only for module2
    correct: int
    time_spent: int
    subject: str
    unit: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None

@dataclass
class SectionAttempt:
    subject: str  # 'Reading and Writing' or 'Math'
    module1: List[Question] = field(default_factory=list)
    module2: List[Question] = field(default_factory=list)
    module2_diff: Optional[DiffTag] = None  # inferred from module2 questions

    def totals(self) -> Tuple[int, int, int, int]:
        m1_total = len(self.module1)
        m1_correct = sum(q.correct for q in self.module1)
        m2_total = len(self.module2)
        m2_correct = sum(q.correct for q in self.module2)
        return m1_total, m1_correct, m2_total, m2_correct

@dataclass
class Attempt:
    # Two sections
    sections: Dict[str, SectionAttempt]  # keys: 'Reading and Writing', 'Math'
    student_id: Optional[str] = None
    practiceset_id: Optional[str] = None
    title: Optional[str] = None

def _norm_diff(tag: Optional[str]) -> Optional[DiffTag]:
    if not tag:
        return None
    tag = tag.lower().strip()
    if tag in {"hard", "easy"}:
        return tag  # type: ignore
    return None

def _derive_module(section_field: str) -> ModuleTag:
    return "module1" if section_field.lower() == "static" else "module2"

def _maybe_get(d: dict, *keys: str) -> Optional[str]:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None

def parse_attempt_from_json(path: Path) -> Attempt:
    data = json.loads(Path(path).read_text())
    return _parse_attempt_common(data)

def parse_attempt_from_mongo(client: MongoClient, db_name: str, student_id: str) -> Attempt:
    col: Collection = client[db_name]["student_results"]
    docs = list(col.find({"student_id": student_id}))
    if not docs:
        raise ValueError(f"No attempts found for student_id={student_id}")
    return _parse_attempt_common(docs)

def _parse_attempt_common(rows: List[dict]) -> Attempt:
    if not rows:
        raise ValueError("Empty attempt data")

    # take some root metadata from first row
    meta = rows[0]
    student_id = meta.get("student_id")
    practiceset_id = meta.get("practicesetId")
    title = meta.get("title")

    by_subject: Dict[str, SectionAttempt] = {}
    for r in rows:
        subj = r.get("subject", {}).get("name") or r.get("subject")
        if subj not in by_subject:
            by_subject[subj] = SectionAttempt(subject=subj)

        section_raw = r.get("section")
        module = _derive_module(section_raw or "")
        module2_diff = _norm_diff(section_raw or "")

        # accept both 'complexity' and 'compleixty'
        difficulty = _maybe_get(r, "complexity", "compleixty")

        q = Question(
            question_id=r.get("question_id") or "",
            section=str(section_raw),
            module=module,
            module2_diff=module2_diff,
            correct=int(r.get("correct") or 0),
            time_spent=int(r.get("time_spent") or 0),
            subject=subj,
            unit=_maybe_get(r.get("unit", {}) if isinstance(r.get("unit"), dict) else {}, "name") if r.get("unit") else None,
            topic=_maybe_get(r.get("topic", {}) if isinstance(r.get("topic"), dict) else {}, "name") if r.get("topic") else None,
            difficulty=difficulty,
        )

        if module == "module1":
            by_subject[subj].module1.append(q)
        else:
            by_subject[subj].module2.append(q)

    # infer module2 difficulty
    for sec in by_subject.values():
        diffs = {_norm_diff(q.section) for q in sec.module2}
        diffs.discard(None)
        if len(diffs) == 1:
            sec.module2_diff = list(diffs)[0]  # type: ignore
        elif len(diffs) == 0:
            sec.module2_diff = None
        else:
            # mixed labels shouldn't happen; pick the most frequent tag
            from collections import Counter
            c = Counter([_norm_diff(q.section) for q in sec.module2 if _norm_diff(q.section)])
            sec.module2_diff = c.most_common(1)[0][0]  # type: ignore

    return Attempt(sections=by_subject, student_id=student_id, practiceset_id=practiceset_id, title=title)
