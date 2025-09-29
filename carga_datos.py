import os
import platform
from io import BytesIO
from pathlib import Path
from typing import Dict

import pandas as pd
import streamlit as st

from refactory import (
    format_numeric_columns, read_excel_safe, df_to_excel_bytes,
    build_items_from_df, recalc_item, apply_general_fields, merge_items_with_edit_df,
    validate_confirm_zerousd,
    etapa_i_streamlit, etapa_ii_streamlit, etapa_iii_streamlit, etapa_iv_streamlit
)

st.set_page_config(page_title="ACEVAL - Carga de Datos", layout="wide")


def env_or(default_key: str, fallback: str) -> str:
    v = os.getenv(default_key)
    return v if v else fallback


def get_default_base_dir() -> str:
    if platform.system() == "Windows":
        return env_or("ACEVAL_BASE_DIR", "C:/Users/arian/Desktop/IMP_ACEVAL")
    return env_or("ACEVAL_BASE_DIR", "./outputs")


def get_base_dirs(base_dir: str) -> Dict[str, Path]:
    env_i = os.getenv("ACEVAL_DIR_I")
    env_ii = os.getenv("ACEVAL_DIR_II")
    env_iii = os.getenv("ACEVAL_DIR_III")
    env_iv = os.getenv("ACEVAL_DIR_IV")
    base = Path(base_dir)
    rutas = {
        'I': Path(env_i) if env_i else base / "I_ETAPA",
        'II': Path(env_ii) if env_ii else base / "II_ETAPA",
        'III': Path(env_iii) if env_iii else base / "III_ETAPA",
        'IV': Path(env_iv) if env_iv else base / "IV_ETAPA",
    }
    return rutas


def to_download_bytes(df: pd.DataFrame, filename: str):
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    st.download_button(
        "Descargar " + filename,
        data=bio.getvalue(),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def safe_rerun():
    try:
        st.rerun()
    except AttributeError:
        try:
            st.experimental_rerun()
        except AttributeError:
            pass


def general_fields_ui(defaults: dict):
    col1, col2 = st.columns(2)
    with col1:
        proveedores_lista = ['FORTICA', 'ASG', 'COLMENA', 'BAOLAI']
        prov_def = defaults.get('Proveedor', 'FORTICA')
        idx_prov = proveedores_lista.index(
            prov_def) if prov_def in proveedores_lista else 0
        proveedor = st.selectbox(
            "Proveedor", proveedores_lista, index=idx_prov)

        empresa = st.text_input("Empresa", value=defaults.get('Empresa', ""))

        contrato = st.text_input(
            "Contrato (max 20 chars)", value=defaults.get('Contrato', ""))

        estatus_map = {'1': 0, '2': 1, '3': 2}
        estatus_def = str(defaults.get('Estatus', '1'))
        idx_estatus = estatus_map.get(estatus_def, 0)
        estatus_label = st.selectbox("Estatus", [
                                     '1: No ha llegado', '2: Está en transito', '3: Ya llego'], index=idx_estatus)
        estatus = estatus_label.split(':')[0]

        numero_pedido = st.text_input("Numero de Pedido Aceval (opcional)", value=defaults.get(
            'Numero de Pedido Aceval', "") or "")
    with col2:
        factura = st.text_input("Factura", value=defaults.get('Factura', ""))

        cant_def = defaults.get('Cantidad Productos')
        try:
            cant_def = int(cant_def) if cant_def is not None else 0
        except Exception:
            cant_def = 0
        cantidad_productos = st.number_input(
            "Cantidad de productos (opcional)", min_value=0, value=cant_def, step=1)

        compra_puntual_lista = ['', 'S', 'N']
        cp_def = defaults.get('Compra puntual') or ''
        idx_cp = compra_puntual_lista.index(
            cp_def) if cp_def in compra_puntual_lista else 0
        compra_puntual = st.selectbox(
            "Compra puntual (solo COLMENA)", compra_puntual_lista, index=idx_cp)

        vice = st.text_input("VICE (solo COLMENA)",
                             value=defaults.get('VICE', "") or "")

        origen_lista = ["", "PROVEEDOR", "FACTURA"]
        oi_def = defaults.get('Origen Info') or ""
        idx_oi = origen_lista.index(oi_def) if oi_def in origen_lista else 0
        origen_info = st.selectbox("Origen de la información (COLMENA)",
                                   origen_lista, index=idx_oi) if proveedor == "COLMENA" else ""

    return dict(proveedor=proveedor, empresa=empresa, contrato=contrato, estatus=estatus,
                numero_pedido=numero_pedido, factura=factura, cantidad_productos=cantidad_productos,
                compra_puntual=compra_puntual, vice=vice, origen_info=origen_info)


def rutas_config_ui():
    st.subheader("Configuración de rutas por etapa")
    st.caption("Puedes personalizar las rutas de guardado por etapa. Si usas Streamlit Cloud, usa rutas relativas como ./outputs/I_ETAPA.")
    ss = st.session_state
    base_dir_input = st.text_input(
        "Base de guardado (ACEVAL_BASE_DIR)", value=ss['base_dir'])
    rutas = get_base_dirs(base_dir_input)
    use_custom = st.checkbox(
        "Usar rutas personalizadas por etapa", value=ss.get('use_custom_routes', False))
    if use_custom:
        ruta_i = st.text_input("Ruta Etapa I", value=str(
            ss.get('rutas_salvado', rutas).get('I', rutas['I'])))
        ruta_ii = st.text_input("Ruta Etapa II", value=str(
            ss.get('rutas_salvado', rutas).get('II', rutas['II'])))
        ruta_iii = st.text_input("Ruta Etapa III", value=str(
            ss.get('rutas_salvado', rutas).get('III', rutas['III'])))
        ruta_iv = st.text_input("Ruta Etapa IV", value=str(
            ss.get('rutas_salvado', rutas).get('IV', rutas['IV'])))
        if st.button("Aplicar rutas"):
            ss['base_dir'] = base_dir_input
            ss['use_custom_routes'] = True
            ss['rutas_salvado'] = {
                'I': Path(ruta_i),
                'II': Path(ruta_ii),
                'III': Path(ruta_iii),
                'IV': Path(ruta_iv),
            }
            for p in ss['rutas_salvado'].values():
                Path(p).mkdir(parents=True, exist_ok=True)
            st.success("Rutas personalizadas aplicadas.")
    else:
        if st.button("Usar base y subcarpetas I_ETAPA, II_ETAPA, III_ETAPA, IV_ETAPA"):
            ss['base_dir'] = base_dir_input
            ss['use_custom_routes'] = False
            ss['rutas_salvado'] = get_base_dirs(ss['base_dir'])
            for p in ss['rutas_salvado'].values():
                Path(p).mkdir(parents=True, exist_ok=True)
            st.success("Rutas por defecto aplicadas.")
    st.info(f"Ruta Etapa I: {ss['rutas_salvado']['I']}\n\nRuta Etapa II: {ss['rutas_salvado']['II']}\n\nRuta Etapa III: {ss['rutas_salvado']['III']}\n\nRuta Etapa IV: {ss['rutas_salvado']['IV']}")


def main():
    st.title("ACEVAL - Carga y Procesamiento")

    ss = st.session_state
    ss.setdefault('etapa', 1)
    ss.setdefault('items', [])
    ss.setdefault('factura', "")
    ss.setdefault('proveedor', "FORTICA")
    ss.setdefault('empresa', "")
    ss.setdefault('origen_info', "")
    ss.setdefault('base_dir', get_default_base_dir())
    ss.setdefault('rutas_salvado', get_base_dirs(ss['base_dir']))
    ss.setdefault('use_custom_routes', False)

    with st.expander("Configuración de rutas por etapa", expanded=True):
        rutas_config_ui()

    st.markdown("¿Deseas continuar desde una etapa anterior?")
    cont_prev = st.checkbox("Sí, continuar desde una etapa anterior")
    if cont_prev and 'cont_prev_done' not in ss:
        st.subheader("Cargar archivo de una etapa anterior")
        etapa_prev = st.selectbox(
            "¿Desde qué etapa deseas continuar? (I, II o III)", ['I', 'II', 'III'])
        up_prev = st.file_uploader("Sube el archivo de la etapa seleccionada (.xlsx)", type=[
                                   "xlsx"], key="upload_prev")
        if up_prev is not None:
            try:
                df_loaded = pd.read_excel(up_prev)
                items = df_loaded.to_dict(orient='records')
                if not items:
                    st.error("El archivo cargado no contiene registros.")
                else:
                    first = items[0]
                    ss['items'] = items
                    ss['factura'] = first.get('Factura') or ""
                    ss['proveedor'] = first.get('Proveedor') or "FORTICA"
                    ss['empresa'] = first.get('Empresa') or ""
                    ss['origen_info'] = ""
                    next_stage = {'I': 2, 'II': 3, 'III': 4}[etapa_prev]
                    ss['etapa'] = next_stage
                    ss['from_stage'] = etapa_prev
                    ss['cont_prev_done'] = True
                    st.success(
                        f"Archivo cargado. Puedes editar y guardar en Etapa {etapa_prev} o avanzar a la siguiente.")
                    safe_rerun()
            except Exception as e:
                st.error(f"No se pudo leer el archivo: {e}")

    # ----------------- ETAPA I -----------------
    if ss['etapa'] == 1:
        st.header("Etapa I: Carga y validación")

        defaults = {
            'Proveedor': ss.get('proveedor', "FORTICA"),
            'Empresa': ss.get('empresa', ""),
            'Contrato': "",
            'Estatus': '1',
            'Numero de Pedido Aceval': "",
            'Factura': ss.get('factura', ""),
            'Cantidad Productos': 0,
            'Compra puntual': '',
            'VICE': '',
            'Origen Info': ""
        }
        gf = general_fields_ui(defaults)

        st.markdown(
            "Sube el Excel de productos con columnas: DESCRIPCION, CANTIDAD DE KILOS, CANTIDAD DE PIEZAS, CALIDAD DE METAL")
        uploaded = st.file_uploader("Excel de productos (.xlsx)", type=[
                                    "xlsx"], key="upload_i")

        if uploaded is not None:
            df = pd.read_excel(uploaded)
            for c in ['Costo por Pieza', 'Costo por Tonelada', 'Costo Ton Origen', 'Total Ton + Com', 'Confirmar USD 0']:
                if c not in df.columns:
                    df[c] = None if c != 'Confirmar USD 0' else False

            st.info(
                "Edita costos por fila. Si una fila tiene Piezas y Kilos y dejas ambos costos vacíos, marca 'Confirmar USD 0'.")
            edited_df = st.data_editor(
                df, num_rows="dynamic", use_container_width=True)

            colA, colB = st.columns(2)
            with colA:
                if st.button("Guardar en Etapa I"):
                    bad_rows = validate_confirm_zerousd(edited_df)
                    if bad_rows:
                        st.error(
                            f"Debes confirmar USD=0 en las filas: {', '.join(str(i+1) for i in bad_rows)}")
                    else:
                        try:
                            items, saved_path = etapa_i_streamlit(
                                df_excel=edited_df,
                                proveedor=gf['proveedor'],
                                empresa=gf['empresa'],
                                factura=gf['factura'],
                                contrato=gf['contrato'],
                                estatus=gf['estatus'],
                                numero_pedido=gf['numero_pedido'] or None,
                                compra_puntual=gf['compra_puntual'] or None,
                                vice=gf['vice'] or None,
                                cantidad_productos=int(
                                    gf['cantidad_productos']) if gf['cantidad_productos'] else None,
                                origen_info=gf['origen_info'] or None,
                                rutas_salvado=ss['rutas_salvado']
                            )
                            ss['items'] = items
                            ss['factura'] = gf['factura']
                            ss['proveedor'] = gf['proveedor']
                            ss['empresa'] = gf['empresa']
                            st.success(f"Guardado en Etapa I: {saved_path}")
                            to_download_bytes(
                                pd.DataFrame(items), saved_path.name)
                        except Exception as e:
                            st.error(f"Error al guardar Etapa I: {e}")
            with colB:
                if st.button("Avanzar a Etapa II"):
                    bad_rows = validate_confirm_zerousd(edited_df)
                    if bad_rows:
                        st.error(
                            f"Debes confirmar USD=0 en las filas: {', '.join(str(i+1) for i in bad_rows)}")
                    else:
                        try:
                            items, saved_path = etapa_i_streamlit(
                                df_excel=edited_df,
                                proveedor=gf['proveedor'],
                                empresa=gf['empresa'],
                                factura=gf['factura'],
                                contrato=gf['contrato'],
                                estatus=gf['estatus'],
                                numero_pedido=gf['numero_pedido'] or None,
                                compra_puntual=gf['compra_puntual'] or None,
                                vice=gf['vice'] or None,
                                cantidad_productos=int(
                                    gf['cantidad_productos']) if gf['cantidad_productos'] else None,
                                origen_info=gf['origen_info'] or None,
                                rutas_salvado=ss['rutas_salvado']
                            )
                            ss['items'] = items
                            ss['factura'] = gf['factura']
                            ss['proveedor'] = gf['proveedor']
                            ss['empresa'] = gf['empresa']
                            ss['etapa'] = 2
                            st.success(
                                f"Guardado en Etapa I: {saved_path}. Avanzando a Etapa II...")
                            safe_rerun()
                        except Exception as e:
                            st.error(f"Error al avanzar a Etapa II: {e}")

    # ----------------- ETAPA II -----------------
    if ss['etapa'] == 2:
        st.header("Etapa II: Bancarización y pagos")
        items = ss['items']
        if not items:
            st.warning("No hay items. Vuelve a la Etapa I.")
            return

        st.subheader("Editar items (si es necesario)")
        df_items = pd.DataFrame(items)
        editable_cols = ['Producto', 'Piezas', 'Kilos', 'Costo por Pieza',
                         'Costo por Tonelada', 'Costo Ton Origen', 'Total Ton + Com']
        for c in editable_cols:
            if c not in df_items.columns:
                df_items[c] = None
        edited_df = st.data_editor(
            df_items[editable_cols], num_rows="fixed", use_container_width=True)
        if st.button("Aplicar cambios a los items (recalcular)"):
            try:
                ss['items'] = merge_items_with_edit_df(
                    items, edited_df, ss['proveedor'], ss.get('origen_info') or None)
                st.success("Items actualizados y recalculados.")
            except Exception as e:
                st.error(f"Error al aplicar cambios: {e}")

        with st.expander("Editar campos generales del pedido"):
            gf2 = general_fields_ui({
                'Proveedor': ss.get('proveedor'),
                'Empresa': ss.get('empresa'),
                'Contrato': items[0].get('Contrato', ''),
                'Estatus': items[0].get('Estatus', '1'),
                'Numero de Pedido Aceval': items[0].get('Numero de Pedido Aceval', ''),
                'Factura': ss.get('factura'),
                'Cantidad Productos': items[0].get('Cantidad Productos', 0),
                'Compra puntual': items[0].get('Compra puntual', ''),
                'VICE': items[0].get('VICE', ''),
                'Origen Info': ss.get('origen_info', '')
            })
            if st.button("Aplicar a todos los registros"):
                ss['items'] = apply_general_fields(
                    ss['items'], gf2['empresa'], gf2['factura'], gf2['contrato'], gf2['numero_pedido'], gf2['estatus'])
                ss['proveedor'] = gf2['proveedor']
                ss['empresa'] = gf2['empresa']
                ss['factura'] = gf2['factura']
                st.success("Campos generales aplicados a todos.")

        st.subheader("Parámetros de pago")
        col1, col2 = st.columns(2)
        with col1:
            fecha_pago = st.text_input("Fecha de pago (dd/mm/yyyy)")
            tasa_bcv = st.number_input(
                "Tasa BCV", min_value=0.0, step=0.01, format="%.2f")
            monto_planilla_tn = st.number_input(
                "Monto de la planilla TN", min_value=0.0, step=0.01, format="%.2f")
        with col2:
            monto_planilla_seniat = st.number_input(
                "Monto de la planilla SENIAT", min_value=0.0, step=0.01, format="%.2f")
            monto_celsam = None
            if (ss['proveedor'] or "").upper() == "BAOLAI":
                monto_celsam = st.number_input(
                    "Monto CELSAM (solo BAOLAI)", min_value=0.0, step=0.01, format="%.2f")

        colA, colB = st.columns(2)
        with colA:
            if st.button("Guardar en Etapa II"):
                try:
                    items2, saved_path = etapa_ii_streamlit(
                        items=ss['items'],
                        proveedor=ss['proveedor'],
                        factura=ss['factura'],
                        rutas_salvado=ss['rutas_salvado'],
                        fecha_pago=fecha_pago,
                        tasa_bcv=tasa_bcv,
                        monto_planilla_tn=monto_planilla_tn,
                        monto_planilla_seniat=monto_planilla_seniat,
                        monto_celsam=monto_celsam
                    )
                    ss['items'] = items2
                    st.success(f"Guardado en Etapa II: {saved_path}")
                    to_download_bytes(pd.DataFrame(items2), saved_path.name)
                except Exception as e:
                    st.error(f"Error al guardar Etapa II: {e}")
        with colB:
            if st.button("Avanzar a Etapa III"):
                try:
                    items2, saved_path = etapa_ii_streamlit(
                        items=ss['items'],
                        proveedor=ss['proveedor'],
                        factura=ss['factura'],
                        rutas_salvado=ss['rutas_salvado'],
                        fecha_pago=fecha_pago,
                        tasa_bcv=tasa_bcv,
                        monto_planilla_tn=monto_planilla_tn,
                        monto_planilla_seniat=monto_planilla_seniat,
                        monto_celsam=monto_celsam
                    )
                    ss['items'] = items2
                    ss['etapa'] = 3
                    st.success(
                        f"Guardado en Etapa II: {saved_path}. Avanzando a Etapa III...")
                    safe_rerun()
                except Exception as e:
                    st.error(f"Error al avanzar a Etapa III: {e}")

    # ----------------- ETAPA III -----------------
    if ss['etapa'] == 3:
        st.header("Etapa III: Recepción y costos logísticos")
        items = ss['items']
        if not items:
            st.warning("No hay items. Vuelve a la Etapa I.")
            return

        df_items = pd.DataFrame(items)
        base_rec = df_items[['Producto']].copy()
        base_rec['Kilos Recibidos'] = None
        base_rec['Piezas Recibidas'] = None

        st.info("Ingresa Kilos Recibidos y Piezas Recibidas (opcional) por producto.")
        edited_rec = st.data_editor(
            base_rec, num_rows="fixed", use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            fecha_recepcion = st.text_input("Fecha de recepción (dd/mm/yyyy)")
        with col2:
            cantidad_gandolas = st.number_input(
                "Cantidad de gandolas", min_value=1, step=1)

        colA, colB = st.columns(2)
        with colA:
            if st.button("Guardar en Etapa III"):
                try:
                    items3, saved_path = etapa_iii_streamlit(
                        items=items,
                        factura=ss['factura'],
                        proveedor=ss['proveedor'],
                        rutas_salvado=ss['rutas_salvado'],
                        fecha_recepcion=fecha_recepcion,
                        df_recibidos=edited_rec,
                        cantidad_gandolas=int(cantidad_gandolas)
                    )
                    ss['items'] = items3
                    st.success(f"Guardado en Etapa III: {saved_path}")
                    to_download_bytes(pd.DataFrame(items3), saved_path.name)
                except Exception as e:
                    st.error(f"Error al guardar Etapa III: {e}")
        with colB:
            if st.button("Avanzar a Etapa IV"):
                try:
                    items3, saved_path = etapa_iii_streamlit(
                        items=items,
                        factura=ss['factura'],
                        proveedor=ss['proveedor'],
                        rutas_salvado=ss['rutas_salvado'],
                        fecha_recepcion=fecha_recepcion,
                        df_recibidos=edited_rec,
                        cantidad_gandolas=int(cantidad_gandolas)
                    )
                    ss['items'] = items3
                    ss['etapa'] = 4
                    st.success(
                        f"Guardado en Etapa III: {saved_path}. Avanzando a Etapa IV...")
                    safe_rerun()
                except Exception as e:
                    st.error(f"Error al avanzar a Etapa IV: {e}")

    # ----------------- ETAPA IV -----------------
    if ss['etapa'] == 4:
        st.header("Etapa IV: Costos reales y diferencias")
        items = ss['items']
        if not items:
            st.warning("No hay items. Vuelve a la Etapa I.")
            return

        st.subheader("Items actuales")
        st.dataframe(pd.DataFrame(items))

        colA, colB = st.columns(2)
        with colA:
            if st.button("Guardar en Etapa IV"):
                try:
                    items4, saved_path = etapa_iv_streamlit(
                        items=items,
                        factura=ss['factura'],
                        proveedor=ss['proveedor'],
                        rutas_salvado=ss['rutas_salvado']
                    )
                    ss['items'] = items4
                    st.success(f"Guardado en Etapa IV: {saved_path}")
                    df_final = pd.DataFrame(items4)
                    to_download_bytes(df_final, saved_path.name)
                except Exception as e:
                    st.error(f"Error al guardar Etapa IV: {e}")
        with colB:
            if st.button("Finalizar proceso (calcular y permitir descarga)"):
                try:
                    items4, saved_path = etapa_iv_streamlit(
                        items=items,
                        factura=ss['factura'],
                        proveedor=ss['proveedor'],
                        rutas_salvado=ss['rutas_salvado']
                    )
                    ss['items'] = items4
                    st.success(
                        f"Proceso completado. Archivo: {saved_path}. Descárgalo a continuación.")
                    df_final = pd.DataFrame(items4)
                    to_download_bytes(df_final, saved_path.name)
                except Exception as e:
                    st.error(f"Error al finalizar: {e}")

    st.markdown("---")
    if st.button("Reiniciar flujo"):
        for k in ['items', 'factura', 'proveedor', 'empresa', 'origen_info', 'cont_prev_done', 'from_stage']:
            if k in ss:
                del ss[k]
        ss['etapa'] = 1
        safe_rerun()


if __name__ == "__main__":
    main()
