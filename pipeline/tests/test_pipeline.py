import ast
import dataclasses
import importlib
import json
import typing
from pathlib import Path

import pytest

import pipeline.run as p
from contracts.orchestrator import ROUTES, OrchestratorOut
from contracts.safety import SafetyOut

ROOT = Path(__file__).resolve().parents[2]
SYSTEMS = {  # top-level import name -> folder
    "safety": "safety", "orch": "orchestrator/src", "quick_reply": "quick_reply",
    "lightweight": "lightweight/src", "agentic": "agentic", "verification": "verification",
}
EXAMPLES = {  # example file / contracts module -> class prefix
    "safety": "Safety", "orchestrator": "Orchestrator", "quick_reply": "QuickReply",
    "lightweight": "Lightweight", "agentic": "Agentic", "verification": "Verification",
}


@pytest.mark.parametrize("route", ROUTES)
def test_every_route(monkeypatch, route):
    monkeypatch.setattr(p.orch.run, "run", lambda x: OrchestratorOut(route, "test", 1.0))
    expected = p.REFUSAL if route == "refuse" else f"[{route} stub] not implemented yet"
    assert p.run("q").text == expected


def test_blocked_never_reaches_orchestrator(monkeypatch):
    monkeypatch.setattr(p.safety.run, "run", lambda x: SafetyOut(False, "SECURITY_BLOCK", user_message="no"))
    monkeypatch.setattr(p.orch.run, "run", lambda x: pytest.fail("called"))
    assert p.run("q").text == "no"


def test_systems_do_not_import_each_other():
    for name, folder in SYSTEMS.items():
        files = list((ROOT / folder).rglob("*.py"))
        assert files, folder
        for f in files:
            for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    mods = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    mods = [node.module]
                else:
                    continue
                for m in mods:
                    assert m.split(".")[0] not in (set(SYSTEMS) | {"pipeline"}) - {name}, f"{f} imports {m}"


def build(tp, value):
    """JSON value -> contract type; fails on missing or unknown keys."""
    if dataclasses.is_dataclass(tp):
        hints = typing.get_type_hints(tp)
        assert set(value) == set(hints), f"{tp.__name__}: {set(value) ^ set(hints)}"
        return tp(**{k: build(hints[k], v) for k, v in value.items()})
    args = typing.get_args(tp)
    if typing.get_origin(tp) is list:
        return [build(args[0], v) for v in value]
    if args:  # Optional[X]
        return None if value is None else build(args[0], value)
    assert isinstance(value, (int, float) if tp is float else tp), f"{value!r} is not {tp}"
    return value


@pytest.mark.parametrize("name,prefix", EXAMPLES.items())
def test_examples_match_contracts(name, prefix):
    module = importlib.import_module(f"contracts.{name}")
    data = json.loads((ROOT / "contracts" / "examples" / f"{name}.json").read_text(encoding="utf-8"))
    for side in ("In", "Out"):
        build(getattr(module, prefix + side), data[side.lower()])
