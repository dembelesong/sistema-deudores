"""
Autenticación con Supabase Auth (email + contraseña), incluyendo
recuperación de contraseña olvidada.
"""

import streamlit as st
from utils.db import get_supabase_client
from utils.style import brand_logo_svg


def _apply_session(session, user):
    st.session_state["sb_session"] = session
    st.session_state["sb_user"] = user


def logout():
    supabase = get_supabase_client()
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    for k in ("sb_session", "sb_user", "negocio_id", "negocio_nombre"):
        st.session_state.pop(k, None)
    st.rerun()


def is_logged_in() -> bool:
    return st.session_state.get("sb_user") is not None


def current_user_id() -> str | None:
    user = st.session_state.get("sb_user")
    return user.id if user else None


def current_negocio_id() -> str | None:
    """A qué 'negocio' (cuenta compartida) pertenece la persona logueada.
    Se guarda en session_state para no consultarlo en cada acción."""
    if "negocio_id" not in st.session_state:
        _cargar_negocio()
    return st.session_state.get("negocio_id")


def current_negocio_nombre() -> str:
    """Nombre del negocio de la persona logueada (para mostrar en pantalla)."""
    if "negocio_nombre" not in st.session_state:
        _cargar_negocio()
    return st.session_state.get("negocio_nombre") or "Mi negocio"


def _cargar_negocio():
    supabase = get_supabase_client()
    try:
        fila = (
            supabase.table("perfiles")
            .select("negocio_id, negocios(nombre)")
            .eq("user_id", current_user_id())
            .single()
            .execute()
            .data
        )
        st.session_state["negocio_id"] = fila["negocio_id"] if fila else None
        st.session_state["negocio_nombre"] = (
            (fila.get("negocios") or {}).get("nombre") if fila else None
        )
    except Exception:
        st.session_state["negocio_id"] = None
        st.session_state["negocio_nombre"] = None


def _login_ui(supabase):
    with st.form("form_login"):
        email = st.text_input("Correo electrónico")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Iniciar sesión", use_container_width=True)

    if submitted:
        if not email or not password:
            st.warning("Completa correo y contraseña.")
            return
        try:
            res = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            _apply_session(res.session, res.user)
            st.rerun()
        except Exception as e:
            st.error(f"No se pudo iniciar sesión: {e}")

    with st.expander("¿Olvidaste tu contraseña?"):
        with st.form("form_forgot"):
            forgot_email = st.text_input("Tu correo electrónico", key="forgot_email")
            enviar = st.form_submit_button("Enviar enlace para restablecer")
        if enviar:
            if not forgot_email:
                st.warning("Escribe tu correo primero.")
            else:
                try:
                    supabase.auth.reset_password_for_email(forgot_email)
                    st.success(
                        "✅ Si ese correo tiene una cuenta, te llegará un enlace para "
                        "crear una contraseña nueva. Revisa tu bandeja de entrada "
                        "(y la carpeta de spam)."
                    )
                except Exception as e:
                    st.error(f"No se pudo enviar el correo: {e}")


def _signup_ui(supabase):
    with st.form("form_signup"):
        email = st.text_input("Correo electrónico", key="signup_email")
        password = st.text_input(
            "Contraseña (mínimo 6 caracteres)", type="password", key="signup_pw"
        )
        submitted = st.form_submit_button("Crear cuenta", use_container_width=True)

    if submitted:
        if not email or not password:
            st.warning("Completa correo y contraseña.")
            return
        try:
            res = supabase.auth.sign_up({"email": email, "password": password})
            if res.session:
                _apply_session(res.session, res.user)
                st.rerun()
            else:
                st.success(
                    "Cuenta creada ✅ Si tu proyecto de Supabase pide confirmación "
                    "por correo, revisa tu bandeja de entrada antes de iniciar sesión."
                )
        except Exception as e:
            st.error(f"No se pudo crear la cuenta: {e}")


def render_login_screen():
    html = (
        '<div style="text-align:center; margin-top:2rem; margin-bottom:1.5rem;">'
        '<div style="display:flex; justify-content:center; margin-bottom:14px;">' + brand_logo_svg(110) + '</div>'
        '<div style="color:#6b7280;">Inventario, ventas y deudores</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

    supabase = get_supabase_client()

    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        with st.container(border=True):
            _login_ui(supabase)


def render_password_reset_screen(code: str):
    """Pantalla que se muestra cuando el usuario llega desde el enlace del
    correo de 'olvidé mi contraseña'. Cambia la contraseña y lo deja logueado."""
    supabase = get_supabase_client()

    html = (
        '<div style="text-align:center; margin-top:2rem; margin-bottom:1.5rem;">'
        '<div style="display:flex; justify-content:center; margin-bottom:14px;">' + brand_logo_svg(90) + '</div>'
        '<div style="color:#6b7280;">Elige tu nueva contraseña</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

    if not st.session_state.get("_recovery_session_ready"):
        try:
            supabase.auth.exchange_code_for_session({"auth_code": code})
            st.session_state["_recovery_session_ready"] = True
        except Exception as e:
            st.error(
                "Este enlace ya no es válido o expiró. Pide uno nuevo desde "
                "'¿Olvidaste tu contraseña?' en la pantalla de inicio de sesión."
            )
            with st.expander("Detalle técnico"):
                st.code(str(e))
            return

    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        with st.container(border=True):
            with st.form("form_reset_password"):
                nueva = st.text_input("Nueva contraseña (mínimo 6 caracteres)", type="password")
                repetir = st.text_input("Repite la nueva contraseña", type="password")
                submitted = st.form_submit_button("Actualizar contraseña", use_container_width=True)

            if submitted:
                if not nueva or len(nueva) < 6:
                    st.warning("La contraseña debe tener al menos 6 caracteres.")
                elif nueva != repetir:
                    st.warning("Las contraseñas no coinciden.")
                else:
                    try:
                        supabase.auth.update_user({"password": nueva})
                        st.success("✅ Contraseña actualizada. Ya puedes iniciar sesión normalmente.")
                        st.session_state.pop("_recovery_session_ready", None)
                        st.query_params.clear()
                        if st.button("Ir al inicio de sesión"):
                            st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo actualizar la contraseña: {e}")


def require_login():
    """Llamar al inicio de cada página. Detiene la ejecución si no hay sesión."""
    params = st.query_params
    if "code" in params and not is_logged_in():
        render_password_reset_screen(params["code"])
        st.stop()

    if not is_logged_in():
        render_login_screen()
        st.stop()

    if current_negocio_id() is None:
        st.error(
            "⚠️ Tu cuenta todavía no tiene un negocio asignado. "
            "Pídele al administrador que la vincule desde Supabase."
        )
        if st.button("Cerrar sesión"):
            logout()
        st.stop()
