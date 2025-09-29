import logging
import re
from io import BytesIO
from pathlib import Path
from typing import Optional, List, Dict, Tuple

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# ---------- Helpers numéricos robustos ----------


def to_float(value, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        try:
            return float(value)
        except Exception:
            return default
    if isinstance(value, str):
        s = value.strip()
        if s == "":
            return default
        neg = False
        if s.startswith("(") and s.endswith(")"):
            neg = True
            s = s[1:-1].strip()
        s = re.sub(r"[^\d,.\-]", "", s)
        if "," in s and "." in s:
            s = s.replace(",", "")
        else:
            if "," in s and "." not in s:
                s = s.replace(",", ".")
        try:
            val = float(s)
            return -val if neg else val
        except Exception:
            return default
    try:
        return float(value)
    except Exception:
        return default


def to_int(value, default: Optional[int] = None) -> Optional[int]:
    f = to_float(value, default=None)
    if f is None:
        return default
    try:
        return int(f)
    except Exception:
        return default

# ---------- Formateo ----------


def format_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col], errors='coerce').round(2)
        except Exception:
            continue
    return df


def format_item_numbers(item: Dict) -> Dict:
    for k, v in item.items():
        if isinstance(v, (int, float)) or (isinstance(v, str) and re.match(r"^[\d.,\-()]+$", v)):
            item[k] = round(to_float(v), 2)
    return item

# ---------- IO ----------


def read_excel_safe(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No existe el archivo: {path}")
    try:
        df = pd.read_excel(p, engine='openpyxl')
        return df
    except Exception as e:
        raise IOError(f"No se pudo leer {path}: {e}")


def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()


def guardar_excel(df: pd.DataFrame, nombre_archivo: str, ruta_destino: str | Path) -> Path:
    """
    Guarda el DataFrame en la ruta de etapa indicada.
    Devuelve la ruta completa del archivo guardado.
    """
    df = format_numeric_columns(df.copy())
    ruta_destino = Path(ruta_destino)
    ruta_destino.mkdir(parents=True, exist_ok=True)
    ruta_completa = ruta_destino / nombre_archivo
    try:
        df.to_excel(ruta_completa, index=False)
        logger.info("Archivo guardado en: %s", ruta_completa)
        return ruta_completa
    except Exception as e:
        raise IOError(f"No se pudo guardar el archivo {ruta_completa}: {e}")

# ---------- ViceChecker ----------


class ViceChecker:
    def __init__(self):
        self._cache: Dict[Path, pd.DataFrame] = {}

    def load(self, path: str | Path):
        p = Path(path)
        if p in self._cache:
            return
        try:
            df = pd.read_excel(p, engine='openpyxl')
            self._cache[p] = df
        except Exception as e:
            raise IOError(f"Error al leer archivo VICE {path}: {e}")

    def verificar(self, vice: str, rutas: List[str | Path]) -> bool:
        for ruta in rutas:
            p = Path(ruta)
            if p not in self._cache:
                try:
                    self.load(p)
                except Exception:
                    continue
            df = self._cache.get(p)
            if df is None:
                continue
            if 'VICE' in df.columns:
                if str(vice) in df['VICE'].astype(str).values:
                    return True
        return False

# ---------- Re-cálculo de un item ----------


def recalc_item(item: Dict, proveedor: str, origen_info: Optional[str]):
    kilos = to_float(item.get('Kilos'), 0.0)
    toneladas = kilos / 1000.0 if kilos else 0.0
    item['Toneladas'] = toneladas

    costo_puerto = to_float(item.get('Costo Puerto'), 0.0)
    porcentaje_com = item.get('Porcentaje Com')
    total_kilo_proveedor = 0.0
    total_usd_proveedor = 0.0
    total_ton_com = to_float(item.get('Total Ton + Com'), 0.0)

    prov_upper = (proveedor or item.get('Proveedor') or "").upper()
    costo_por_pieza = item.get('Costo por Pieza')
    costo_por_ton = item.get('Costo por Tonelada')
    piezas = to_int(item.get('Piezas') or 0, default=0) or 0

    if prov_upper == "COLMENA":
        if origen_info == "PROVEEDOR":
            costo_ton_origen = to_float(item.get('Costo Ton Origen'), 0.0)
            porcentaje_com_val = to_float(porcentaje_com, 0.95) or 0.95
            total_ton_com = (costo_ton_origen + costo_puerto) / \
                porcentaje_com_val if porcentaje_com_val != 0 else 0.0
            total_kilo_proveedor = total_ton_com / 1000.0
            total_usd_proveedor = total_kilo_proveedor * kilos
            item['Costo Ton Origen'] = round(costo_ton_origen, 2)
            item['Porcentaje Com'] = round(porcentaje_com_val, 2)
            item['Total Ton + Com'] = round(total_ton_com, 2)
            item['Total Kilo Proveedor'] = round(total_kilo_proveedor, 2)
            item['Total USD Proveedor'] = round(total_usd_proveedor, 2)
        else:
            if piezas and costo_por_pieza not in (None, ""):
                item['Total USD Proveedor'] = round(
                    piezas * to_float(costo_por_pieza, 0.0), 2)
                item['Total Kilo Proveedor'] = None
            elif costo_por_ton not in (None, ""):
                item['Total USD Proveedor'] = round(
                    toneladas * to_float(costo_por_ton, 0.0), 2)
                item['Total Kilo Proveedor'] = None
            else:
                item['Total USD Proveedor'] = round(
                    to_float(item.get('Total USD Proveedor'), 0.0), 2)
    else:
        if piezas and costo_por_pieza not in (None, ""):
            item['Total USD Proveedor'] = round(
                piezas * to_float(costo_por_pieza, 0.0), 2)
            item['Total Kilo Proveedor'] = None
        elif costo_por_ton not in (None, ""):
            item['Total USD Proveedor'] = round(
                toneladas * to_float(costo_por_ton, 0.0), 2)
            item['Total Kilo Proveedor'] = None
        else:
            total_ton_com = to_float(item.get('Total Ton + Com'), 0.0)
            if total_ton_com:
                total_kilo_proveedor = total_ton_com / 1000.0
                total_usd_proveedor = total_kilo_proveedor * kilos
                item['Total Ton + Com'] = round(total_ton_com, 2)
                item['Total Kilo Proveedor'] = round(total_kilo_proveedor, 2)
                item['Total USD Proveedor'] = round(total_usd_proveedor, 2)
            else:
                item['Total USD Proveedor'] = round(
                    to_float(item.get('Total USD Proveedor'), 0.0), 2)

    item['Toneladas'] = round(to_float(item.get('Toneladas'), 0.0), 2)
    return item

# ---------- Construcción de items desde DF (Etapa I o edición) ----------


def build_items_from_df(
    df_excel: pd.DataFrame,
    proveedor: str,
    empresa: str,
    factura: str,
    contrato: str,
    estatus: str,
    numero_pedido: Optional[str],
    compra_puntual: Optional[str],
    vice: Optional[str],
    cantidad_productos: Optional[int],
    origen_info: Optional[str]
) -> List[Dict]:
    items: List[Dict] = []

    col_desc = 'DESCRIPCION'
    col_kilos = 'CANTIDAD DE KILOS'
    col_piezas = 'CANTIDAD DE PIEZAS'
    col_calidad = 'CALIDAD DE METAL'
    col_cost_pieza = 'Costo por Pieza'
    col_cost_ton = 'Costo por Tonelada'
    col_cost_ton_origen = 'Costo Ton Origen'
    col_total_ton_com = 'Total Ton + Com'

    for _, row in df_excel.iterrows():
        producto = str(row.get(col_desc, '')).strip()
        kilos = to_float(row.get(col_kilos), 0.0)
        piezas = to_int(row.get(col_piezas), 0) or 0
        calidad_metal = str(row.get(col_calidad, '')).strip()
        toneladas = kilos / 1000.0 if kilos else 0.0

        costo_por_pieza = row.get(col_cost_pieza)
        costo_por_tonelada = row.get(col_cost_ton)
        costo_ton_origen = to_float(row.get(col_cost_ton_origen), 0.0)
        total_ton_com = to_float(row.get(col_total_ton_com), 0.0)

        costo_puerto = 15.0 if (
            proveedor.upper() == "COLMENA" and origen_info == "PROVEEDOR") else 0.0
        porcentaje_com = 0.95 if (
            proveedor.upper() == "COLMENA" and origen_info == "PROVEEDOR") else None
        total_kilo_proveedor = 0.0
        total_usd_proveedor = 0.0

        if (piezas and kilos):
            if costo_por_pieza not in (None, ""):
                total_usd_proveedor = piezas * to_float(costo_por_pieza, 0.0)
            elif costo_por_tonelada not in (None, ""):
                total_usd_proveedor = toneladas * \
                    to_float(costo_por_tonelada, 0.0)
            else:
                total_usd_proveedor = 0.0
                costo_por_pieza = None
                costo_por_tonelada = None
        else:
            if proveedor.upper() == "COLMENA":
                if origen_info == "PROVEEDOR":
                    if costo_ton_origen:
                        total_ton_com = (costo_ton_origen +
                                         costo_puerto) / 0.95
                        total_kilo_proveedor = total_ton_com / 1000.0
                        total_usd_proveedor = total_kilo_proveedor * kilos
                    else:
                        total_usd_proveedor = 0.0
                elif origen_info == "FACTURA":
                    if piezas and costo_por_pieza not in (None, ""):
                        total_usd_proveedor = piezas * \
                            to_float(costo_por_pieza, 0.0)
                    elif costo_por_tonelada not in (None, ""):
                        total_usd_proveedor = toneladas * \
                            to_float(costo_por_tonelada, 0.0)
                    else:
                        total_usd_proveedor = 0.0
            else:
                if piezas and not kilos:
                    total_usd_proveedor = piezas * \
                        to_float(costo_por_pieza, 0.0) if costo_por_pieza not in (
                            None, "") else 0.0
                else:
                    if total_ton_com:
                        total_kilo_proveedor = total_ton_com / 1000.0
                        total_usd_proveedor = total_kilo_proveedor * kilos
                    else:
                        total_usd_proveedor = 0.0

        item = {
            'Empresa': empresa,
            'Proveedor': proveedor,
            'Numero de Pedido Aceval': numero_pedido,
            'Estatus': estatus,
            'VICE': vice if proveedor.upper() == "COLMENA" else None,
            'Factura': factura,
            'Contrato': contrato,
            'Compra puntual': compra_puntual if proveedor.upper() == "COLMENA" else None,
            'Cantidad Productos': int(cantidad_productos) if cantidad_productos else int(len(df_excel)),
            'Producto': producto,
            'Piezas': piezas,
            'Kilos': kilos,
            'Toneladas': toneladas,
            'Costo Ton Origen': costo_ton_origen if (proveedor.upper() == "COLMENA" and origen_info == "PROVEEDOR") else None,
            'Porcentaje Com': porcentaje_com if (proveedor.upper() == "COLMENA" and origen_info == "PROVEEDOR") else None,
            'Costo Puerto': costo_puerto,
            'Calidad de Metal': calidad_metal,
            'Total Ton + Com': total_ton_com if total_ton_com else None,
            'Total Kilo Proveedor': total_kilo_proveedor if total_kilo_proveedor else None,
            'Total USD Proveedor': total_usd_proveedor,
            'Costo por Tonelada': to_float(costo_por_tonelada, 0.0) if costo_por_tonelada not in (None, "") else None,
            'Costo por Pieza': to_float(costo_por_pieza, 0.0) if costo_por_pieza not in (None, "") else None
        }
        recalc_item(item, proveedor, origen_info)
        items.append(format_item_numbers(item))
    return items


def validate_confirm_zerousd(df: pd.DataFrame) -> List[int]:
    """
    Filas con Piezas>0 y Kilos>0 y ambos costos vacíos deben tener Confirmar USD 0 = True.
    Devuelve lista de índices (posición) que incumplen.
    """
    req_col = 'Confirmar USD 0'
    if req_col not in df.columns:
        return []
    bad: List[int] = []
    for idx, r in df.iterrows():
        piezas = to_int(r.get('CANTIDAD DE PIEZAS'), 0) or 0
        kilos = to_float(r.get('CANTIDAD DE KILOS'), 0.0)
        cp = r.get('Costo por Pieza')
        ct = r.get('Costo por Tonelada')
        if piezas and kilos and (cp in (None, "", 0, 0.0)) and (ct in (None, "", 0, 0.0)):
            if not bool(r.get(req_col, False)):
                bad.append(idx)
    return bad


def apply_general_fields(items: List[Dict], empresa: Optional[str], factura: Optional[str],
                         contrato: Optional[str], numero_pedido: Optional[str], estatus: Optional[str]) -> List[Dict]:
    if not items:
        return items
    for it in items:
        if empresa is not None:
            it['Empresa'] = empresa
        if factura is not None:
            it['Factura'] = factura
        if contrato is not None:
            it['Contrato'] = contrato
        if numero_pedido is not None:
            it['Numero de Pedido Aceval'] = numero_pedido
        if estatus is not None:
            it['Estatus'] = estatus
    return items


def merge_items_with_edit_df(items: List[Dict], df_edit: pd.DataFrame, proveedor: str, origen_info: Optional[str]) -> List[Dict]:
    """
    Actualiza items con valores editados del DataFrame y recalcula.
    Columnas usadas si existen: Producto, Piezas, Kilos, Costo por Pieza, Costo por Tonelada, Costo Ton Origen, Total Ton + Com
    """
    cols_map = {
        'Producto': 'Producto',
        'Piezas': 'Piezas',
        'Kilos': 'Kilos',
        'Costo por Pieza': 'Costo por Pieza',
        'Costo por Tonelada': 'Costo por Tonelada',
        'Costo Ton Origen': 'Costo Ton Origen',
        'Total Ton + Com': 'Total Ton + Com',
    }
    for i in range(min(len(items), len(df_edit))):
        row = df_edit.iloc[i]
        it = items[i]
        for cdf, citem in cols_map.items():
            if cdf in df_edit.columns:
                it[citem] = row.get(cdf, it.get(citem))
        it['Piezas'] = to_int(it.get('Piezas'), 0) or 0
        it['Kilos'] = to_float(it.get('Kilos'), 0.0)
        it['Costo por Pieza'] = None if row.get('Costo por Pieza') in (
            "", None) else to_float(row.get('Costo por Pieza'), 0.0)
        it['Costo por Tonelada'] = None if row.get('Costo por Tonelada') in (
            "", None) else to_float(row.get('Costo por Tonelada'), 0.0)
        it['Costo Ton Origen'] = to_float(it.get('Costo Ton Origen'), 0.0)
        it['Total Ton + Com'] = to_float(it.get('Total Ton + Com'), 0.0)
        recalc_item(it, proveedor, origen_info)
        format_item_numbers(it)
    return items

# ---------- Etapas Streamlit ----------


def etapa_i_streamlit(
    df_excel: pd.DataFrame,
    proveedor: str,
    empresa: str,
    factura: str,
    contrato: str,
    estatus: str,
    numero_pedido: Optional[str],
    compra_puntual: Optional[str],
    vice: Optional[str],
    cantidad_productos: Optional[int],
    origen_info: Optional[str],
    rutas_salvado: Dict[str, Path]
) -> Tuple[List[Dict], Path]:
    items = build_items_from_df(
        df_excel, proveedor, empresa, factura, contrato, estatus,
        numero_pedido, compra_puntual, vice, cantidad_productos, origen_info
    )
    df_out = pd.DataFrame(items)
    nombre_archivo = f"ETAPA_I_{factura}_{proveedor}.xlsx"
    saved_path = guardar_excel(df_out, nombre_archivo, rutas_salvado['I'])
    return items, saved_path


def etapa_ii_streamlit(items: List[Dict], proveedor: str, factura: str, rutas_salvado: Dict[str, Path],
                       fecha_pago: str, tasa_bcv: float, monto_planilla_tn: float, monto_planilla_seniat: float,
                       monto_celsam: Optional[float]) -> Tuple[List[Dict], Path]:
    for item in items:
        total_usd = to_float(item.get('Total USD Proveedor'), 0.0)
        item['Bancarizacion'] = round(total_usd * 0.03, 2)

    if (proveedor or "").upper() == "BAOLAI" and monto_celsam is not None:
        total_kilos = sum(to_float(it.get('Kilos'), 0.0) for it in items)
        if total_kilos > 0:
            for item in items:
                kilos = to_float(item.get('Kilos'), 0.0)
                item['CELSAM'] = round(
                    (to_float(monto_celsam, 0.0) / total_kilos) * kilos, 2)
        else:
            for item in items:
                item['CELSAM'] = 0.0
    else:
        for item in items:
            item['CELSAM'] = 0.0

    tasa_bcv = to_float(tasa_bcv, 0.0)
    if tasa_bcv == 0:
        raise ZeroDivisionError("La tasa BCV no puede ser 0.")
    monto_tn_por_item = (to_float(monto_planilla_tn, 0.0) /
                         tasa_bcv) / max(1, len(items))
    monto_seniat_por_item = (
        to_float(monto_planilla_seniat, 0.0) / tasa_bcv) / max(1, len(items))

    for item in items:
        item['Planilla TN'] = round(monto_tn_por_item, 2)
        item['Planilla SENIAT'] = round(monto_seniat_por_item, 2)
        item['Fecha de Pago'] = fecha_pago
        item['Tasa de Pago'] = round(tasa_bcv, 2)

    items = [format_item_numbers(it) for it in items]
    df = pd.DataFrame(items)
    nombre_archivo = f"ETAPA_II_{factura}_{proveedor}.xlsx"
    saved_path = guardar_excel(df, nombre_archivo, rutas_salvado['II'])
    return items, saved_path


def etapa_iii_streamlit(items: List[Dict], factura: str, proveedor: str, rutas_salvado: Dict[str, Path],
                        fecha_recepcion: str, df_recibidos: pd.DataFrame, cantidad_gandolas: int) -> Tuple[List[Dict], Path]:
    if not items:
        nombre_archivo = f"ETAPA_III_{factura}_{proveedor}.xlsx"
        empty_path = guardar_excel(pd.DataFrame(
            []), nombre_archivo, rutas_salvado['III'])
        return items, empty_path
    kilos_total = 0.0
    prod_to_row = {str(r['Producto']).strip(): r for _,
                   r in df_recibidos.iterrows()}

    for item in items:
        prod = str(item.get('Producto', '')).strip()
        rec = prod_to_row.get(prod, {})
        kilos_rec = to_float(rec.get('Kilos Recibidos'), 0.0)
        piezas_rec = to_int(rec.get('Piezas Recibidas'), default=None) if rec.get(
            'Piezas Recibidas') not in (None, "") else None

        item['Fecha de Recepción'] = fecha_recepcion
        item['Kilos Recibidos'] = round(kilos_rec, 2)
        item['Piezas Recibidas'] = piezas_rec
        item['Toneladas Recibidas'] = round(kilos_rec / 1000.0, 2)
        kilos_total += kilos_rec

    if cantidad_gandolas <= 0:
        raise ValueError("La cantidad de gandolas debe ser mayor que 0.")
    toneladas_por_gandola = (kilos_total / 1000.0) / \
        cantidad_gandolas if cantidad_gandolas else 0.0

    for item in items:
        ton_item = to_float(item.get('Toneladas Recibidas'), 0.0)
        factor_gand = (
            ton_item / toneladas_por_gandola) if toneladas_por_gandola != 0 else 0.0
        item['FACTOR GAND'] = round(factor_gand, 6)
        if (proveedor or "").upper() == "ASG":
            item['ADUANA'] = 0.0
            item['FLETE'] = 0.0
            item['NACIONALIZACION'] = 0.0
            item['MUELA'] = 0.0
        else:
            item['ADUANA'] = round(750.0 * factor_gand, 2)
            item['FLETE'] = round(3650.0 * factor_gand, 2)
            item['NACIONALIZACION'] = round(1000.0 * factor_gand, 2)
            item['MUELA'] = round(600.0 * factor_gand, 2)

    items = [format_item_numbers(it) for it in items]
    df = pd.DataFrame(items)
    nombre_archivo = f"ETAPA_III_{factura}_{proveedor}.xlsx"
    saved_path = guardar_excel(df, nombre_archivo, rutas_salvado['III'])
    return items, saved_path


def etapa_iv_streamlit(items: List[Dict], factura: str, proveedor: str, rutas_salvado: Dict[str, Path]) -> Tuple[List[Dict], Path]:
    if not items:
        nombre_archivo = f"IV_ETAPA_{factura}_{proveedor}.xlsx"
        empty_path = guardar_excel(pd.DataFrame(
            []), nombre_archivo, rutas_salvado['IV'])
        return items, empty_path
    for item in items:
        suma_costos = 0.0
        campos = ['Total USD Proveedor', 'Bancarizacion', 'CELSAM', 'Planilla TN', 'Planilla SENIAT',
                  'ADUANA', 'FLETE', 'NACIONALIZACION', 'MUELA']
        for c in campos:
            suma_costos += to_float(item.get(c), 0.0)

        if (item.get('Proveedor') or "").upper() == "FORTICA":
            trader = suma_costos * 0.01
            item['Trader'] = round(trader, 2)
        else:
            item['Trader'] = 0.0

        suma_costos_total = suma_costos + to_float(item.get('Trader'), 0.0)
        toneladas_recibidas = to_float(item.get('Toneladas Recibidas'), 0.0)

        if toneladas_recibidas == 0:
            item['Costo Real por Tonelada'] = None
            item['Costo Real con Gastos'] = None
            item['Costo Real por Kilo'] = None
        else:
            item['Costo Real por Tonelada'] = round(
                suma_costos_total / toneladas_recibidas, 2)
            item['Costo Real con Gastos'] = round(
                item['Costo Real por Tonelada'] * toneladas_recibidas, 2)
            item['Costo Real por Kilo'] = round(
                item['Costo Real por Tonelada'] / 1000.0, 6)

        piezas_rec_raw = item.get('Piezas Recibidas')
        piezas_rec = to_int(
            piezas_rec_raw, default=None) if piezas_rec_raw is not None else None
        kilos_rec = to_float(item.get('Kilos Recibidos'), 0.0)
        item['Peso de Pieza'] = round(
            (kilos_rec / piezas_rec), 6) if (piezas_rec and piezas_rec != 0) else None

        peso_pieza_val = item.get('Peso de Pieza')
        costo_real_kilo_val = item.get('Costo Real por Kilo')
        item['Costo Real de Pieza'] = round(float(peso_pieza_val) * float(costo_real_kilo_val), 6) if (
            peso_pieza_val is not None and costo_real_kilo_val is not None) else None

        kilos_original = to_float(item.get('Kilos'), 0.0)
        item['Diferencias de Kilos'] = round(kilos_rec - kilos_original, 2)
        piezas_original = to_int(item.get('Piezas'), 0) or 0
        item['Diferencia de Piezas'] = (
            piezas_rec - piezas_original) if (piezas_rec is not None) else None

    items = [format_item_numbers(it) for it in items]
    df = pd.DataFrame(items)
    nombre_archivo = f"IV_ETAPA_{factura}_{proveedor}.xlsx"
    saved_path = guardar_excel(df, nombre_archivo, rutas_salvado['IV'])
    return items, saved_path
