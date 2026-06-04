---
description: Valida un dataset (esquema, nulos, outliers, cardinalidad) y genera docs/data_report.md
argument-hint: <ruta-a-archivo | archivo.sqlite::tabla | nombre-de-dataset-de-load_datasets>
---

Aplica el procedimiento de `.claude/skills/data_validation/SKILL.md` al siguiente dataset:

**$ARGUMENTS**

Si no se indicó ningún dataset, pregunta cuál validar o usa por defecto el dataset `base`
de `utils.data.load_datasets()`. Al terminar, confirma la ruta del informe generado
(`docs/data_report.md`) y resume los hallazgos clave.
