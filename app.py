# app.py
import logging
import os

import dash_bootstrap_components as dbc
import vizro.models as vm
from dash import get_asset_url, html
from vizro import Vizro

from utils.data import load_datasets  # espera db_path
from utils.pages import (
    build_page_deep_dive,
    build_page_exec,
    build_page_opportunities,
    build_page_regional,
    build_page_risks,
)


# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
def setup_logging():
    level = os.getenv("LOG_LEVEL", "WARNING").upper()
    logging.basicConfig(level=level, format="%(levelname)s:%(name)s:%(message)s")
    logging.getLogger("dash").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)


def is_reloader_process() -> bool:
    return os.environ.get("WERKZEUG_RUN_MAIN") == "true"


def get_db_path() -> str:
    """
    Resuelve el path de la DB.
    Prioridad:
      1) env var DB_PATH
      2) copia interna del submódulo (SQL-Connection-Module/examples/, versionada en el repo)
      3) copia externa (un nivel por encima del repo) — legado, por compatibilidad
    """
    env_path = os.getenv("DB_PATH")
    if env_path:
        return env_path

    here = os.path.dirname(__file__)
    rel = ("SQL-Connection-Module", "examples", "toys_and_models.sqlite")
    candidates = [
        os.path.abspath(os.path.join(here, *rel)),        # interna (preferida)
        os.path.abspath(os.path.join(here, "..", *rel)),  # externa (legado)
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    # Ninguna existe: devuelve la interna para que el error apunte a la ruta esperada.
    return candidates[0]


# -----------------------------------------------------------------------------
# App factory
# -----------------------------------------------------------------------------
def create_app():
    setup_logging()
    log = logging.getLogger("app")

    db_path = get_db_path()
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at: {db_path}")

    datasets = load_datasets(db_path=db_path)


    pages = [
        build_page_exec(datasets),
        build_page_regional(datasets),
        build_page_risks(datasets),
        build_page_opportunities(datasets),
        build_page_deep_dive(datasets),
    ]

    dashboard = vm.Dashboard(
        pages=pages,
        title="Classic Models Sales - KPI Report",
        navigation=vm.Navigation(
            nav_selector=vm.NavBar(
                items=[
                    vm.NavLink(label="Executive View", icon="leaderboard", pages=["Executive View"]),
                    vm.NavLink(label="Risks", icon="warning", pages=["Risks & Diagnostics"]),
                    vm.NavLink(label="Opportunities", icon="trending_up", pages=["Opportunities"]),
                    vm.NavLink(label="Deep Dive", icon="table_view", pages=["Deep Dive"]),
                ]
            )
        ),
    )

    vizro_app = Vizro().build(dashboard)

    vizro_app.dash.layout.children.append(
        dbc.NavLink(
            ["Powered by ", html.Img(src=get_asset_url("images/logo.svg"), id="banner", alt="Vizro logo"), "Vizro"],
            href="https://github.com/mckinsey/vizro",
            target="_blank",
            external_link=True,
            className="anchor-container",
        )
    )

    if not is_reloader_process():
        log.info("Dashboard built successfully")

    return vizro_app


# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    debug = True
    use_reloader = False
    app.run(debug=debug, use_reloader=use_reloader)

