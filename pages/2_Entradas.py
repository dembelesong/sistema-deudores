import streamlit as st

st.set_page_config(page_title="Entradas", page_icon="⬇️", layout="wide")

from utils.style import inject_css, page_header, sidebar_brand, avisar, mostrar_aviso_pendiente
from utils.auth import require_login, logout, current_negocio_nombre
from utils.db import get_supabase_client
from utils.queries import list_productos, list_proveedores, add_entrada, list_entradas
from utils.format import formatear_fecha_hora
from utils.reports import entradas_excel_bytes

inject_css()
require_login()
supabase = get_supabase_client()

with st.sidebar:
    sidebar_brand(current_negocio_nombre())
    st.caption(st.session_state["sb_user"].email)
    if st.button("Cerrar sesión", use_container_width=True):
        logout()

page_header("⬇️ Entradas", "Registra ingresos de mercadería y suma stock automáticamente.")

mostrar_aviso_pendiente()

productos = list_productos(supabase)
proveedores = list_proveedores(supabase)

if not productos:
    st.warning("Primero agrega al menos un producto en la sección **Productos**.")
    st.stop()

opciones_producto = {p["nombre"]: p["id"] for p in productos}
opciones_proveedor = {"— Sin proveedor —": None}
opciones_proveedor.update({p["nombre"]: p["id"] for p in proveedores})

col_form, col_list = st.columns([1, 2], gap="large")

with col_form:
    st.subheader("Registrar entrada")
    with st.form("form_entrada", clear_on_submit=True):
        producto_sel = st.selectbox("Producto", list(opciones_producto.keys()))
        cantidad = st.number_input("Cantidad", min_value=0.01, step=1.0)
        precio_unitario = st.number_input("Precio unitario", min_value=0.0, step=100.0)
        proveedor_sel = st.selectbox("Proveedor", list(opciones_proveedor.keys()))
        notas = st.text_area("Notas", placeholder="Opcional")
        submitted = st.form_submit_button("Registrar entrada", use_container_width=True)

    if submitted:
        ok = add_entrada(
            supabase,
            opciones_producto[producto_sel],
            cantidad,
            precio_unitario,
            opciones_proveedor[proveedor_sel],
            notas,
        )
        if ok:
            avisar(f"✅ Entrada registrada: +{cantidad} {producto_sel}")
            st.rerun()

with col_list:
    top1, top2 = st.columns([2, 1])
    with top1:
        st.subheader("Historial de entradas")
    with top2:
        entradas_actuales = list_entradas(supabase)
        if entradas_actuales:
            st.download_button(
                "⬇️ Exportar a Excel",
                data=entradas_excel_bytes(supabase),
                file_name="entradas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    busqueda = st.text_input("Buscar por producto", placeholder="Escribe un nombre...")
    entradas = entradas_actuales
    if busqueda:
        b = busqueda.lower()
        entradas = [e for e in entradas if b in ((e.get("productos") or {}).get("nombre", "")).lower()]
    if not entradas:
        st.caption("No se encontraron entradas." if busqueda else "Aún no hay entradas registradas.")
    for e in entradas:
        nombre_producto = (e.get("productos") or {}).get("nombre", "—")
        nombre_proveedor = (e.get("proveedores") or {}).get("nombre", "—")
        with st.container(border=True):
            st.write(
                f"🔽 **{nombre_producto}**  ·  +{e['cantidad']}  ·  "
                f"${e['precio_unitario']:,.0f} c/u  ·  {nombre_proveedor}  ·  {formatear_fecha_hora(e['fecha'])}"
            )
            if e.get("notas"):
                st.caption(e["notas"])
