import streamlit as st
import pandas as pd

st.set_page_config(page_title="HVM", page_icon="📦", layout="wide")

from utils.style import inject_css, page_header, sidebar_brand
from utils.auth import require_login, logout, current_negocio_nombre
from utils.db import get_supabase_client
from utils.queries import (
    list_productos, list_entradas, list_salidas, total_por_cobrar,
    productos_bajo_stock,
)
from utils.format import formatear_fecha_hora

inject_css()
require_login()  # detiene la app aquí si no hay sesión

supabase = get_supabase_client()

with st.sidebar:
    sidebar_brand(current_negocio_nombre())
    st.caption(st.session_state["sb_user"].email)
    if st.button("Cerrar sesión", use_container_width=True):
        logout()

page_header("Panel", "Resumen general de tu negocio.")

productos = list_productos(supabase)
entradas = list_entradas(supabase)
salidas = list_salidas(supabase)
por_cobrar = total_por_cobrar(supabase)
bajo_stock = productos_bajo_stock(supabase)

valor_inventario = sum(
    float(p["stock"]) * float(p["precio_venta"] or 0) for p in productos
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Productos", len(productos))
col2.metric("Valor inventario (venta)", f"${valor_inventario:,.0f}")
col3.metric("Entradas registradas", len(entradas))
col4.metric("Por cobrar (deudores)", f"${por_cobrar:,.0f}")

if bajo_stock:
    with st.container(border=True):
        st.markdown("**⚠️ Productos con poco stock**")
        for p in bajo_stock:
            st.write(f"- **{p['nombre']}**: quedan {p['stock']} (mínimo {p.get('stock_minimo') or 0})")

st.write("")

if salidas:
    st.subheader("Ventas")
    df_salidas = pd.DataFrame(salidas)
    df_salidas["fecha"] = pd.to_datetime(df_salidas["fecha"]).dt.date
    df_salidas["total"] = df_salidas["cantidad"].astype(float) * df_salidas["precio_unitario"].astype(float)

    c1, c2 = st.columns(2)
    with c1:
        st.caption("Ventas por día")
        por_dia = df_salidas.groupby("fecha")["total"].sum()
        st.bar_chart(por_dia)
    with c2:
        st.caption("Productos más vendidos (unidades)")
        df_salidas["producto_nombre"] = df_salidas["productos"].apply(
            lambda x: (x or {}).get("nombre", "—") if isinstance(x, dict) else "—"
        )
        por_producto = df_salidas.groupby("producto_nombre")["cantidad"].sum().sort_values(ascending=False).head(8)
        st.bar_chart(por_producto)

st.write("")
c1, c2 = st.columns(2)

with c1:
    st.subheader("Últimas entradas")
    if entradas:
        for e in entradas[:5]:
            nombre_producto = (e.get("productos") or {}).get("nombre", "—")
            st.write(f"🔽 **{nombre_producto}** · +{e['cantidad']} · {formatear_fecha_hora(e['fecha'])}")
    else:
        st.caption("Aún no hay entradas registradas.")

with c2:
    st.subheader("Últimas salidas")
    if salidas:
        for s in salidas[:5]:
            nombre_producto = (s.get("productos") or {}).get("nombre", "—")
            st.write(f"🔼 **{nombre_producto}** · -{s['cantidad']} · {formatear_fecha_hora(s['fecha'])}")
    else:
        st.caption("Aún no hay salidas registradas.")

st.info("Usa el menú de la izquierda para ir a Productos, Entradas, Salidas, Proveedores o Deudores.")
