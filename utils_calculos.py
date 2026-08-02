from datetime import date, datetime, timedelta, timezone

import pandas as pd

try:
    from zoneinfo import ZoneInfo
    ZONA_PERU = ZoneInfo("America/Lima")
except Exception:
    # Si el sistema no tiene la base de datos de zonas horarias (falta tzdata en
    # Windows), Perú siempre es UTC-5 fijo, sin horario de verano.
    ZONA_PERU = timezone(timedelta(hours=-5))


def hoy():
    """Fecha de hoy según la zona horaria de Perú, no la del reloj/zona local del equipo."""
    return datetime.now(ZONA_PERU).date()


STATUS_OPTIONS = ["Sin Empezar", "En Proceso", "Atrasado", "Completado"]

STATUS_COLORS = {
    "Sin Empezar": {"bg": "#A6A6A6", "text": "#FFFFFF"},
    "En Proceso": {"bg": "#FFC000", "text": "#1A1A1A"},
    "Atrasado": {"bg": "#E8551F", "text": "#FFFFFF"},
    "Completado": {"bg": "#4CAF50", "text": "#FFFFFF"},
}

GRID_LABELS = {"Completado": "C", "En Proceso": "PR", "Atrasado": "X"}

FILL_COLOR = "#2E75B6"
WEEKEND_COLOR = "#D9D9D9"

WEEKDAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
WEEKDAYS_ABBR = {
    "Lunes": "LUN", "Martes": "MAR", "Miércoles": "MIÉ", "Jueves": "JUE",
    "Viernes": "VIE", "Sábado": "SÁB", "Domingo": "DOM",
}
MESES_ES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


def to_date(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return pd.to_datetime(value).date()


def format_fecha(d):
    return f"{d.day}/{d.month:02d}/{d.year}"


def days_remaining(fecha_fin):
    fecha_fin = to_date(fecha_fin)
    if fecha_fin is None:
        return None
    return (fecha_fin - hoy()).days


def dias_restantes_estilo(dias_restantes, status):
    """Devuelve (texto, color) para la columna 'Días restantes'."""
    if status == "Completado":
        return "Completado", None
    if dias_restantes is None:
        return "", None
    if dias_restantes < -7:
        return str(dias_restantes), "#E8231A"
    if dias_restantes < 0:
        return str(dias_restantes), "#E8731F"
    if dias_restantes <= 3:
        return str(dias_restantes), "#F2C230"
    return str(dias_restantes), None


def expected_progress(fecha_inicio, fecha_fin, today=None):
    fecha_inicio = to_date(fecha_inicio)
    fecha_fin = to_date(fecha_fin)
    if fecha_inicio is None or fecha_fin is None:
        return 0.0
    today = today or hoy()
    total_days = (fecha_fin - fecha_inicio).days
    if total_days <= 0:
        return 100.0 if today >= fecha_fin else 0.0
    elapsed = (today - fecha_inicio).days
    pct = (elapsed / total_days) * 100
    return max(0.0, min(100.0, pct))


def avance_real_auto(status, fecha_inicio, fecha_fin, today=None):
    """% Avance real ya no lo registra el usuario: se deriva del Estado."""
    if status == "Completado":
        return 100.0
    if status == "Sin Empezar":
        return 0.0
    # "En Proceso"/"Atrasado" nunca deben mostrar 0% ni 100%: esos valores son
    # exclusivos de "Sin Empezar" y "Completado". Sin el tope, una actividad
    # cuya fecha fin ya pasó (pero que sigue En Proceso/Atrasado, no marcada
    # Completada) calcularía 100% de avance esperado y se vería como terminada.
    pct = round(expected_progress(fecha_inicio, fecha_fin, today), 0)
    return max(1.0, min(99.0, pct))


def project_progress(df):
    if df.empty:
        return 0.0
    avances = df.apply(
        lambda r: avance_real_auto(r["Status"], r["Fecha_Inicio"], r["Fecha_Fin"]), axis=1
    )
    if avances.empty:
        return 0.0
    return round(float(avances.mean()), 1)


_FERIADOS_FIJOS_PERU = [
    (1, 1),    # Año Nuevo
    (5, 1),    # Día del Trabajo
    (6, 29),   # San Pedro y San Pablo
    (7, 28),   # Fiestas Patrias
    (7, 29),   # Fiestas Patrias
    (8, 30),   # Santa Rosa de Lima
    (10, 8),   # Combate de Angamos
    (11, 1),   # Todos los Santos
    (12, 8),   # Inmaculada Concepción
    (12, 9),   # Batalla de Ayacucho
    (12, 25),  # Navidad
]

_cache_feriados_peru = {}


def _domingo_pascua(anio):
    """Domingo de Pascua (algoritmo de Butcher, calendario gregoriano)."""
    a = anio % 19
    b = anio // 100
    c = anio % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(anio, mes, dia)


def feriados_peru(anio):
    """Feriados nacionales de Perú para un año (fijos + Jueves y Viernes Santo)."""
    if anio in _cache_feriados_peru:
        return _cache_feriados_peru[anio]
    pascua = _domingo_pascua(anio)
    feriados = {date(anio, mes, dia) for mes, dia in _FERIADOS_FIJOS_PERU}
    feriados.add(pascua - timedelta(days=3))  # Jueves Santo
    feriados.add(pascua - timedelta(days=2))  # Viernes Santo
    _cache_feriados_peru[anio] = feriados
    return feriados


def is_non_working_day(day, dia_excluido_1, dia_excluido_2):
    weekday_name = WEEKDAYS[day.weekday()]
    if weekday_name in (dia_excluido_1, dia_excluido_2):
        return True
    return day in feriados_peru(day.year)


def dias_excluidos_totales(start, end, dia_excluido_1, dia_excluido_2):
    if start is None or end is None or start > end:
        return 0
    total = 0
    current = start
    while current <= end:
        if is_non_working_day(current, dia_excluido_1, dia_excluido_2):
            total += 1
        current += timedelta(days=1)
    return total


def duracion_dias(start, end):
    if start is None or end is None or start > end:
        return 0
    return (end - start).days + 1


def duracion_meses(start, end):
    dias = duracion_dias(start, end)
    return round(dias / 30, 1)


def status_counts(df):
    counts = {status: 0 for status in STATUS_OPTIONS}
    if not df.empty and "Status" in df.columns:
        vc = df["Status"].value_counts()
        for status in STATUS_OPTIONS:
            counts[status] = int(vc.get(status, 0))
    return counts
