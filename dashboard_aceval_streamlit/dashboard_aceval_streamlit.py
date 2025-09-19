import streamlit as st
import pandas as pd
from pathlib import Path
import io
import plotly.express as px
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard Aceval", layout="wide")
st.title("Dashboard Aceval - Importaciones")

base_dir = Path("C:/Users/arian/Desktop/IMP_ACEVAL")
etapas = {
    "I_ETAPA": base_dir / "I_ETAPA",
    "II_ETAPA": base_dir / "II_ETAPA",
    "III_ETAPA": base_dir / "III_ETAPA",
    "IV_ETAPA": base_dir / "IV_ETAPA"
}

# --- Actualización dinámica ---
if st.button("Actualizar archivos y datos"):
    st.rerun()

selected_etapa = st.selectbox("Selecciona etapa", list(etapas.keys()))
carpeta = etapas[selected_etapa]

archivos = sorted(list(carpeta.glob("*.xlsx")))
if not archivos:
    st.warning(f"No se encontraron archivos Excel en {carpeta}")

seleccionar_todos_archivos = st.checkbox("Seleccionar todos los archivos")
if seleccionar_todos_archivos:
    archivos_seleccionados = archivos
else:
    archivos_seleccionados = st.multiselect(
        "Selecciona uno o más archivos Excel",
        archivos,
        format_func=lambda x: x.name if x else ""
    )

st.markdown(
    f"**Archivos seleccionados ({selected_etapa}):** {len(archivos_seleccionados)}")

# --- Leer datos ---
dataframes = []
for archivo in archivos_seleccionados:
    try:
        df = pd.read_excel(archivo)
        df['__archivo__'] = archivo.name
        dataframes.append(df)
    except Exception as e:
        st.error(f"Error leyendo {archivo.name}: {e}")

if dataframes:
    df_todos = pd.concat(dataframes, ignore_index=True)
    st.subheader("Datos combinados")
    st.dataframe(df_todos, use_container_width=True)

    # --- Filtros avanzados ---
    # Proveedor
    if "Proveedor" in df_todos.columns:
        proveedores = sorted(df_todos["Proveedor"].dropna().unique())
        seleccionar_todos_proveedores = st.checkbox("Todos los proveedores")
        if seleccionar_todos_proveedores:
            proveedores_seleccionados = proveedores
        else:
            proveedores_seleccionados = st.multiselect(
                "Filtrar por proveedor",
                proveedores,
                default=proveedores
            )
        if proveedores_seleccionados:
            df_todos = df_todos[df_todos["Proveedor"].isin(
                proveedores_seleccionados)]

    # Producto
    if "Producto" in df_todos.columns:
        productos = sorted(df_todos["Producto"].dropna().unique())
        seleccionar_todos_productos = st.checkbox("Todos los productos")
        if seleccionar_todos_productos:
            productos_seleccionados = productos
        else:
            productos_seleccionados = st.multiselect(
                "Filtrar por producto",
                productos,
                default=productos
            )
        if productos_seleccionados:
            df_todos = df_todos[df_todos["Producto"].isin(
                productos_seleccionados)]

    # Categoría
    if "Categoria" in df_todos.columns or "Categoría" in df_todos.columns:
        col_categoria = "Categoria" if "Categoria" in df_todos.columns else "Categoría"
        categorias = sorted(df_todos[col_categoria].dropna().unique())
        seleccionar_todas_categorias = st.checkbox("Todas las categorías")
        if seleccionar_todas_categorias:
            categorias_seleccionadas = categorias
        else:
            categorias_seleccionadas = st.multiselect(
                "Filtrar por categoría",
                categorias,
                default=categorias
            )
        if categorias_seleccionadas:
            df_todos = df_todos[df_todos[col_categoria].isin(
                categorias_seleccionadas)]

    # Fecha (asume columna 'Fecha' en formato fecha o texto convertible)
    if "Fecha" in df_todos.columns:
        df_todos["Fecha"] = pd.to_datetime(df_todos["Fecha"], errors="coerce")
        min_fecha, max_fecha = df_todos["Fecha"].min(), df_todos["Fecha"].max()
        fecha_rango = st.date_input(
            "Filtrar por rango de fecha",
            value=(min_fecha.date() if pd.notnull(min_fecha) else datetime.today().date(),
                   max_fecha.date() if pd.notnull(max_fecha) else datetime.today().date())
        )
        if isinstance(fecha_rango, tuple) and len(fecha_rango) == 2:
            start, end = fecha_rango
            df_todos = df_todos[
                (df_todos["Fecha"].dt.date >= start) &
                (df_todos["Fecha"].dt.date <= end)
            ]

    st.subheader("Vista filtrada")
    st.dataframe(df_todos, use_container_width=True)

    # --- Métricas disponibles ---
    metricas_posibles = [
        "Kilos Recibidos",
        "Piezas Recibidas",
        "Total USD Proveedor",
        "Kilos Recibidos Producto",
        "Piezas Recibidas Producto",
        "Total USD Producto"
    ]
    metricas_disponibles = [
        col for col in metricas_posibles if col in df_todos.columns]
    if metricas_disponibles:
        metrica_grafico = st.selectbox(
            "Selecciona métrica para gráfico:",
            metricas_disponibles,
            index=0
        )
        # LIMPIEZA
        df_todos[metrica_grafico] = pd.to_numeric(
            df_todos[metrica_grafico], errors="coerce")
        num_nan = df_todos[metrica_grafico].isna().sum()
        st.write(
            f"Valores no numéricos ignorados en '{metrica_grafico}': {num_nan}")

        # --- Agrupamiento dinámico ---
        # Permite elegir agrupamiento por proveedor, producto, categoría, fecha
        opciones_agrupamiento = []
        if "Proveedor" in df_todos.columns:
            opciones_agrupamiento.append("Proveedor")
        if "Producto" in df_todos.columns:
            opciones_agrupamiento.append("Producto")
        if "Categoria" in df_todos.columns or "Categoría" in df_todos.columns:
            opciones_agrupamiento.append(col_categoria)
        if "Fecha" in df_todos.columns:
            opciones_agrupamiento.append("Fecha")
        grupo_por = st.multiselect(
            "Agrupar gráfico por:",
            opciones_agrupamiento,
            default=[opciones_agrupamiento[0]] if opciones_agrupamiento else []
        )

        if grupo_por:
            resumen = df_todos.groupby(
                grupo_por)[metrica_grafico].sum().reset_index()
            # Formatea columna numérica
            resumen[metrica_grafico] = resumen[metrica_grafico].apply(
                lambda x: f"{x:,.2f}")
            st.markdown(f"### {metrica_grafico} por {' y '.join(grupo_por)}")
            fig = px.bar(
                resumen,
                x=grupo_por[0],
                y=metrica_grafico,
                color=grupo_por[1] if len(grupo_por) > 1 else None,
                title=f"{metrica_grafico} por {' y '.join(grupo_por)}",
                text=metrica_grafico
            )
            fig.update_traces(texttemplate='%{text}', textposition='auto')
            fig.update_layout(yaxis_tickformat=',.2f')
            st.plotly_chart(fig, use_container_width=True)
            st.write("Tabla resumen", resumen)
        else:
            st.warning("Selecciona al menos una opción de agrupamiento.")
    else:
        st.warning("No hay métricas disponibles para graficar.")

    # --- Descargar Excel filtrado ---
    st.markdown("### Descargar datos filtrados")
    excel_buffer = io.BytesIO()
    df_todos.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    st.download_button(
        "Descargar datos filtrados en Excel",
        excel_buffer,
        file_name=f"datos_filtrados_{selected_etapa}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Selecciona uno o más archivos o marca 'Seleccionar todos los archivos' para ver datos.")

st.markdown("---")
st.caption(
    "Dashboard Aceval · Selecciona archivos y proveedores en el panel principal")
