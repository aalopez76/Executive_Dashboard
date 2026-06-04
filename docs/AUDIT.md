# Auditoría técnica — Executive_KPI_Dashboard

> Fecha: 2026-06-03 · Rama de trabajo: `chore/reproducibility-and-tests` · Punto de retorno: `backup/pre-refactor-2026-06-03`
> Reemplaza al `AUDIT.md` de la raíz (consolidado aquí).

## 1. Resumen ejecutivo

Proyecto **BI** (no ML): dashboard ejecutivo de KPIs sobre la base SQLite *Classic Models*
(`toys_and_models.sqlite`), construido con **Vizro/Dash + pandas** y alimentado por dos submódulos
(`SQL-Connection-Module`, `SQL-Queries`). El código está **razonablemente modularizado** en `utils/`
(carga, motor de datos, lectura de SQL, páginas), con una *app factory* limpia (`app.create_app`).

El proyecto **funciona**, pero no es **reproducible ni verificable**: las dependencias transitivas
no están fijadas, **no hay tests** que protejan la carga de datos ni el build del dashboard, y el
**despliegue del repo raíz está roto** (arranca con `uvicorn` siendo una app WSGI). La intervención
se centra en cerrar estos cuatro frentes —reproducibilidad, testing, deploy y organización— **sin
tocar la lógica de negocio**.

## 2. Lo que está bien (rescatable)

- ✅ **App factory** (`app.create_app`) y separación de responsabilidades en `utils/`
  (`data.py`, `data_engine.py`, `query_reader.py`, `pages.py`, `_charts.py`).
- ✅ **Contrato de datos explícito**: `load_datasets()` documenta y devuelve un dict canónico de ~20 datasets.
- ✅ **SQL versionado** y desacoplado en un submódulo, cargado por ruta vía `query_reader`.
- ✅ **Dependencias directas fijadas** con `==` (`vizro`, `pandas`, `gunicorn`).
- ✅ **Resolución de BD configurable** por entorno (`DB_PATH`) con fallback razonable.
- ✅ Existe un **bundle de despliegue** funcional para Hugging Face Spaces (`Executive-kpi-dashboard/`)
  que ya expone `server` para gunicorn — referencia válida para arreglar el raíz.
- ✅ Configuración de Claude Code (skills, commands, hooks, `configs/thresholds.yaml`) ya sembrada.

## 3. Problemas detectados (por gravedad)

### 🔴 Críticos
| # | Problema | Evidencia | Impacto |
|---|----------|-----------|---------|
| C1 | **Sin lockfile / deps transitivas no fijadas** | `requirements.txt` fija solo directas; `vizro` arrastra `dash`/`plotly`/etc. sin pin | El entorno no es reproducible; un build futuro puede romper sin cambios en el código |
| C2 | **Sin tests en el repo raíz** | No existe `tests/`; solo el submódulo tiene tests | Cualquier cambio puede romper la carga de datos, las queries o el build sin que nadie lo note |

### 🟡 Mejorables
| # | Problema | Evidencia | Impacto |
|---|----------|-----------|---------|
| M1 | **Despliegue del raíz roto** | `Dockerfile`: `CMD uvicorn app:app`; Vizro/Dash es **WSGI** y `app.py` no expone `server` | El contenedor del repo raíz no arranca; diverge del bundle HF que sí funciona |
| M2 | **Sin README** | No hay `README.md` en la raíz | Onboarding y reproducción manual difíciles |
| M3 | **Sin config de estilo** | No hay `pyproject.toml`; `ruff`/`black` sin line-length/target | Diffs ruidosos; el hook de formateo no es determinista |
| M4 | **Trabajo/Config sin versionar** | `.claude/`, `configs/`, `docs/` estaban *untracked* | Riesgo de pérdida; ya respaldado en Fase 0 |
| M5 | **Bundle HF ensucia el repo** | `Executive-kpi-dashboard/` (repo git propio) aparece como *untracked* | Confunde `git status`; debe ignorarse |

### 🟢 Recomendaciones a futuro
| # | Recomendación |
|---|---------------|
| F1 | **CI/CD avanzado**: matriz de versiones, cache de pip, publicación automática a HF Spaces |
| F2 | **`pre-commit`** con ruff/black para mover el formateo al lado del desarrollador |
| F3 | **Healthcheck/observabilidad**: endpoint de salud, logging estructurado, métricas |
| F4 | **Caché de datos**: `load_datasets()` recarga todo en cada arranque; cachear si crece |
| F5 | **Tests de UI/humo** del dashboard servido (p. ej. Playwright contra el server WSGI) |

## 4. Recomendaciones concretas y ordenadas

1. **Fijar el entorno** (C1): introducir `pyproject.toml` (estilo + pytest) y generar un lockfile
   con `pip-tools` (`requirements.in` → `requirements.txt` pinneado).
2. **Red de tests** (C2): `tests/` con integridad de datos (`load_datasets`), resolución de queries
   y build del dashboard, usando la BD real como fixture y los umbrales de `configs/thresholds.yaml`.
3. **Automatizar** (C2/F1): `Makefile` (`run`/`lint`/`format`/`test`/`review`) y CI en GitHub Actions
   con submódulos, lint y tests.
4. **Arreglar el deploy** (M1): `wsgi.py` que exponga `server` (sin tocar `app.py`) y `Dockerfile`
   con `gunicorn wsgi:server`, alineado con el bundle HF.
5. **Higiene** (M2/M4/M5): `README.md`, `.env.example`, `.gitignore` (ignorar el bundle), y versionar
   la configuración. Mantener `CLAUDE.md` como fuente de verdad.

> Orden alineado con `docs/REFACTOR_PLAN.md`. Prioridad: 🔴 antes que 🟡; 🟢 queda para iteraciones futuras.
