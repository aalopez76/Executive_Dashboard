# utils/datasets.py
import pandas as pd

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

def _fix_country_names(df: pd.DataFrame, col: str = "country") -> pd.DataFrame:
    df = df.copy()
    country_fix = {
        "USA": "United States",
        "UK": "United Kingdom",
        "England": "United Kingdom",
    }
    df[col] = df[col].replace(country_fix)
    return df

def build_datasets(
    df_orders: pd.DataFrame,
    df_orderdetails: pd.DataFrame,
    df_customers_raw: pd.DataFrame,
    df_products_raw: pd.DataFrame,
    df_employees_raw: pd.DataFrame,
    df_payments: pd.DataFrame,
    df_offices: pd.DataFrame,
) -> dict:
    # 1) Base enriquecida
    df_base = build_enriched_base(
        df_orders=df_orders,
        df_orderdetails=df_orderdetails,
        df_customers=df_customers_raw,
        df_products=df_products_raw,
        df_employees=df_employees_raw,
    )

    # 2) Agregaciones “core”
    df_monthly = calculate_monthly_kpis(df_base)
    df_customers = aggregate_customers(df_base)
    df_products = aggregate_products(df_base)
    df_regions = aggregate_by_region(df_base)
    df_salesreps = aggregate_salesreps(df_base)

    # 3) Diagnóstico
    df_high_risk = identify_high_risk_customers(df_base)
    df_misalignment = identify_credit_misalignment(df_base)
    df_geo_anomalies = check_geographic_credit_anomalies(df_base)

    # 4) Predictivo / oportunidades
    df_product_trends = calculate_product_demand_trend(df_base)
    df_customer_rfm = calculate_customer_rfm(df_base)
    df_next_orders = calculate_customer_next_order_prediction(df_base)
    df_cross_sell = identify_product_cross_sell_pairs(df_base, min_cooccurrence=5)

    # 5) Contexto + KPI cards
    df_kpi_cards = create_kpi_card_data(
        df_monthly=df_monthly,
        df_base=df_base,
        df_payments=df_payments,
        df_customers=df_customers,
        df_products=df_products,
    )
    context_data = get_context_banner_data(df_base, df_offices, df_employees_raw)
    diagnostic_summary = calculate_diagnostic_summary(df_high_risk, df_misalignment)

    # 6) Datasets “listos para gráficos”
    df_customers_abc_counts = df_customers[["abc_class"]].copy()
    df_customers_abc_counts["n"] = 1

    df_top_products_long = df_base[["productName"]].copy()
    df_top_products_long["n"] = 1

    df_risk_by_country = (
        df_high_risk.groupby("country", dropna=False)["amount_at_risk"]
        .sum()
        .reset_index()
        .rename(columns={"amount_at_risk": "risk_amount"})
    )
    df_risk_by_country = _fix_country_names(df_risk_by_country, "country")

    # Importante: si usarás choropleth con locationmode="country names",
    # también conviene normalizar df_base/datasets con esos nombres.
    df_base_fixed = _fix_country_names(df_base, "country")

    return {
        "base": df_base_fixed,
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
        "context": context_data,
        "diagnostic_summary": diagnostic_summary,
        "customers_abc_counts": df_customers_abc_counts,
        "top_products_long": df_top_products_long,
        "risk_by_country": df_risk_by_country,
    }
