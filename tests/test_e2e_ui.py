"""Tests end-to-end con navegador (Playwright).

Marcados con @pytest.mark.e2e y EXCLUIDOS del run normal (ver addopts en pyproject).
Ejecutar con:  pytest -m e2e   (requiere `playwright install chromium`).
"""

import os
import threading
import time

import pytest


@pytest.fixture(scope="module")
def live_server(db_path):
    """Levanta el dashboard en un servidor WSGI local en un hilo, para navegarlo."""
    os.environ["DB_PATH"] = db_path
    from werkzeug.serving import make_server

    import app as app_module

    server = make_server("127.0.0.1", 8051, app_module.app.dash.server, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(2)  # margen para el arranque
    try:
        yield "http://127.0.0.1:8051"
    finally:
        server.shutdown()


@pytest.mark.e2e
def test_home_renderiza_kpis(live_server, page):
    page.goto(live_server, wait_until="domcontentloaded")
    # Las KPI cards se renderizan en cliente; esperamos un título conocido.
    page.wait_for_selector("text=Total Revenue", timeout=20000)
    assert page.get_by_text("Total Revenue").count() >= 1


@pytest.mark.e2e
def test_health_endpoint(live_server, page):
    resp = page.request.get(f"{live_server}/health")
    assert resp.status == 200
    assert "ok" in resp.text()
