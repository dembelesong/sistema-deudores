import textwrap

import streamlit as st

PRIMARY = "#0f4c46"
DANGER = "#dc2626"
BG = "#f7f6f2"


def inject_css():
    st.markdown(
        textwrap.dedent(
            f"""\
            <style>
            .stApp {{
                background-color: {BG};
            }}
            [data-testid="stSidebar"] {{
                background-color: #ffffff;
                border-right: 1px solid #e5e7eb;
            }}
            div[data-testid="stMetric"] {{
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 14px;
                padding: 1rem 1.2rem;
            }}
            div[data-testid="stForm"] {{
                background-color: white;
                border-radius: 16px;
                padding: 1.2rem;
                border: 1px solid #e5e7eb;
            }}
            .card {{
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 16px;
                padding: 1.3rem 1.4rem;
                margin-bottom: 1rem;
            }}
            .card h3 {{
                margin: 0 0 .3rem 0;
            }}
            .saldo-positivo {{
                color: {DANGER};
                font-weight: 700;
            }}
            h1, h2, h3 {{
                color: #1f2937;
            }}
            .stButton>button {{
                border-radius: 10px;
            }}
            </style>
            """
        ),
        unsafe_allow_html=True,
    )


def brand_logo_svg(size: int = 64) -> str:
    """Badge cuadrado redondeado con las iniciales HVM."""
    svg = f"""<svg width="{size}" height="{size}" viewBox="0 0 72 72" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Logo HVM"><defs><clipPath id="badgeClip"><rect width="72" height="72" rx="20"/></clipPath></defs><g clip-path="url(#badgeClip)"><rect width="72" height="72" fill="{PRIMARY}"/><rect y="58" width="72" height="14" fill="#d97757"/><text x="36" y="39" font-family="'Segoe UI', Arial, sans-serif" font-size="23" font-weight="800" fill="#ffffff" text-anchor="middle" letter-spacing="1">HVM</text></g></svg>"""
    return svg


def whatsapp_link(telefono: str, mensaje: str) -> str:
    """Arma un link de wa.me a partir de un teléfono y un mensaje."""
    import urllib.parse

    solo_numeros = "".join(ch for ch in (telefono or "") if ch.isdigit())
    texto = urllib.parse.quote(mensaje)
    return f"https://wa.me/{solo_numeros}?text={texto}"


def badge_atraso_html(dias) -> str:
    if dias is None:
        texto, bg, color = "Al día", "#dcfce7", "#15803d"
    elif dias < 7:
        texto, bg, color = f"{dias} días", "#dcfce7", "#15803d"
    elif dias <= 15:
        texto, bg, color = f"{dias} días de atraso", "#fef3c7", "#b45309"
    else:
        texto, bg, color = f"{dias} días de atraso", "#fee2e2", "#dc2626"
    return (
        '<span style="background:' + bg + ';color:' + color + ';font-size:12px;'
        'padding:3px 10px;border-radius:999px;white-space:nowrap;">' + texto + '</span>'
    )


def sidebar_brand(nombre_negocio: str = "HVM"):
    html = (
        '<div style="display:flex; align-items:center; gap:10px; margin-bottom:2px;">'
        + brand_logo_svg(34)
        + '<span style="font-weight:800; font-size:1.15rem; color:#1f2937;">' + nombre_negocio + '</span>'
        + '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def avisar(mensaje: str, tipo: str = "success"):
    """Guarda un mensaje para mostrarlo apenas la página se recargue
    (así el aviso alcanza a verse, en vez de perderse con el rerun)."""
    st.session_state["_aviso"] = (tipo, mensaje)


def mostrar_aviso_pendiente():
    """Llamar al principio de cada página, después de page_header."""
    if "_aviso" in st.session_state:
        tipo, mensaje = st.session_state.pop("_aviso")
        getattr(st, tipo)(mensaje)


def page_header(title: str, subtitle: str = ""):
    st.markdown(f"# {title}")
    if subtitle:
        st.markdown(f"<div style='color:#6b7280; margin-top:-0.8rem;'>{subtitle}</div>", unsafe_allow_html=True)
    st.write("")
