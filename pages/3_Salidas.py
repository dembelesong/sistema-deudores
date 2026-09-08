import streamlit as st

st.set_page_config(page_title="Salidas", page_icon="⬆️", layout="wide")

from utils.style import inject_css, page_header, sidebar_brand, avisar, mostrar_aviso_pendiente
from utils.auth import require_login, logout, current_negocio_nombre
from utils.db import get_supabase_client
from utils.queries import list_productos, add_salida, list_salidas
from utils.format import formatear_fecha_hora
from utils.reports import salidas_excel_bytes

inject_css()
require_login()
supabase = get_supabase_client()

with st.sidebar:
    sidebar_brand(current_negocio_nombre())
    st.caption(st.session_state["sb_user"].email)
    if st.button("Cerrar sesión", use_container_width=True):
        logout()

page_header("⬆️ Salidas", "Registra ventas o egresos de mercadería y resta stock automáticamente.")

mostrar_aviso_pendiente()

productos = list_productos(supabase)

if not productos:
    st.warning("Primero agrega al menos un producto en la sección **Productos**.")
    st.stop()

opciones_producto = {p["nombre"]: p for p in productos}

col_form, col_list = st.columns([1, 2], gap="large")

with col_form:
    st.subheader("Registrar salida")
    with st.form("form_salida", clear_on_submit=True):
        producto_sel = st.selectbox("Producto", list(opciones_producto.keys()))
        stock_disponible = opciones_producto[producto_sel]["stock"]
        st.caption(f"Stock disponible: {stock_disponible}")
        cantidad = st.number_input("Cantidad", min_value=0.01, step=1.0)
        precio_unitario = st.number_input(
            "Precio unitario",
            min_value=0.0,
            step=100.0,
            value=float(opciones_producto[producto_sel]["precio_venta"] or 0),
        )
        notas = st.text_area("Notas", placeholder="Opcional")
        submitted = st.form_submit_button("Registrar salida", use_container_width=True)

    if submitted:
        if cantidad > float(stock_disponible):
            st.error("No hay stock suficiente para esa cantidad.")
        else:
            ok = add_salida(supabase, opciones_producto[producto_sel]["id"], cantidad, precio_unitario, notas)
            if ok:
                avisar(f"✅ Salida registrada: -{cantidad} {producto_sel}")
                st.rerun()

with col_list:
    top1, top2 = st.columns([2, 1])
    with top1:
        st.subheader("Historial de salidas")
    with top2:
        salidas_actuales = list_salidas(supabase)
        if salidas_actuales:
            st.download_button(
                "⬇️ Exportar a Excel",
                data=salidas_excel_bytes(supabase),
                file_name="salidas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    busqueda = st.text_input("Buscar por producto", placeholder="Escribe un nombre...")
    salidas = salidas_actuales
    if busqueda:
        b = busqueda.lower()
        salidas = [s for s in salidas if b in ((s.get("productos") or {}).get("nombre", "")).lower()]
    if not salidas:
        st.caption("No se encontraron salidas." if busqueda else "Aún no hay salidas registradas.")
    for s in salidas:
        nombre_producto = (s.get("productos") or {}).get("nombre", "—")
        with st.container(border=True):
            st.write(
                f"🔼 **{nombre_producto}**  ·  -{s['cantidad']}  ·  "
                f"${s['precio_unitario']:,.0f} c/u  ·  {formatear_fecha_hora(s['fecha'])}"
            )
            if s.get("notas"):
                st.caption(s["notas"])
