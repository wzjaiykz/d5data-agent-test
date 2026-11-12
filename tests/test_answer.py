from __future__ import annotations

import re
from pathlib import Path

ANSWER = Path(__file__).resolve().parents[1] / "answer.md"


def test_answer_has_all_required_sections():
    text = ANSWER.read_text(encoding="utf-8")
    for heading in (
        "## 0. Tools and independent re-verification",
        "## 1. Task feasibility and factual baseline",
        "## 2. Rollout risk-oriented spot check",
        "## 3. Probe review",
        "## 4. Scorer diagnosis and rubric redesign",
        "## 5. Acceptance verdict and regression tests",
    ):
        assert heading in text
    assert "任务状态：需要返修" in text
    assert "评分器状态：不可用" in text


def test_new_rubric_has_eight_weighted_items_summing_to_100():
    text = ANSWER.read_text(encoding="utf-8")
    rows = re.findall(r"^\|\s*R([1-8])\s*\|[^|]*\|\s*([0-9]+)%\s*\|", text, flags=re.MULTILINE)
    assert len(rows) == 8, rows
    assert [int(item[0]) for item in rows] == list(range(1, 9))
    assert sum(int(item[1]) for item in rows) == 100


def test_answer_contains_at_least_four_distinct_regression_tests():
    text = ANSWER.read_text(encoding="utf-8")
    tests = re.findall(r"^\|\s*T([1-9])\b", text, flags=re.MULTILINE)
    assert len(tests) >= 4
    assert len(set(tests)) == len(tests)


def test_answer_contains_at_least_one_false_positive_and_false_negative():
    text = ANSWER.read_text(encoding="utf-8").lower()
    assert "false positive" in text
    assert "false negative" in text
    assert "probe-03" in text
    assert "rollout-01" in text


def test_answer_mentions_quantified_facts_and_scorer_evidence():
    text = ANSWER.read_text(encoding="utf-8")
    for fact in ("2023→2024", "2024→2025", "+48", "+59", "0.947368", "5.5576", "65%"):
        assert fact in text
