from __future__ import annotations

import pytest

from audit.ledger import (
    EXPECTED_BRIDGE,
    EXPECTED_DAYPARTS,
    EXPECTED_STATUS,
    EXPECTED_TOTALS,
    bridge,
    dayparts,
    read_ledger,
    validate_baseline,
)


@pytest.fixture(scope="module")
def ledger():
    data = read_ledger()
    validate_baseline(data)
    return data


def test_totals_are_recomputed_from_leaves(ledger):
    for key, (base, current, net) in EXPECTED_TOTALS.items():
        period = ledger[key]
        assert (period.total_base, period.total_current, period.net) == (base, current, net)
        assert sum(row.base for row in period.rows) == base
        assert sum(row.current for row in period.rows) == current
        assert sum(row.change for row in period.rows) == net


def test_each_period_has_eighteen_leaves_and_three_dayparts(ledger):
    for period in ledger.values():
        assert len(period.rows) == 18
        assert len(period.stores) == 6
        for store in period.stores:
            assert {row.daypart for row in period.rows if row.store == store} == {"早餐", "午餐", "晚餐"}


def test_store_bridge_matches_expected_signs_and_denominator(ledger):
    for key, expected in EXPECTED_BRIDGE.items():
        actual = bridge(ledger[key])
        for status, (impact, contribution) in expected.items():
            assert actual[status]["impact"] == impact
            assert actual[status]["contribution"] == pytest.approx(contribution, abs=1e-12)
        assert sum(item["impact"] for item in actual.values()) == ledger[key].net
        assert sum(item["contribution"] for item in actual.values()) == pytest.approx(1.0, abs=1e-12)


def test_daypart_three_way_chains_close(ledger):
    for key, expected in EXPECTED_DAYPARTS.items():
        actual = dayparts(ledger[key])
        for daypart, (change, components, contribution) in expected.items():
            assert actual[daypart]["change"] == change
            assert actual[daypart]["components"] == components
            assert sum(actual[daypart]["components"]) == change
            assert actual[daypart]["contribution"] == pytest.approx(contribution, abs=1e-12)
        assert sum(item["change"] for item in actual.values()) == ledger[key].net
        assert sum(item["contribution"] for item in actual.values()) == pytest.approx(1.0, abs=1e-12)


def test_statuses_are_period_scoped_not_store_permanent(ledger):
    for key, expected in EXPECTED_STATUS.items():
        assert {store: ledger[key].status(store) for store in expected} == expected
    assert ledger["2023→2024"].status("湖滨店") == "新开"
    assert ledger["2024→2025"].status("湖滨店") == "持续经营"
    assert ledger["2023→2024"].status("西苑店") == "持续经营"
    assert ledger["2024→2025"].status("西苑店") == "关闭"
    assert ledger["2023→2024"].status("北站店") == "持续经营"
    assert ledger["2024→2025"].status("北站店") == "持续经营"


def test_new_and_closed_placeholders_are_zero_and_not_yoy(ledger):
    first = ledger["2023→2024"]
    second = ledger["2024→2025"]
    for row in first.rows:
        if row.store == "湖滨店":
            assert row.status == "新开" and row.base == 0
        if row.store == "客运港店":
            assert row.status == "关闭" and row.current == 0
    for row in second.rows:
        if row.store == "云庭店":
            assert row.status == "新开" and row.base == 0
        if row.store == "西苑店":
            assert row.status == "关闭" and row.current == 0
