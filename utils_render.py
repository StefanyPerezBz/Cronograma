from datetime import timedelta

import pandas as pd

import utils_calculos as calc

HEADER_BLUE = "#2E5FA3"
TABLE_HEADER_BLUE = "#1F3864"
CATEGORY_GRAY = "#E7E7E7"
BORDER_COLOR = "#AFAFAF"

KPI_COLORS = {
    "total": {"bg": "#595959", "text": "#FFFFFF"},
    "sin_empezar": {"bg": "#BFBFBF", "text": "#1A1A1A"},
    "en_proceso": {"bg": "#FFC000", "text": "#1A1A1A"},
    "atrasado": {"bg": "#E8231A", "text": "#FFFFFF"},
    "completado": {"bg": "#4CAF50", "text": "#FFFFFF"},
    "avance": {"bg": "#2E75B6", "text": "#FFFFFF"},
    "secundaria": {"bg": "#8FAADC", "text": "#1A1A1A"},
}


def render_header_bar(titulo="CRONOGRAMA DE ACTIVIDADES"):
    return (
        f'<div style="background:{HEADER_BLUE};color:#FFFFFF;text-align:center;'
        f'padding:16px 8px;font-size:clamp(16px,3.5vw,26px);font-weight:800;letter-spacing:1px;'
        f'border-radius:4px;margin-bottom:8px;word-break:break-word;">{titulo}</div>'
    )


def render_date_controls(fecha_actual, fecha_inicio, fecha_fin):
    def box(label, value):
        return (
            '<div style="display:inline-flex;align-items:center;margin:4px 22px 4px 0;">'
            f'<span style="font-weight:800;font-size:13px;margin-right:8px;">{label}</span>'
            '<span style="background:#EDEDED;border:1px solid #B0B0B0;border-radius:4px;'
            f'padding:5px 16px;font-weight:600;color:#1A1A1A;">{value}</span></div>'
        )
    return (
        '<div style="padding:8px 4px 14px 4px;display:flex;flex-wrap:wrap;">'
        + box("FECHA ACTUAL", calc.format_fecha(fecha_actual))
        + box("FECHA INICIO", calc.format_fecha(fecha_inicio))
        + box("FECHA FIN", calc.format_fecha(fecha_fin))
        + "</div>"
    )


def _kpi_card(numero, etiqueta1, etiqueta2, colores):
    return (
        f'<div style="background:{colores["bg"]};color:{colores["text"]};border-radius:8px;'
        'padding:10px 4px;text-align:center;flex:1;min-width:70px;">'
        f'<div style="font-size:26px;font-weight:800;line-height:1.1;">{numero}</div>'
        f'<div style="font-size:11px;font-weight:800;border-top:1px solid rgba(0,0,0,0.25);'
        f'margin-top:5px;padding-top:3px;">{etiqueta1}</div>'
        f'<div style="font-size:10px;">{etiqueta2}</div></div>'
    )


def render_kpi_row(counts, avance_pct, dias_excluidos, dur_meses, dur_dias):
    cards = [
        _kpi_card(counts["total"], "Actividad", "PLAN", KPI_COLORS["total"]),
        _kpi_card(counts["Sin Empezar"], "Sin Empezar", "SE", KPI_COLORS["sin_empezar"]),
        _kpi_card(counts["En Proceso"], "En Proceso", "PR", KPI_COLORS["en_proceso"]),
        _kpi_card(counts["Atrasado"], "Atrasado", "X", KPI_COLORS["atrasado"]),
        _kpi_card(counts["Completado"], "Completado", "C", KPI_COLORS["completado"]),
        _kpi_card(f"{avance_pct:.0f}", "Proyecto", "% Avance", KPI_COLORS["avance"]),
        '<div style="width:14px;"></div>',
        _kpi_card(dias_excluidos, "Días", "Excluidos", KPI_COLORS["secundaria"]),
        _kpi_card(dur_meses, "Duración", "Meses", KPI_COLORS["secundaria"]),
        _kpi_card(dur_dias, "Duración", "Días", KPI_COLORS["secundaria"]),
    ]
    return (
        '<div style="overflow-x:auto;padding-bottom:4px;">'
        '<div style="display:flex;gap:8px;align-items:stretch;min-width:min-content;">'
        + "".join(cards) + "</div></div>"
    )


def _progress_bar_html(pct, color, height="14px"):
    pct = max(0.0, min(100.0, pct))
    return (
        f'<div style="background:#DDDDDD;border-radius:6px;overflow:hidden;height:{height};'
        f'width:100%;min-width:60px;position:relative;" title="{pct:.0f}%">'
        f'<div style="background:{color};width:{pct:.0f}%;height:100%;"></div>'
        f'<span style="position:absolute;inset:0;text-align:center;line-height:{height};'
        f'font-size:9px;font-weight:800;color:#1A1A1A;">{pct:.0f}%</span></div>'
    )


def render_total_progress_bar(pct):
    color = calc.STATUS_COLORS["Completado"]["bg"] if pct >= 100 else HEADER_BLUE
    pct_clamped = max(0.0, min(100.0, pct))
    return (
        '<div style="margin:6px 0 4px 0;">'
        f'<div style="font-weight:800;font-size:13px;margin-bottom:4px;">'
        f'Avance total del proyecto: {pct:.0f}%</div>'
        '<div style="background:#DDDDDD;border-radius:8px;overflow:hidden;height:22px;'
        'width:100%;position:relative;">'
        f'<div style="background:{color};width:{pct_clamped:.0f}%;height:100%;'
        'transition:width .3s;"></div>'
        '<span style="position:absolute;inset:0;text-align:center;line-height:22px;'
        f'font-size:12px;font-weight:800;color:#1A1A1A;">{pct:.0f}%</span></div></div>'
    )


def render_status_bars(counts):
    max_count = max((counts[s] for s in calc.STATUS_OPTIONS), default=0) or 1
    rows = []
    for status in calc.STATUS_OPTIONS:
        count = counts[status]
        ancho = (count / max_count) * 100
        color = calc.STATUS_COLORS[status]["bg"]
        rows.append(
            '<div style="display:flex;align-items:center;gap:8px;margin:6px 0;">'
            f'<div style="width:110px;font-size:12px;font-weight:700;flex-shrink:0;">{status}</div>'
            '<div style="flex:1;background:#DDDDDD;border-radius:4px;overflow:hidden;height:18px;min-width:40px;">'
            f'<div style="background:{color};width:{ancho:.0f}%;height:100%;" '
            f'title="{status}: {count}"></div></div>'
            f'<div style="width:28px;font-size:12px;font-weight:800;text-align:right;flex-shrink:0;">{count}</div>'
            "</div>"
        )
    return "".join(rows)


def _legend_html(items):
    """items: lista de (etiqueta, valor, color)."""
    total = sum(valor for _, valor, _ in items) or 1
    rows = []
    for etiqueta, valor, color in items:
        pct = valor / total * 100
        rows.append(
            '<div style="display:flex;align-items:center;gap:8px;margin:4px 0;font-size:12px;">'
            f'<span style="width:12px;height:12px;border-radius:3px;background:{color};flex-shrink:0;"></span>'
            f'<span style="font-weight:700;">{etiqueta}</span>'
            f'<span style="margin-left:auto;opacity:0.7;">{valor} ({pct:.0f}%)</span></div>'
        )
    return "".join(rows)


def render_status_pie(counts):
    """Gráfico de torta (conic-gradient) con la distribución de actividades por Estado."""
    total = sum(counts[s] for s in calc.STATUS_OPTIONS)
    if total == 0:
        return '<p style="font-size:13px;">No hay actividades registradas.</p>'

    stops = []
    acumulado = 0
    for status in calc.STATUS_OPTIONS:
        count = counts[status]
        if count == 0:
            continue
        color = calc.STATUS_COLORS[status]["bg"]
        inicio = acumulado / total * 360
        acumulado += count
        fin = acumulado / total * 360
        stops.append(f"{color} {inicio:.2f}deg {fin:.2f}deg")
    gradient = ", ".join(stops)

    items = [(status, counts[status], calc.STATUS_COLORS[status]["bg"]) for status in calc.STATUS_OPTIONS]
    return (
        '<div style="display:flex;align-items:center;gap:28px;flex-wrap:wrap;">'
        f'<div style="width:170px;height:170px;border-radius:50%;flex-shrink:0;'
        f'background:conic-gradient({gradient});" title="Distribución de actividades por estado"></div>'
        f'<div style="min-width:180px;">{_legend_html(items)}</div></div>'
    )


def render_progress_donut(pct, size=150):
    """Gráfico de torta con anillo (donut) para el avance total del proyecto."""
    pct_clamped = max(0.0, min(100.0, pct))
    color = calc.STATUS_COLORS["Completado"]["bg"] if pct >= 100 else HEADER_BLUE
    deg = pct_clamped / 100 * 360
    hole = int(size * 0.62)
    return (
        f'<div style="width:{size}px;height:{size}px;border-radius:50%;'
        f'background:conic-gradient({color} 0deg {deg:.2f}deg, #DDDDDD {deg:.2f}deg 360deg);'
        'display:flex;align-items:center;justify-content:center;">'
        f'<div style="width:{hole}px;height:{hole}px;border-radius:50%;display:flex;'
        'align-items:center;justify-content:center;'
        'background:var(--background-color,#FFFFFF);color:var(--text-color,#1A1A1A);'
        f'font-size:{int(size*0.15)}px;font-weight:800;">{pct:.0f}%</div></div>'
    )


def render_category_bars(df_act, df_cat):
    if df_act.empty:
        return '<p style="font-size:13px;">No hay actividades registradas.</p>'
    cat_map = dict(zip(df_cat["ID"], df_cat["Nombre"])) if not df_cat.empty else {}
    df = df_act.copy()
    df["CategoriaNombre"] = df["ID_Categoria"].map(cat_map).fillna("Sin categoría")
    rows = []
    for categoria, group in df.groupby("CategoriaNombre", sort=False):
        avg = group.apply(
            lambda r: calc.avance_real_auto(r["Status"], r["Fecha_Inicio"], r["Fecha_Fin"]), axis=1
        ).mean()
        rows.append(
            '<div style="display:flex;align-items:center;gap:8px;margin:6px 0;">'
            '<div style="width:220px;font-size:12px;font-weight:700;flex-shrink:0;'
            f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="{categoria}">{categoria}</div>'
            '<div style="flex:1;background:#DDDDDD;border-radius:4px;overflow:hidden;height:18px;min-width:40px;">'
            f'<div style="background:{HEADER_BLUE};width:{avg:.0f}%;height:100%;" '
            f'title="{categoria}: {avg:.0f}%"></div></div>'
            f'<div style="width:40px;font-size:12px;font-weight:800;text-align:right;flex-shrink:0;">{avg:.0f}%</div>'
            "</div>"
        )
    return "".join(rows)


def render_historico_card(anio, total, completadas, avance_prom):
    return (
        f'<div style="background:{HEADER_BLUE};color:#FFFFFF;border-radius:10px;'
        'padding:14px 18px;margin-bottom:10px;display:flex;align-items:center;'
        'gap:24px;flex-wrap:wrap;">'
        f'<div style="font-size:24px;font-weight:800;min-width:70px;">{anio}</div>'
        '<div style="display:flex;gap:24px;flex-wrap:wrap;font-size:13px;">'
        f'<div><div style="font-weight:800;font-size:18px;">{total}</div>Actividades</div>'
        f'<div><div style="font-weight:800;font-size:18px;">{completadas}</div>Completadas</div>'
        f'<div><div style="font-weight:800;font-size:18px;">{avance_prom:.0f}%</div>Avance promedio</div>'
        "</div></div>"
    )


def render_section_title(titulo):
    return (
        f'<div style="background:{HEADER_BLUE};color:#FFFFFF;font-weight:800;'
        f'font-size:15px;padding:7px 10px;margin-top:14px;">{titulo}</div>'
    )


_FIXED_COLUMNS = [
    ("#", "38px"),
    ("Actividades", "220px"),
    ("Responsable", "120px"),
    ("Fecha Inicio", "90px"),
    ("Fecha Fin", "90px"),
    ("Días restantes", "80px"),
    ("Estado", "100px"),
    ("Avance Real %", "80px"),
    ("Avance Esperado %", "90px"),
]


def _th_fixed(label, width):
    return (
        f'<th rowspan="3" style="background:{TABLE_HEADER_BLUE};color:#FFFFFF;'
        f'font-weight:800;font-size:11px;padding:4px 6px;border:1px solid {BORDER_COLOR};'
        f'min-width:{width};vertical-align:middle;">{label}</th>'
    )


def _month_header_cells(all_days):
    cells = []
    i = 0
    while i < len(all_days):
        d = all_days[i]
        count = 1
        while i + count < len(all_days) and all_days[i + count].month == d.month and all_days[i + count].year == d.year:
            count += 1
        label = calc.MESES_ES[d.month - 1].upper()
        cells.append(
            f'<th colspan="{count}" style="background:{TABLE_HEADER_BLUE};color:#FFFFFF;'
            f'font-weight:800;font-size:11px;padding:3px;border:1px solid {BORDER_COLOR};">{label}</th>'
        )
        i += count
    return "".join(cells)


def _weekday_header_cells(all_days):
    cells = []
    for d in all_days:
        abbr = calc.WEEKDAYS_ABBR[calc.WEEKDAYS[d.weekday()]]
        cells.append(
            f'<th style="background:{TABLE_HEADER_BLUE};color:#FFFFFF;font-weight:700;'
            f'font-size:10px;padding:2px;border:1px solid {BORDER_COLOR};width:26px;">{abbr}</th>'
        )
    return "".join(cells)


def _date_header_cells(all_days):
    cells = []
    for d in all_days:
        cells.append(
            f'<th style="background:{TABLE_HEADER_BLUE};color:#FFFFFF;font-weight:600;'
            f'font-size:9px;padding:2px;border:1px solid {BORDER_COLOR};writing-mode:vertical-rl;'
            f'text-orientation:mixed;height:70px;">{calc.format_fecha(d)}</th>'
        )
    return "".join(cells)


def _day_cell(d, fecha_inicio, fecha_fin, status, dia_1, dia_2):
    in_range = fecha_inicio is not None and fecha_fin is not None and fecha_inicio <= d <= fecha_fin
    is_weekend = calc.is_non_working_day(d, dia_1, dia_2)

    if in_range and status in calc.GRID_LABELS:
        colores = calc.STATUS_COLORS[status]
        bg, text_color, label = colores["bg"], colores["text"], calc.GRID_LABELS[status]
    elif is_weekend:
        bg, text_color, label = calc.WEEKEND_COLOR, "#1A1A1A", ""
    else:
        bg, text_color, label = calc.FILL_COLOR, "#FFFFFF", ""

    return (
        f'<td style="width:26px;height:22px;text-align:center;background:{bg};'
        f'color:{text_color};font-weight:700;font-size:10px;border:1px solid {BORDER_COLOR};">'
        f'{label}</td>'
    )


def _category_day_cells(count):
    cell = f'<td style="background:{CATEGORY_GRAY};border:1px solid {BORDER_COLOR};"></td>'
    return cell * count


def render_cronograma_table(df_act, df_cat, config):
    start = config["Fecha_Inicio_Proyecto"]
    end = config["Fecha_Fin_Proyecto"]
    if start > end:
        return "<p>Rango de fechas de proyecto inválido (revisa Configuración).</p>"

    dia_1 = config["Dia_Excluido_1"]
    dia_2 = config["Dia_Excluido_2"]
    all_days = [start + timedelta(days=i) for i in range((end - start).days + 1)]

    cat_map = dict(zip(df_cat["ID"], df_cat["Nombre"])) if not df_cat.empty else {}
    df = df_act.copy()
    df["CategoriaNombre"] = df["ID_Categoria"].map(cat_map).fillna("Sin categoría")

    header_row1 = "".join(_th_fixed(label, width) for label, width in _FIXED_COLUMNS)
    header_row1 += _month_header_cells(all_days)
    header_row2 = _weekday_header_cells(all_days)
    header_row3 = _date_header_cells(all_days)

    rows_html = [
        f"<tr>{header_row1}</tr>",
        f"<tr>{header_row2}</tr>",
        f"<tr>{header_row3}</tr>",
    ]

    def td(value, extra_style=""):
        return f'<td style="border:1px solid {BORDER_COLOR};padding:3px 6px;{extra_style}">{value}</td>'

    for categoria, group in df.groupby("CategoriaNombre", sort=False):
        avance_real_prom = round(
            group.apply(
                lambda r: calc.avance_real_auto(r["Status"], r["Fecha_Inicio"], r["Fecha_Fin"]), axis=1
            ).mean(),
            0,
        )
        avance_esp_prom = round(
            group.apply(
                lambda r: calc.expected_progress(r["Fecha_Inicio"], r["Fecha_Fin"]), axis=1
            ).mean(),
            0,
        )
        row_style = f"background:{CATEGORY_GRAY};color:#1A1A1A;font-weight:700;font-size:11px;"
        cells = (
            td("", row_style) + td(categoria, row_style) + td("", row_style) + td("", row_style)
            + td("", row_style) + td("", row_style) + td("", row_style)
            + td(_progress_bar_html(avance_real_prom, HEADER_BLUE), row_style)
            + td(f"{avance_esp_prom:.0f}%", row_style)
        )
        cells += _category_day_cells(len(all_days))
        rows_html.append(f"<tr>{cells}</tr>")

        for _, act in group.iterrows():
            fecha_inicio = act["Fecha_Inicio"]
            fecha_fin = act["Fecha_Fin"]
            status = act["Status"]
            dias_rest = calc.days_remaining(fecha_fin)
            dias_texto, dias_color = calc.dias_restantes_estilo(dias_rest, status)
            dias_style = f"color:{dias_color};font-weight:700;" if dias_color else ""
            avance_real = calc.avance_real_auto(status, fecha_inicio, fecha_fin)
            avance_esperado = calc.expected_progress(fecha_inicio, fecha_fin)
            status_colors = calc.STATUS_COLORS.get(status, {"bg": "#FFFFFF", "text": "#000000"})
            status_style = (
                f'background:{status_colors["bg"]};color:{status_colors["text"]};'
                'font-weight:700;text-align:center;'
            )

            row_style = "font-size:11px;"
            cells = (
                td(int(act["#"]) if pd.notna(act["#"]) else "", row_style)
                + td(act["Nombre"], row_style + "white-space:nowrap;")
                + td(act["Responsable"], row_style)
                + td(calc.format_fecha(fecha_inicio), row_style)
                + td(calc.format_fecha(fecha_fin), row_style)
                + td(dias_texto, row_style + dias_style)
                + td(status, row_style + status_style)
                + td(_progress_bar_html(avance_real, status_colors["bg"]), row_style)
                + td(f"{avance_esperado:.0f}%", row_style)
            )
            cells += "".join(
                _day_cell(d, fecha_inicio, fecha_fin, status, dia_1, dia_2) for d in all_days
            )
            rows_html.append(f"<tr>{cells}</tr>")

    table = (
        '<div style="overflow-x:auto;">'
        '<table style="border-collapse:collapse;font-family:Segoe UI,Arial,sans-serif;">'
        + "".join(rows_html)
        + "</table></div>"
    )
    return table
