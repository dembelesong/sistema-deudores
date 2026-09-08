import streamlit as st

st.set_page_config(page_title="Proveedores", page_icon="🚚", layout="wide")

from utils.style import inject_css, page_header, sidebar_brand, avisar, mostrar_aviso_pendiente
from utils.auth import require_login, logout, current_negocio_nombre
from utils.db import get_supabase_client
from utils.queries import list_proveedores, add_proveedor, update_proveedor, delete_proveedor
from utils.reports import proveedores_excel_bytes

inject_css()
require_login()
supabase = get_supabase_client()

with st.sidebar:
    sidebar_brand(current_negocio_nombre())
    st.caption(st.session_state["sb_user"].email)
    if st.button("Cerrar sesión", use_container_width=True):
        logout()

page_header("🚚 Proveedores", "A quién le compras tu mercadería.")

mostrar_aviso_pendiente()

col_form, col_list = st.columns([1, 2], gap="large")

with col_form:
    st.subheader("Nuevo proveedor")
    with st.form("form_proveedor", clear_on_submit=True):
        nombre = st.text_input("Nombre")
        telefono = st.text_input("Teléfono", placeholder="+56 9")
        email = st.text_input("Correo", placeholder="Opcional")
        notas = st.text_area("Notas", placeholder="Opcional")
        submitted = st.form_submit_button("Agregar proveedor", use_container_width=True)

    if submitted:
        if not nombre:
            st.warning("El nombre es obligatorio.")
        else:
            if add_proveedor(supabase, nombre, telefono, email, notas):
                avisar(f"✅ Proveedor '{nombre}' agregado.")
                st.rerun()

with col_list:
    top1, top2 = st.columns([2, 1])
    with top1:
        st.subheader("Listado")
    with top2:
        proveedores_actuales = list_proveedores(supabase)
        if proveedores_actuales:
            st.download_button(
                "⬇️ Exportar a Excel",
                data=proveedores_excel_bytes(supabase),
                file_name="proveedores.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    busqueda = st.text_input("Buscar proveedor", placeholder="Escribe un nombre...")

    proveedores = proveedores_actuales
    if busqueda:
        b = busqueda.lower()
        proveedores = [p for p in proveedores if b in p["nombre"].lower()]

    if not proveedores:
        st.caption("No se encontraron proveedores." if busqueda else "Todavía no has agregado proveedores.")

    for p in proveedores:
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"**{p['nombre']}**")
                if p.get("telefono"):
                    st.write(f"📞 {p['telefono']}")
                if p.get("email"):
                    st.write(f"✉️ {p['email']}")
                if p.get("notas"):
                    st.caption(p["notas"])
            with c2:
                if st.button("🗑️", key=f"del_prov_{p['id']}"):
                    if delete_proveedor(supabase, p["id"]):
                        st.rerun()

            with st.expander("✏️ Editar"):
                with st.form(f"form_editar_prov_{p['id']}"):
                    e_nombre = st.text_input("Nombre", value=p["nombre"], key=f"e_nombre_prov_{p['id']}")
                    e_telefono = st.text_input("Teléfono", value=p.get("telefono") or "", key=f"e_tel_prov_{p['id']}")
                    e_email = st.text_input("Correo", value=p.get("email") or "", key=f"e_email_prov_{p['id']}")
                    e_notas = st.text_area("Notas", value=p.get("notas") or "", key=f"e_notas_prov_{p['id']}")
                    if st.form_submit_button("Guardar cambios"):
                        if update_proveedor(supabase, p["id"], e_nombre, e_telefono, e_email, e_notas):
                            avisar("✅ Proveedor actualizado.")
                            st.rerun()
