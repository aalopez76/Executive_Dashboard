# AUDIT.md — Auditoría del proyecto

> Generado el 2026-06-03 como **Fase 0** de la configuración del entorno de Claude Code.
> Objetivo: dejar por escrito qué es realmente este proyecto antes de añadir skills, hooks y comandos.

## 1. Naturaleza del proyecto

**Esto NO es un proyecto de machine learning.** Es un **dashboard ejecutivo de KPIs (BI)**
construido sobre la base de datos de ejemplo *Classic Models* (`toys_and_models.sqlite`).

| Dimensión | Realidad observada |
|-----------|--------------------|
| Tipo | Dashboard analítico / BI, no entrenamiento de modelos |
| Framework UI | **Vizro 0.1.44** (sobre Dash / Plotly / dash-bootstrap-components) |
| Procesamiento | **pandas 2.2.2** |
| Fuente de datos | **SQLite** (`toys_and_models.sqlite`) leída vía submódulo SQL |
| Servidor producción | **gunicorn 23.0.0** (WSGI) declarado en requirements |
| Gestor de dependencias | **pip + `requirements.txt`** (NO Poetry) |
| Versión de Python | Dockerfile fija **3.11-slim** |
| Tracking de experimentos | **Ninguno** (no hay MLflow) |
| Versionado de datos | **Ninguno** (no hay DVC) |
| Modelos serializados | **Ninguno** (no hay `.pkl`, `.joblib`, `.onnx`, etc.) |
| Tests | Solo en el submódulo `SQL-Connection-Module/tests/` |

> ⚠️ Las queries de la carpeta `predictive/` (RFM, cross-sell, next-order, demand-trend)
> son **SQL analítico**, no modelos entrenados. No hay paso de `fit`/`predict` en Python.

## 2. Estructura real

```
Executive_Dashboard/
├── app.py                      # App factory Vizro → create_app()
├── Dockerfile                  # python:3.11-slim
├── requirements.txt            # vizro, pandas, gunicorn, -e ./SQL-Connection-Module
├── utils/
│   ├── data.py                 # Carga/enriquece datasets; calcula KPIs y diagnósticos
│   ├── data_engine.py          # DataEngine: SQLite + ejecuta SQL versionado
│   ├── query_reader.py         # Localiza ficheros .sql en SQL-Queries/
│   ├── pages.py                # Construye páginas Vizro (exec, risks, opps, deep dive, regional)
│   └── _charts.py              # Helpers de gráficos
├── assets/                     # css, favicon, imágenes (logo, gif/png del dashboard)
├── SQL-Connection-Module/      # [submódulo git] conector multi-motor + tests
└── SQL-Queries/                # [submódulo git] queries .sql (analytical/diagnostic/predictive)
```

### Submódulos (`.gitmodules`)
- `SQL-Connection-Module` → https://github.com/aalopez76/SQL-Connection-Module
- `SQL-Queries` → https://github.com/aalopez76/SQL-Queries

## 3. Flujo de datos

1. `app.py::get_db_path()` resuelve la ruta a `toys_and_models.sqlite` (env `DB_PATH` o ruta relativa).
2. `DataEngine` (utils/data_engine.py) abre SQLite y ejecuta SQL versionado vía `query_reader`.
3. `load_datasets()` (utils/data.py) construye `df_base` enriquecido y ~20 datasets
   (monthly, customers, products, regions, high_risk, rfm, cross_sell, kpi_cards…).
4. `pages.py` arma las páginas Vizro; `app.py` ensambla el `vm.Dashboard`.

## 4. Hallazgos / riesgos detectados

| # | Severidad | Hallazgo |
|---|-----------|----------|
| 1 | 🟢 Resuelto | **`Executive-kpi-dashboard/` es un bundle de despliegue para Hugging Face Spaces**, no una copia accidental. Remote: `huggingface.co/spaces/aalpzp/Executive_KPI_Dashboard`. Es self-contained: BD local en `data/`, queries copiadas en lugar de submódulos, `requirements.txt` con `numpy`/`sqlalchemy` explícitos y sin `-e ./SQL-Connection-Module`. **Expone `app = create_app()` y `server = app.dash.server`** para gunicorn. Recomendación: dejar intacto y añadir a `.gitignore` del repo raíz para que no contamine `git status` (es un repo git propio). |
| 2 | 🟠 Media | **Dockerfile del repo raíz probablemente roto**: `CMD uvicorn app:app`. Vizro/Dash es **WSGI**, no ASGI → `uvicorn` no es el servidor adecuado (en requirements está `gunicorn`). Además `app.py` raíz **no** expone un objeto `app`/`server` a nivel de módulo, solo `create_app()`. El bundle de HF (hallazgo #1) sí lo hace bien; el repo raíz debería alinearse: `gunicorn app:server` previa exposición de `server`. |
| 3 | 🟠 Media | **Incoherencia de versión de Python**: Dockerfile usa 3.11; cualquier config nueva debería alinearse (la plantilla propuesta menciona 3.12). |
| 4 | 🟡 Baja | **Sin tests ni linting en el repo raíz**: no hay `pytest`, `ruff`, `black` declarados ni configurados. Solo el submódulo tiene tests. |
| 5 | 🟡 Baja | **Sin README** en la raíz del proyecto. |
| 6 | 🟡 Baja | Cambios sin commit en `app.py`, `Dockerfile`, `requirements.txt`, `utils/pages.py`. |

## 5. Implicaciones para la configuración de Claude Code

La plantilla solicitada (skills de **revisión de modelos**, `CLAUDE.md` con
**Poetry / scikit-learn / MLflow / DVC / `make train`**) **no corresponde a este proyecto**.
Aplicarla tal cual produciría un `CLAUDE.md` que *miente* sobre el stack y una skill
`model_review` inútil (no hay modelos). Antes de la Fase 2 hay que decidir cómo adaptarla
(ver propuesta en el chat).
