[README.md](https://github.com/user-attachments/files/22990850/README.md)
# Dashboard Financiero (Streamlit + Polars)

App de Streamlit que replica la lógica de tus scripts y agrega UI para:
- Limpieza:
  - Eliminar clientes cuyo `NOMCLIE` empieza por un prefijo (por defecto `.AIC-`).
  - Eliminar filas con `NOMVEND` en una lista configurable (prellenada con tus valores).
- Filtros dependientes (Mes y Empresa multiselección; el resto con “Todos”).
- Análisis:
  1. Clientes únicos.
  2. Ventas por mes (cuenta de `CLAVE UNICA` que termina en “-A”).
  3. Monto por cliente y mes.
  4. Detalle por cliente: productos únicos + monto total.
  5. Total de venta por EMP y Mes (pivot).
  6. Total de venta por Vendedor y Mes (pivot) + ranking general.

Estilo: fuente Century Gothic y márgenes laterales de 4 cm.

## Ejecutar localmente

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Luego abre el enlace que te indica Streamlit, sube tu archivo CSV/Excel y usa los controles de la barra lateral.

## Notas de rendimiento

- Polars procesa filtros y agrupaciones muy rápido en ~300k filas.
- Convertimos a pandas únicamente para visualización/descarga de tablas.
- Si el archivo es fijo, conviene convertirlo a Parquet para cargas futuras más rápidas.
