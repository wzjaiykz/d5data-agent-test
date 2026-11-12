"""Static inspection of the supplied scoring policy and score ledger."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from .ledger import PACKAGE_DIR, SCORER


DECLARED_PARAMS = SCORER / "scoring_params.json"
FROZEN_POLICY = SCORER / "frozen_owner_policy.json"
FRESH_POLICY = SCORER / "fresh_owner_policy.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_declared_weights() -> dict[str, float]:
    return json.loads(DECLARED_PARAMS.read_text(encoding="utf-8"))["positive_weights"]


def _literal_assignment(path: Path, name: str) -> Any:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise ValueError(f"{name} not found in {path}")


def load_effective_weights() -> dict[str, float]:
    return {key: float(value) for key, value in _literal_assignment(FRESH_POLICY, "WEIGHTS").items()}


def load_alpha() -> dict[str, float]:
    return {key: float(value) for key, value in _literal_assignment(FRESH_POLICY, "ALPHA").items()}


def load_frozen_policy() -> dict[str, Any]:
    return json.loads(FROZEN_POLICY.read_text(encoding="utf-8"))


def frozen_artifact(path: Path) -> dict[str, Any] | None:
    return load_frozen_policy()["artifacts"].get(sha256(path))


def credit(completion: float, alpha: float) -> float:
    return 1.0 if completion == 1 else alpha * completion


def effective_reward(completion: dict[str, float]) -> float:
    weights = load_effective_weights()
    alpha = load_alpha()
    return sum(weight * credit(float(completion.get(owner, 0.0)), alpha[owner]) for owner, weight in weights.items())


def load_fresh_policy_module():
    spec = importlib.util.spec_from_file_location("audit_fresh_owner_policy", FRESH_POLICY)
    if spec is None or spec.loader is None:
        raise ImportError(FRESH_POLICY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def r9_dependency(path: Path) -> tuple[float, list[int]]:
    """Run the actual, undisclosed R9 heuristic from the supplied snapshot."""
    module = load_fresh_policy_module()
    return module.r9_dependency(path)


def r8_traceability(path: Path) -> tuple[float, list[int]]:
    module = load_fresh_policy_module()
    return module.r8_traceability(path)


def score_table() -> list[dict[str, Any]]:
    frozen = load_frozen_policy()
    rows: list[dict[str, Any]] = []
    for path in sorted((PACKAGE_DIR / "rollouts").glob("*.xlsx")):
        digest = sha256(path)
        record = frozen["artifacts"].get(digest, {})
        rows.append(
            {
                "file": path.name,
                "sha256": digest,
                "frozen": bool(record),
                "reward": record.get("reward"),
                "completion": record.get("completion", {}),
            }
        )
    return rows


def weight_comparison() -> list[dict[str, float | str]]:
    declared = load_declared_weights()
    effective = load_effective_weights()
    rows = []
    for key in ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9"):
        if key == "R6":
            effective_value = sum(float(effective.get(part, 0.0)) for part in ("R6A", "R6B", "R6C", "R6D", "R6E", "R6F"))
        else:
            effective_value = float(effective.get(key, 0.0))
        rows.append(
            {
                "item": key,
                "declared": float(declared.get(key, 0.0)),
                "effective": effective_value,
            }
        )
    return rows


def load_current_scores() -> str:
    return (PACKAGE_DIR / "rollouts" / "current_scores.md").read_text(encoding="utf-8")


def probe_r9() -> dict[str, tuple[float, list[int]]]:
    return {path.name: r9_dependency(path) for path in sorted((PACKAGE_DIR / "probes").glob("*.xlsx"))}
