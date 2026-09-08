import streamlit as st

st.set_page_config(page_title="Productos", page_icon="📦", layout="wide")

from utils.style import inject_css, page_header, sidebar_brand, avisar, mostrar_aviso_pendiente
from utils.auth import require_login, logout, current_negocio_nombre
from utils.db import get_supabase_client
from utils.queries import (
    list_productos, add_producto, update_producto, delete_producto, list_proveedores,
)
from utils.reports import productos_excel_bytes

inject_css()
require_login()
supabase = get_supabase_client()

with st.sidebar:
    sidebar_brand(current_negocio_nombre())
    st.caption(st.session_state["sb_user"].email)
    if st.button("Cerrar sesión", use_container_width=True):
        logout()

page_header("📦 Productos", "Tu catálogo e inventario.")

mostrar_aviso_pendiente()

proveedores = list_proveedores(supabase)
opciones_proveedor = {"— Sin proveedor —": None}
opciones_proveedor.update({p["nombre"]: p["id"] for p in proveedores})


def _nombre_proveedor(pid):
    for nombre, id_ in opciones_proveedor.items():
        if id_ == pid:
            return nombre
    return "— Sin proveedor —"


col_form, col_list = st.columns([1, 2], gap="large")

with col_form:
    st.subheader("Nuevo producto")
    with st.form("form_producto", clear_on_submit=True):
        nombre = st.text_input("Nombre")
        categoria = st.text_input("Categoría")
        stock = st.number_input("Stock inicial", min_value=0.0, step=1.0)
        stock_minimo = st.number_input("Avisarme cuando el stock baje de", min_value=0.0, step=1.0, value=5.0)
        precio_compra = st.number_input("Precio compra", min_value=0.0, step=100.0)
        precio_venta = st.number_input("Precio venta", min_value=0.0, step=100.0)
        proveedor_sel = st.selectbox("Proveedor", list(opciones_proveedor.keys()))
        submitted = st.form_submit_button("Agregar producto", use_container_width=True)

    if submitted:
        if not nombre:
            st.warning("El nombre es obligatorio.")
        else:
            ok = add_producto(
                supabase, nombre, categoria, stock, stock_minimo, precio_compra, precio_venta,
                opciones_proveedor[proveedor_sel],
            )
            if ok:
                avisar(f"✅ Producto '{nombre}' agregado.")
                st.rerun()

with col_list:
    top1, top2 = st.columns([2, 1])
    with top1:
        st.subheader("Catálogo")
    with top2:
        productos_actuales = list_productos(supabase)
        if productos_actuales:
            st.download_button(
                "⬇️ Exportar a Excel",
                data=productos_excel_bytes(supabase),
                file_name="productos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    busqueda = st.text_input("Buscar producto", placeholder="Escribe un nombre o categoría...")

    productos = productos_actuales
    if busqueda:
        b = busqueda.lower()
        productos = [
            p for p in productos
            if b in p["nombre"].lower() or b in (p.get("categoria") or "").lower()
        ]

    if not productos:
        st.caption("No se encontraron productos." if busqueda else "Todavía no has agregado productos.")

    for p in productos:
        proveedor_nombre = (p.get("proveedores") or {}).get("nombre", "—")
        bajo_stock = float(p["stock"]) <= float(p.get("stock_minimo") or 0)
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                titulo = f"**{p['nombre']}**  ·  {p.get('categoria') or 'Sin categoría'}"
                if bajo_stock:
                    titulo += "  ⚠️ *stock bajo*"
                st.markdown(titulo)
                st.write(
                    f"Stock: **{p['stock']}**  ·  Compra: ${p['precio_compra']:,.0f}  ·  "
                    f"Venta: ${p['precio_venta']:,.0f}  ·  Proveedor: {proveedor_nombre}"
                )
            with c2:
                if st.button("🗑️", key=f"del_prod_{p['id']}"):
                    if delete_producto(supabase, p["id"]):
                        st.rerun()

            with st.expander("✏️ Editar"):
                with st.form(f"form_editar_prod_{p['id']}"):
                    e_nombre = st.text_input("Nombre", value=p["nombre"], key=f"e_nombre_{p['id']}")
                    e_categoria = st.text_input("Categoría", value=p.get("categoria") or "", key=f"e_cat_{p['id']}")
                    e_stock = st.number_input("Stock", min_value=0.0, step=1.0, value=float(p["stock"]), key=f"e_stock_{p['id']}")
                    e_stock_min = st.number_input(
                        "Avisarme cuando el stock baje de", min_value=0.0, step=1.0,
                        value=float(p.get("stock_minimo") or 0), key=f"e_stockmin_{p['id']}",
                    )
                    e_compra = st.number_input("Precio compra", min_value=0.0, step=100.0, value=float(p["precio_compra"] or 0), key=f"e_compra_{p['id']}")
                    e_venta = st.number_input("Precio venta", min_value=0.0, step=100.0, value=float(p["precio_venta"] or 0), key=f"e_venta_{p['id']}")
                    proveedores_keys = list(opciones_proveedor.keys())
                    idx = proveedores_keys.index(_nombre_proveedor(p.get("proveedor_id")))
                    e_proveedor = st.selectbox("Proveedor", proveedores_keys, index=idx, key=f"e_prov_{p['id']}")
                    if st.form_submit_button("Guardar cambios"):
                        ok = update_producto(
                            supabase, p["id"], e_nombre, e_categoria, e_stock, e_stock_min,
                            e_compra, e_venta, opciones_proveedor[e_proveedor],
                        )
                        if ok:
                            avisar("✅ Producto actualizado.")
                            st.rerun()
