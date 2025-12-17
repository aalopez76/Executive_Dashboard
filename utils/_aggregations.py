"""
Funciones para replicar las agregaciones de las queries SQL usando Pandas.
Más flexible y fácil de mantener que SQL puro.

VERSIÓN CORREGIDA - Fixes aplicados:
1. aggregate_salesreps() - estructura de merge corregida
2. Funciones de diagnóstico - ahora requieren df_customers con creditLimit
3. get_top_bottom_products_by_line() - ahora usa productLine
4. df_base debe ser construido con todas las columnas necesarias

Estructura:
1. KPI Overview (company_monthly_timeseries)
2. Customer Aggregations (customer_deep_agg)
3. Product Aggregations (products_deep_agg)
4. Geographic Aggregations (sales_by_country_vs_region)
5. Sales Rep Performance (salesrep_performance_deep_agg)
6. Diagnostic Queries (high_risk_customers, credit_misalignment)
7. Predictive Queries (product_demand_trend, customer_rfm, cross_sell)
8. Helper Functions (KPI cards, concentrations, etc.)
"""

import pandas as pd
import numpy as np
from typing import Literal, Tuple, Optional
from datetime import datetime


# ============================================================================
# HELPER: Construcción de df_base enriquecido
# ============================================================================

def build_enriched_base(
    df_orders: pd.DataFrame,
    df_orderdetails: pd.DataFrame,
    df_customers: pd.DataFrame,
    df_products: pd.DataFrame,
    df_employees: pd.DataFrame
) -> pd.DataFrame:
    """
    Construye el DataFrame base enriquecido con todas las columnas necesarias.
    
    Este es el punto de partida para todas las agregaciones.
    Incluye: order data, customer data, product data, employee data.
    
    Args:
        df_orders: tabla orders
        df_orderdetails: tabla orderdetails
        df_customers: tabla customers (con creditLimit)
        df_products: tabla products (con productLine)
        df_employees: tabla employees
    
    Returns:
        DataFrame base con todas las columnas necesarias
    """
    # 1. Base: orders + orderdetails
    df_base = df_orders.merge(
        df_orderdetails,
        on='orderNumber',
        how='inner'
    )
    
    # 2. Agregar customer info (incluyendo creditLimit y salesRepEmployeeNumber)
    df_base = df_base.merge(
        df_customers[[
            'customerNumber', 'customerName', 'country', 'city',
            'creditLimit', 'salesRepEmployeeNumber'
        ]],
        on='customerNumber',
        how='left'
    )
    
    # 3. Agregar product info (incluyendo productLine)
    df_base = df_base.merge(
        df_products[['productCode', 'productName', 'productLine']],
        on='productCode',
        how='left'
    )
    
    # 4. Agregar employee info (sales rep)
    df_employees_clean = df_employees.copy()
    df_employees_clean['employeeName'] = (
        df_employees_clean['firstName'] + ' ' + df_employees_clean['lastName']
    )
    
    df_base = df_base.merge(
        df_employees_clean[[
            'employeeNumber', 'employeeName', 'jobTitle', 'officeCode'
        ]],
        left_on='salesRepEmployeeNumber',
        right_on='employeeNumber',
        how='left',
        suffixes=('', '_salesrep')
    )
    
    # 5. Calcular lineSales
    df_base['lineSales'] = df_base['quantityOrdered'] * df_base['priceEach']
    
    return df_base


# ============================================================================
# 1. KPI OVERVIEW - Equivalente a company_monthly_timeseries.sql
# ============================================================================

def calculate_monthly_kpis(df_base: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula KPIs mensuales a nivel empresa.
    Replica: 01_company_monthly_timeseries.sql
    
    Returns:
        DataFrame con columnas: salesMonth, totalSales, totalOrders, 
        totalCustomers, avgOrderValue, onTimeRate_pct
    """
    df = df_base.copy()

    # Conversión robusta de fechas
    df['orderDate'] = pd.to_datetime(df['orderDate'], errors='coerce')
    df['shippedDate'] = pd.to_datetime(df['shippedDate'], errors='coerce')
    df['requiredDate'] = pd.to_datetime(df['requiredDate'], errors='coerce')

    # Verificar filas con fechas inválidas
    invalid_rows = (~df['orderDate'].notna()) | (~df['shippedDate'].notna()) | (~df['requiredDate'].notna())
    if invalid_rows.any():
        print(f"[WARN] Filas con fechas inválidas: {invalid_rows.sum()} (se excluyen de KPIs)")

    df['salesMonth'] = df['orderDate'].dt.to_period('M').astype(str)
    df['year'] = df['orderDate'].dt.year
    df['month'] = df['orderDate'].dt.month
    
    # Calcular on-time delivery
    df['isOnTime'] = (
        (df['shippedDate'].notna()) & 
        (df['requiredDate'].notna()) & 
        (df['shippedDate'] <= df['requiredDate'])
    ).astype(int)
    
    # Agregación mensual
    monthly = df.groupby('salesMonth').agg({
        'lineSales': 'sum',
        'orderNumber': 'nunique',
        'customerNumber': 'nunique',
        'isOnTime': 'sum'
    }).rename(columns={
        'lineSales': 'totalSales',
        'orderNumber': 'totalOrders',
        'customerNumber': 'totalCustomers',
        'isOnTime': 'onTimeOrders'
    })
    
    # Calcular métricas derivadas
    monthly['avgOrderValue'] = monthly['totalSales'] / monthly['totalOrders']
    monthly['onTimeRate_pct'] = (monthly['onTimeOrders'] / monthly['totalOrders']) * 100
    
    # Agregar MoM y YoY
    monthly = monthly.sort_index()
    monthly['mom_change'] = monthly['totalSales'].diff()
    monthly['mom_pct'] = (monthly['totalSales'].pct_change() * 100)
    monthly['yoy_change'] = monthly['totalSales'].diff(12)
    monthly['yoy_pct'] = (monthly['totalSales'].pct_change(12) * 100)
    
    # Rolling 3M average
    monthly['rolling3M_avg'] = monthly['totalSales'].rolling(window=3, min_periods=1).mean()
    
    return monthly.reset_index().round(2)


def calculate_payment_coverage(df_base: pd.DataFrame, df_payments: pd.DataFrame) -> float:
    """
    Calcula % de payment coverage global.
    
    Returns:
        Float: Porcentaje de cobertura de pagos
    """
    # Total facturado por cliente
    total_sales = df_base.groupby('customerNumber')['lineSales'].sum()
    
    # Total pagado por cliente
    total_paid = df_payments.groupby('customerNumber')['amount'].sum()
    
    # Merge y calcular coverage
    coverage_df = pd.DataFrame({
        'sales': total_sales,
        'paid': total_paid
    }).fillna(0)
    
    coverage_pct = (coverage_df['paid'].sum() / coverage_df['sales'].sum()) * 100
    return round(coverage_pct, 2)


# ============================================================================
# 2. CUSTOMER AGGREGATIONS - Equivalente a customer_deep_agg_phase2.sql
# ============================================================================

def aggregate_customers(df_base: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega métricas por cliente con ABC classification.
    Replica: 03_customer_deep_agg_phase2.sql
    
    Returns:
        DataFrame con métricas completas por cliente
    """
    # Agregación base
    customer_agg = df_base.groupby(['customerNumber', 'customerName', 'country']).agg({
        'lineSales': 'sum',
        'quantityOrdered': 'sum',
        'orderNumber': 'nunique',
        'productCode': 'nunique'
    }).rename(columns={
        'lineSales': 'total_sales',
        'quantityOrdered': 'total_units',
        'orderNumber': 'num_orders',
        'productCode': 'num_products'
    })
    
    # Métricas derivadas
    customer_agg['avg_sales_per_order'] = customer_agg['total_sales'] / customer_agg['num_orders']
    customer_agg['avg_units_per_order'] = customer_agg['total_units'] / customer_agg['num_orders']
    customer_agg['avg_sales_per_product'] = customer_agg['total_sales'] / customer_agg['num_products']
    
    # % de global sales
    total_global_sales = customer_agg['total_sales'].sum()
    customer_agg['pct_of_global_sales'] = (customer_agg['total_sales'] / total_global_sales) * 100
    
    # Sort por ventas y calcular cumulative
    customer_agg = customer_agg.sort_values('total_sales', ascending=False).reset_index()
    customer_agg['cumulative_pct_of_global_sales'] = customer_agg['pct_of_global_sales'].cumsum()
    
    # Ranking
    customer_agg['sales_rank'] = range(1, len(customer_agg) + 1)
    
    # ABC Classification (CORREGIDO)
    customer_agg['abc_class'] = np.where(
        customer_agg.index < (customer_agg['cumulative_pct_of_global_sales'] <= 80).sum(), 'A',
        np.where(
            customer_agg.index < (customer_agg['cumulative_pct_of_global_sales'] <= 95).sum(), 'B',
            'C'
        )
    )
    
    return customer_agg.round(2)


def calculate_customer_concentration(df_customers: pd.DataFrame, top_pct: float = 0.2) -> float:
    """
    Calcula % de revenue en el top X% de clientes.
    
    Args:
        df_customers: DataFrame de aggregate_customers()
        top_pct: Porcentaje de clientes top a considerar (default 20%)
    
    Returns:
        Float: Porcentaje de revenue concentrado
    """
    df_sorted = df_customers.sort_values('total_sales', ascending=False)
    top_n = int(len(df_sorted) * top_pct)
    
    top_revenue = df_sorted.head(top_n)['total_sales'].sum()
    total_revenue = df_sorted['total_sales'].sum()
    
    return round((top_revenue / total_revenue) * 100, 2)


# ============================================================================
# 3. PRODUCT AGGREGATIONS - Equivalente a products_deep_agg.sql
# ============================================================================

def aggregate_products(df_base: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega métricas por producto con ABC classification.
    Replica: 02_products_deep_agg.sql
    
    Returns:
        DataFrame con métricas completas por producto
    """
    # Agregación base
    product_agg = df_base.groupby(['productCode', 'productName', 'productLine']).agg({
        'lineSales': 'sum',
        'quantityOrdered': 'sum',
        'orderNumber': 'nunique',
        'customerNumber': 'nunique'
    }).rename(columns={
        'lineSales': 'total_sales',
        'quantityOrdered': 'total_units',
        'orderNumber': 'num_orders',
        'customerNumber': 'num_customers'
    })
    
    # Métricas derivadas
    product_agg['avg_sales_per_order'] = product_agg['total_sales'] / product_agg['num_orders']
    product_agg['avg_units_per_order'] = product_agg['total_units'] / product_agg['num_orders']
    product_agg['avg_sales_per_customer'] = product_agg['total_sales'] / product_agg['num_customers']
    
    # % de global sales
    total_global_sales = product_agg['total_sales'].sum()
    product_agg['pct_of_global_sales'] = (product_agg['total_sales'] / total_global_sales) * 100
    
    # Sort y cumulative
    product_agg = product_agg.sort_values('total_sales', ascending=False).reset_index()
    product_agg['cumulative_pct_of_global_sales'] = product_agg['pct_of_global_sales'].cumsum()
    
    # Ranking
    product_agg['sales_rank'] = range(1, len(product_agg) + 1)
    
    # ABC Classification (CORREGIDO)
    product_agg['abc_class'] = np.where(
        product_agg.index < (product_agg['cumulative_pct_of_global_sales'] <= 80).sum(), 'A',
        np.where(
            product_agg.index < (product_agg['cumulative_pct_of_global_sales'] <= 95).sum(), 'B',
            'C'
        )
    )
    
    return product_agg.round(2)


def calculate_product_concentration(df_products: pd.DataFrame, top_n: int = 10) -> float:
    """
    Calcula % de revenue en los top N productos.
    
    Args:
        df_products: DataFrame de aggregate_products()
        top_n: Número de productos top (default 10)
    
    Returns:
        Float: Porcentaje de revenue concentrado
    """
    df_sorted = df_products.sort_values('total_sales', ascending=False)
    
    top_revenue = df_sorted.head(top_n)['total_sales'].sum()
    total_revenue = df_sorted['total_sales'].sum()
    
    return round((top_revenue / total_revenue) * 100, 2)


def get_top_bottom_products_by_line(df_base: pd.DataFrame) -> pd.DataFrame:
    """
    Identifica top y bottom productos por línea de producto.
    Replica: 06_top_bottom_product_by_productline.sql
    
    CORREGIDO: Ahora usa productLine del df_base enriquecido
    
    Returns:
        DataFrame con top y bottom seller por línea
    """
    # Agregar por producto (incluyendo productLine)
    product_sales = df_base.groupby(['productLine', 'productCode', 'productName']).agg({
        'lineSales': 'sum'
    }).rename(columns={'lineSales': 'totalSales'})
    
    # Ranking dentro de cada línea
    product_sales['salesRankDesc'] = product_sales.groupby('productLine')['totalSales'].rank(
        ascending=False, method='min'
    )
    product_sales['salesRankAsc'] = product_sales.groupby('productLine')['totalSales'].rank(
        ascending=True, method='min'
    )
    
    # Filtrar solo top y bottom
    top_bottom = product_sales[
        (product_sales['salesRankDesc'] == 1) | (product_sales['salesRankAsc'] == 1)
    ].copy()
    
    # Categoría
    top_bottom['category'] = np.where(
        top_bottom['salesRankDesc'] == 1,
        'Top Seller',
        'Worst Seller'
    )
    
    return top_bottom.reset_index()[
        ['productLine', 'productCode', 'productName', 'totalSales', 'category']
    ].sort_values(['productLine', 'category'], ascending=[True, False]).round(2)


# ============================================================================
# 4. GEOGRAPHIC AGGREGATIONS - Equivalente a sales_by_country_vs_region.sql
# ============================================================================

def aggregate_by_region(df_base: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega ventas por país y región con métricas comparativas.
    Replica: 01_sales_by_country_vs_region.sql
    
    Returns:
        DataFrame con métricas por país y región
    """
    # Mapeo de regiones
    region_mapping = {
        'USA': 'North America',
        'Canada': 'North America',
        'France': 'Europe',
        'UK': 'Europe',
        'England': 'Europe',
        'Germany': 'Europe',
        'Spain': 'Europe',
        'Norway': 'Europe',
        'Denmark': 'Europe',
        'Sweden': 'Europe',
        'Finland': 'Europe',
        'Italy': 'Europe',
        'Belgium': 'Europe',
        'Ireland': 'Europe',
        'Switzerland': 'Europe',
        'Austria': 'Europe',
        'Australia': 'Asia-Pacific',
        'Japan': 'Asia-Pacific',
        'Singapore': 'Asia-Pacific',
        'Hong Kong': 'Asia-Pacific',
        'Philippines': 'Asia-Pacific',
        'New Zealand': 'Asia-Pacific',
        'Brazil': 'Latin America',
        'Argentina': 'Latin America',
        'Chile': 'Latin America',
        'Mexico': 'Latin America',
        'Venezuela': 'Latin America',
    }
    
    df = df_base.copy()
    df['region'] = df['country'].map(region_mapping).fillna('Other')
    
    # Agregación por país
    country_agg = df.groupby(['region', 'country']).agg({
        'lineSales': 'sum',
        'orderNumber': 'nunique',
        'customerNumber': 'nunique'
    }).rename(columns={
        'lineSales': 'total_sales',
        'orderNumber': 'num_orders',
        'customerNumber': 'num_customers'
    })
    
    # Agregación por región
    region_totals = df.groupby('region').agg({
        'lineSales': 'sum',
        'orderNumber': 'nunique',
        'customerNumber': 'nunique'
    }).rename(columns={
        'lineSales': 'region_total_sales',
        'orderNumber': 'region_num_orders',
        'customerNumber': 'region_num_customers'
    })
    
    # Merge
    result = country_agg.join(region_totals, on='region')
    
    # Métricas derivadas
    result['avg_sales_per_customer'] = result['total_sales'] / result['num_customers']
    result['avg_order_value'] = result['total_sales'] / result['num_orders']
    result['pct_of_region_sales'] = (result['total_sales'] / result['region_total_sales']) * 100
    
    # % global
    global_total = result['total_sales'].sum()
    result['pct_of_global_sales'] = (result['total_sales'] / global_total) * 100
    
    # Ranking dentro de región
    result['rank_in_region'] = result.groupby('region')['total_sales'].rank(
        ascending=False, method='min'
    )
    
    return result.reset_index().round(2)


# ============================================================================
# 5. SALES REP PERFORMANCE - Equivalente a salesrep_performance_deep_agg.sql
# ============================================================================

def aggregate_salesreps(df_base: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega métricas de performance por sales rep.
    Replica: 04_salesrep_performance_deep_agg.sql
    
    CORREGIDO: Ahora usa la estructura correcta de merge.
    df_base ya debe tener employeeNumber, employeeName, jobTitle, officeCode
    del merge con employees (vía salesRepEmployeeNumber).
    
    Returns:
        DataFrame con métricas completas por sales rep
    """
    # Verificar que df_base tenga las columnas necesarias
    required_cols = ['employeeNumber', 'employeeName', 'jobTitle', 'officeCode']
    missing_cols = [col for col in required_cols if col not in df_base.columns]
    if missing_cols:
        raise ValueError(
            f"df_base debe incluir las columnas: {missing_cols}. "
            f"Usa build_enriched_base() para construir df_base correctamente."
        )
    
    # Agregar por sales rep
    rep_agg = df_base.groupby(['employeeNumber', 'employeeName', 'jobTitle', 'officeCode']).agg({
        'lineSales': 'sum',
        'quantityOrdered': 'sum',
        'orderNumber': 'nunique',
        'customerNumber': 'nunique',
        'country': 'nunique'
    }).rename(columns={
        'lineSales': 'total_sales',
        'quantityOrdered': 'total_units',
        'orderNumber': 'num_orders',
        'customerNumber': 'num_customers',
        'country': 'num_customer_countries'
    })
    
    # Métricas derivadas
    rep_agg['avg_sales_per_order'] = rep_agg['total_sales'] / rep_agg['num_orders']
    rep_agg['avg_units_per_order'] = rep_agg['total_units'] / rep_agg['num_orders']
    rep_agg['avg_sales_per_customer'] = rep_agg['total_sales'] / rep_agg['num_customers']
    
    # % de global sales
    total_global_sales = rep_agg['total_sales'].sum()
    rep_agg['pct_of_global_sales'] = (rep_agg['total_sales'] / total_global_sales) * 100
    
    # Sort y cumulative
    rep_agg = rep_agg.sort_values('total_sales', ascending=False).reset_index()
    rep_agg['cumulative_pct_of_global_sales'] = rep_agg['pct_of_global_sales'].cumsum()
    
    # Ranking
    rep_agg['sales_rank'] = range(1, len(rep_agg) + 1)
    
    # ABC Classification (CORREGIDO)
    rep_agg['abc_class'] = np.where(
        rep_agg.index < (rep_agg['cumulative_pct_of_global_sales'] <= 80).sum(), 'A',
        np.where(
            rep_agg.index < (rep_agg['cumulative_pct_of_global_sales'] <= 95).sum(), 'B',
            'C'
        )
    )
    
    return rep_agg.round(2)


# ============================================================================
# 6. DIAGNOSTIC QUERIES
# ============================================================================

def identify_high_risk_customers(
    df_base: pd.DataFrame, 
    credit_ratio_threshold: float = 2.0,
    recency_threshold_days: int = 180
) -> pd.DataFrame:
    """
    Identifica clientes de alto riesgo basado en ratios y recency.
    Replica: 04_high_risk_customers_ratio.sql
    
    CORREGIDO: Ahora usa creditLimit del df_base enriquecido
    
    Args:
        df_base: DataFrame base con creditLimit incluido
        credit_ratio_threshold: Umbral para ratio credit/sales (default 2.0)
        recency_threshold_days: Umbral de días sin ordenar (default 180)
    
    Returns:
        DataFrame con clientes de alto riesgo
    """
    # Verificar que creditLimit esté presente
    if 'creditLimit' not in df_base.columns:
        raise ValueError(
            "df_base debe incluir 'creditLimit'. "
            "Usa build_enriched_base() para construir df_base correctamente."
        )
    
    # Agregar ventas y última orden por cliente
    customer_sales = df_base.groupby(['customerNumber', 'customerName', 'country', 'creditLimit']).agg({
        'lineSales': 'sum',
        'orderDate': 'max'
    }).rename(columns={
        'lineSales': 'totalSales',
        'orderDate': 'lastOrderDate'
    }).reset_index()
    
    # Calcular recency
    max_order_date = pd.to_datetime(df_base['orderDate'].max())
    customer_sales['lastOrderDate'] = pd.to_datetime(customer_sales['lastOrderDate'])
    customer_sales['daysSinceLastOrder'] = (
        max_order_date - customer_sales['lastOrderDate']
    ).dt.days
    
    # Ratios
    customer_sales['credit_to_sales_ratio'] = np.where(
        customer_sales['totalSales'] > 0,
        customer_sales['creditLimit'] / customer_sales['totalSales'],
        np.nan
    )
    
    customer_sales['sales_to_credit_ratio'] = np.where(
        customer_sales['creditLimit'] > 0,
        customer_sales['totalSales'] / customer_sales['creditLimit'],
        np.nan
    )
    
    # Flags
    customer_sales['activityFlag'] = customer_sales.apply(
        lambda row: 'NO ORDERS / CREDIT ASSIGNED' if pd.isna(row['lastOrderDate'])
        else ('STALE ACTIVITY (>= 180 days)' if row['daysSinceLastOrder'] >= recency_threshold_days
        else 'RECENT ACTIVITY'),
        axis=1
    )
    
    customer_sales['ratioFlag'] = customer_sales.apply(
        lambda row: 'HIGH CREDIT / LOW SALES' if (
            row['credit_to_sales_ratio'] >= credit_ratio_threshold and row['totalSales'] > 0
        ) else ('LOW CREDIT / HIGH SALES' if (
            row['sales_to_credit_ratio'] >= credit_ratio_threshold and row['creditLimit'] > 0
        ) else None),
        axis=1
    )
    
    # Filtrar solo alto riesgo
    high_risk = customer_sales[
        (customer_sales['ratioFlag'].notna()) |
        (customer_sales['daysSinceLastOrder'] >= recency_threshold_days) |
        (customer_sales['lastOrderDate'].isna())
    ].copy()
    
    high_risk['riskCategory'] = 'HIGH RISK CUSTOMER'
    
    # Calcular monto en riesgo
    high_risk['amount_at_risk'] = high_risk.apply(
        lambda row: row['creditLimit'] if row['ratioFlag'] == 'HIGH CREDIT / LOW SALES' 
        else row['totalSales'],
        axis=1
    )
    
    return high_risk.round(2)


def identify_credit_misalignment(
    df_base: pd.DataFrame,
    ratio_threshold: float = 2.0
) -> pd.DataFrame:
    """
    Identifica misalignment entre credit limit y sales.
    Replica: 03_credit_vs_sales_misalignment_ratio.sql
    
    CORREGIDO: Ahora usa creditLimit del df_base enriquecido
    
    Args:
        df_base: DataFrame base con creditLimit incluido
        ratio_threshold: Umbral para considerar misalignment (default 2.0)
    
    Returns:
        DataFrame con casos de misalignment
    """
    # Verificar que creditLimit esté presente
    if 'creditLimit' not in df_base.columns:
        raise ValueError(
            "df_base debe incluir 'creditLimit'. "
            "Usa build_enriched_base() para construir df_base correctamente."
        )
    
    # Agregar ventas por cliente
    customer_sales = df_base.groupby(['customerNumber', 'customerName', 'country', 'creditLimit']).agg({
        'lineSales': 'sum'
    }).rename(columns={'lineSales': 'totalSales'}).reset_index()
    
    # Calcular ratios
    customer_sales['credit_to_sales_ratio'] = np.where(
        customer_sales['totalSales'] > 0,
        customer_sales['creditLimit'] / customer_sales['totalSales'],
        np.nan
    )
    
    customer_sales['sales_to_credit_ratio'] = np.where(
        customer_sales['creditLimit'] > 0,
        customer_sales['totalSales'] / customer_sales['creditLimit'],
        np.nan
    )
    
    # Categorizar misalignment
    customer_sales['misalignmentCategory'] = customer_sales.apply(
        lambda row: 'HIGH CREDIT / LOW SALES (credit >= 2x sales)' if (
            row['credit_to_sales_ratio'] >= ratio_threshold and row['totalSales'] > 0
        ) else ('LOW CREDIT / HIGH SALES (sales >= 2x credit)' if (
            row['sales_to_credit_ratio'] >= ratio_threshold and row['creditLimit'] > 0
        ) else 'NORMAL'),
        axis=1
    )
    
    # Filtrar solo misalignment
    misalignment = customer_sales[
        customer_sales['misalignmentCategory'] != 'NORMAL'
    ].copy()
    
    return misalignment.round(2)


def check_geographic_credit_anomalies(df_base: pd.DataFrame) -> pd.DataFrame:
    """
    Detecta anomalías en credit vs sales a nivel geográfico.
    Replica: 01_geographic_credit_anomalies.sql
    
    CORREGIDO: Ahora usa creditLimit del df_base enriquecido
    
    Returns:
        DataFrame con países anómalos
    """
    # Verificar que creditLimit esté presente
    if 'creditLimit' not in df_base.columns:
        raise ValueError(
            "df_base debe incluir 'creditLimit'. "
            "Usa build_enriched_base() para construir df_base correctamente."
        )
    
    # Agregar por cliente
    customer_sales = df_base.groupby(['customerNumber', 'country', 'creditLimit']).agg({
        'lineSales': 'sum'
    }).rename(columns={'lineSales': 'totalSales'}).reset_index()
    
    # Agregar por país
    country_profile = customer_sales.groupby('country').agg({
        'customerNumber': 'count',
        'creditLimit': ['sum', 'mean'],
        'totalSales': ['sum', 'mean']
    })
    country_profile.columns = ['num_customers', 'total_credit_limit', 'avg_credit_limit', 
                                'total_sales', 'avg_sales_per_customer']
    
    # Ratio credit/sales
    country_profile['credit_to_sales_ratio'] = np.where(
        country_profile['total_sales'] > 0,
        country_profile['total_credit_limit'] / country_profile['total_sales'],
        np.nan
    )
    
    # Percentiles
    country_profile['ratio_pct'] = country_profile['credit_to_sales_ratio'].rank(pct=True) * 100
    
    # Filtrar anomalías (top 10% y bottom 10%)
    anomalies = country_profile[
        (country_profile['ratio_pct'] >= 90) | (country_profile['ratio_pct'] <= 10)
    ].copy()
    
    # Categorizar
    anomalies['anomalyCategory'] = np.where(
        anomalies['ratio_pct'] >= 90,
        'HIGH CREDIT VS SALES (Top 10%)',
        'LOW CREDIT VS SALES (Bottom 10%)'
    )
    
    return anomalies.reset_index().round(2)


# ============================================================================
# 7. PREDICTIVE QUERIES
# ============================================================================

def calculate_product_demand_trend(df_base: pd.DataFrame) -> pd.DataFrame:
    """
    Clasifica productos como GROWING, STABLE o DECLINING.
    Replica: 05_product_demand_trend_flag.sql
    
    Returns:
        DataFrame con trend flag por producto
    """
    df = df_base.copy()
    df['orderDate'] = pd.to_datetime(df['orderDate'])
    df['salesMonth'] = df['orderDate'].dt.to_period('M')
    
    # Agregar por producto-mes
    monthly_product = df.groupby(['productCode', 'productName', 'salesMonth']).agg({
        'lineSales': 'sum'
    }).rename(columns={'lineSales': 'totalSales'})
    
    # Calcular months_ago
    max_month = monthly_product.index.get_level_values('salesMonth').max()
    monthly_product = monthly_product.reset_index()
    monthly_product['months_ago'] = (max_month - monthly_product['salesMonth']).apply(lambda x: x.n)
    
    # Ventanas: reciente (0-2 meses) vs previa (3-5 meses)
    trend_agg = monthly_product.groupby(['productCode', 'productName']).apply(
        lambda x: pd.Series({
            'recent_avg': x[x['months_ago'].between(0, 2)]['totalSales'].mean(),
            'prev_avg': x[x['months_ago'].between(3, 5)]['totalSales'].mean()
        }), include_groups=False
    ).reset_index()
    
    # Growth rate
    trend_agg['growth_rate'] = np.where(
        (trend_agg['prev_avg'].notna()) & (trend_agg['prev_avg'] > 0),
        (trend_agg['recent_avg'] - trend_agg['prev_avg']) / trend_agg['prev_avg'],
        np.nan
    )
    
    trend_agg['growth_rate_pct'] = trend_agg['growth_rate'] * 100
    
    # Clasificación
    trend_agg['demand_trend_flag'] = trend_agg['growth_rate'].apply(
        lambda x: 'INSUFFICIENT_DATA' if pd.isna(x)
        else ('GROWING' if x >= 0.15
        else ('DECLINING' if x <= -0.15
        else 'STABLE'))
    )
    
    return trend_agg.round(2)


def calculate_customer_rfm(df_base: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula RFM score por cliente.
    Replica: 06_customer_rfm_score.sql
    
    Returns:
        DataFrame con scores RFM por cliente
    """
    # Agregar por cliente
    customer_rfm = df_base.groupby(['customerNumber', 'customerName', 'country']).agg({
        'orderNumber': 'nunique',
        'lineSales': 'sum',
        'orderDate': 'max'
    }).rename(columns={
        'orderNumber': 'freq_orders',
        'lineSales': 'monetary',
        'orderDate': 'last_order_date'
    }).reset_index()
    
    # Recency
    max_order_date = pd.to_datetime(df_base['orderDate'].max())
    customer_rfm['last_order_date'] = pd.to_datetime(customer_rfm['last_order_date'])
    customer_rfm['days_since_last_order'] = (
        max_order_date - customer_rfm['last_order_date']
    ).dt.days

    # Funciones auxiliares para scores robustos
    def _quantile_score(series: pd.Series, reverse: bool = False) -> pd.Series:
        """
        Devuelve scores 1..n_bins según cuantiles.
        reverse=True => valores más pequeños tienen mejor score (mayor número).
        """
        s = series.astype(float)

        # si todos los valores son iguales o hay muy pocos, devolvemos score medio
        if s.nunique() <= 1:
            scores = pd.Series(3.0, index=s.index)
            return scores

        # número real de bins (no más que 5 ni más que valores únicos)
        q = min(5, s.nunique())

        # usamos qcut sin labels fijos para evitar el error de bin edges
        bins = pd.qcut(s, q=q, duplicates='drop')

        # codes: 0..n_bins-1, -1 para NaN
        codes = bins.cat.codes
        # 1..n_bins
        scores = codes.replace(-1, np.nan) + 1
        n_bins = int(scores.max())

        if reverse:
            # para recency: menos días = mejor score -> invertimos
            scores = (n_bins + 1 - scores)

        return scores.astype(float)

    # Recency: menor días = mejor score (invertido)
    customer_rfm['r_score'] = _quantile_score(
        customer_rfm['days_since_last_order'],
        reverse=True
    )

    # Frequency: más órdenes = mejor score
    customer_rfm['f_score'] = _quantile_score(
        customer_rfm['freq_orders'],
        reverse=False
    )

    # Monetary: más ventas = mejor score
    customer_rfm['m_score'] = _quantile_score(
        customer_rfm['monetary'],
        reverse=False
    )
    
    # RFM total
    customer_rfm['rfm_score'] = (
        customer_rfm['r_score'] + 
        customer_rfm['f_score'] + 
        customer_rfm['m_score']
    )
    
    # Segmentos simplificados
    customer_rfm['rfm_segment'] = customer_rfm['rfm_score'].apply(
        lambda x: 'Champions' if x >= 12
        else ('Loyal' if x >= 9
        else ('Potential' if x >= 6
        else 'At Risk'))
    )
    
    return customer_rfm.round(2)


def calculate_customer_next_order_prediction(df_base: pd.DataFrame) -> pd.DataFrame:
    """
    Predice fecha de próxima orden basado en intervalos históricos.
    Replica: 07_customer_next_order_prediction.sql
    
    Returns:
        DataFrame con predicción de próxima orden por cliente
    """
    df = df_base.copy()
    df['orderDate'] = pd.to_datetime(df['orderDate'])
    
    # Órdenes por cliente ordenadas por fecha
    customer_orders = df.groupby(['customerNumber', 'customerName', 'country', 'orderNumber']).agg({
        'orderDate': 'first'
    }).reset_index().sort_values(['customerNumber', 'orderDate'])
    
    # Calcular gaps entre órdenes consecutivas
    customer_orders['prev_order_date'] = customer_orders.groupby('customerNumber')['orderDate'].shift(1)
    customer_orders['gap_days'] = (
        customer_orders['orderDate'] - customer_orders['prev_order_date']
    ).dt.days
    
    # Promedio de gap por cliente
    gap_stats = customer_orders.groupby(['customerNumber', 'customerName', 'country']).agg({
        'orderDate': 'max',
        'gap_days': 'mean'
    }).rename(columns={
        'orderDate': 'last_order_date',
        'gap_days': 'avg_gap_days'
    }).reset_index()
    
    # Predicción de próxima orden
    gap_stats['expected_next_order_date'] = gap_stats.apply(
        lambda row: row['last_order_date'] + pd.Timedelta(days=row['avg_gap_days'])
        if pd.notna(row['avg_gap_days']) else None,
        axis=1
    )
    
    return gap_stats.round(1)


def identify_product_cross_sell_pairs(
    df_base: pd.DataFrame,
    min_cooccurrence: int = 3
) -> pd.DataFrame:
    """
    Identifica pares de productos que se compran juntos.
    Replica: 08_product_cross_sell_pairs.sql
    
    Args:
        df_base: DataFrame base
        min_cooccurrence: Mínimo número de co-ocurrencias (default 3)
    
    Returns:
        DataFrame con pares de productos y métricas de asociación
    """
    # Productos únicos por orden
    order_products = df_base[['orderNumber', 'productCode', 'productName']].drop_duplicates()
    
    # Self-join para obtener pares
    pairs = order_products.merge(
        order_products,
        on='orderNumber',
        suffixes=('_1', '_2')
    )
    
    # Filtrar: solo pares donde productCode1 < productCode2 (evitar duplicados)
    pairs = pairs[pairs['productCode_1'] < pairs['productCode_2']]
    
    # Contar co-ocurrencias
    pair_counts = pairs.groupby([
        'productCode_1', 'productName_1', 
        'productCode_2', 'productName_2'
    ]).size().reset_index(name='cooccurrence_count')
    
    # Filtrar por umbral mínimo
    pair_counts = pair_counts[pair_counts['cooccurrence_count'] >= min_cooccurrence]
    
    # Órdenes totales
    total_orders = df_base['orderNumber'].nunique()
    
    # Órdenes por producto
    product_order_counts = df_base.groupby('productCode')['orderNumber'].nunique()
    
    # Merge con counts
    pair_counts['product1_orders'] = pair_counts['productCode_1'].map(product_order_counts)
    pair_counts['product2_orders'] = pair_counts['productCode_2'].map(product_order_counts)
    pair_counts['total_orders'] = total_orders
    
    # Métricas de asociación
    pair_counts['support'] = pair_counts['cooccurrence_count'] / total_orders
    pair_counts['confidence_from_p1'] = pair_counts['cooccurrence_count'] / pair_counts['product1_orders']
    pair_counts['confidence_from_p2'] = pair_counts['cooccurrence_count'] / pair_counts['product2_orders']
    
    # Lift (opcional)
    pair_counts['expected_cooccurrence'] = (
        pair_counts['product1_orders'] * pair_counts['product2_orders'] / total_orders
    )
    pair_counts['lift'] = pair_counts['cooccurrence_count'] / pair_counts['expected_cooccurrence']
    
    return pair_counts.sort_values('support', ascending=False).round(4)


# ============================================================================
# 8. HELPER FUNCTIONS - Crear data para KPI cards
# ============================================================================

def create_kpi_card_data(
    df_monthly: pd.DataFrame, 
    df_base: pd.DataFrame, 
    df_payments: pd.DataFrame, 
    df_customers: pd.DataFrame,
    df_products: pd.DataFrame,
    current_year: Optional[int] = None,
    previous_year: Optional[int] = None
) -> pd.DataFrame:
    """
    Prepara data en formato para kpi_card_reference de Vizro.
    
    Args:
        df_monthly: Output de calculate_monthly_kpis()
        df_base: DataFrame base
        df_payments: DataFrame de payments
        df_customers: Output de aggregate_customers()
        df_products: Output de aggregate_products()
        current_year: Año actual (default: último año en data)
        previous_year: Año previo (default: año anterior al actual)
    
    Returns:
        DataFrame con KPIs en formato para kpi_card_reference
    """
    # Determinar años si no se especifican
    df_monthly['year'] = pd.to_datetime(df_monthly['salesMonth'] + '-01').dt.year
    
    if current_year is None or previous_year is None:
        years = sorted(df_monthly['year'].unique())
        if len(years) >= 2:
            current_year = years[-1]
            previous_year = years[-2]
        else:
            current_year = years[-1] if years else datetime.now().year
            previous_year = current_year - 1
    
    # Filtrar por años
    df_current = df_monthly[df_monthly['year'] == current_year]
    df_previous = df_monthly[df_monthly['year'] == previous_year]
    
    # KPIs calculados
    kpi_data = {
        # Total Revenue
        f'Total_Revenue_{current_year}': df_current['totalSales'].sum(),
        f'Total_Revenue_{previous_year}': df_previous['totalSales'].sum(),
        
        # Total Orders
        f'Total_Orders_{current_year}': df_current['totalOrders'].sum(),
        f'Total_Orders_{previous_year}': df_previous['totalOrders'].sum(),
        
        # AOV (Average Order Value)
        f'AOV_{current_year}': df_current['avgOrderValue'].mean(),
        f'AOV_{previous_year}': df_previous['avgOrderValue'].mean(),
        
        # On-Time Rate
        f'OnTimeRate_{current_year}': df_current['onTimeRate_pct'].mean(),
        f'OnTimeRate_{previous_year}': df_previous['onTimeRate_pct'].mean(),
        
        # Payment Coverage
        f'PaymentCoverage_{current_year}': calculate_payment_coverage(df_base, df_payments),
        f'PaymentCoverage_{previous_year}': calculate_payment_coverage(df_base, df_payments),
        
        # Customer Concentration
        f'CustomerConcentration_{current_year}': calculate_customer_concentration(df_customers, top_pct=0.2),
        f'CustomerConcentration_{previous_year}': calculate_customer_concentration(df_customers, top_pct=0.2),
        
        # Product Concentration
        f'ProductConcentration_{current_year}': calculate_product_concentration(df_products, top_n=10),
        f'ProductConcentration_{previous_year}': calculate_product_concentration(df_products, top_n=10),
    }
    
    return pd.DataFrame([kpi_data])


def get_context_banner_data(
    df_base: pd.DataFrame,
    df_offices: pd.DataFrame,
    df_employees: pd.DataFrame
) -> dict:
    """
    Genera data para el context banner (números estructurales).
    
    Returns:
        Dict con: offices, sales_reps, countries_served, customers
    """
    return {
        'offices': df_offices['officeCode'].nunique(),
        'sales_reps': df_employees['employeeNumber'].nunique(),
        'countries_served': df_base['country'].nunique(),
        'customers': df_base['customerNumber'].nunique(),
    }


def calculate_diagnostic_summary(
    df_high_risk: pd.DataFrame,
    df_misalignment: pd.DataFrame
) -> dict:
    """
    Genera resumen de métricas de riesgo para el dashboard.
    
    Args:
        df_high_risk: Output de identify_high_risk_customers()
        df_misalignment: Output de identify_credit_misalignment()
    
    Returns:
        Dict con conteos y montos en riesgo
    """
    high_risk_count = len(df_high_risk)
    high_risk_amount = df_high_risk['amount_at_risk'].sum() if 'amount_at_risk' in df_high_risk.columns else 0
    
    misalignment_count = len(df_misalignment)
    over_credited = len(df_misalignment[
        df_misalignment['misalignmentCategory'].str.contains('HIGH CREDIT', na=False)
    ])
    under_credited = len(df_misalignment[
        df_misalignment['misalignmentCategory'].str.contains('LOW CREDIT', na=False)
    ])
    
    return {
        'high_risk_customers_count': high_risk_count,
        'high_risk_customers_pct': round(high_risk_count / df_misalignment['customerNumber'].nunique() * 100, 1),
        'amount_at_risk': round(high_risk_amount, 2),
        'misalignment_count': misalignment_count,
        'over_credited_count': over_credited,
        'under_credited_count': under_credited,
    }


# ============================================================================
# 9. UTILITY FUNCTIONS
# ============================================================================

def add_mom_yoy_metrics(df: pd.DataFrame, value_col: str, date_col: str = 'salesMonth') -> pd.DataFrame:
    """
    Agrega métricas MoM (Month-over-Month) y YoY (Year-over-Year) a cualquier serie temporal.
    
    Args:
        df: DataFrame con columna de valores y fechas
        value_col: Nombre de la columna con valores
        date_col: Nombre de la columna con fechas (default 'salesMonth')
    
    Returns:
        DataFrame con columnas adicionales: mom_change, mom_pct, yoy_change, yoy_pct
    """
    df = df.copy().sort_values(date_col)
    
    # MoM
    df['mom_change'] = df[value_col].diff()
    df['mom_pct'] = df[value_col].pct_change() * 100
    
    # YoY (12 meses atrás)
    df['yoy_change'] = df[value_col].diff(12)
    df['yoy_pct'] = df[value_col].pct_change(12) * 100
    
    # Rolling averages
    df['rolling3M_avg'] = df[value_col].rolling(window=3, min_periods=1).mean()
    df['rolling6M_avg'] = df[value_col].rolling(window=6, min_periods=1).mean()
    
    return df.round(2)


def filter_top_n_by_group(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    n: int = 5,
    ascending: bool = False
) -> pd.DataFrame:
    """
    Filtra los top N registros por grupo.
    
    Args:
        df: DataFrame a filtrar
        group_col: Columna por la cual agrupar
        value_col: Columna por la cual rankear
        n: Número de registros a mantener por grupo
        ascending: Si True, toma los N menores; si False, los N mayores
    
    Returns:
        DataFrame filtrado
    """
    return df.groupby(group_col, group_keys=False).apply(
        lambda x: x.nlargest(n, value_col) if not ascending else x.nsmallest(n, value_col),
        include_groups=False
    ).reset_index(drop=True)