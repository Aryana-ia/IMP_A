# IMP_ACEVAL - Streamlit App

Aplicación Streamlit para gestionar el flujo ACEVAL por etapas (I–IV), con:
- Guardar en etapa actual o avanzar a la siguiente.
- Continuar desde una etapa anterior cargando el Excel generado.
- Edición de campos generales y por fila.
- Validadores y recálculos fieles al script original.

## Estructura recomendada

- `carga_datos.py` (archivo principal de la app)
- `refactory.py` (lógica y helpers)
- `requirements.txt` (dependencias)

## Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run carga_datos.py
```

Por defecto, guarda archivos bajo `./outputs`. Puedes cambiarlo vía variable de entorno `ACEVAL_OUTPUT_DIR`.

## Despliegue en Streamlit Community Cloud

1. Sube estos archivos a tu repo (ej. `Aryana-ia/IMP_ACEVAL`) en la **raíz** del repositorio.
2. En Streamlit Cloud:
   - New app
   - Repository: `Aryana-ia/IMP_ACEVAL`
   - Branch: `main`
   - Main file path: `carga_datos.py`
3. Deploy.

Notas:
- El sistema de archivos del contenedor es efímero; también se ofrece descarga del Excel luego de guardar.
- Si usabas una subcarpeta con espacios, evita usarla y coloca `carga_datos.py` y `refactory.py` en la raíz.
