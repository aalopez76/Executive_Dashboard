---
name: data_validation
description: Valida la calidad de un dataset tabular (esquema, tipos, nulos, valores extremos por IQR, cardinalidad de categóricas, duplicados) y produce un informe reproducible en docs/data_report.md. Úsala cuando se pida validar datos, comprobar la calidad de un CSV/parquet/tabla SQLite o de un dataset de load_datasets, o antes de alimentar el dashboard.
---

# Skill: Validación de datos

Proyecto BI (Vizro/Dash + pandas + SQLite). Valida un dataset tabular y genera un informe.

## Entrada

La ruta/identificador indicado puede ser:
- Un archivo: `.csv`, `.parquet`.
- Una tabla SQLite: `ruta/al.sqlite::tabla`.
- El nombre de un dataset producido por `utils.data.load_datasets()`
  (p.ej. `base`, `monthly`, `customers`, `products`, `high_risk`, `customer_rfm`).

## Procedimiento

1. **Cargar** el dataset:
   - CSV/Parquet → `pandas.read_csv` / `read_parquet`.
   - `archivo.sqlite::tabla` → `sqlite3.connect` + `pd.read_sql("SELECT * FROM tabla", conn)`.
   - Nombre lógico → `from utils.data import load_datasets; df = load_datasets(db_path)[<nombre>]`
     (usa `app.get_db_path()` para resolver `db_path`).
2. **Esquema**: nº de filas y columnas; lista de columnas con su dtype. Señala columnas
   esperadas que falten o dtypes sospechosos (p.ej. fechas guardadas como `object`).
3. **Nulos**: conteo y % por columna. Marca en rojo las que superen
   `data_quality.max_null_pct` de `configs/thresholds.yaml`.
4. **Valores extremos** (numéricas): `min`, `max`, media, std y nº de outliers por regla IQR
   (fuera de `[Q1 − 1.5·IQR, Q3 + 1.5·IQR]`).
5. **Cardinalidad** (categóricas/`object`): nº de valores únicos y top-5 más frecuentes.
   Avisa si la cardinalidad ≈ nº de filas (posible identificador, no categórica).
6. **Duplicados**: filas totalmente duplicadas y duplicados sobre la clave candidata si se conoce.
7. **Informe**: escribe/actualiza `docs/data_report.md` con tablas markdown, fecha (`2026-...`),
   dataset analizado y un veredicto: **OK** / **OK con avisos** / **FALLA** según los umbrales.

## Salida

- `docs/data_report.md` actualizado (no sobrescribas informes de otros datasets: añade sección).
- Resumen en el chat con los 3 hallazgos más relevantes.

**No modifiques los datos de origen.** Ejecuta el análisis con un script Python temporal o inline.
