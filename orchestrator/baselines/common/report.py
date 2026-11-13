"""report.md writer (chapter 05, 'Report format'). Takes the metrics dict from evaluate()."""
from pathlib import Path


def _f(x, d=3):
    return "n/a" if x is None else (f"{x:.{d}f}" if isinstance(x, float) else str(x))


def _quality(title, m):
    L = [f"### {title}", "", f"n = {m['n']} · accuracy {_f(m['accuracy'])} · macro-F1 {_f(m['macro_f1'])}", "",
         "| class | precision | recall | F1 | support |", "|---|---|---|---|---|"]
    for c, v in m["per_class"].items():
        L.append(f"| {c} | {_f(v['precision'])} | {_f(v['recall'])} | {_f(v['f1'])} | {v['support']} |")
    return L + [""]


def render(M):
    run = M.get("run", {})
    L = [f"# Report · {M['pipeline']} · {M['split']}", "", "## Run header", "",
         f"- model: `{M['model_id']}` @ `{M['model_revision']}`",
         f"- dtype {run.get('dtype', 'n/a')} · device {run.get('device', 'n/a')} · latency mode {run.get('latency_mode', 'n/a')}",
         f"- libraries: {run.get('libraries', 'n/a')}",
         f"- rows {M['n_rows']} · error rows {M['n_error_rows']} · truncated {M['n_truncated']}",
         f"- dispatcher oracle (gold fields): {M['dispatcher_oracle']['matches']}/{M['dispatcher_oracle']['n']}", "",
         "## Quality", ""]
    for k in ("scope_check", "feature_classification", "complexity_estimation"):
        L += _quality(k + (" (gold in_scope rows)" if k == "complexity_estimation" else ""), M[k])
    L += _quality("route, end-to-end (tau=None)", M["route"])
    L += ["### Route attribution (first wrong field for each wrong route)", "", "| first wrong | n |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in sorted(M["route_attribution"].items(), key=lambda kv: -kv[1])] + [""]
    rr = M["refuse_recall"]
    L += ["## Refusal recall", "", "| slice | gold refuse | recall |", "|---|---|---|"]
    for name in ("all", "safety_leak", "non_leak"):
        L.append(f"| {name} | {rr[name]['n_gold_refuse']} | {_f(rr[name]['recall'])} |")
    for t, v in rr["by_leak_type"].items():
        L.append(f"| leak: {t} | {v['n_gold_refuse']} | {_f(v['recall'])} |")
    L += ["", "## Calibration (probabilities as shipped, 10 bins)", "", "| question | n | ECE | Brier |", "|---|---|---|---|"]
    for k, v in M["calibration"].items():
        L.append(f"| {k} | {v['n']} | {_f(v['ece'])} | {_f(v['brier'])} |")
    L += ["", "## Tokens, latency, size", "", "| quantity | n | mean | median | p95 | total |", "|---|---|---|---|---|---|"]
    for k, v in M["tokens"].items():
        L.append(f"| {k} | {v.get('n')} | {_f(v.get('mean'), 1)} | {_f(v.get('median'), 1)} | {_f(v.get('p95'), 1)} | {_f(v.get('total'), 0)} |")
    lt = M["latency_ms"]
    L.append(f"| latency_ms | {lt.get('n')} | {_f(lt.get('mean'), 1)} | {_f(lt.get('p50'), 1)} | {_f(lt.get('p95'), 1)} | |")
    L += ["", f"Warm-up rows excluded from latency: {lt.get('n_warmup_excluded')}.", ""]
    ms = run.get("model_size")
    if ms:
        L.append(f"Model size: {ms}")
    return "\n".join(L) + "\n"


def write_report(M, path):
    Path(path).write_text(render(M), encoding="utf-8")
