# Despliegue a Hugging Face Spaces

El Space `aalpzp/Executive_KPI_Dashboard` (`sdk: docker`) se despliega desde un **bundle
self-contained generado desde este repo** (fuente única de verdad). **No edites el bundle a mano**:
regénéralo con el script.

El código (`app.py`, `utils/`) del bundle es **idéntico** al del repo; funciona allí gracias a las
variables de entorno que fija el `Dockerfile` generado (`QUERIES_DIR=/app/queries`,
`DB_PATH=/app/data/toys_and_models.sqlite`).

## 1. Generar el bundle

```bash
python scripts/build_hf_bundle.py        # -> build/hf_bundle/
```

Incluye: `app.py` + `utils/` (del repo), `queries/` (de `SQL-Queries`),
`data/toys_and_models.sqlite` (de `SQL-Connection-Module`), `requirements.txt` (sin el editable),
`Dockerfile` y `README.md` (metadata HF). Requiere los submódulos inicializados.

## 2. Revisar

```bash
# Si tienes clonado el repo del Space, compara:
diff -r build/hf_bundle <ruta-al-clon-del-Space>
```

## 3. Publicar (git push a HF) — manual

El Space es un repo git propio. Con **git-lfs** instalado (para la BD):

```bash
git lfs install
git clone https://huggingface.co/spaces/aalpzp/Executive_KPI_Dashboard hf-space
cp -r build/hf_bundle/. hf-space/
cd hf-space
git lfs track "*.sqlite"          # si no estaba ya
git add -A
git commit -m "Deploy: regenerar bundle desde el repo"
git push                          # pide usuario/token de Hugging Face
```

## 4. Verificar post-deploy

El Space reconstruye solo (`sdk: docker`). Comprueba:

```bash
curl -s https://aalpzp-executive-kpi-dashboard.hf.space/health   # -> ok
```

y la home del Space en el navegador.

## Notas

- **Nunca** edites `Executive-kpi-dashboard/` a mano; es un artefacto generado.
- El servidor arranca con `gunicorn app:server` (Vizro/Dash es WSGI), puerto `7860`.
- Si cambian dependencias, regenera el bundle (toma `requirements.txt` del lock del repo sin el editable).
