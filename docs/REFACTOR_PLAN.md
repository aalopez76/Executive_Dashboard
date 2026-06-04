# Plan de refactorización — Executive_KPI_Dashboard

> Derivado de `docs/AUDIT.md`. Orden por impacto, de mayor a menor, **sin romper la funcionalidad
> existente**. Cada tarea se entrega en un commit Conventional Commits independiente.
> Rama de trabajo: `chore/reproducibility-and-tests` · Retorno: `backup/pre-refactor-2026-06-03`.

## Leyenda
- **Objetivo** · **Archivos** · **Hecho cuando** · **No rompe** (garantía de seguridad).

---

## T1 — Config de estilo y pytest (`pyproject.toml`) 🔴
- **Objetivo:** estilo determinista (ruff/black, line-length, `target=py311`) y config de pytest.
- **Archivos:** `pyproject.toml` (nuevo).
- **Hecho cuando:** `ruff check .` y `black --check .` corren con reglas explícitas; `pytest` descubre `tests/`.
- **No rompe:** solo añade configuración; no toca código ejecutable.
- **Commit:** `build: add pyproject.toml with ruff/black/pytest config`.

## T2 — Lockfile reproducible (`pip-tools`) 🔴
- **Objetivo:** fijar dependencias transitivas.
- **Archivos:** `requirements.in` (nuevo, deps directas), `requirements.txt` (regenerado pinneado).
- **Hecho cuando:** `pip-compile` produce `requirements.txt` con versiones exactas; instalación limpia reproducible.
- **Nota:** el editable `-e ./SQL-Connection-Module` no admite `--generate-hashes`; lock sin hashes o submódulo aparte (se decide al ejecutar).
- **No rompe:** mismas versiones directas ya en uso; solo se añaden pins transitivos.
- **Commit:** `build: pin transitive deps with pip-tools lockfile`.

## T3 — Red de tests (`tests/`) 🔴
- **Objetivo:** regresión sobre datos, queries y build.
- **Archivos:** `tests/conftest.py`, `tests/test_data_integrity.py`, `tests/test_queries.py`, `tests/test_dashboard_build.py`.
- **Reusa:** `utils.data.load_datasets`, `utils.data_engine.DataEngine`, `utils.query_reader.load_sql_query`, `app.create_app/get_db_path`, `configs/thresholds.yaml`.
- **Fixture:** BD real `SQL-Connection-Module/examples/toys_and_models.sqlite`.
- **Hecho cuando:** `pytest` en verde; cubre contrato de ~20 datasets, resolución de SQL y `create_app()` con las `required_pages`.
- **No rompe:** solo lee; no modifica datos ni lógica.
- **Commit:** `test: add data-integrity, query and dashboard-build tests`.

## T4 — Automatización (`Makefile`) 🟡
- **Objetivo:** comandos únicos y memorizables.
- **Archivos:** `Makefile` (targets `run`, `lint`, `format`, `test`, `review`, `clean`).
- **Hecho cuando:** cada target ejecuta su comando real; documentado para PowerShell en README.
- **No rompe:** wrappers de comandos ya válidos.
- **Commit:** `build: add Makefile with run/lint/format/test targets`.

## T5 — CI (GitHub Actions) 🟡
- **Objetivo:** verificación automática en cada push/PR.
- **Archivos:** `.github/workflows/ci.yml`.
- **Hecho cuando:** workflow con `checkout` (submódulos), Python 3.11, install, `ruff`, `black --check`, `pytest`.
- **No rompe:** infraestructura nueva, aislada del runtime.
- **Commit:** `ci: add GitHub Actions pipeline (lint + tests)`.

## T6 — Deploy WSGI (`wsgi.py` + `Dockerfile`) 🟡
- **Objetivo:** contenedor que arranca correctamente.
- **Archivos:** `wsgi.py` (nuevo, expone `server`), `Dockerfile` (`gunicorn wsgi:server`).
- **Reusa:** `app.create_app` (sin modificar `app.py`).
- **Hecho cuando:** `python -c "import wsgi"` expone `server`; `gunicorn wsgi:server` sirve localmente; alineado con bundle HF.
- **No rompe:** `wsgi.py` es aditivo; `app.py` intacto.
- **Commit:** `fix: serve dashboard via gunicorn wsgi:server`.

## T7 — Higiene (`.gitignore`, `.env.example`) 🟡
- **Objetivo:** repo limpio y configurable.
- **Archivos:** `.gitignore` (ignora `Executive-kpi-dashboard/`, `.claude/settings.local.json`, artefactos), `.env.example`.
- **Hecho cuando:** `git status` deja de listar el bundle; variables documentadas.
- **No rompe:** no afecta runtime.
- **Commit:** `chore: ignore HF bundle and add .env.example`.

## T8 — Documentación final (`README.md`, `CLAUDE.md`) 🟢
- **Objetivo:** onboarding y fuente de verdad al día.
- **Archivos:** `README.md` (nuevo), `CLAUDE.md` (actualizado).
- **Hecho cuando:** README explica instalar (con submódulos), ejecutar y testear; `CLAUDE.md` refleja Makefile/wsgi/CI.
- **No rompe:** solo documentación.
- **Commit:** `docs: add README and update CLAUDE.md to final state`.

---

### Verificación global
`pytest` verde · `ruff`/`black` limpios · `python app.py` arranca · `import wsgi` expone `server` · CI verde.
Reversión: `git reset --hard backup/pre-refactor-2026-06-03`.
