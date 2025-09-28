import streamlit as st
import pandas as pd
from pathlib import Path
import os

# Importa tu lógica desde refactory.py
from refactory import (
    format_numeric_columns, format_item_numbers, read_excel_safe,
    etapa_i_interactiva, etapa_ii, etapa_iii, etapa_iv, ViceChecker,
    handle_edit_loaded_items
)

st.set_page_config(page_title="ACEVAL Dashboard", layout="wide")


def get_base_dirs(base_dir):
    return {
        'I': Path(base_dir) / "I_ETAPA",
        'II': Path(base_dir) / "II_ETAPA",
        'III': Path(base_dir) / "III_ETAPA",
        'IV': Path(base_dir) / "IV_ETAPA",
    }


def main():
    st.title("ACEVAL Dashboard")
    st.write("Aplicación para carga y procesamiento de información ACEVAL")

    # Configuración de rutas
    default_base_dir = "C:/Users/arian/Desktop/IMP_ACEVAL"
    base_dir = st.text_input(
        "Directorio base para guardar salidas:", value=default_base_dir)
    rutas_salvado = get_base_dirs(base_dir)

    # Estado de la sesión
    if 'etapa' not in st.session_state:
        st.session_state['etapa'] = 1
    if 'items' not in st.session_state:
        st.session_state['items'] = []
    if 'factura' not in st.session_state:
        st.session_state['factura'] = None
    if 'proveedor' not in st.session_state:
        st.session_state['proveedor'] = None

    vchecker = ViceChecker()

    # ETAPA I
    if st.session_state['etapa'] == 1:
        st.header("Etapa I: Carga y validación")
        uploaded_file = st.file_uploader(
            "Carga tu Excel de productos", type=["xlsx"])
        proveedor = st.selectbox(
            "Proveedor", ['FORTICA', 'ASG', 'COLMENA', 'BAOLAI'])
        empresa = st.text_input("Empresa")
        factura = st.text_input("Factura")
        contrato = st.text_input("Contrato")
        estatus = st.selectbox(
            "Estatus", ['1: No ha llegado', '2: Está en tránsito', '3: Ya llegó'])
        numero_pedido = st.text_input("Numero de Pedido Aceval")
        compra_puntual = st.selectbox("Compra puntual", ['S', 'N'])
        vice = st.text_input("VICE")
        cantidad_productos = st.number_input(
            "Cantidad de productos", min_value=1, step=1)
        origen_info = None
        if proveedor == "COLMENA":
            origen_info = st.selectbox("Origen de la información", [
                                       "PROVEEDOR", "FACTURA"])
        if uploaded_file and st.button("Procesar Etapa I"):
            df_excel = pd.read_excel(uploaded_file)
            # Aquí deberías adaptar etapa_i_interactiva para tomar estos datos y el df_excel
            # Puedes hacerlo creando una función etapa_i_interactiva_streamlit
            items = []  # Llama a tu función adaptada aquí
            # Ejemplo de asignación (deberías adaptar la función):
            # items, factura, proveedor = etapa_i_interactiva_streamlit(...)
            st.session_state['items'] = items
            st.session_state['factura'] = factura
            st.session_state['proveedor'] = proveedor
            st.session_state['etapa'] = 2
            st.success("Etapa I procesada correctamente.")

    # ETAPA II
    if st.session_state['etapa'] == 2:
        st.header("Etapa II: Bancarización y pagos")
        items = st.session_state['items']
        proveedor = st.session_state['proveedor']
        factura = st.session_state['factura']
        # Aquí deberías mostrar los datos y permitir edición si deseas
        st.dataframe(pd.DataFrame(items))
        if st.button("Procesar Etapa II"):
            # items = etapa_ii_streamlit(items, proveedor, factura, rutas_salvado)
            st.session_state['items'] = items
            st.session_state['etapa'] = 3
            st.success("Etapa II procesada correctamente.")

    # ETAPA III
    if st.session_state['etapa'] == 3:
        st.header("Etapa III: Recepción y costos logísticos")
        items = st.session_state['items']
        factura = st.session_state['factura']
        proveedor = st.session_state['proveedor']
        st.dataframe(pd.DataFrame(items))
        if st.button("Procesar Etapa III"):
            # items = etapa_iii_streamlit(items, factura, proveedor, rutas_salvado)
            st.session_state['items'] = items
            st.session_state['etapa'] = 4
            st.success("Etapa III procesada correctamente.")

    # ETAPA IV
    if st.session_state['etapa'] == 4:
        st.header("Etapa IV: Costos reales y diferencias")
        items = st.session_state['items']
        factura = st.session_state['factura']
        proveedor = st.session_state['proveedor']
        st.dataframe(pd.DataFrame(items))
        if st.button("Procesar Etapa IV"):
            # items = etapa_iv_streamlit(items, factura, proveedor, rutas_salvado)
            st.session_state['items'] = items
            st.success("Etapa IV procesada correctamente.")
            # Permite descargar el resultado final
            df_final = pd.DataFrame(items)
            st.download_button("Descargar Excel final", df_final.to_excel(
                index=False), file_name=f"IV_ETAPA_{factura}_{proveedor}.xlsx")

    # Opciones para reiniciar flujo
    if st.button("Reiniciar flujo"):
        st.session_state['items'] = []
        st.session_state['factura'] = None
        st.session_state['proveedor'] = None
        st.session_state['etapa'] = 1
        st.experimental_rerun()


if __name__ == "__main__":
    main()
