# utils/data.py
import os
import logging
import pandas as pd

from .data_engine import DataEngine

logger = logging.getLogger(__name__)


# ----------------------------
# Helpers
# ----------------------------
def _fix_country_names(df: pd.DataFrame, col: str = "country") -> pd.DataFrame:
    if df is None or df.empty or col not in df.columns:
        return df
    country_fix = {"USA": "United States", "UK": "United Kingdom", "England": "United Kingdom"}
    df = df.copy()
    df[col] = df[col].replace(country_fix)
    return df


def _ensure_monthly_year(df_monthly: pd.DataFrame) -> pd.DataFrame:
    if df_monthly is None or df_monthly.empty:
        return df_monthly
    df = df_monthly.copy()
    # soporta salesMonth tipo 'YYYY-MM' o fecha
    if "salesMonth" in df.columns and "year" not in df.columns:
        dt = pd.to_datetime(df["salesMonth"].astype(str) + "-01", errors="coerce")
        df["year"] = dt.dt.year
        df["month"] = dt.dt.month
    return df


def _rename_sales_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Homologa columnas típicas entre SQL y Pandas.
    - totalSales -> total_sales
    - totalUnits -> total_units
    - avgOrderValue -> avgOrderValue (se deja tal cual si ya coincide con pages)
    """
    if df is None or df.empty:
        return df
    df = df.copy()
    rename_map = {
        "totalSales": "total_sales",
        "totalUnits": "total_units",
        "totalOrders": "totalOrders",          # pages.py lo usa así en KPI cards (kpi_card_data)
        "totalCustomers": "totalCustomers",
        "onTimeRate_pct": "onTimeRate_pct",
    }
    # aplicar solo si existen
    present = {k: v for k, v in rename_map.items() if k in df.columns and v not in df.columns}
    if present:
        df = df.rename(columns=present)
    return df


def build_enriched_base(
    df_orders: pd.DataFrame,
    df_orderdetails: pd.DataFrame,
    df_customers: pd.DataFrame,
    df_products: pd.DataFrame,
    df_employees: pd.DataFrame,
) -> pd.DataFrame:
    # 1) orders + orderdetails
    df_base = df_orders.merge(df_orderdetails, on="orderNumber", how="inner")

    # 2) customers
    df_base = df_base.merge(
        df_customers[
            ["customerNumber", "customerName", "country", "city", "creditLimit", "salesRepEmployeeNumber"]
        ],
        on="customerNumber",
        how="left",
    )

    # 3) products
    df_base = df_base.merge(
        df_products[["productCode", "productName", "productLine"]],
        on="productCode",
        how="left",
    )

    # 4) employees (sales rep)
    df_emp = df_employees.copy()
    df_emp["employeeName"] = df_emp["firstName"].astype(str) + " " + df_emp["lastName"].astype(str)

    df_base = df_base.merge(
        df_emp[["employeeNumber", "employeeName", "jobTitle", "officeCode"]],
        left_on="salesRepEmployeeNumber",
        right_on="employeeNumber",
        how="left",
        suffixes=("", "_salesrep"),
    )

    # 5) lineSales
    df_base["lineSales"] = df_base["quantityOrdered"] * df_base["priceEach"]

    # 6) normalización de países (para choropleth locationmode="country names")
    df_base = _fix_country_names(df_base, "country")
    return df_base


def calculate_payment_coverage(df_base: pd.DataFrame, df_payments: pd.DataFrame) -> float:
    if df_base is None or df_base.empty:
        return 0.0
    sales = df_base.groupby("customerNumber")["lineSales"].sum()
    paid = df_payments.groupby("customerNumber")["amount"].sum() if df_payments is not None and not df_payments.empty else 0
    coverage_df = pd.DataFrame({"sales": sales, "paid": paid}).fillna(0)
    denom = coverage_df["sales"].sum()
    return round((coverage_df["paid"].sum() / denom) * 100, 2) if denom else 0.0


def calculate_customer_concentration(df_customers: pd.DataFrame, top_pct: float = 0.2) -> float:
    if df_customers is None or df_customers.empty:
        return 0.0
    col = "total_sales" if "total_sales" in df_customers.columns else ("totalSales" if "totalSales" in df_customers.columns else None)
    if col is None:
        return 0.0
    df_sorted = df_customers.sort_values(col, ascending=False)
    top_n = max(int(len(df_sorted) * top_pct), 1)
    top_rev = df_sorted.head(top_n)[col].sum()
    tot = df_sorted[col].sum()
    return round((top_rev / tot) * 100, 2) if tot else 0.0


def calculate_product_concentration(df_products: pd.DataFrame, top_n: int = 10) -> float:
    if df_products is None or df_products.empty:
        return 0.0
    col = "total_sales" if "total_sales" in df_products.columns else ("totalSales" if "totalSales" in df_products.columns else None)
    if col is None:
        return 0.0
    df_sorted = df_products.sort_values(col, ascending=False)
    top_rev = df_sorted.head(top_n)[col].sum()
    tot = df_sorted[col].sum()
    return round((top_rev / tot) * 100, 2) if tot else 0.0


def create_kpi_card_data(
    df_monthly: pd.DataFrame,
    df_base: pd.DataFrame,
    df_payments: pd.DataFrame,
    df_customers: pd.DataFrame,
    df_products: pd.DataFrame,
) -> pd.DataFrame:
    """
    Produce el dataset 1-row para KPI cards, compatible con build_kpi_banner().
    """
    dfm = _ensure_monthly_year(df_monthly)
    years = sorted(dfm["year"].dropna().unique()) if dfm is not None and not dfm.empty and "year" in dfm.columns else []
    current_year = int(years[-1]) if years else 2024
    previous_year = int(years[-2]) if len(years) > 1 else current_year - 1

    dfc = dfm[dfm["year"] == current_year] if "year" in dfm.columns else dfm
    dfp = dfm[dfm["year"] == previous_year] if "year" in dfm.columns else dfm

    # Columnas esperadas desde SQL monthly: totalSales, totalOrders, avgOrderValue, onTimeRate_pct
    def _safe_sum(df, col): return float(df[col].sum()) if df is not None and not df.empty and col in df.columns else 0.0
    def _safe_mean(df, col): return float(df[col].mean()) if df is not None and not df.empty and col in df.columns else 0.0

    kpi = {
        f"Total_Revenue_{current_year}": _safe_sum(dfc, "totalSales"),
        f"Total_Revenue_{previous_year}": _safe_sum(dfp, "totalSales"),

        f"Total_Orders_{current_year}": _safe_sum(dfc, "totalOrders"),
        f"Total_Orders_{previous_year}": _safe_sum(dfp, "totalOrders"),

        f"AOV_{current_year}": _safe_mean(dfc, "avgOrderValue"),
        f"AOV_{previous_year}": _safe_mean(dfp, "avgOrderValue"),

        f"OnTimeRate_{current_year}": _safe_mean(dfc, "onTimeRate_pct"),
        f"OnTimeRate_{previous_year}": _safe_mean(dfp, "onTimeRate_pct"),

        f"PaymentCoverage_{current_year}": calculate_payment_coverage(df_base, df_payments),
        f"PaymentCoverage_{previous_year}": calculate_payment_coverage(df_base, df_payments),

        f"CustomerConcentration_{current_year}": calculate_customer_concentration(df_customers, top_pct=0.2),
        f"CustomerConcentration_{previous_year}": calculate_customer_concentration(df_customers, top_pct=0.2),

        f"ProductConcentration_{current_year}": calculate_product_concentration(df_products, top_n=10),
        f"ProductConcentration_{previous_year}": calculate_product_concentration(df_products, top_n=10),
    }
    return pd.DataFrame([kpi])


def get_context_banner_data(df_base: pd.DataFrame, df_offices: pd.DataFrame, df_employees: pd.DataFrame) -> dict:
    return {
        "offices": int(df_offices["officeCode"].nunique()) if df_offices is not None and not df_offices.empty else 0,
        "sales_reps": int(df_employees["employeeNumber"].nunique()) if df_employees is not None and not df_employees.empty else 0,
        "countries_served": int(df_base["country"].nunique()) if df_base is not None and not df_base.empty else 0,
        "customers": int(df_base["customerNumber"].nunique()) if df_base is not None and not df_base.empty else 0,
    }


def calculate_diagnostic_summary(df_high_risk: pd.DataFrame, df_misalignment: pd.DataFrame) -> dict:
    hr_count = int(len(df_high_risk)) if df_high_risk is not None else 0
    amt = float(df_high_risk["amount_at_risk"].sum()) if df_high_risk is not None and not df_high_risk.empty and "amount_at_risk" in df_high_risk.columns else 0.0

    mis_count = int(len(df_misalignment)) if df_misalignment is not None else 0
    over = int(df_misalignment["misalignmentCategory"].str.contains("HIGH CREDIT", na=False).sum()) if df_misalignment is not None and not df_misalignment.empty and "misalignmentCategory" in df_misalignment.columns else 0
    under = int(df_misalignment["misalignmentCategory"].str.contains("LOW CREDIT", na=False).sum()) if df_misalignment is not None and not df_misalignment.empty and "misalignmentCategory" in df_misalignment.columns else 0

    base_den = int(df_misalignment["customerNumber"].nunique()) if df_misalignment is not None and not df_misalignment.empty and "customerNumber" in df_misalignment.columns else 0
    hr_pct = round((hr_count / base_den) * 100, 1) if base_den else 0.0

    return {
        "high_risk_customers_count": hr_count,
        "high_risk_customers_pct": hr_pct,
        "amount_at_risk": round(amt, 2),
        "misalignment_count": mis_count,
        "over_credited_count": over,
        "under_credited_count": under,
    }


# ----------------------------
# Public API
# ----------------------------
def load_datasets(db_path: str) -> dict:
    """
    Contrato canónico (referencia única):
      base, monthly, customers, products, regions, salesreps,
      high_risk, misalignment, geo_anomalies,
      product_trends, customer_rfm, next_orders, cross_sell,
      kpi_cards, context, diagnostic_summary,
      risk_by_country, data_quality
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"DB no encontrada: {os.path.abspath(db_path)}")

    engine = DataEngine(db_path)

    try:
        # 1) Raw tables -> df_base (Pandas)
        raw = engine.get_raw_inputs()
        df_base = build_enriched_base(
            df_orders=raw["orders"],
            df_orderdetails=raw["orderdetails"],
            df_customers=raw["customers"],
            df_products=raw["products"],
            df_employees=raw["employees"],
        )

        # 2) SQL datasets
        core = engine.get_core_datasets()
        diag = engine.get_diagnostics()
        pred = engine.get_predictive()

        df_monthly = _ensure_monthly_year(core.get("monthly", pd.DataFrame()))
        df_customers = _rename_sales_columns(core.get("customers", pd.DataFrame()))
        df_products = _rename_sales_columns(core.get("products", pd.DataFrame()))
        df_regions = _rename_sales_columns(core.get("regions", pd.DataFrame()))
        df_salesreps = _rename_sales_columns(core.get("salesreps", pd.DataFrame()))

        df_high_risk = diag.get("high_risk", pd.DataFrame())
        df_misalignment = diag.get("misalignment", pd.DataFrame())
        df_geo_anomalies = diag.get("geo_anomalies", pd.DataFrame())

        df_product_trends = pred.get("product_trends", pd.DataFrame())
        df_customer_rfm = pred.get("customer_rfm", pd.DataFrame())
        df_next_orders = pred.get("next_orders", pd.DataFrame())
        df_cross_sell = pred.get("cross_sell", pd.DataFrame())

        # 3) KPI cards + context + diagnostic summary
        df_kpi_cards = create_kpi_card_data(
            df_monthly=df_monthly,
            df_base=df_base,
            df_payments=raw.get("payments", pd.DataFrame()),
            df_customers=df_customers,
            df_products=df_products,
        )

        context = get_context_banner_data(df_base, raw.get("offices", pd.DataFrame()), raw.get("employees", pd.DataFrame()))
        diagnostic_summary = calculate_diagnostic_summary(df_high_risk, df_misalignment)

        # 4) Data quality: invalid dates (misma lógica que tenías)
        tmp = df_base.copy()
        tmp["orderDate"] = pd.to_datetime(tmp.get("orderDate"), errors="coerce")
        tmp["shippedDate"] = pd.to_datetime(tmp.get("shippedDate"), errors="coerce")
        tmp["requiredDate"] = pd.to_datetime(tmp.get("requiredDate"), errors="coerce")
        invalid_rows = (~tmp["orderDate"].notna()) | (~tmp["shippedDate"].notna()) | (~tmp["requiredDate"].notna())
        invalid_count = int(invalid_rows.sum())
        invalid_pct = round(invalid_count / max(len(tmp), 1) * 100, 2)
        if invalid_count:
            logger.warning("Filas con fechas inválidas: %s (%.2f%%) - excluidas de KPIs", invalid_count, invalid_pct)

        # 5) Risk by country (usa amount_at_risk; si no existe, fallback a totalSales)
        if df_high_risk is not None and not df_high_risk.empty and "country" in df_high_risk.columns:
            risk_col = "amount_at_risk" if "amount_at_risk" in df_high_risk.columns else ("totalSales" if "totalSales" in df_high_risk.columns else None)
            if risk_col:
                df_risk_by_country = (
                    df_high_risk.groupby("country", dropna=False)[risk_col].sum().reset_index().rename(columns={risk_col: "risk_amount"})
                )
                df_risk_by_country = _fix_country_names(df_risk_by_country, "country")
            else:
                df_risk_by_country = pd.DataFrame(columns=["country", "risk_amount"])
        else:
            df_risk_by_country = pd.DataFrame(columns=["country", "risk_amount"])

        # 6) Extra datasets usados en pages.py
        df_customers_abc_counts = df_customers[["abc_class"]].copy() if "abc_class" in df_customers.columns else pd.DataFrame({"abc_class": []})
        if not df_customers_abc_counts.empty:
            df_customers_abc_counts["n"] = 1

        df_top_products_long = df_base[["productName"]].copy() if "productName" in df_base.columns else pd.DataFrame({"productName": []})
        if not df_top_products_long.empty:
            df_top_products_long["n"] = 1

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
            # compat (si los sigues usando en pages.py)
            "customers_abc_counts": df_customers_abc_counts,
            "top_products_long": df_top_products_long,
        }

    finally:
        engine.close()
