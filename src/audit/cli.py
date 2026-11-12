"""Command-line audit report used by the README and CI."""
from __future__ import annotations

import argparse
import sys

from .ledger import (
    EXPECTED_TOTALS,
    GOLD,
    PACKAGE_DIR,
    PROBES,
    ROLLOUTS,
    bridge,
    dayparts,
    read_ledger,
    validate_baseline,
)
from .scorer_audit import (
    effective_reward,
    frozen_artifact,
    load_effective_weights,
    load_frozen_policy,
    load_declared_weights,
    probe_r9,
    r9_dependency,
    score_table,
    sha256,
    weight_comparison,
)


def _pct(value: float) -> str:
    return f"{value * 100:.4f}%"


def _print_baseline() -> None:
    ledger = read_ledger()
    validate_baseline(ledger)
    print("SOURCE BASELINE (recomputed from the 36 leaf rows, not Gold)")
    print("period       base -> current   net    continuing / new / closed       breakfast / lunch / dinner")
    for key in ("2023→2024", "2024→2025"):
        period = ledger[key]
        b = bridge(period)
        d = dayparts(period)
        parts = [b[s] for s in ("持续经营", "新开", "关闭")]
        bridge_text = " / ".join(f"{p['impact']:+d} ({_pct(float(p['contribution']))})" for p in parts)
        day_text = " / ".join(
            f"{d[x]['change']:+d} ({_pct(float(d[x]['contribution']))})" for x in ("早餐", "午餐", "晚餐")
        )
        print(f"{key}   {period.total_base:3d} -> {period.total_current:3d}      {period.net:+3d}    {bridge_text}    {day_text}")
    print()
    for key in ("2023→2024", "2024→2025"):
        period = ledger[key]
        print(f"STATUS {key}: " + ", ".join(f"{store}={period.status(store)}" for store in period.stores))
    print()


def _print_scores() -> None:
    print("ROLLOUT SCORES (frozen hash path; effective owner weights, not public weights)")
    for row in score_table():
        completion = row["completion"]
        effective = effective_reward(completion) if completion else None
        print(
            f"{row['file']:14s} frozen={str(row['frozen']):5s} "
            f"stored={row['reward']:.6f} effective_from_completion={effective:.6f}"
        )
        if completion:
            zeros = [key for key, value in completion.items() if float(value) == 0]
            partial = {key: round(float(value), 6) for key, value in completion.items() if 0 < float(value) < 1}
            print(f"  zeros={zeros}")
            print(f"  partial={partial}")
    gold = frozen_artifact(GOLD)
    print(f"Gold frozen={bool(gold)} stored={gold['reward'] if gold else None}")
    print()


def _print_weights() -> None:
    print("DECLARED vs EFFECTIVE WEIGHTS")
    print("item   declared   effective")
    for row in weight_comparison():
        print(f"{row['item']:4s}   {row['declared'] * 100:7.3f}%   {row['effective'] * 100:7.3f}%")
    print(f"sum effective = {sum(load_effective_weights().values()) * 100:.3f}%")
    print(f"declared weights = {load_declared_weights()}")
    print(f"effective weights = {load_effective_weights()}")
    print()


def _print_r9() -> None:
    print("UNDISCLOSED R9 FORMULA-DEPENDENCY HEURISTIC")
    for path in [GOLD] + sorted(PROBES.glob("*.xlsx")) + sorted(ROLLOUTS.glob("*.xlsx")):
        value, points = r9_dependency(path)
        print(f"{path.name:18s} R9={value:.6f} points={points}")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit the supplied restaurant traffic evaluation package.")
    parser.add_argument("--check", action="store_true", help="fail on baseline, ledger or weight inconsistencies")
    args = parser.parse_args(argv)

    _print_baseline()
    _print_scores()
    _print_weights()
    _print_r9()

    if args.check:
        ledger = read_ledger()
        validate_baseline(ledger)
        for key, expected in EXPECTED_TOTALS.items():
            assert (ledger[key].total_base, ledger[key].total_current, ledger[key].net) == expected
        effective = load_effective_weights()
        assert abs(sum(effective.values()) - 1.0) < 1e-12, effective
        # The audit's central finding: the public and scored vectors differ.
        assert effective["R5"] < 0.10, effective
        assert "R9" not in load_declared_weights()
        frozen = load_frozen_policy()
        for path in sorted(ROLLOUTS.glob("*.xlsx")):
            assert sha256(path) in frozen["artifacts"], path
        print("CHECK OK: source closes, Gold hash is frozen, public/effective weights differ as documented.")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
