# Executive KPI Dashboard

Dashboard ejecutivo de **KPIs de ventas** (BI) sobre la base de ejemplo *Classic Models*
(`toys_and_models.sqlite`), construido con **Vizro/Dash + pandas** y alimentado por queries SQL
versionadas. No es un proyecto de machine learning: las vistas `predictive/` son SQL analítico
(RFM, cross-sell, tendencias), no modelos entrenados.

> Documentación de arquitectura y decisiones: [`docs/AUDIT.md`](docs/AUDIT.md) ·
> [`docs/REFACTOR_PLAN.md`](docs/REFACTOR_PLAN.md) · [`CLAUDE.md`](CLAUDE.md).

## Requisitos

- **Python 3.11**
- **git** (el proyecto usa submódulos: `SQL-Connection-Module` y `SQL-Queries`)

## Instalación

```bash
# 1) Clonar CON submódulos (imprescindible)
git clone --recurse-submodules <url-del-repo>
cd Executive_Dashboard
# Si ya clonaste sin submódulos:
git submodule update --init --recursive

# 2) Entorno virtual
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate

# 3) Dependencias (runtime + desarrollo)
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

`requirements.txt` es un **lockfile** generado con `pip-tools` (versiones transitivas fijadas y
alineadas al entorno probado: `dash 3.1.1`, `plotly 5.24.0`, `flask 3.0.3`). Para regenerarlo,
ver la cabecera del propio archivo o editar `requirements.in`.

## Configuración

Copia `.env.example` a `.env` y ajusta `DB_PATH` para apuntar a la BD del submódulo:

```bash
DB_PATH=./SQL-Connection-Module/examples/toys_and_models.sqlite
```

> Sin `DB_PATH`, `app.get_db_path()` resuelve a una copia del submódulo **un nivel por encima**
> del repo, que puede no existir en un clon limpio. Fijar `DB_PATH` evita sorpresas.

## Ejecutar el dashboard

```bash
make run                      # = python app.py
# Windows sin make:
.venv\Scripts\python.exe app.py
```

Abre el dashboard en `http://127.0.0.1:8050`.

## Tests

```bash
make test                     # = python -m pytest
# Windows sin make:
.venv\Scripts\python.exe -m pytest
```

La suite valida el contrato de datos (`load_datasets`), la resolución de las queries SQL y que el
dashboard se construye con las páginas requeridas. Usa la BD del submódulo como fixture; si no está
disponible, esos tests se omiten (skip).

## Lint y formato

```bash
make lint                     # ruff check .
make format                   # ruff check --fix . && black .
```

## Despliegue (producción)

WSGI con gunicorn (Vizro/Dash no es ASGI):

```bash
gunicorn wsgi:server --bind 0.0.0.0:8050
```

Con Docker:

```bash
docker build -t executive-kpi-dashboard .
docker run -p 8050:8050 executive-kpi-dashboard
```

El `Dockerfile` fija `DB_PATH` a la BD interna y arranca `gunicorn wsgi:server`. La carpeta
`Executive-kpi-dashboard/` es un bundle self-contained aparte para Hugging Face Spaces.

## Comandos rápidos (equivalencia PowerShell ↔ make)

| Acción | make | PowerShell (sin make) |
|--------|------|------------------------|
| Ejecutar | `make run` | `.venv\Scripts\python.exe app.py` |
| Tests | `make test` | `.venv\Scripts\python.exe -m pytest` |
| Lint | `make lint` | `.venv\Scripts\python.exe -m ruff check .` |
| Formato | `make format` | `.venv\Scripts\python.exe -m ruff check --fix .; .venv\Scripts\python.exe -m black .` |

## Estructura

```
app.py                 # App factory Vizro -> create_app()
wsgi.py                # Entrypoint WSGI (gunicorn wsgi:server)
utils/                 # data, data_engine, query_reader, pages, _charts
tests/                 # pytest: integridad de datos, queries, build
configs/thresholds.yaml# umbrales para tests y /dashboard_review
requirements*.txt      # lockfile (runtime) y dev; requirements.in (fuente)
Makefile               # run/lint/format/test/review/clean
.github/workflows/     # CI (lint + tests)
.claude/               # skills, commands y hooks de Claude Code
docs/                  # AUDIT.md, REFACTOR_PLAN.md, informes generados
SQL-Connection-Module/ # [submódulo] conector SQL + BD de ejemplo
SQL-Queries/           # [submódulo] queries .sql versionadas
```

## Claude Code

El repo incluye skills y comandos: `/data_validation <ruta>` (valida un dataset → `docs/data_report.md`)
y `/dashboard_review` (dictamen de salud vs. `configs/thresholds.yaml`). Ver [`CLAUDE.md`](CLAUDE.md).
