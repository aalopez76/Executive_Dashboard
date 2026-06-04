# utils/query_reader.py
import logging
import os

logger = logging.getLogger(__name__)

# .../Executive_Dashboard/utils/query_reader.py -> .../Executive_Dashboard
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# QUERIES_DIR configurable por env var (p.ej. /app/queries en HF Spaces);
# por defecto, las queries versionadas del submódulo SQL-Queries.
QUERIES_DIR = os.getenv("QUERIES_DIR") or os.path.join(BASE_DIR, "SQL-Queries", "queries")


def load_sql_query(relative_path: str) -> str:
    """
    Busca SQL en:
      1) <QUERIES_DIR>/<folder>/.sql/<name>
      2) <QUERIES_DIR>/<folder>/.sql/<name>.sql
      3) <QUERIES_DIR>/<folder>/<name>
      4) <QUERIES_DIR>/<folder>/<name>.sql
    """
    rel = relative_path.replace("\\", "/").strip("/")
    parts = rel.split("/")
    folder_path = os.path.join(QUERIES_DIR, *parts[:-1])
    filename = parts[-1]

    fname_no_ext, _ = os.path.splitext(filename)

    candidates = [
        # estructura nueva (SQL-Queries estandarizado): <folder>/sql/<file>
        os.path.normpath(os.path.join(folder_path, "sql", filename)),
        os.path.normpath(os.path.join(folder_path, "sql", fname_no_ext)),
        # estructura antigua (compatibilidad): <folder>/.sql/<file>
        os.path.normpath(os.path.join(folder_path, ".sql", filename)),
        os.path.normpath(os.path.join(folder_path, ".sql", fname_no_ext)),
        os.path.normpath(os.path.join(folder_path, filename)),
        os.path.normpath(os.path.join(folder_path, fname_no_ext)),
    ]

    final_path = next((p for p in candidates if os.path.exists(p)), None)
    if final_path is None:
        error_msg = (
            "No se encontró el SQL. Intentado en:\n"
            + "\n".join([f"{i+1}. {p}" for i, p in enumerate(candidates)])
            + f"\nQUERIES_DIR activo: {QUERIES_DIR}"
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    with open(final_path, "r", encoding="utf-8") as f:
        return f.read()
