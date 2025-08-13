from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, Literal, List, Tuple
import copy
import pandas as pd

from .attempt_parser import Attempt, SectionAttempt, Question
from .scoring import ScoringMaps, Difficulty

@dataclass
class SectionScore:
    subject: str
    raw: int
    scaled: int
    module2_diff: Difficulty

@dataclass
class TotalScore:
    total_scaled: int
    by_section: Dict[str, SectionScore]

class DSATWhatIfAnalyzer:
    def __init__(self, scoring_maps: ScoringMaps, adaptive_threshold: float = 0.50):
        self.scoring_maps = scoring_maps
        if not (0.0 <= adaptive_threshold <= 1.0):
            raise ValueError("adaptive_threshold must be in [0,1]")
        self.adaptive_threshold = adaptive_threshold

    # ---- Helpers ----
    def _section_score(self, sec: SectionAttempt) -> SectionScore:
        raw = sum(q.correct for q in (sec.module1 + sec.module2))
        # infer difficulty: if labeled, use it; else fallback by threshold
        diff = sec.module2_diff
        if diff is None:
            m1_total = len(sec.module1)
            m1_correct = sum(q.correct for q in sec.module1)
            perf = (m1_correct / m1_total) if m1_total else 0.0
            diff = "hard" if perf >= self.adaptive_threshold else "easy"
        scaled = self.scoring_maps.get(sec.subject).scaled(raw, diff)
        return SectionScore(subject=sec.subject, raw=raw, scaled=scaled, module2_diff=diff)

    def _total_score(self, attempt: Attempt) -> TotalScore:
        scores: Dict[str, SectionScore] = {}
        for subj, sec in attempt.sections.items():
            scores[subj] = self._section_score(sec)
        total = sum(s.scaled for s in scores.values())
        return TotalScore(total_scaled=total, by_section=scores)

    # ---- What-if for one question ----
    def _flip_one(self, attempt: Attempt, subject: str, qidx: int, in_module1: bool) -> TotalScore:
        # deep copy to avoid mutating original
        attempt2 = copy.deepcopy(attempt)
        sec = attempt2.sections[subject]
        target_list = sec.module1 if in_module1 else sec.module2
        target_q = target_list[qidx]

        # already correct? if yes, impact is zero — but caller should only pass incorrect items
        if target_q.correct == 1:
            return self._total_score(attempt2)

        # Flip this one to correct
        target_q.correct = 1

        # If the flipped question is in Module 1 AND the section was 'easy',
        # check whether the Module 2 path upgrades to 'hard' under the threshold rule.
        if in_module1:
            m1_total = len(sec.module1)
            m1_correct = sum(q.correct for q in sec.module1)
            perf = (m1_correct / m1_total) if m1_total else 0.0
            # Only upgrade if currently easy
            current_sec = attempt.sections[subject]
            current_diff = current_sec.module2_diff
            # compute from original attempt's sec
            if current_diff is None:
                # if unlabeled originally, treat as threshold-based both before and after
                current_diff = "hard" if (sum(q.correct for q in attempt.sections[subject].module1) / m1_total) >= self.adaptive_threshold else "easy"
            if current_diff == "easy" and perf >= self.adaptive_threshold:
                sec.module2_diff = "hard"

        return self._total_score(attempt2)

    # ---- Public: analyze entire attempt ----
    def analyze_attempt(self, attempt: Attempt) -> Dict:
        # current score
        current = self._total_score(attempt)

        rows: List[Dict] = []
        for subj, sec in attempt.sections.items():
            # collect incorrect in module1 and module2
            m1_incorrect = [(i, q) for i, q in enumerate(sec.module1) if q.correct == 0]
            m2_incorrect = [(i, q) for i, q in enumerate(sec.module2) if q.correct == 0]

            for i, q in m1_incorrect:
                new_total = self._flip_one(attempt, subj, i, in_module1=True)
                impact_total = new_total.total_scaled - current.total_scaled
                rows.append({
                    "subject": subj,
                    "module": 1,
                    "module2_difficulty_current": sec.module2_diff or "threshold_based",
                    "question_id": q.question_id,
                    "unit": q.unit,
                    "topic": q.topic,
                    "difficulty": q.difficulty,
                    "time_spent": q.time_spent,
                    "impact_total_scaled": impact_total,
                    "impact_section_scaled": new_total.by_section[subj].scaled - current.by_section[subj].scaled,
                    "raw_before": current.by_section[subj].raw,
                    "raw_after": new_total.by_section[subj].raw,
                    "scaled_before": current.by_section[subj].scaled,
                    "scaled_after": new_total.by_section[subj].scaled,
                })

            for i, q in m2_incorrect:
                new_total = self._flip_one(attempt, subj, i, in_module1=False)
                impact_total = new_total.total_scaled - current.total_scaled
                rows.append({
                    "subject": subj,
                    "module": 2,
                    "module2_difficulty_current": sec.module2_diff or "threshold_based",
                    "question_id": q.question_id,
                    "unit": q.unit,
                    "topic": q.topic,
                    "difficulty": q.difficulty,
                    "time_spent": q.time_spent,
                    "impact_total_scaled": impact_total,
                    "impact_section_scaled": new_total.by_section[subj].scaled - current.by_section[subj].scaled,
                    "raw_before": current.by_section[subj].raw,
                    "raw_after": new_total.by_section[subj].raw,
                    "scaled_before": current.by_section[subj].scaled,
                    "scaled_after": new_total.by_section[subj].scaled,
                })

        # Rank by total impact desc, keep stable order for ties
        import pandas as pd
        impacts_df = pd.DataFrame(rows).sort_values(
            by=["impact_total_scaled", "subject", "module"], ascending=[False, True, True]
        ).reset_index(drop=True)

        summary = {
            "student_id": attempt.student_id,
            "title": attempt.title,
            "current_total_scaled": current.total_scaled,
            "current_by_section": {
                subj: {
                    "raw": s.raw,
                    "scaled": s.scaled,
                    "module2_difficulty": s.module2_diff,
                } for subj, s in current.by_section.items()
            },
            "top5": impacts_df.head(5).to_dict(orient="records"),
            "threshold_used": self.adaptive_threshold,
            "notes": [
                "Module 1 flips can also upgrade Module 2 from easy→hard if threshold is crossed.",
                "Impacts include both raw→scaled change and any adaptive difficulty upgrade.",
            ],
        }
        return {"impacts_df": impacts_df, "summary": summary}
