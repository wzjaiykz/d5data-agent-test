from __future__ import annotations

import pytest
from openpyxl import load_workbook

from audit.ledger import PROBES


def _wb(name: str):
    return load_workbook(PROBES / name, data_only=True, read_only=False)


def test_probe_01_uses_the_wrong_common_denominator_in_the_first_period():
    wb = _wb("probe-01.xlsx")
    try:
        ws = wb["审查样本"]
        assert ws["J2"].value == 23  # should be 48
        assert ws["K2"].value == pytest.approx(48 / 23)
        for row in range(3, 9):
            assert ws[f"J{row}"].value == 23
            assert ws[f"K{row}"].value == pytest.approx(ws[f"I{row}"].value / 23)
        assert ws["J9"].value == 59
        assert ws["K4"].value == pytest.approx(89 / 23)
        assert ws["K8"].value == pytest.approx(38 / 23)
    finally:
        wb.close()


def test_probe_02_is_an_honest_first_period_only_artifact():
    wb = _wb("probe-02.xlsx")
    try:
        ws = wb["审查样本"]
        assert ws.max_row == 9
        assert ws["N9"].value == "仅完成第一比较期间"
        assert all("2024→2025" not in str(c.value) for row in ws.iter_rows() for c in row if c.value is not None)
        assert ws["J2"].value == 48
    finally:
        wb.close()


def test_probe_03_has_no_material_traffic_values_only_claims_and_a_toy_formula():
    wb = _wb("probe-03.xlsx")
    try:
        ws = wb["审查样本"]
        numeric = [c.value for row in ws.iter_rows() for c in row if isinstance(c.value, (int, float))]
        assert len(numeric) == 40
        assert set(numeric) == set(range(1, 21))
        assert numeric.count(2) >= 20
        traffic_values = {374, 422, 48, 59, 23, 89, 64, 31, 79, 51}
        assert not traffic_values.intersection({abs(value) for value in numeric})
        assert all(ws[f"J{row}"].value == "勾稽通过" for row in range(2, 22))
    finally:
        wb.close()
    wf = load_workbook(PROBES / "probe-03.xlsx", data_only=False, read_only=False)
    try:
        assert wf["审查样本"]["O2"].value == "=1+1"
    finally:
        wf.close()
