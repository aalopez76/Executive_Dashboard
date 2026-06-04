"""Smoke del servidor servido: el dashboard responde y el healthcheck está activo."""


def test_server_sirve_index(db_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", db_path)
    import app as app_module

    client = app_module.app.dash.server.test_client()
    resp = client.get("/")
    assert resp.status_code == 200


def test_healthcheck(db_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", db_path)
    import app as app_module

    client = app_module.app.dash.server.test_client()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert b"ok" in resp.data
