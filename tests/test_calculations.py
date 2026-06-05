"""Tests unitarios de las funciones de cálculo de utils.data (puras, sin BD)."""

import pandas as pd

from utils.data import (
    _fix_country_names,
    calculate_customer_concentration,
    calculate_diagnostic_summary,
    calculate_payment_coverage,
    calculate_product_concentration,
    get_context_banner_data,
)


def test_fix_country_names_normaliza_y_no_muta():
    df = pd.DataFrame({"country": ["USA", "UK", "England", "France"]})
    out = _fix_country_names(df, "country")
    assert out["country"].tolist() == ["United States", "United Kingdom", "United Kingdom", "France"]
    # no muta el original
    assert df["country"].tolist() == ["USA", "UK", "England", "France"]


def test_fix_country_names_columna_ausente():
    df = pd.DataFrame({"x": [1]})
    assert _fix_country_names(df, "country") is df


def test_payment_coverage():
    # ventas: cliente 1 -> 500, cliente 2 -> 500 (total 1000); pagado 800 -> 80%
    base = pd.DataFrame({"customerNumber": [1, 1, 2], "lineSales": [400.0, 100.0, 500.0]})
    payments = pd.DataFrame({"customerNumber": [1, 2], "amount": [500.0, 300.0]})
    assert calculate_payment_coverage(base, payments) == 80.0


def test_payment_coverage_base_vacia():
    assert calculate_payment_coverage(pd.DataFrame(), pd.DataFrame()) == 0.0


def test_payment_coverage_sin_pagos():
    base = pd.DataFrame({"customerNumber": [1], "lineSales": [100.0]})
    assert calculate_payment_coverage(base, pd.DataFrame()) == 0.0


def test_customer_concentration_top20():
    # ventas 100..10 desc; top 20% de 10 = 2 clientes (100+90=190) sobre total 550
    df = pd.DataFrame({"total_sales": [100, 90, 80, 70, 60, 50, 40, 30, 20, 10]})
    assert calculate_customer_concentration(df, top_pct=0.2) == round(190 / 550 * 100, 2)


def test_customer_concentration_columna_legacy():
    df = pd.DataFrame({"totalSales": [100, 0]})  # top_n = max(int(0.4), 1) = 1
    assert calculate_customer_concentration(df, top_pct=0.2) == 100.0


def test_customer_concentration_sin_columna_ventas():
    assert calculate_customer_concentration(pd.DataFrame({"x": [1]})) == 0.0


def test_product_concentration():
    df = pd.DataFrame({"total_sales": [50, 30, 20]})
    assert calculate_product_concentration(df, top_n=10) == 100.0  # todos
    assert calculate_product_concentration(df, top_n=1) == 50.0  # el mayor (50/100)


def test_context_banner_data():
    base = pd.DataFrame({"country": ["US", "US", "FR"], "customerNumber": [1, 2, 2]})
    offices = pd.DataFrame({"officeCode": [1, 2, 2]})
    employees = pd.DataFrame({"employeeNumber": [10, 11]})
    out = get_context_banner_data(base, offices, employees)
    assert out == {"offices": 2, "sales_reps": 2, "countries_served": 2, "customers": 2}


def test_diagnostic_summary():
    high_risk = pd.DataFrame({"amount_at_risk": [100.0, 50.0]})
    mis = pd.DataFrame(
        {
            "customerNumber": [1, 2, 3],
            "misalignmentCategory": ["HIGH CREDIT risk", "LOW CREDIT gap", "OK"],
        }
    )
    out = calculate_diagnostic_summary(high_risk, mis, total_customers=8)
    assert out["high_risk_customers_count"] == 2
    assert out["amount_at_risk"] == 150.0
    assert out["misalignment_count"] == 3
    assert out["over_credited_count"] == 1
    assert out["under_credited_count"] == 1
    assert out["high_risk_customers_pct"] == 25.0  # 2 high-risk / 8 customers


def test_diagnostic_summary_vacio():
    out = calculate_diagnostic_summary(pd.DataFrame(), pd.DataFrame())
    assert out["high_risk_customers_count"] == 0
    assert out["amount_at_risk"] == 0.0
    assert out["high_risk_customers_pct"] == 0.0
