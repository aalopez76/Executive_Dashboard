# CLAUDE.md — Single source of truth

> Dashboard ejecutivo de KPIs (BI). **No es un proyecto de ML.** Stack real verificado por
> auditoría (ver `docs/AUDIT.md`). Cualquier futura skill/hook/comando debe respetar esta realidad.

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

> Hay `Makefile` (en Windows sin `make`, usar el python del `.venv` directamente; ver README).
> Override del intérprete: `make test PYTHON=.venv/Scripts/python.exe`.

| Acción | make | Directo |
|--------|------|---------|
| Ejecutar app (local) | `make run` | `python app.py` |
| Lint | `make lint` | `ruff check .` |
| Format (opt-in) | `make format` | `ruff check --fix . ; black .` |
| Tests | `make test` | `python -m pytest` |
| Servir (prod) | — | `gunicorn wsgi:server --bind 0.0.0.0:$PORT` |
| Regenerar lockfile | — | `pip-compile --no-annotate --strip-extras requirements.in` |
| Validar un dataset | — | `/data_validation <ruta-o-nombre>` |
| Revisar el dashboard | — | `/dashboard_review` |

> **BD en tests/deploy:** fijar `DB_PATH` a `SQL-Connection-Module/examples/toys_and_models.sqlite`;
> `get_db_path()` por defecto apunta a una copia externa al repo (no fiable en clon limpio/CI).

## Estructura

```
app.py                 # App factory Vizro -> create_app()
wsgi.py                # Entrypoint WSGI (gunicorn wsgi:server)
utils/                 # data, data_engine, query_reader, pages, _charts
tests/                 # pytest: data_integrity, queries, dashboard_build
configs/thresholds.yaml# umbrales para tests y /dashboard_review
requirements.in        # deps directas (fuente del lockfile)
requirements.txt       # LOCKFILE (pip-compile) · requirements-dev.txt (tooling)
pyproject.toml         # config ruff / black / pytest
Makefile               # run/lint/format/test/review/clean
.github/workflows/     # CI (ruff + pytest)
.claude/               # skills, commands, hooks, settings
docs/                  # AUDIT.md, REFACTOR_PLAN.md, informes generados
SQL-Connection-Module/ # [submódulo] conector SQL multi-motor + BD de ejemplo
SQL-Queries/           # [submódulo] queries .sql (analytical/diagnostic/predictive)
Executive-kpi-dashboard/ # bundle de despliegue HF Spaces (repo git propio, gitignored)
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

## Estado (rama chore/reproducibility-and-tests)

Resuelto en esta iteración: lockfile (`pip-tools`), suite de tests (`tests/`, 19 tests verdes),
config de estilo (`pyproject.toml`), CI (`.github/workflows/ci.yml`), deploy WSGI
(`wsgi.py` + `Dockerfile` con gunicorn), `README.md` y `.env.example`. Respaldo: rama
`backup/pre-refactor-2026-06-03`.

### Deuda técnica pendiente
- 🟡 `get_db_path()` por defecto apunta fuera del repo; en local/CI se mitiga con `DB_PATH`,
  pero convendría corregir la ruta por defecto a la copia interna del submódulo.
- 🟢 `black --check` no es bloqueante en CI (el código heredado no está black-formateado);
  aplicar `make format` en un commit `style:` dedicado si se desea activarlo.
