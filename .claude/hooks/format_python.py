#!/usr/bin/env python
"""PostToolUse hook (Claude Code): formatea archivos .py tras Write/Edit con ruff + black.

Lee el evento JSON del harness por stdin, extrae tool_input.file_path y, si es un .py,
aplica `ruff check --fix` y `black`. Multiplataforma (Windows/macOS/Linux).
Falla en silencio si las herramientas no están instaladas: nunca bloquea la edición.
"""
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0

    file_path = (event.get("tool_input") or {}).get("file_path", "")
    if not file_path or not file_path.endswith(".py"):
        return 0

    target = Path(file_path)
    if not target.is_file():
        return 0

    for cmd in (["ruff", "check", "--fix", str(target)], ["black", str(target)]):
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        except (FileNotFoundError, subprocess.SubprocessError):
            pass  # herramienta ausente o error: no interrumpir el flujo de edición

    return 0


if __name__ == "__main__":
    sys.exit(main())
