"""Fixtures compartidas para la suite de tests del dashboard BI."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
# BD de ejemplo DENTRO del submódulo versionado. No se usa get_db_path() por defecto porque
# resuelve a una copia externa (un nivel por encima del repo) que no existe en un clon limpio/CI.
DB_FILE = REPO_ROOT / "SQL-Connection-Module" / "examples" / "toys_and_models.sqlite"


@pytest.fixture(scope="session")
def db_path():
    if not DB_FILE.exists():
        pytest.skip(f"BD de ejemplo no encontrada: {DB_FILE} (¿submódulos inicializados?)")
    return str(DB_FILE)


@pytest.fixture(scope="session")
def datasets(db_path):
    from utils.data import load_datasets

    return load_datasets(db_path=db_path)


@pytest.fixture(scope="session")
def thresholds():
    import yaml

    with open(REPO_ROOT / "configs" / "thresholds.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(autouse=True)
def _isolate_vizro_models():
    """Limpia el model_manager global de Vizro alrededor de cada test (evita IDs duplicados)."""
    try:
        from vizro.managers import model_manager

        model_manager._clear()
        yield
        model_manager._clear()
    except Exception:
        yield
