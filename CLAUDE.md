# CLAUDE.md — Single source of truth

> Dashboard ejecutivo de KPIs (BI). **No es un proyecto de ML.** Stack real verificado por
> auditoría (ver `AUDIT.md`). Cualquier futura skill/hook/comando debe respetar esta realidad.

## Proyecto

- **Nombre:** Executive_KPI_Dashboard
- **Tipo:** Dashboard analítico / BI (no entrenamiento de modelos)
- **Datos:** Base SQLite *Classic Models* (`toys_and_models.sqlite`) — ventas, clientes, productos, pagos.

## Stack (real)

| Capa | Tecnología |
|------|-----------|
| Lenguaje | Python **3.11** (Dockerfile: `python:3.11-slim`) |
| UI | **Vizro 0.1.44** (Dash · Plotly · dash-bootstrap-components) |
| Datos | **pandas 2.2.2** |
| Fuente | **SQLite** vía submódulo `SQL-Connection-Module` |
| Queries | SQL versionado en submódulo `SQL-Queries` |
| Dependencias | **pip + `requirements.txt`** (NO Poetry) |
| Servidor prod | **gunicorn** (WSGI) |
| Tracking experimentos | **N/A** (sin MLflow) |
| Versionado de datos | **N/A** (sin DVC) |
| Modelos | **N/A** (las queries `predictive/` son SQL analítico, no modelos) |

## Comandos

> No hay `Makefile`. Estos son los comandos reales del proyecto (PowerShell/Windows).

| Acción | Comando |
|--------|---------|
| Ejecutar app (local) | `python app.py` |
| Lint | `ruff check .` |
| Format | `ruff check --fix . ; black .` |
| Tests (submódulo) | `python -m pytest SQL-Connection-Module/tests` |
| Validar un dataset | `/data_validation <ruta-o-nombre>` |
| Revisar el dashboard | `/dashboard_review` |

## Estructura

```
app.py                 # App factory Vizro -> create_app()
utils/                 # data, data_engine, query_reader, pages, _charts
SQL-Connection-Module/ # [submódulo] conector SQL multi-motor + tests
SQL-Queries/           # [submódulo] queries .sql (analytical/diagnostic/predictive)
configs/thresholds.yaml# umbrales para /dashboard_review
docs/                  # informes generados (data_report.md, ...)
.claude/               # skills, commands, hooks, settings
Executive-kpi-dashboard/ # bundle de despliegue para Hugging Face Spaces (repo git propio)
```

## Skills (auto-invocables por contexto)

| Skill | Archivo | Para qué |
|-------|---------|----------|
| `data_validation` | `.claude/skills/data_validation/SKILL.md` | Validar calidad de un dataset → `docs/data_report.md` |
| `dashboard_review` | `.claude/skills/dashboard_review/SKILL.md` | Dictamen de salud del dashboard vs. umbrales |

## Comandos personalizados (slash commands)

| Comando | Archivo | Invocación |
|---------|---------|-----------|
| `/data_validation` | `.claude/commands/data_validation.md` | `/data_validation <ruta-o-nombre>` |
| `/dashboard_review` | `.claude/commands/dashboard_review.md` | `/dashboard_review` |

## Hooks

> ⚠️ Los hooks de Claude Code **NO** se configuran aquí en YAML — se configuran en
> `.claude/settings.json` y los ejecuta el harness. Esto es solo documentación.

- **PostToolUse** sobre `Write|Edit`: ejecuta `.claude/hooks/format_python.py`, que aplica
  `ruff check --fix` + `black` a los archivos `.py` editados. Multiplataforma; no bloquea si
  falla una herramienta.
- *Prettier para `.md` NO configurado*: prettier no está instalado en este entorno.

## Deuda técnica conocida (de AUDIT.md)

- 🟠 `Dockerfile` raíz arranca con `uvicorn app:app`; debería ser `gunicorn app:server` previa
  exposición de `server = create_app().dash.server` (el bundle de HF ya lo hace bien).
- 🟡 Sin README en la raíz.
