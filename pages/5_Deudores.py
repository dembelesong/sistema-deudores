import streamlit as st

st.set_page_config(page_title="Deudores", page_icon="💰", layout="wide")

from utils.style import inject_css, page_header, sidebar_brand, whatsapp_link, badge_atraso_html, avisar, mostrar_aviso_pendiente
from utils.auth import require_login, logout, current_negocio_nombre
from utils.db import get_supabase_client
from utils.queries import (
    list_deudores, add_deudor, update_deudor, delete_deudor,
    add_deuda, add_abono, totales_deudor, total_por_cobrar,
    list_deudas_deudor, list_abonos_deudor, delete_deuda, delete_abono,
    dias_atraso_deudor,
)
from utils.reports import deudores_excel_bytes
from utils.format import formatear_fecha_hora

inject_css()
require_login()
supabase = get_supabase_client()

with st.sidebar:
    sidebar_brand(current_negocio_nombre())
    st.caption(st.session_state["sb_user"].email)
    if st.button("Cerrar sesión", use_container_width=True):
        logout()

col_title, col_metric = st.columns([3, 1])
with col_title:
    page_header("💰 Deudores", "Quién te debe, cuánto ha abonado y cuánto queda pendiente.")
with col_metric:
    st.metric("Por cobrar", f"${total_por_cobrar(supabase):,.0f}")

mostrar_aviso_pendiente()

col_form, col_list = st.columns([1, 2], gap="large")

with col_form:
    st.subheader("Nuevo deudor")
    with st.form("form_deudor", clear_on_submit=True):
        nombre = st.text_input("Nombre")
        telefono = st.text_input("Teléfono", placeholder="+56 9")
        notas = st.text_area("Notas", placeholder="Ej: Fiado de la semana")
        submitted = st.form_submit_button("Agregar deudor", use_container_width=True)

    if submitted:
        if not nombre:
            st.warning("El nombre es obligatorio.")
        else:
            nuevo_id = add_deudor(supabase, nombre, telefono, notas)
            if nuevo_id:
                avisar(f"✅ Deudor '{nombre}' agregado.")
                st.rerun()

with col_list:
    top1, top2 = st.columns([2, 1])
    with top1:
        st.subheader("Listado")
    with top2:
        deudores_actuales = list_deudores(supabase)
        if deudores_actuales:
            st.download_button(
                "⬇️ Exportar a Excel",
                data=deudores_excel_bytes(supabase),
                file_name="deudores.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    busqueda = st.text_input("Buscar deudor", placeholder="Escribe un nombre...")

    deudores = deudores_actuales
    if busqueda:
        b = busqueda.lower()
        deudores = [d for d in deudores if b in d["nombre"].lower()]

    if not deudores:
        st.caption("No se encontraron deudores." if busqueda else "Todavía no has agregado deudores.")

    for d in deudores:
        deuda, abonado, saldo = totales_deudor(supabase, d["id"])
        dias = dias_atraso_deudor(supabase, d["id"])
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(
                    f"### {d['nombre']}&nbsp;&nbsp;{badge_atraso_html(dias)}",
                    unsafe_allow_html=True,
                )
                if d.get("telefono"):
                    st.write(f"📞 {d['telefono']}")
                if d.get("notas"):
                    st.caption(d["notas"])
            with c2:
                if st.button("🗑️", key=f"del_deudor_{d['id']}"):
                    if delete_deudor(supabase, d["id"]):
                        st.rerun()

            m1, m2, m3 = st.columns(3)
            m1.metric("Deuda", f"${deuda:,.0f}")
            m2.metric("Abonado", f"${abonado:,.0f}")
            m3.metric("Saldo", f"${saldo:,.0f}")

            if saldo > 0 and d.get("telefono"):
                mensaje = (
                    f"Hola {d['nombre']}, te escribo para recordarte que tienes un saldo "
                    f"pendiente de ${saldo:,.0f}. ¡Gracias!"
                )
                st.link_button("💬 Recordar por WhatsApp", whatsapp_link(d["telefono"], mensaje))

            tab_mov, tab_edit, tab_hist = st.tabs(["➕ Deuda / abono", "✏️ Editar", "📋 Historial"])

            with tab_mov:
                t1, t2 = st.tabs(["➕ Nueva deuda", "💵 Registrar abono"])
                with t1:
                    with st.form(f"form_deuda_{d['id']}", clear_on_submit=True):
                        monto = st.number_input("Monto", min_value=0.0, step=100.0, key=f"monto_deuda_{d['id']}")
                        descripcion = st.text_input("Descripción", placeholder="Ej: 2 pan, 1 leche")
                        if st.form_submit_button("Agregar deuda"):
                            if add_deuda(supabase, d["id"], monto, descripcion):
                                avisar(f"✅ Deuda de ${monto:,.0f} agregada a {d['nombre']}.")
                                st.rerun()
                with t2:
                    with st.form(f"form_abono_{d['id']}", clear_on_submit=True):
                        monto_abono = st.number_input("Monto abonado", min_value=0.0, step=100.0, key=f"monto_abono_{d['id']}")
                        if st.form_submit_button("Registrar abono"):
                            if add_abono(supabase, d["id"], monto_abono):
                                avisar(f"✅ Abono de ${monto_abono:,.0f} registrado para {d['nombre']}.")
                                st.rerun()

            with tab_edit:
                with st.form(f"form_editar_deudor_{d['id']}"):
                    e_nombre = st.text_input("Nombre", value=d["nombre"], key=f"e_nombre_deudor_{d['id']}")
                    e_telefono = st.text_input("Teléfono", value=d.get("telefono") or "", key=f"e_tel_deudor_{d['id']}")
                    e_notas = st.text_area("Notas", value=d.get("notas") or "", key=f"e_notas_deudor_{d['id']}")
                    if st.form_submit_button("Guardar cambios"):
                        if update_deudor(supabase, d["id"], e_nombre, e_telefono, e_notas):
                            avisar("✅ Deudor actualizado.")
                            st.rerun()

            with tab_hist:
                deudas = list_deudas_deudor(supabase, d["id"])
                abonos = list_abonos_deudor(supabase, d["id"])
                if not deudas and not abonos:
                    st.caption("Todavía no hay movimientos.")
                for deu in deudas:
                    hc1, hc2 = st.columns([5, 1])
                    with hc1:
                        st.write(f"🔴 Deuda: **${float(deu['monto']):,.0f}**  ·  {deu.get('descripcion') or 'Sin descripción'}  ·  {formatear_fecha_hora(deu['fecha'])}")
                    with hc2:
                        if st.button("🗑️", key=f"del_deuda_{deu['id']}"):
                            if delete_deuda(supabase, deu["id"]):
                                st.rerun()
                for ab in abonos:
                    hc1, hc2 = st.columns([5, 1])
                    with hc1:
                        st.write(f"🟢 Abono: **${float(ab['monto']):,.0f}**  ·  {formatear_fecha_hora(ab['fecha'])}")
                    with hc2:
                        if st.button("🗑️", key=f"del_abono_{ab['id']}"):
                            if delete_abono(supabase, ab["id"]):
                                st.rerun()
