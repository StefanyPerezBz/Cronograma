import calendar as pycalendar
from datetime import date

import streamlit as st

import utils_calculos as calc

MESES_ES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


def fecha_input_anual(label, value, key):
    """Selector de fecha en español con el año fijo al actual (el cronograma es anual)."""
    anio_actual = calc.hoy().year
    value = value or calc.hoy()
    st.markdown(f"**{label}** ({anio_actual})")
    col_d, col_m = st.columns(2)
    dia = col_d.selectbox("Día", list(range(1, 32)), index=min(value.day, 31) - 1, key=f"{key}_dia")
    mes_nombre = col_m.selectbox("Mes", MESES_ES, index=value.month - 1, key=f"{key}_mes")
    mes_num = MESES_ES.index(mes_nombre) + 1
    max_dia = pycalendar.monthrange(anio_actual, mes_num)[1]
    return date(anio_actual, mes_num, min(dia, max_dia))


ALERT_STYLES = {
    "success": {"bg": "#EAFBF0", "border": "#4CAF50", "icon": "✓", "titulo": "¡Listo!"},
    "error": {"bg": "#FDECEC", "border": "#E8231A", "icon": "✕", "titulo": "¡Error!"},
    "warning": {"bg": "#FFF8E6", "border": "#F2A900", "icon": "!", "titulo": "Atención"},
    "info": {"bg": "#EAF2FB", "border": "#2E75B6", "icon": "i", "titulo": "Información"},
}


def alerta(tipo, mensaje, toast=True):
    """Alerta con estilo tipo SweetAlert (HTML/CSS propios, sin dependencias externas)."""
    estilo = ALERT_STYLES.get(tipo, ALERT_STYLES["info"])
    posicion = (
        "position:fixed;top:20px;right:20px;z-index:9999;"
        "animation:swalIn .25s ease-out,swalOut .4s ease-in 3.2s forwards;"
        if toast else "margin:8px 0;animation:swalIn .25s ease-out;"
    )
    html = f'''
    <div style="{posicion}background:{estilo["bg"]};border-left:6px solid {estilo["border"]};
    border-radius:10px;box-shadow:0 4px 14px rgba(0,0,0,0.18);padding:12px 18px;
    display:flex;align-items:center;gap:12px;max-width:100%;box-sizing:border-box;
    font-family:'Segoe UI',Arial,sans-serif;">
      <div style="background:{estilo["border"]};color:#FFFFFF;width:28px;height:28px;
      border-radius:50%;display:flex;align-items:center;justify-content:center;
      font-weight:800;flex-shrink:0;">{estilo["icon"]}</div>
      <div style="color:#1A1A1A;min-width:0;">
        <div style="font-weight:800;font-size:14px;">{estilo["titulo"]}</div>
        <div style="font-size:13px;word-break:break-word;">{mensaje}</div>
      </div>
    </div>
    <style>
    @keyframes swalIn {{ from {{opacity:0;transform:translateY(-10px);}} to {{opacity:1;transform:translateY(0);}} }}
    @keyframes swalOut {{ to {{opacity:0;transform:translateY(-10px);}} }}
    @media (max-width: 640px) {{
      div[style*="position:fixed"][style*="z-index:9999"] {{
        left:12px !important;right:12px !important;max-width:none !important;
      }}
    }}
    </style>
    '''
    st.markdown(html, unsafe_allow_html=True)


def queue_alert(tipo, mensaje, toast=True):
    """Guarda una alerta para mostrarla tras un st.rerun().

    Si se llama a alerta() justo antes de st.rerun(), el rerun reemplaza la
    página antes de que el toast alcance a pintarse (dura una fracción de
    segundo). Se guarda en session_state y se muestra con flush_pending_alert()
    en la siguiente ejecución, donde ya no hay un rerun inmediato después.
    """
    st.session_state["_pending_alert"] = {"tipo": tipo, "mensaje": mensaje, "toast": toast}


def flush_pending_alert():
    pendiente = st.session_state.pop("_pending_alert", None)
    if pendiente:
        alerta(**pendiente)
