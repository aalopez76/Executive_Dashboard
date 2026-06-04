---
description: Revisa la salud del dashboard (datos, queries, build, deploy) y emite un dictamen
argument-hint: (sin argumentos)
---

Ejecuta la revisión completa del dashboard siguiendo `.claude/skills/dashboard_review/SKILL.md`.

Usa los umbrales definidos en `configs/thresholds.yaml`. Termina con un dictamen inequívoco:
**APROBADO** o **NECESITA REVISIÓN** (con el detalle de cada check fallido: valor vs. umbral).
