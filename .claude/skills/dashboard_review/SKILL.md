---
name: dashboard_review
description: Revisa la salud del dashboard de KPIs antes de publicar — valida la calidad de datos contra los umbrales de configs/thresholds.yaml, comprueba que las queries SQL resuelven, que el dashboard se construye sin error y que el bundle de despliegue está listo, y emite un dictamen aprobado/necesita revisión. Úsala al revisar el dashboard, antes de un deploy, o para un chequeo de release. Sustituye a "model_review" porque este proyecto NO tiene modelos ML.
---

# Skill: Revisión del dashboard (adaptada de "model_review")

> La plantilla original pedía revisar un **modelo** (accuracy/F1/RMSE, MLflow, DVC). Este
> proyecto es **BI sin modelos entrenados, MLflow ni DVC**. Esta skill revisa lo que sí es
> crítico aquí: integridad de datos, resolución de queries y construcción del dashboard.

## Procedimiento

1. **Umbrales**: carga `configs/thresholds.yaml`.
2. **Datasets**: `from utils.data import load_datasets; ds = load_datasets(db_path)`
   (resuelve `db_path` con `app.get_db_path()`).
3. **Calidad vs. umbrales**:
   - % de nulos por columna crítica ≤ `data_quality.max_null_pct`.
   - `ds["data_quality"]["invalid_date_pct"]` ≤ `data_quality.max_invalid_date_pct`.
   - cobertura de pagos (de `kpi_cards` / `calculate_payment_coverage`) ≥ `min_payment_coverage_pct`.
   - nº de filas por dataset clave ≥ `datasets.*_min_rows`.
4. **Queries**: comprueba que las SQL referenciadas en `utils/data_engine.py` resuelven vía
   `utils.query_reader.load_sql_query` (sin `FileNotFoundError`) y devuelven DataFrame no vacío.
5. **Construcción**: `from app import create_app; create_app()` debe completar sin excepción y
   generar las `dashboard.required_pages` de los umbrales.
6. **Despliegue**: verifica que el bundle `Executive-kpi-dashboard/` expone `server` para gunicorn.
   Recuerda: el `app.py` **raíz** hoy NO lo hace (ver `AUDIT.md` #2).
7. **Versionado de artefactos** (sección MLflow/DVC de la plantilla original):
   no aplica hoy → reporta `N/A — sin MLflow/DVC en este proyecto`, no lo cuentes como fallo.

## Dictamen

Termina SIEMPRE con uno de:
- ✅ **APROBADO** — todos los umbrales y checks pasan.
- ⚠️ **NECESITA REVISIÓN** — enumera cada check fallido con `valor_actual` vs. `umbral`.
