from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import load_workbook

from audit.ledger import GOLD, PACKAGE_DIR, ROLLOUTS


ROLLOUT_CELLS = {
    "rollout-01.xlsx": {
        "品牌总览": {"H5": 48, "I5": 0.128342245989305, "H6": 59},
        "组合桥接": {"H5": 23, "J5": 0.4791666666666667, "H6": 89, "J6": 1.854166666666667, "H7": -64, "J7": -1.333333333333333, "L8": "通过"},
        "餐段归因": {"J5": -11, "L5": -0.2291666666666667, "J6": 21, "L6": 0.4375, "J7": 38, "L7": 0.7916666666666666, "Q8": "通过"},
    },
    "rollout-02.xlsx": {
        "01_品牌总览": {"I4": 48, "J4": 0.128342245989305, "I5": 59},
        "02_组合桥接": {"K4": 23, "M4": 0.4791666666666667, "K5": 89, "M5": 1.854166666666667, "K6": -64, "M6": -1.333333333333333},
        "03_时段归因": {"K7": -11, "N7": -0.2291666666666667, "K11": 21, "N11": 0.4375, "K15": 38, "N15": 0.7916666666666666},
    },
    "rollout-03.xlsx": {
        "结论摘要": {"D7": 48, "E7": 0.128342245989305, "D29": 59, "E29": 0.139810426540284},
        "门店组合桥接": {"H4": 23, "J4": 0.4791666666666667, "H5": 89, "J5": 1.854166666666667, "H6": -64, "J6": -1.333333333333333},
        "餐段归因": {"J7": -0.2291666666666667, "J11": 0.4375, "J15": 0.7916666666666666, "N7": "通过", "N11": "通过", "N15": "通过"},
    },
    "rollout-04.xlsx": {
        "总览结论": {"D2": 48, "E2": 0.128342245989305, "D3": 59, "E3": 0.139810426540284},
        "组合桥接": {"F2": 23, "H2": 0.4791666666666667, "F3": 89, "H3": 1.854166666666667, "F4": -64, "H4": -1.333333333333333},
        "餐段归因": {"F2": 4, "I2": -11, "J2": -0.2291666666666667, "F5": 11, "I5": 21, "J5": 0.4375},
    },
    "rollout-05.xlsx": {
        "品牌总览": {"I2": 48, "J2": 0.128342245989305, "I3": 59, "J3": 0.139810426540284},
        "组合桥": {"G2": 23, "I2": 0.4791666666666667, "G3": 89, "I3": 1.854166666666667, "G4": -64, "I4": -1.333333333333333},
        "时段贡献": {"K2": -11, "L2": -0.2291666666666667, "K5": 21, "L5": 0.4375, "K8": 38, "L8": 0.7916666666666666},
    },
}


def test_every_workbook_is_readable():
    paths = [GOLD] + sorted(ROLLOUTS.glob("*.xlsx")) + sorted((PACKAGE_DIR / "probes").glob("*.xlsx"))
    assert len(paths) == 9
    for path in paths:
        wb = load_workbook(path, data_only=True, read_only=True)
        try:
            assert wb.sheetnames
            for ws in wb:
                assert ws.max_row >= 1
        finally:
            wb.close()


@pytest.mark.parametrize("filename", sorted(ROLLOUT_CELLS))
def test_rollout_key_evidence_cells(filename):
    path = ROLLOUTS / filename
    wb = load_workbook(path, data_only=True, read_only=False)
    try:
        for sheet, cells in ROLLOUT_CELLS[filename].items():
            ws = wb[sheet]
            for coordinate, expected in cells.items():
                actual = ws[coordinate].value
                if isinstance(expected, float):
                    assert actual == pytest.approx(expected, abs=1e-12), (filename, sheet, coordinate)
                else:
                    assert actual == expected, (filename, sheet, coordinate)
    finally:
        wb.close()


def test_gold_matches_the_independent_baseline():
    wb = load_workbook(GOLD, data_only=True, read_only=False)
    try:
        bridge = wb["门店组合桥"]
        assert [bridge[f"E{r}"].value for r in range(2, 8)] == [23, 89, -64, 31, 79, -51]
        assert [bridge[f"F{r}"].value for r in range(2, 8)] == [48, 48, 48, 59, 59, 59]
        daypart = wb["餐段归因"]
        assert [daypart[f"G{r}"].value for r in range(2, 8)] == [-11, 21, 38, 1, 17, 41]
        assert [daypart[f"H{r}"].value for r in range(2, 8)] == [48, 48, 48, 59, 59, 59]
    finally:
        wb.close()


def test_gold_is_static_not_formula_driven():
    """This is a task-design finding, pinned so it cannot silently change."""
    wb = load_workbook(GOLD, data_only=False, read_only=True)
    try:
        formula_cells = [(ws.title, cell.coordinate) for ws in wb for row in ws.iter_rows() for cell in row if cell.data_type == "f"]
        assert formula_cells == []
    finally:
        wb.close()
