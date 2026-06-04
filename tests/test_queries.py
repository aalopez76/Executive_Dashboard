"""Las queries SQL referenciadas por DataEngine deben resolverse en disco."""

import pytest

from utils.query_reader import load_sql_query

# Rutas relativas usadas en utils/data_engine.py (get_core_datasets/diagnostics/predictive).
QUERY_PATHS = [
    "predictive/01_company_monthly_timeseries.sql",
    "analytical/03_customer_deep_agg_phase2.sql",
    "analytical/02_products_deep_agg.sql",
    "analytical/01_sales_by_country_vs_region.sql",
    "analytical/04_salesrep_performance_deep_agg.sql",
    "analytical/06_top_bottom_product_by_productline.sql",
    "diagnostic/04_high_risk_customers_ratio.sql",
    "diagnostic/03_credit_vs_sales_misalignment_ratio.sql",
    "diagnostic/01_geographic_credit_anomalies.sql",
    "predictive/05_product_demand_trend_flag.sql",
    "predictive/06_customer_rfm_score.sql",
    "predictive/07_customer_next_order_prediction.sql",
    "predictive/08_product_cross_sell_pairs.sql",
]


@pytest.mark.parametrize("rel_path", QUERY_PATHS)
def test_query_resolves_and_non_empty(rel_path):
    sql = load_sql_query(rel_path)
    assert sql.strip(), f"SQL vacío o no resuelto: {rel_path}"
