"""
Decorador para que cualquier falla de conexión con Supabase muestre un
mensaje amigable en vez de un error técnico feo, y para que el resto del
código pueda seguir funcionando (mostrando listas vacías, etc.) en vez de
romper toda la página.
"""

import functools
import streamlit as st


def db_safe(default=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                st.error(
                    "⚠️ No pudimos comunicarnos con la base de datos. "
                    "Revisa tu conexión a internet e intenta de nuevo en unos segundos."
                )
                with st.expander("Detalle técnico"):
                    st.code(str(e))
                return default
        return wrapper
    return decorator
