"""Entrypoint WSGI para servidores de producción.

Uso:
    gunicorn wsgi:server --bind 0.0.0.0:$PORT

No modifica app.py: construye la app Vizro y expone el servidor Flask subyacente
(`server`), que es el callable WSGI que gunicorn necesita. Requiere que DB_PATH esté
definido o que la BD sea resoluble por app.get_db_path().
"""

from app import create_app

application = create_app()
server = application.dash.server
