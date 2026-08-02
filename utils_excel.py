import os
from datetime import date

import pandas as pd

import utils_calculos as calc

EXCEL_FILE = "cronograma.xlsx"

SHEET_ACTIVIDADES = "Actividades"
SHEET_CATEGORIAS = "Categorías"
SHEET_CONFIG = "Config"
SHEET_HISTORICO = "Historico"

COLS_ACTIVIDADES = [
    "#", "Nombre", "ID_Categoria", "Responsable",
    "Fecha_Inicio", "Fecha_Fin", "Avance_Real", "Status",
]
COLS_CATEGORIAS = ["ID", "Nombre"]
COLS_CONFIG = ["Fecha_Inicio_Proyecto", "Fecha_Fin_Proyecto", "Dia_Excluido_1", "Dia_Excluido_2"]
COLS_HISTORICO = [
    "Año", "#", "Nombre", "Categoria_Nombre", "Responsable",
    "Fecha_Inicio", "Fecha_Fin", "Avance_Real", "Status",
]


def init_excel(path=EXCEL_FILE):
    if os.path.exists(path):
        return
    df_act = pd.DataFrame(columns=COLS_ACTIVIDADES)
    df_cat = pd.DataFrame(columns=COLS_CATEGORIAS)
    df_cfg = pd.DataFrame([{
        "Fecha_Inicio_Proyecto": pd.Timestamp(date(calc.hoy().year, 1, 1)),
        "Fecha_Fin_Proyecto": pd.Timestamp(date(calc.hoy().year, 12, 31)),
        "Dia_Excluido_1": "Sábado",
        "Dia_Excluido_2": "Domingo",
    }])
    df_hist = pd.DataFrame(columns=COLS_HISTORICO)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df_act.to_excel(writer, sheet_name=SHEET_ACTIVIDADES, index=False)
        df_cat.to_excel(writer, sheet_name=SHEET_CATEGORIAS, index=False)
        df_cfg.to_excel(writer, sheet_name=SHEET_CONFIG, index=False)
        df_hist.to_excel(writer, sheet_name=SHEET_HISTORICO, index=False)


def _save_sheet(df, sheet_name, path=EXCEL_FILE):
    init_excel(path)
    with pd.ExcelWriter(path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)


def load_actividades(path=EXCEL_FILE):
    init_excel(path)
    df = pd.read_excel(path, sheet_name=SHEET_ACTIVIDADES)
    for col in COLS_ACTIVIDADES:
        if col not in df.columns:
            df[col] = None
    df = df[COLS_ACTIVIDADES].copy()
    if not df.empty:
        df["Fecha_Inicio"] = pd.to_datetime(df["Fecha_Inicio"]).dt.date
        df["Fecha_Fin"] = pd.to_datetime(df["Fecha_Fin"]).dt.date
        df["#"] = pd.to_numeric(df["#"], errors="coerce").astype("Int64")
        df["ID_Categoria"] = pd.to_numeric(df["ID_Categoria"], errors="coerce").astype("Int64")
        df["Avance_Real"] = pd.to_numeric(df["Avance_Real"], errors="coerce").fillna(0)
    return df


def save_actividades(df, path=EXCEL_FILE):
    _save_sheet(df, SHEET_ACTIVIDADES, path)


def load_categorias(path=EXCEL_FILE):
    init_excel(path)
    df = pd.read_excel(path, sheet_name=SHEET_CATEGORIAS)
    for col in COLS_CATEGORIAS:
        if col not in df.columns:
            df[col] = None
    df = df[COLS_CATEGORIAS].copy()
    if not df.empty:
        df["ID"] = pd.to_numeric(df["ID"], errors="coerce").astype("Int64")
    return df


def save_categorias(df, path=EXCEL_FILE):
    _save_sheet(df, SHEET_CATEGORIAS, path)


def load_config(path=EXCEL_FILE):
    init_excel(path)
    df = pd.read_excel(path, sheet_name=SHEET_CONFIG)
    if df.empty:
        return {
            "Fecha_Inicio_Proyecto": calc.hoy(),
            "Fecha_Fin_Proyecto": calc.hoy(),
            "Dia_Excluido_1": "Sábado",
            "Dia_Excluido_2": "Domingo",
        }
    row = df.iloc[0]
    return {
        "Fecha_Inicio_Proyecto": pd.to_datetime(row["Fecha_Inicio_Proyecto"]).date(),
        "Fecha_Fin_Proyecto": pd.to_datetime(row["Fecha_Fin_Proyecto"]).date(),
        "Dia_Excluido_1": row.get("Dia_Excluido_1", "Sábado") if pd.notna(row.get("Dia_Excluido_1")) else "Sábado",
        "Dia_Excluido_2": row.get("Dia_Excluido_2", "Domingo") if pd.notna(row.get("Dia_Excluido_2")) else "Domingo",
    }


def save_config(config, path=EXCEL_FILE):
    df = pd.DataFrame([{
        "Fecha_Inicio_Proyecto": pd.Timestamp(config["Fecha_Inicio_Proyecto"]),
        "Fecha_Fin_Proyecto": pd.Timestamp(config["Fecha_Fin_Proyecto"]),
        "Dia_Excluido_1": config["Dia_Excluido_1"],
        "Dia_Excluido_2": config["Dia_Excluido_2"],
    }])
    _save_sheet(df, SHEET_CONFIG, path)


def next_activity_id(df):
    if df.empty:
        return 1
    return int(pd.to_numeric(df["#"], errors="coerce").max()) + 1


def load_historico(path=EXCEL_FILE):
    init_excel(path)
    try:
        df = pd.read_excel(path, sheet_name=SHEET_HISTORICO)
    except ValueError:
        # Archivo creado antes de que existiera la hoja "Historico".
        df = pd.DataFrame(columns=COLS_HISTORICO)
        _save_sheet(df, SHEET_HISTORICO, path)
    for col in COLS_HISTORICO:
        if col not in df.columns:
            df[col] = None
    df = df[COLS_HISTORICO].copy()
    if not df.empty:
        df["Año"] = pd.to_numeric(df["Año"], errors="coerce").astype("Int64")
        df["Fecha_Inicio"] = pd.to_datetime(df["Fecha_Inicio"]).dt.date
        df["Fecha_Fin"] = pd.to_datetime(df["Fecha_Fin"]).dt.date
        df["Avance_Real"] = pd.to_numeric(df["Avance_Real"], errors="coerce").fillna(0)
    return df


def save_historico(df, path=EXCEL_FILE):
    _save_sheet(df, SHEET_HISTORICO, path)


def archive_if_year_changed(path=EXCEL_FILE):
    """Si el año del proyecto configurado ya pasó, archiva sus actividades en
    'Historico' y reinicia Actividades/Config para el año actual. Devuelve
    la lista de años archivados (vacía si no hizo falta)."""
    anio_hoy = calc.hoy().year
    anios_archivados = []

    config = load_config(path)
    while config["Fecha_Fin_Proyecto"].year < anio_hoy:
        anio_cerrado = config["Fecha_Fin_Proyecto"].year

        df_act = load_actividades(path)
        if not df_act.empty:
            df_cat = load_categorias(path)
            cat_map = dict(zip(df_cat["ID"], df_cat["Nombre"])) if not df_cat.empty else {}
            df_archivo = pd.DataFrame({
                "Año": anio_cerrado,
                "#": df_act["#"],
                "Nombre": df_act["Nombre"],
                "Categoria_Nombre": df_act["ID_Categoria"].map(cat_map).fillna("Sin categoría"),
                "Responsable": df_act["Responsable"],
                "Fecha_Inicio": df_act["Fecha_Inicio"],
                "Fecha_Fin": df_act["Fecha_Fin"],
                "Avance_Real": df_act["Avance_Real"],
                "Status": df_act["Status"],
            })
            df_historico = load_historico(path)
            df_historico = pd.concat([df_historico, df_archivo], ignore_index=True)
            save_historico(df_historico, path)

        save_actividades(pd.DataFrame(columns=COLS_ACTIVIDADES), path)

        nuevo_anio = anio_cerrado + 1
        config = {
            "Fecha_Inicio_Proyecto": date(nuevo_anio, 1, 1),
            "Fecha_Fin_Proyecto": date(nuevo_anio, 12, 31),
            "Dia_Excluido_1": config["Dia_Excluido_1"],
            "Dia_Excluido_2": config["Dia_Excluido_2"],
        }
        save_config(config, path)
        anios_archivados.append(anio_cerrado)

    return anios_archivados
