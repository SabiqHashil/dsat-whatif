# SAT What-If Analysis Tool

This project implements a **What-If Analysis** for SAT (Digital SAT) results to identify which questions have the most impact on a student’s score improvement.
It uses the official scoring maps and a student's test attempt data to simulate flipping incorrect answers to correct and re-calculating scaled scores, including **adaptive module penalties**.

---

## Features

* Imports SAT scoring model (`scoring_DSAT_v2.json`) and student attempt data into MongoDB (optional).
* Supports **file mode** (read directly from JSON) or **Mongo mode**.
* Simulates **adaptive scoring** for both Math and Reading & Writing:

  * Considers Module 1 performance’s impact on Module 2 difficulty (Easy vs Hard).
  * Applies penalty for Easy Module 2 as per scoring model.
* Calculates and ranks **high-impact questions** by potential score gain.
* Outputs:

  * CSV file with each question’s impact.
  * JSON summary with total score, per-section details, and top recommendations.

---

## Project Structure

```
dsat-whatif/
  ├─ dsat_whatif/                 # Core package
  │   ├─ analyzer.py              # What-If logic
  │   ├─ attempt_parser.py        # Parse attempt data
  │   ├─ scoring.py               # Load scoring map
  │   ├─ db.py                    # MongoDB utilities
  │   └─ utils.py
  ├─ scripts/
  │   └─ load_to_mongo.py         # Load JSON data into MongoDB
  ├─ outputs/                     # Generated results
  ├─ main.py                      # CLI to run analysis
  ├─ requirements.txt
  └─ README.md
```

---

## Installation

```bash
git clone <your-repo-url>
cd dsat-whatif
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Usage

### 1. Run in File Mode

```bash
python main.py \
  --scoring-file scoring_DSAT_v2.json \
  --attempt-file 67f2aae2c084263d16dbe462user_attempt_v2.json \
  --threshold 0.50 \
  --out outputs/student_v2
```

### 2. Run in MongoDB Mode

```bash
# Load data into MongoDB
python scripts/load_to_mongo.py \
  --mongo-uri mongodb://localhost:27017 \
  --db sat_analysis \
  --scoring-file scoring_DSAT_v2.json \
  --attempt-files 67f2aae2c084263d16dbe462user_attempt_v2.json \
                   66fece285a916f0bb5aea9c5user_attempt_v3.json

# Run analysis
python main.py \
  --use-mongo \
  --mongo-uri mongodb://localhost:27017 \
  --db sat_analysis \
  --student-id <student_id> \
  --threshold 0.50 \
  --out outputs/from_mongo_run
```

---

## Output

* `*_impacts.csv` → Ranked list of incorrect questions with score impact.
* `*_summary.json` → Total score, per-section breakdown, top recommendations.

---

## Notes

* Default **adaptive threshold** is `0.50` (50% correct in Module 1 triggers Hard Module 2).
* You can adjust with `--threshold <value>` if actual SAT data suggests a different cutoff.

---
