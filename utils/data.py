# utils/data.py
import os
import logging
import pandas as pd

from sql_connection import get_connector

from utils._aggregations import (
    build_enriched_base,
    calculate_monthly_kpis,
    aggregate_customers,
    aggregate_products,
    aggregate_by_region,
    aggregate_salesreps,
    identify_high_risk_customers,
    identify_credit_misalignment,
    check_geographic_credit_anomalies,
    calculate_product_demand_trend,
    calculate_customer_rfm,
    calculate_customer_next_order_prediction,
    identify_product_cross_sell_pairs,
    create_kpi_card_data,
    get_context_banner_data,
    calculate_diagnostic_summary,
)

logger = logging.getLogger(__name__)


def load_datasets(db_path: str) -> dict:
    """Carga tablas, construye df_base y genera datasets agregados para el dashboard."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"DB no encontrada: {os.path.abspath(db_path)}")

    conn = get_connector("sqlite", path=db_path)

    with conn:
        df_orders = conn.read_sql("SELECT * FROM orders")
        df_orderdetails = conn.read_sql("SELECT * FROM orderdetails")
        df_customers_raw = conn.read_sql("SELECT * FROM customers")
        df_products_raw = conn.read_sql("SELECT * FROM products")
        df_employees_raw = conn.read_sql("SELECT * FROM employees")
        df_payments = conn.read_sql("SELECT customerNumber, paymentDate, amount FROM payments")
        df_offices = conn.read_sql("SELECT officeCode, city, country, territory FROM offices")

    df_base = build_enriched_base(
        df_orders=df_orders,
        df_orderdetails=df_orderdetails,
        df_customers=df_customers_raw,
        df_products=df_products_raw,
        df_employees=df_employees_raw,
    )

    df_monthly = calculate_monthly_kpis(df_base)

    df_customers = aggregate_customers(df_base)
    df_products = aggregate_products(df_base)
    df_regions = aggregate_by_region(df_base)
    df_salesreps = aggregate_salesreps(df_base)

    df_high_risk = identify_high_risk_customers(df_base)
    df_misalignment = identify_credit_misalignment(df_base)
    df_geo_anomalies = check_geographic_credit_anomalies(df_base)

    df_product_trends = calculate_product_demand_trend(df_base)
    df_customer_rfm = calculate_customer_rfm(df_base)
    df_next_orders = calculate_customer_next_order_prediction(df_base)
    df_cross_sell = identify_product_cross_sell_pairs(df_base, min_cooccurrence=5)

    df_kpi_cards = create_kpi_card_data(
        df_monthly=df_monthly,
        df_base=df_base,
        df_payments=df_payments,
        df_customers=df_customers,
        df_products=df_products,
    )

    context = get_context_banner_data(df_base, df_offices, df_employees_raw)
    diagnostic_summary = calculate_diagnostic_summary(df_high_risk, df_misalignment)

    # --- data quality info (filas con fechas inválidas)
    # (calculate_monthly_kpis ya hace el warn, aquí lo convertimos en un insight “visible”.)
    # Para eso, recalculamos el conteo de inválidas de forma determinística:
    tmp = df_base.copy()
    tmp["orderDate"] = pd.to_datetime(tmp["orderDate"], errors="coerce")
    tmp["shippedDate"] = pd.to_datetime(tmp["shippedDate"], errors="coerce")
    tmp["requiredDate"] = pd.to_datetime(tmp["requiredDate"], errors="coerce")
    invalid_rows = (~tmp["orderDate"].notna()) | (~tmp["shippedDate"].notna()) | (~tmp["requiredDate"].notna())
    invalid_count = int(invalid_rows.sum())
    invalid_pct = round(invalid_count / max(len(tmp), 1) * 100, 2)
    if invalid_count:
        logger.warning("Filas con fechas inválidas: %s (%.2f%%) - excluidas de KPIs", invalid_count, invalid_pct)

    # --- dataset para mapa de riesgo (Opción B)
    df_risk_by_country = (
        df_high_risk.groupby("country", dropna=False)["amount_at_risk"]
        .sum()
        .reset_index()
        .rename(columns={"amount_at_risk": "risk_amount"})
    )
    country_fix = {"USA": "United States", "UK": "United Kingdom", "England": "United Kingdom"}
    df_risk_by_country["country"] = df_risk_by_country["country"].replace(country_fix)

    return {
        "base": df_base,
        "monthly": df_monthly,
        "customers": df_customers,
        "products": df_products,
        "regions": df_regions,
        "salesreps": df_salesreps,
        "high_risk": df_high_risk,
        "misalignment": df_misalignment,
        "geo_anomalies": df_geo_anomalies,
        "product_trends": df_product_trends,
        "customer_rfm": df_customer_rfm,
        "next_orders": df_next_orders,
        "cross_sell": df_cross_sell,
        "kpi_cards": df_kpi_cards,
        "context": context,
        "diagnostic_summary": diagnostic_summary,
        "risk_by_country": df_risk_by_country,
        "data_quality": {"invalid_date_rows": invalid_count, "invalid_date_pct": invalid_pct},
    }
