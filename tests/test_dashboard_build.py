"""El dashboard debe construirse sin error y exponer las páginas requeridas."""

import vizro.models as vm
from vizro.managers import model_manager


def test_create_app_builds_required_pages(db_path, thresholds, monkeypatch):
    # Fuerza la BD interna: get_db_path() por defecto apunta a una copia externa del submódulo.
    monkeypatch.setenv("DB_PATH", db_path)
    import app as app_module

    # app.py expone `app` a nivel de módulo (gunicorn app:app); se construye al importar.
    vizro_app = app_module.app
    assert hasattr(vizro_app, "dash"), "app.py no expuso una app Vizro válida"

    titles = {page.title for page in model_manager._get_models(vm.Page)}
    required = set(thresholds["dashboard"]["required_pages"])
    missing = required - titles
    assert not missing, f"Faltan páginas requeridas: {sorted(missing)}"
