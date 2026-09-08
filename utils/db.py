"""
Conexión a Supabase.

Busca las credenciales en este orden:
1. st.secrets (recomendado para Streamlit Community Cloud)
2. Variables de entorno / archivo .env (recomendado para uso local)
"""

import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


def _get_credential(key: str) -> str | None:
    # 1) st.secrets (si existe secrets.toml)
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    # 2) variables de entorno / .env
    return os.getenv(key)


@st.cache_resource(show_spinner=False)
def get_supabase_client() -> Client:
    url = _get_credential("SUPABASE_URL")
    key = _get_credential("SUPABASE_KEY")

    if not url or not key:
        st.error(
            "⚠️ Faltan las credenciales de Supabase.\n\n"
            "Configúralas en `.streamlit/secrets.toml` (nube) o en un archivo "
            "`.env` en la raíz del proyecto (local). Revisa el README."
        )
        st.stop()

    return create_client(url, key)
