# IMP_ACEVAL Streamlit Dashboard

Aplicación Streamlit para cargar y procesar información ACEVAL en varias etapas, respetando todas las reglas y validaciones del flujo original.

## Estructura

- `dashboard_aceval_streamlit.py`: Aplicación principal Streamlit. Interfaz por etapas.
- `aceval_refactor.py`: Lógica de negocio y helpers. Adaptado para interacción con Streamlit.
- `requirements.txt`: Dependencias para instalar.
- `README.md`: Documentación y guía de uso.

## Uso rápido

1. Instala dependencias:
   ```
   pip install -r requirements.txt
   ```
2. Ejecuta la app:
   ```
   streamlit run dashboard_aceval_streamlit.py
   ```
3. Ve completando cada etapa en la interfaz web.

## Notas

- La lógica de cada etapa está separada y puede adaptarse para mayor interacción.
- El sistema respeta todas las validaciones de tu flujo original.
- Puedes editar y mejorar los formularios de cada etapa para mayor comodidad.
