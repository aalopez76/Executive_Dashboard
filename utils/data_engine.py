# utils/data_engine.py
import logging
import sqlite3
from typing import Dict

import pandas as pd

from .query_reader import load_sql_query

logger = logging.getLogger(__name__)


class DataEngine:
    """
    Motor de datos basado en SQLite:
    - Lee tablas raw (para df_base en Pandas).
    - Ejecuta queries SQL versionadas (analytical/diagnostic/predictive/descriptive).
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        logger.info("DataEngine conectado a: %s", db_path)

    def _execute_query(self, relative_path: str) -> pd.DataFrame:
        """
        Carga el SQL desde disco mediante query_reader y ejecuta en SQLite.
        Devuelve DF vacío si hay error para no romper UI.
        """
        try:
            sql = load_sql_query(relative_path)
            return pd.read_sql(sql, self.conn)
        except Exception as e:
            logger.error("Error ejecutando query %s: %s", relative_path, e)
            return pd.DataFrame()

    def get_table(self, table: str, cols: str = "*") -> pd.DataFrame:
        """
        Lectura directa de tablas. Se usa para construir df_base (Pandas).
        """
        try:
            return pd.read_sql(f"SELECT {cols} FROM {table}", self.conn)
        except Exception as e:
            logger.error("Error leyendo tabla %s: %s", table, e)
            return pd.DataFrame()

    def get_raw_inputs(self) -> Dict[str, pd.DataFrame]:
        """
        Inputs mínimos para construir df_base + métricas auxiliares (payments/offices).
        """
        return {
            "orders": self.get_table("orders"),
            "orderdetails": self.get_table("orderdetails"),
            "customers": self.get_table("customers"),
            "products": self.get_table("products"),
            "employees": self.get_table("employees"),
            "payments": self.get_table("payments", "customerNumber, paymentDate, amount"),
            "offices": self.get_table("offices", "officeCode, city, country, territory"),
        }

    # ---------------------------
    # DATASETS “CORE” (SQL)
    # ---------------------------
    def get_core_datasets(self) -> Dict[str, pd.DataFrame]:
        """
        Datasets equivalentes al set 'core' que consumía tu dashboard.
        """
        return {
            # timeseries empresa
            "monthly": self._execute_query("predictive/01_company_monthly_timeseries.sql"),

            # ABCs
            "customers": self._execute_query("analytical/03_customer_deep_agg_phase2.sql"),
            "products": self._execute_query("analytical/02_products_deep_agg.sql"),

            # geografía comparativa
            "regions": self._execute_query("analytical/01_sales_by_country_vs_region.sql"),

            # performance reps (nombre correcto del archivo)
            "salesreps": self._execute_query("analytical/04_salesrep_performance_deep_agg.sql"),

            # opcionales
            "top_bottom": self._execute_query("analytical/06_top_bottom_product_by_productline.sql"),
        }

    def get_diagnostics(self) -> Dict[str, pd.DataFrame]:
        return {
            "high_risk": self._execute_query("diagnostic/04_high_risk_customers_ratio.sql"),
            "misalignment": self._execute_query("diagnostic/03_credit_vs_sales_misalignment_ratio.sql"),
            "geo_anomalies": self._execute_query("diagnostic/01_geographic_credit_anomalies.sql"),
        }

    def get_predictive(self) -> Dict[str, pd.DataFrame]:
        return {
            "product_trends": self._execute_query("predictive/05_product_demand_trend_flag.sql"),
            "customer_rfm": self._execute_query("predictive/06_customer_rfm_score.sql"),
            "next_orders": self._execute_query("predictive/07_customer_next_order_prediction.sql"),
            "cross_sell": self._execute_query("predictive/08_product_cross_sell_pairs.sql"),
        }

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception as e:
            logger.warning("Error cerrando conexión SQLite: %s", e)
