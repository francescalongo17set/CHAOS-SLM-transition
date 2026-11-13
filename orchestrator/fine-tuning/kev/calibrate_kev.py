"""FT-P2 step 3: fit the temperature of a fine-tuned Kev checkpoint on the calibration partition and write it into head.pt.

  python kev/calibrate_kev.py --run runs/kev/kev-0.8b-ft-a/checkpoint --calibration data/kev/calibration.jsonl \
        --out runs/kev/kev-0.8b-ft-a/calibration [--device cuda]

Mirrors upstream skills/kev-finetune/scripts/kev_modal.py (score + write_meta): a raw-logit predictor (temperature 1.0),
kev.benchmark.evaluate_records on the calibration records, kev.metrics.fit_temperature(rows, aggregation="micro"), then the
value and its provenance go into head.pt (meta.temperature, extra["temperature_fit"]). The argmax never changes.
`scripts/calibrate_checkpoint.py` is not used: it refuses rows it cannot place and would call ours "in-distribution".
Needs torch + upstream kev. Run only after training; never on validation or test rows.
"""
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="checkpoint directory (adapter + head.pt)")
    ap.add_argument("--calibration", required=True)
    ap.add_argument("--out", required=True, help="fresh folder for the calibration report (evaluate_records refuses an existing one)")
    ap.add_argument("--device", default="cuda")
    a = ap.parse_args()

    from kev.benchmark import evaluate_records
    from kev.checkpoint import LoadOptions, read_meta, write_meta
    from kev.data import load_records
    from kev.metrics import fit_temperature
    from kev.predictors import LocalPredictor

    records = load_records(a.calibration)
    predictor = LocalPredictor(a.run, a.device, LoadOptions(temperature=1.0))     # fp32 exact path, raw logits
    report, rows = evaluate_records(records, predictor, Path(a.out))
    T = fit_temperature(rows, aggregation="micro")
    if not (T > 0 and T == T and T != float("inf")):
        raise SystemExit(f"BLOCKED: fitted temperature {T!r} is not a finite positive number")
    meta = read_meta(a.run)
    previous = meta.temperature
    meta.temperature = T
    meta.extra["temperature_fit"] = {"rows": str(Path(a.calibration).name), "n_records": len(records), "n_questions": len(rows),
                                     "method": "min NLL, micro, kev.metrics.fit_temperature (81-point grid 0.25..4)",
                                     "value": T, "previous": previous, "reason": "fit on our calibration partition (FT-C-07)"}
    write_meta(a.run, meta)
    Path(a.out, "temperature.json").write_text(json.dumps(meta.extra["temperature_fit"], indent=2), encoding="utf-8")
    print(f"temperature {T:.4f} (previous {previous:.4f}) on {len(records)} records, {len(rows)} questions")


if __name__ == "__main__":
    main()
