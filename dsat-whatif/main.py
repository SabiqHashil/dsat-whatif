import argparse
import json
from pathlib import Path
from dsat_whatif.analyzer import DSATWhatIfAnalyzer
from dsat_whatif.scoring import ScoringMaps
from dsat_whatif.attempt_parser import parse_attempt_from_json, parse_attempt_from_mongo
from dsat_whatif.db import MongoClientFactory
from dsat_whatif.utils import ensure_dir, to_csv, to_json

def run_from_json(scoring_file: Path, attempt_file: Path, threshold: float, out_prefix: Path):
    scoring_maps = ScoringMaps.from_file(scoring_file)
    attempt = parse_attempt_from_json(attempt_file)
    analyzer = DSATWhatIfAnalyzer(scoring_maps, adaptive_threshold=threshold)
    results = analyzer.analyze_attempt(attempt)

    ensure_dir(out_prefix.parent)
    to_csv(results['impacts_df'], out_prefix.with_name(out_prefix.name + "_impacts.csv"))
    to_json(results['summary'], out_prefix.with_name(out_prefix.name + "_summary.json"))
    print(f"Written: {out_prefix}_impacts.csv, {out_prefix}_summary.json")

def run_from_mongo(mongo_uri: str, db_name: str, student_id: str, threshold: float, out_prefix: Path):
    client = MongoClientFactory.get(mongo_uri)
    scoring_maps = ScoringMaps.from_mongo(client, db_name)
    attempt = parse_attempt_from_mongo(client, db_name, student_id)
    analyzer = DSATWhatIfAnalyzer(scoring_maps, adaptive_threshold=threshold)
    results = analyzer.analyze_attempt(attempt)

    ensure_dir(out_prefix.parent)
    to_csv(results['impacts_df'], out_prefix.with_name(out_prefix.name + "_impacts.csv"))
    to_json(results['summary'], out_prefix.with_name(out_prefix.name + "_summary.json"))
    print(f"Written: {out_prefix}_impacts.csv, {out_prefix}_summary.json")

def main():
    ap = argparse.ArgumentParser(description="DSAT What-If Analysis")
    ap.add_argument("--scoring-file", type=Path, help="scoring_DSAT_v2.json")
    ap.add_argument("--attempt-file", type=Path, help="student attempt json")
    ap.add_argument("--threshold", type=float, default=0.50, help="module 1 performance cut-off (0..1)")
    ap.add_argument("--out", type=Path, default=Path("outputs/run"))
    ap.add_argument("--use-mongo", action="store_true")
    ap.add_argument("--mongo-uri", type=str, default="mongodb://localhost:27017")
    ap.add_argument("--db", type=str, default="sat_analysis")
    ap.add_argument("--student-id", type=str, help="student_id to analyze (when using MongoDB)")
    args = ap.parse_args()

    if args.use_mongo:
        if not args.student_id:
            raise SystemExit("--student-id is required with --use-mongo")
        run_from_mongo(args.mongo_uri, args.db, args.student_id, args.threshold, args.out)
    else:
        if not args.scoring_file or not args.attempt_file:
            raise SystemExit("--scoring-file and --attempt-file required in file mode")
        run_from_json(args.scoring_file, args.attempt_file, args.threshold, args.out)

if __name__ == "__main__":
    main()
