import argparse
import json
from pathlib import Path
from pymongo import MongoClient

def load_scoring(col, scoring_file: Path):
    data = json.loads(Path(scoring_file).read_text())
    col.delete_many({})
    col.insert_many(data)
    print(f"Inserted scoring maps: {len(data)} docs")

def load_attempts(col, attempt_files):
    for p in attempt_files:
        rows = json.loads(Path(p).read_text())
        # Upsert each row; or simply insert_many for demo
        col.insert_many(rows)
        # Extract basic student id for info
        sid = rows[0].get("student_id")
        print(f"Inserted {len(rows)} attempt rows for student_id={sid}")

def main():
    ap = argparse.ArgumentParser(description="Load scoring & attempts into MongoDB")
    ap.add_argument("--mongo-uri", type=str, default="mongodb://localhost:27017")
    ap.add_argument("--db", type=str, default="sat_analysis")
    ap.add_argument("--scoring-file", type=Path, required=True)
    ap.add_argument("--attempt-files", type=Path, nargs="+", required=True)
    args = ap.parse_args()

    client = MongoClient(args.mongo_uri)
    db = client[args.db]
    load_scoring(db["sat_scoring"], args.scoring_file)
    load_attempts(db["student_results"], args.attempt_files)

if __name__ == "__main__":
    main()
