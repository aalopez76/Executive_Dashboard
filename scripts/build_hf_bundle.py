#!/usr/bin/env python
"""Genera el bundle self-contained para Hugging Face Spaces DESDE el repo principal.

Fuente única de verdad = este repo. El bundle (código + queries + BD + deploy) se ensambla
de forma reproducible y deja de mantenerse a mano. El push a HF es manual (ver docs/DEPLOY_HF.md).

El código (`app.py`, `utils/`) se copia SIN cambios: funciona en el bundle gracias a las env vars
del Dockerfile generado (`QUERIES_DIR=/app/queries`, `DB_PATH=/app/data/...`).

Uso:
    python scripts/build_hf_bundle.py [--output build/hf_bundle]
"""

import argparse
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEMPLATES = Path(__file__).resolve().parent / "hf_templates"

DB_SRC = REPO / "SQL-Connection-Module" / "examples" / "toys_and_models.sqlite"
QUERIES_SRC = REPO / "SQL-Queries" / "queries"
CONNECTOR_SRC = REPO / "SQL-Connection-Module" / "src" / "sql_connection"
_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".ipynb_checkpoints")


def _copytree(src: Path, dst: Path, ignore=_IGNORE) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=ignore)


# Para queries: solo SQL, sin documentación/imágenes.
_IGNORE_QUERIES = shutil.ignore_patterns("__pycache__", "*.pyc", "img", "*.png", "*.jpg", "*.md")


def _bundle_requirements(repo_req: Path) -> str:
    """requirements del repo SIN el editable -e (el conector se vendoriza como sql_connection/)."""
    keep = [
        line
        for line in repo_req.read_text(encoding="utf-8").splitlines()
        if not line.strip().startswith("-e") and "SQL-Connection-Module" not in line
    ]
    return "\n".join(keep).strip() + "\n"


def build(output: Path) -> None:
    for src, what in [(DB_SRC, "BD"), (QUERIES_SRC, "queries"), (CONNECTOR_SRC, "conector")]:
        if not src.exists():
            raise SystemExit(f"No se encontró {what} en {src} (¿submódulos inicializados?)")

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    # 1) Código del repo (idéntico; parametrizado por env QUERIES_DIR/DB_PATH).
    shutil.copy2(REPO / "app.py", output / "app.py")
    _copytree(REPO / "utils", output / "utils")
    _copytree(REPO / "assets", output / "assets")
    # Conector vendorizado: el dashboard lo importa en runtime; el bundle no instala el editable.
    _copytree(CONNECTOR_SRC, output / "sql_connection")

    # 2) Queries materializadas desde el submódulo SQL-Queries (solo .sql).
    _copytree(QUERIES_SRC, output / "queries", ignore=_IGNORE_QUERIES)

    # 3) BD de ejemplo desde el submódulo SQL-Connection-Module.
    (output / "data").mkdir()
    shutil.copy2(DB_SRC, output / "data" / "toys_and_models.sqlite")

    # 4) requirements sin el editable.
    (output / "requirements.txt").write_text(
        _bundle_requirements(REPO / "requirements.txt"), encoding="utf-8"
    )

    # 5) Plantillas de deploy (Dockerfile con env vars + README con metadata HF).
    shutil.copy2(TEMPLATES / "Dockerfile", output / "Dockerfile")
    shutil.copy2(TEMPLATES / "README.md", output / "README.md")

    files = sorted(p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file())
    print(f"Bundle generado en: {output}  ({len(files)} archivos)")
    for f in files:
        print(f"  {f}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Genera el bundle de HF Spaces desde el repo.")
    ap.add_argument("--output", default=str(REPO / "build" / "hf_bundle"), help="directorio de salida")
    build(Path(ap.parse_args().output))


if __name__ == "__main__":
    main()
