"""P1 step 7: shared evaluation + report for each split present in a run directory.

  python kev/make_report.py runs/kev/<run_id>
Writes metrics_<split>.json, confusion CSVs and report_<split>.md next to the logs (common/evaluate.py, report.py).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orchestrator.baselines.common.evaluate import evaluate   # noqa: E402
from orchestrator.baselines.common.report import write_report  # noqa: E402


def main():
    run_dir = Path(sys.argv[1])
    for split in ("validation", "test"):
        log = run_dir / f"{split}.jsonl"
        if not log.exists():
            print(f"{split}: no log, skipped")
            continue
        M = evaluate(log, split, run_json=run_dir / "run.json", out_dir=run_dir)
        write_report(M, run_dir / f"report_{split}.md")
        print(f"{split}: report written ({M['n_rows']} rows, {M['n_error_rows']} error rows)")


if __name__ == "__main__":
    main()
