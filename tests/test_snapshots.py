"""Snapshot de regresión de métricas de datos.

Detecta *drift* en los cálculos de utils.data / las queries (cambios de valor no esperados).
Regenerar conscientemente tras un cambio legítimo:  UPDATE_SNAPSHOTS=1 pytest tests/test_snapshots.py
"""

import json
import os
from pathlib import Path

import pytest

SNAPSHOT = Path(__file__).parent / "snapshots" / "data_metrics.json"


def _current_metrics(datasets) -> dict:
    from utils.data import calculate_customer_concentration, calculate_product_concentration

    return {
        "orders": int(datasets["base"]["orderNumber"].nunique()),
        "customers_active": int(datasets["context"]["customers"]),
        "monthly_rows": len(datasets["monthly"]),
        "top10_product_conc": round(calculate_product_concentration(datasets["products"], 10), 2),
        "top20_customer_conc": round(calculate_customer_concentration(datasets["customers"], 0.2), 2),
        "high_risk_count": int(datasets["diagnostic_summary"]["high_risk_customers_count"]),
        "amount_at_risk": round(float(datasets["diagnostic_summary"]["amount_at_risk"]), 2),
        "invalid_date_pct": float(datasets["data_quality"]["invalid_date_pct"]),
        "cross_sell_pairs": len(datasets["cross_sell"]),
        "rfm_customers": len(datasets["customer_rfm"]),
    }


def test_data_metrics_snapshot(datasets):
    current = _current_metrics(datasets)

    if os.getenv("UPDATE_SNAPSHOTS") == "1":
        SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        pytest.skip("snapshot regenerado")

    if not SNAPSHOT.exists():
        pytest.skip(f"snapshot ausente: {SNAPSHOT} (genera con UPDATE_SNAPSHOTS=1)")

    expected = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert set(current) == set(expected), "el conjunto de métricas cambió; regenera el snapshot"
    for key, exp in expected.items():
        cur = current[key]
        if isinstance(exp, float):
            assert cur == pytest.approx(exp, rel=1e-4), f"drift en {key}: {cur} != {exp}"
        else:
            assert cur == exp, f"drift en {key}: {cur} != {exp}"
