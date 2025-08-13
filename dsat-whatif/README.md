# DSAT What‑If Analysis (Starter Project)

This project analyzes **which DSAT questions (Reading & Writing, Math)** would have contributed the **most to a student’s total scaled score improvement**.  
It uses the provided scoring map and two student attempt files and simulates flipping each incorrect answer to correct, taking into account the **adaptive module** (easy/hard) rules.

---

## Quick Start

### 1) Clone / unzip
Unzip this folder or clone the GitHub repo you create from it.

### 2) Create a virtual environment & install deps
```bash
python -m venv .venv
. .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3) Place the provided files
Copy these files into the project root or update paths via CLI flags:

- `scoring_DSAT_v2.json`
- `67f2aae2c084263d16dbe462user_attempt_v2.json`
- `66fece285a916f0bb5aea9c5user_attempt_v3.json`

(They are already in this workspace if you downloaded the zip produced here.)

### 4) (Optional) Load into MongoDB
If you have MongoDB running locally:

```bash
python scripts/load_to_mongo.py \
  --mongo-uri mongodb://localhost:27017 \
  --db sat_analysis \
  --scoring-file scoring_DSAT_v2.json \
  --attempt-files 67f2aae2c084263d16dbe462user_attempt_v2.json 66fece285a916f0bb5aea9c5user_attempt_v3.json
```

Collections created:
- `sat_scoring`
- `student_results`

> If MongoDB isn’t available, the analysis runs **directly from the JSON files**.

### 5) Run analysis (JSON files)
```bash
python main.py \
  --scoring-file scoring_DSAT_v2.json \
  --attempt-file 67f2aae2c084263d16dbe462user_attempt_v2.json \
  --threshold 0.50 \
  --out outputs/student_v2
```

Run for second student:
```bash
python main.py \
  --scoring-file scoring_DSAT_v2.json \
  --attempt-file 66fece285a916f0bb5aea9c5user_attempt_v3.json \
  --threshold 0.50 \
  --out outputs/student_v3
```

Outputs per run:
- CSV: `*_impacts.csv` → ranked question-level impacts
- JSON: `*_summary.json` → current scores + insights

### 6) Run analysis (MongoDB)
```bash
python main.py \
  --use-mongo \
  --mongo-uri mongodb://localhost:27017 \
  --db sat_analysis \
  --student-id <student_id_from_json> \
  --threshold 0.50 \
  --out outputs/from_mongo_run
```

---

## How it works

1. **Parse** student attempt:
   - Split by **subject** (“Reading and Writing”, “Math”) and **module** (Module 1 = `Static`; Module 2 = `hard` or `easy`).
2. **Compute current score**:
   - Raw = correct answers across both modules in a section.
   - Scaled = lookup from `scoring_DSAT_v2.json` using the section’s Module 2 difficulty.
3. **What‑If for each incorrect Q**:
   - Flip that single question to **correct**.
   - If it’s **Module 1** and current Module 2 is `easy`, check if the new Module 1 performance **crosses the threshold** → if yes, switch Module 2 to `hard`.
   - Recalculate scaled score and compute **impact** = (new_total_scaled − current_total_scaled).
4. **Rank questions** by impact and export.

**Threshold (adaptive cut‑off)**  
Default is `0.50` (= 50% correct in Module 1). Make it configurable (`--threshold`) and tune later with your data.

---

## Notes

- Handles the misspelled field `compleixty` (falls back to `complexity`).
- If a section *already* has Module 2 = `hard`, flipping M1 questions will **not** change the path (but still increases raw score).
- You can add topic clustering, time‑spent weights, etc., later.

---

## Project Tree
```
dsat-whatif/
  ├─ dsat_whatif/
  │   ├─ __init__.py
  │   ├─ analyzer.py
  │   ├─ attempt_parser.py
  │   ├─ config.py
  │   ├─ db.py
  │   ├─ scoring.py
  │   └─ utils.py
  ├─ scripts/
  │   └─ load_to_mongo.py
  ├─ outputs/
  ├─ tests/
  ├─ main.py
  ├─ requirements.txt
  └─ README.md
```

Happy shipping!
