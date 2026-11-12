"""Independent, read-only recomputation of the restaurant traffic ledger.

The functions here do not trust the Gold workbook.  They read the two source
sheets and derive the totals, the store-portfolio bridge and the daypart
chains used in the audit answer.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from openpyxl import load_workbook


PACKAGE_DIR = Path(__file__).resolve().parents[2] / "restaurant-portfolio-traffic-change-audit"
MATERIALS = PACKAGE_DIR / "materials" / "门店餐段客流台账.xlsx"
GOLD = PACKAGE_DIR / "gold" / "expected_answer.xlsx"
ROLLOUTS = PACKAGE_DIR / "rollouts"
PROBES = PACKAGE_DIR / "probes"
SCORER = PACKAGE_DIR / "scorer"


@dataclass(frozen=True)
class Period:
    key: str
    base_year: int
    current_year: int
    sheet: str


PERIODS = (
    Period("2023→2024", 2023, 2024, "客流对比_2024"),
    Period("2024→2025", 2024, 2025, "客流对比_2025"),
)

# The expected statuses are part of the audit baseline, not copied from a
# workbook.  The two comparison boundaries are deliberately independent.
EXPECTED_STATUS = {
    "2023→2024": {
        "青禾店": "持续经营",
        "西苑店": "持续经营",
        "星港店": "持续经营",
        "北站店": "持续经营",
        "湖滨店": "新开",
        "客运港店": "关闭",
    },
    "2024→2025": {
        "青禾店": "持续经营",
        "西苑店": "关闭",
        "星港店": "持续经营",
        "北站店": "持续经营",
        "湖滨店": "持续经营",
        "云庭店": "新开",
    },
}

# The four test files and the expected aggregate figures are fixed audit
# facts.  They make accidental changes to the fixture visible immediately.
EXPECTED_TOTALS = {
    "2023→2024": (374, 422, 48),
    "2024→2025": (422, 481, 59),
}

EXPECTED_BRIDGE = {
    "2023→2024": {
        "持续经营": (23, 0.4791666666666667),
        "新开": (89, 1.854166666666667),
        "关闭": (-64, -1.333333333333333),
    },
    "2024→2025": {
        "持续经营": (31, 0.5254237288135594),
        "新开": (79, 1.338983050847458),
        "关闭": (-51, -0.864406779661017),
    },
}

EXPECTED_DAYPARTS = {
    "2023→2024": {
        "早餐": (-11, (4, 7, -22), -0.2291666666666667),
        "午餐": (21, (11, 34, -24), 0.4375),
        "晚餐": (38, (8, 48, -18), 0.7916666666666666),
    },
    "2024→2025": {
        "早餐": (1, (4, 6, -9), 0.01694915254237288),
        "午餐": (17, (12, 29, -24), 0.288135593220339),
        "晚餐": (41, (15, 44, -18), 0.6949152542372882),
    },
}


@dataclass(frozen=True)
class StoreDay:
    period: str
    store: str
    store_format: str
    daypart: str
    status: str
    base: int
    current: int
    base_cell: str
    current_cell: str

    @property
    def change(self) -> int:
        return self.current - self.base


@dataclass
class PeriodData:
    period: Period
    rows: list[StoreDay]
    total_base: int
    total_current: int

    @property
    def net(self) -> int:
        return self.total_current - self.total_base

    @property
    def stores(self) -> list[str]:
        seen: list[str] = []
        for row in self.rows:
            if row.store not in seen:
                seen.append(row.store)
        return seen

    def day_rows(self, daypart: str) -> list[StoreDay]:
        return [row for row in self.rows if row.daypart == daypart]

    def status(self, store: str) -> str:
        values = {row.status for row in self.rows if row.store == store}
        if len(values) != 1:
            raise ValueError(f"{self.period.key}: {store} has inconsistent statuses: {values}")
        return values.pop()


def read_ledger(path: Path = MATERIALS) -> dict[str, PeriodData]:
    """Read both source blocks and verify the 18-leaf + total shape."""
    wb = load_workbook(path, data_only=True, read_only=True)
    try:
        result: dict[str, PeriodData] = {}
        for period in PERIODS:
            ws = wb[period.sheet]
            rows: list[StoreDay] = []
            total_base = total_current = None
            for row in ws.iter_rows(min_row=4, max_row=22, min_col=1, max_col=6, values_only=False):
                store, store_format, daypart, status = (row[i].value for i in range(4))
                current, base = row[4].value, row[5].value
                if store == "全品牌":
                    total_base, total_current = int(base), int(current)
                    continue
                if store is None:
                    continue
                if daypart not in {"早餐", "午餐", "晚餐"}:
                    raise ValueError(f"{period.sheet}: unexpected daypart {daypart!r}")
                rows.append(
                    StoreDay(
                        period=period.key,
                        store=str(store),
                        store_format=str(store_format),
                        daypart=str(daypart),
                        status=str(status),
                        base=int(base),
                        current=int(current),
                        base_cell=row[5].coordinate,
                        current_cell=row[4].coordinate,
                    )
                )
            if len(rows) != 18:
                raise ValueError(f"{period.sheet}: expected 18 leaves, got {len(rows)}")
            if total_base is None or total_current is None:
                raise ValueError(f"{period.sheet}: missing brand total row")
            result[period.key] = PeriodData(period, rows, total_base, total_current)
        return result
    finally:
        wb.close()


def bridge(period: PeriodData) -> dict[str, dict[str, float | int]]:
    """Return the six portfolio components with the brand-net denominator."""
    net = period.net
    components: dict[str, dict[str, float | int]] = {}
    for status in ("持续经营", "新开", "关闭"):
        rows = [row for row in period.rows if row.status == status]
        if status == "持续经营":
            impact = sum(row.current - row.base for row in rows)
        elif status == "新开":
            impact = sum(row.current for row in rows)
        else:
            impact = -sum(row.base for row in rows)
        components[status] = {
            "impact": impact,
            "contribution": impact / net,
            "base": sum(row.base for row in rows),
            "current": sum(row.current for row in rows),
        }
    if sum(item["impact"] for item in components.values()) != net:
        raise ValueError(f"{period.period.key}: portfolio bridge does not close")
    return components


def dayparts(period: PeriodData) -> dict[str, dict[str, object]]:
    """Return the three daypart changes and their three-way components."""
    net = period.net
    result: dict[str, dict[str, object]] = {}
    for daypart in ("早餐", "午餐", "晚餐"):
        rows = period.day_rows(daypart)
        by_status = {status: [row for row in rows if row.status == status] for status in ("持续经营", "新开", "关闭")}
        components = (
            sum(row.current - row.base for row in by_status["持续经营"]),
            sum(row.current for row in by_status["新开"]),
            -sum(row.base for row in by_status["关闭"]),
        )
        change = sum(row.current - row.base for row in rows)
        if sum(components) != change:
            raise ValueError(f"{period.period.key}/{daypart}: three-way chain does not close")
        result[daypart] = {
            "base": sum(row.base for row in rows),
            "current": sum(row.current for row in rows),
            "change": change,
            "components": components,
            "contribution": change / net,
        }
    if sum(item["change"] for item in result.values()) != net:
        raise ValueError(f"{period.period.key}: daypart totals do not close")
    return result


def validate_baseline(ledger: dict[str, PeriodData]) -> None:
    """Fail loudly if the fixture or the recomputation drifts."""
    for key, expected in EXPECTED_TOTALS.items():
        period = ledger[key]
        got = (period.total_base, period.total_current, period.net)
        if got != expected:
            raise AssertionError(f"{key}: totals {got} != {expected}")

    for key, expected in EXPECTED_BRIDGE.items():
        actual = bridge(ledger[key])
        for status, (impact, contribution) in expected.items():
            item = actual[status]
            if item["impact"] != impact or abs(float(item["contribution"]) - contribution) > 1e-12:
                raise AssertionError(f"{key}/{status}: {item} != {(impact, contribution)}")

    for key, expected in EXPECTED_DAYPARTS.items():
        actual = dayparts(ledger[key])
        for daypart, (change, components, contribution) in expected.items():
            item = actual[daypart]
            if item["change"] != change or tuple(item["components"]) != components:
                raise AssertionError(f"{key}/{daypart}: {item} != {(change, components)}")
            if abs(float(item["contribution"]) - contribution) > 1e-12:
                raise AssertionError(f"{key}/{daypart}: contribution mismatch")

    for key, expected in EXPECTED_STATUS.items():
        actual = {store: ledger[key].status(store) for store in expected}
        if actual != expected:
            raise AssertionError(f"{key}: statuses {actual} != {expected}")


def original_values(period: PeriodData) -> dict[tuple[str, str, str], int]:
    """Map (store, daypart, base|current) to the source value."""
    values: dict[tuple[str, str, str], int] = {}
    for row in period.rows:
        values[(row.store, row.daypart, "base")] = row.base
        values[(row.store, row.daypart, "current")] = row.current
    return values
