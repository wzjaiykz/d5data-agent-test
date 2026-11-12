from __future__ import annotations

import pytest

from audit.ledger import GOLD, PACKAGE_DIR, PROBES, ROLLOUTS
from audit.scorer_audit import (
    effective_reward,
    frozen_artifact,
    load_declared_weights,
    load_effective_weights,
    load_frozen_policy,
    probe_r9,
    r9_dependency,
    sha256,
    weight_comparison,
)


def test_declared_weights_are_a_complete_100_percent_vector():
    declared = load_declared_weights()
    assert set(declared) == {"R1", "R2", "R3", "R4", "R5", "R6", "R7"}
    assert sum(declared.values()) == pytest.approx(1.0)


def test_effective_weights_are_also_a_complete_vector_but_a_different_one():
    effective = load_effective_weights()
    assert set(effective) == {"R4", "R5", "R6B", "R6E", "R9"}
    assert sum(effective.values()) == pytest.approx(1.0)
    declared = load_declared_weights()
    assert effective["R5"] == pytest.approx(0.055576)
    assert effective["R5"] < declared["R5"] / 4
    assert "R1" not in effective and "R2" not in effective and "R3" not in effective and "R7" not in effective
    assert "R9" not in declared


def test_public_and_effective_weight_table_is_not_equal():
    table = {row["item"]: row for row in weight_comparison()}
    assert table["R1"]["declared"] == pytest.approx(0.05)
    assert table["R1"]["effective"] == 0
    assert table["R5"]["declared"] == pytest.approx(0.25)
    assert table["R5"]["effective"] == pytest.approx(0.055576)
    assert table["R6"]["declared"] == pytest.approx(0.10)
    assert table["R6"]["effective"] == pytest.approx(0.65)


def test_all_five_rollouts_are_frozen_by_hash():
    frozen = load_frozen_policy()
    for path in sorted(ROLLOUTS.glob("*.xlsx")):
        assert sha256(path) in frozen["artifacts"]
        assert frozen_artifact(path) is not None


def test_frozen_reward_is_reproduced_by_the_effective_formula():
    for path in sorted(ROLLOUTS.glob("*.xlsx")):
        record = frozen_artifact(path)
        assert record is not None
        assert effective_reward(record["completion"]) == pytest.approx(record["reward"], abs=1e-12)


def test_r9_accepts_a_shell_and_rejects_gold():
    gold_score, gold_points = r9_dependency(GOLD)
    probe_score, probe_points = probe_r9()["probe-03.xlsx"]
    assert gold_score == 0.0
    assert probe_score == 1.0
    assert gold_points == [0, 0, 0, 0, 0, 0]
    assert probe_points == [1, 1, 1, 1, 1, 1]


def test_declared_deductions_are_not_in_the_effective_policy():
    text = (PACKAGE_DIR / "scorer" / "fresh_owner_policy.py").read_text(encoding="utf-8")
    assert "D-素材回声" not in text
    assert "D-形式替代实质" not in text
    assert "D-自证替代证据" not in text
    assert "alpha" in text


def test_probe_files_are_not_frozen_rollouts():
    frozen = load_frozen_policy()["artifacts"]
    for path in sorted(PROBES.glob("*.xlsx")):
        assert sha256(path) not in frozen
