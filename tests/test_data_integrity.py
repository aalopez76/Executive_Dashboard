"""Integridad del contrato de datos producido por utils.data.load_datasets()."""

# Contrato canónico documentado en utils/data.py::load_datasets.
EXPECTED_KEYS = {
    "base",
    "monthly",
    "customers",
    "products",
    "regions",
    "salesreps",
    "high_risk",
    "misalignment",
    "geo_anomalies",
    "product_trends",
    "customer_rfm",
    "next_orders",
    "cross_sell",
    "kpi_cards",
    "context",
    "diagnostic_summary",
    "risk_by_country",
    "data_quality",
}


def test_contract_keys_present(datasets):
    missing = EXPECTED_KEYS - set(datasets)
    assert not missing, f"Faltan datasets del contrato: {sorted(missing)}"


def test_core_datasets_non_empty(datasets):
    for key in ("base", "monthly", "customers", "products"):
        assert not datasets[key].empty, f"Dataset core vacío: {key}"


def test_min_rows(datasets, thresholds):
    cfg = thresholds["datasets"]
    assert len(datasets["base"]) >= cfg["base_min_rows"]
    assert len(datasets["monthly"]) >= cfg["monthly_min_rows"]
    assert len(datasets["customers"]) >= cfg["customers_min_rows"]


def test_invalid_date_pct_within_threshold(datasets, thresholds):
    pct = datasets["data_quality"]["invalid_date_pct"]
    max_pct = thresholds["data_quality"]["max_invalid_date_pct"]
    assert pct <= max_pct, f"invalid_date_pct={pct} supera el umbral {max_pct}"


def test_kpi_cards_single_row(datasets):
    assert len(datasets["kpi_cards"]) == 1
