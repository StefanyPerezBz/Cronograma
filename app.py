import pandas as pd
import streamlit as st

import utils_calculos as calc
import utils_excel as xio
import utils_render as render
from ui_helpers import alerta, fecha_input_anual, flush_pending_alert, queue_alert

DIAS_ALERTA_POR_VENCER = 5

st.set_page_config(page_title="Cronograma Personal", layout="wide")
st.markdown(
    "<style>.block-container{padding-top:1rem;padding-bottom:1rem;max-width:100%;}</style>",
    unsafe_allow_html=True,
)

xio.init_excel()
anios_archivados = xio.archive_if_year_changed()
flush_pending_alert()
if anios_archivados:
    anios_txt = ", ".join(str(a) for a in anios_archivados)
    alerta(
        "info",
        f"Se archivó el cronograma del/los año(s) {anios_txt} en 'Histórico' y se "
        f"reinició el cronograma para {calc.hoy().year}.",
        toast=False,
    )

SECCIONES = ["Dashboard", "Alertas", "Gráficos", "Actividades", "Categorías", "Configuración", "Histórico"]

# Navegación basada en la URL (?tab=...) en vez de st.radio/st.tabs: no
# depende de la estructura HTML interna de Streamlit (que cambia entre
# versiones y rompe CSS hechos a medida), y al vivir en la URL sobrevive
# automáticamente a cualquier st.rerun() sin lógica extra.
active_tab = st.query_params.get("tab", SECCIONES[0])
if active_tab not in SECCIONES:
    active_tab = SECCIONES[0]

nav_cols = st.columns(len(SECCIONES))
for col, seccion in zip(nav_cols, SECCIONES):
    es_activa = seccion == active_tab
    if col.button(
        seccion,
        key=f"nav_{seccion}",
        type="primary" if es_activa else "secondary",
        use_container_width=True,
    ):
        st.query_params["tab"] = seccion
        st.rerun()
st.divider()

# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
if active_tab == "Dashboard":
    df_act = xio.load_actividades()
    df_cat = xio.load_categorias()
    config = xio.load_config()

    counts = calc.status_counts(df_act)
    counts["total"] = len(df_act)
    avance_pct = calc.project_progress(df_act)
    dias_excluidos = calc.dias_excluidos_totales(
        config["Fecha_Inicio_Proyecto"], config["Fecha_Fin_Proyecto"],
        config["Dia_Excluido_1"], config["Dia_Excluido_2"],
    )
    dur_meses = calc.duracion_meses(config["Fecha_Inicio_Proyecto"], config["Fecha_Fin_Proyecto"])
    dur_dias = calc.duracion_dias(config["Fecha_Inicio_Proyecto"], config["Fecha_Fin_Proyecto"])

    st.markdown(render.render_header_bar("CRONOGRAMA DE ACTIVIDADES"), unsafe_allow_html=True)
    st.markdown(
        render.render_date_controls(
            calc.hoy(), config["Fecha_Inicio_Proyecto"], config["Fecha_Fin_Proyecto"]
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        render.render_kpi_row(counts, avance_pct, dias_excluidos, dur_meses, dur_dias),
        unsafe_allow_html=True,
    )

    st.markdown(render.render_total_progress_bar(avance_pct), unsafe_allow_html=True)

    st.markdown(render.render_section_title("CRONOGRAMA"), unsafe_allow_html=True)
    if df_act.empty:
        st.info("Agrega actividades para ver el cronograma.")
    else:
        st.markdown(render.render_cronograma_table(df_act, df_cat, config), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Alertas
# ---------------------------------------------------------------------------
if active_tab == "Alertas":
    st.subheader("Alertas de actividades")

    df_act = xio.load_actividades()
    df_cat = xio.load_categorias()
    cat_map = dict(zip(df_cat["ID"], df_cat["Nombre"])) if not df_cat.empty else {}

    if df_act.empty:
        alerta("info", "No hay actividades registradas todavía.", toast=False)
    else:
        base = df_act.copy()
        base["Categoría"] = base["ID_Categoria"].map(cat_map).fillna("Sin categoría")
        base["Días restantes"] = base["Fecha_Fin"].apply(calc.days_remaining)
        base = base[base["Status"] != "Completado"]

        vencidas = base[base["Días restantes"] < 0].sort_values("Días restantes")
        por_vencer = base[
            (base["Días restantes"] >= 0) & (base["Días restantes"] <= DIAS_ALERTA_POR_VENCER)
        ].sort_values("Días restantes")

        def tabla_alerta(df):
            out = df.rename(columns={
                "Nombre": "Actividad", "Fecha_Fin": "Fecha fin", "Status": "Estado",
            })[["Actividad", "Categoría", "Responsable", "Fecha fin", "Días restantes", "Estado"]]
            st.dataframe(out, use_container_width=True, hide_index=True, height=min(300, 46 + 35 * len(out)))

        st.markdown(f"#### 🔴 Vencidas / atrasadas ({len(vencidas)})")
        if vencidas.empty:
            alerta("success", "No hay actividades vencidas.", toast=False)
        else:
            tabla_alerta(vencidas)

        st.markdown(f"#### 🟡 Por vencer en los próximos {DIAS_ALERTA_POR_VENCER} días ({len(por_vencer)})")
        if por_vencer.empty:
            alerta("info", "No hay actividades por vencer pronto.", toast=False)
        else:
            tabla_alerta(por_vencer)

# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------
if active_tab == "Gráficos":
    st.subheader("Gráficos del proyecto")

    df_act = xio.load_actividades()
    df_cat = xio.load_categorias()

    if df_act.empty:
        alerta("info", "Agrega actividades para ver los gráficos.", toast=False)
    else:
        avance_pct = calc.project_progress(df_act)
        counts = calc.status_counts(df_act)

        col_donut, col_pie = st.columns(2)
        with col_donut:
            st.markdown("#### Avance total del proyecto")
            st.markdown(render.render_progress_donut(avance_pct), unsafe_allow_html=True)
        with col_pie:
            st.markdown("#### Actividades por estado (torta)")
            st.markdown(render.render_status_pie(counts), unsafe_allow_html=True)

        st.markdown("#### Actividades por estado (barras)")
        st.markdown(render.render_status_bars(counts), unsafe_allow_html=True)

        st.markdown("#### Avance promedio por categoría (barras)")
        st.markdown(render.render_category_bars(df_act, df_cat), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Actividades
# ---------------------------------------------------------------------------
if active_tab == "Actividades":
    df_act = xio.load_actividades()
    df_cat = xio.load_categorias()

    st.subheader("Listado de actividades")
    if df_act.empty:
        st.info("No hay actividades registradas todavía.")
    else:
        cat_map = dict(zip(df_cat["ID"], df_cat["Nombre"])) if not df_cat.empty else {}
        display_df = df_act.copy()
        display_df["Categoría"] = display_df["ID_Categoria"].map(cat_map).fillna("Sin categoría")
        display_df["Días restantes"] = display_df["Fecha_Fin"].apply(calc.days_remaining)
        display_df["% Avance esperado"] = display_df.apply(
            lambda r: round(calc.expected_progress(r["Fecha_Inicio"], r["Fecha_Fin"]), 1), axis=1
        )
        display_df["% Avance real"] = display_df.apply(
            lambda r: calc.avance_real_auto(r["Status"], r["Fecha_Inicio"], r["Fecha_Fin"]), axis=1
        )
        display_df = display_df.rename(columns={
            "Fecha_Inicio": "Fecha inicio",
            "Fecha_Fin": "Fecha fin",
            "Status": "Estado",
        })
        cols_order = ["#", "Nombre", "Categoría", "Responsable", "Fecha inicio", "Fecha fin",
                      "Días restantes", "% Avance real", "% Avance esperado", "Estado"]
        st.dataframe(display_df[cols_order], use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Agregar / Editar actividad")

    if df_cat.empty:
        alerta("warning", "Primero crea al menos una categoría en la pestaña 'Categorías'.", toast=False)
    else:
        modo = st.radio("Modo", ["Nueva actividad", "Editar existente"], horizontal=True, key="modo_actividad")

        PLACEHOLDER = "-- Selecciona una actividad --"
        editing_row = None
        selected_id = None
        mostrar_formulario = modo == "Nueva actividad"

        if modo == "Editar existente":
            if df_act.empty:
                alerta("info", "No hay actividades para editar.", toast=False)
            else:
                opciones = {f'#{int(r["#"])} - {r["Nombre"]}': int(r["#"]) for _, r in df_act.iterrows()}
                seleccion = st.selectbox(
                    "Selecciona actividad", [PLACEHOLDER] + list(opciones.keys()), key="select_actividad_editar"
                )
                if seleccion != PLACEHOLDER:
                    selected_id = opciones[seleccion]
                    editing_row = df_act[df_act["#"] == selected_id].iloc[0]
                    mostrar_formulario = True
                else:
                    alerta("info", "Elige una actividad de la lista para ver el formulario de edición.", toast=False)

        if mostrar_formulario:
            suffix = "new" if modo == "Nueva actividad" else f"edit_{selected_id}"

            cat_nombres = df_cat["Nombre"].tolist()
            cat_ids = [int(i) for i in df_cat["ID"].tolist()]
            default_cat_idx = 0
            if editing_row is not None and pd.notna(editing_row["ID_Categoria"]):
                cat_actual = int(editing_row["ID_Categoria"])
                if cat_actual in cat_ids:
                    default_cat_idx = cat_ids.index(cat_actual)

            with st.form(f"form_actividad_{suffix}", clear_on_submit=(modo == "Nueva actividad")):
                nombre = st.text_input(
                    "Nombre", value=editing_row["Nombre"] if editing_row is not None else "",
                    key=f"nombre_{suffix}",
                )
                categoria_sel = st.selectbox(
                    "Categoría", cat_nombres, index=default_cat_idx, key=f"categoria_{suffix}"
                )
                responsable = st.text_input(
                    "Responsable", value=editing_row["Responsable"] if editing_row is not None else "",
                    key=f"responsable_{suffix}",
                )
                fecha_inicio = fecha_input_anual(
                    "Fecha inicio",
                    editing_row["Fecha_Inicio"] if editing_row is not None else calc.hoy(),
                    key=f"fecha_inicio_{suffix}",
                )
                fecha_fin = fecha_input_anual(
                    "Fecha fin",
                    editing_row["Fecha_Fin"] if editing_row is not None else calc.hoy(),
                    key=f"fecha_fin_{suffix}",
                )
                status_idx = (
                    calc.STATUS_OPTIONS.index(editing_row["Status"])
                    if editing_row is not None and editing_row["Status"] in calc.STATUS_OPTIONS
                    else 0
                )
                status = st.selectbox(
                    "Estado", calc.STATUS_OPTIONS, index=status_idx, key=f"status_{suffix}"
                )
                st.caption("El % Avance real se calcula automáticamente a partir del Estado y las fechas.")

                guardar = st.form_submit_button("Guardar")

            if guardar:
                if not nombre.strip() or not responsable.strip():
                    alerta("error", "Nombre y Responsable no pueden estar vacíos.")
                elif fecha_fin < fecha_inicio:
                    alerta("error", "La fecha fin no puede ser anterior a la fecha inicio.")
                else:
                    cat_id = cat_ids[cat_nombres.index(categoria_sel)]
                    avance_real = calc.avance_real_auto(status, fecha_inicio, fecha_fin)
                    if editing_row is not None:
                        idx = df_act.index[df_act["#"] == editing_row["#"]][0]
                        df_act.loc[idx, ["Nombre", "ID_Categoria", "Responsable", "Fecha_Inicio",
                                          "Fecha_Fin", "Avance_Real", "Status"]] = [
                            nombre.strip(), cat_id, responsable.strip(), fecha_inicio, fecha_fin, avance_real, status,
                        ]
                        xio.save_actividades(df_act)
                        queue_alert("success", f"Actividad #{int(editing_row['#'])} actualizada.")
                    else:
                        new_id = xio.next_activity_id(df_act)
                        nueva = pd.DataFrame([{
                            "#": new_id, "Nombre": nombre.strip(), "ID_Categoria": cat_id,
                            "Responsable": responsable.strip(), "Fecha_Inicio": fecha_inicio,
                            "Fecha_Fin": fecha_fin, "Avance_Real": avance_real, "Status": status,
                        }])
                        df_act = pd.concat([df_act, nueva], ignore_index=True)
                        xio.save_actividades(df_act)
                        queue_alert("success", f"Actividad #{new_id} creada.")
                    st.rerun()

            if editing_row is not None:
                st.divider()
                confirm_key = f"confirm_delete_{int(editing_row['#'])}"
                if st.button("Eliminar actividad"):
                    st.session_state[confirm_key] = True
                if st.session_state.get(confirm_key):
                    alerta(
                        "warning",
                        f"¿Confirmas eliminar la actividad #{int(editing_row['#'])} - {editing_row['Nombre']}?",
                        toast=False,
                    )
                    col_yes, col_no = st.columns(2)
                    if col_yes.button("Sí, eliminar", type="primary"):
                        df_act = df_act[df_act["#"] != editing_row["#"]]
                        xio.save_actividades(df_act)
                        st.session_state[confirm_key] = False
                        queue_alert("success", "Actividad eliminada.")
                        st.rerun()
                    if col_no.button("Cancelar"):
                        st.session_state[confirm_key] = False
                        st.rerun()

# ---------------------------------------------------------------------------
# Categorías
# ---------------------------------------------------------------------------
if active_tab == "Categorías":
    df_cat = xio.load_categorias()
    df_act = xio.load_actividades()

    st.subheader("Categorías existentes")
    if df_cat.empty:
        st.info("No hay categorías registradas todavía.")
    else:
        st.dataframe(df_cat, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Nueva categoría")
    with st.form("form_nueva_categoria", clear_on_submit=True):
        nombre_nueva = st.text_input("Nombre de categoría")
        crear = st.form_submit_button("Crear categoría")
    if crear:
        if not nombre_nueva.strip():
            alerta("error", "El nombre no puede estar vacío.")
        elif not df_cat.empty and nombre_nueva.strip().lower() in df_cat["Nombre"].str.lower().values:
            alerta("error", "Ya existe una categoría con ese nombre.")
        else:
            new_id = 1 if df_cat.empty else int(df_cat["ID"].max()) + 1
            nueva = pd.DataFrame([{"ID": new_id, "Nombre": nombre_nueva.strip()}])
            df_cat = pd.concat([df_cat, nueva], ignore_index=True)
            xio.save_categorias(df_cat)
            queue_alert("success", f"Categoría '{nombre_nueva.strip()}' creada.")
            st.rerun()

    st.divider()
    st.subheader("Editar / eliminar categoría")
    if df_cat.empty:
        st.info("No hay categorías para editar.")
    else:
        opciones = {r["Nombre"]: int(r["ID"]) for _, r in df_cat.iterrows()}
        seleccion = st.selectbox("Selecciona categoría", list(opciones.keys()), key="cat_selector")
        cat_id_sel = opciones[seleccion]
        cat_row = df_cat[df_cat["ID"] == cat_id_sel].iloc[0]

        with st.form("form_editar_categoria"):
            nuevo_nombre = st.text_input("Nombre", value=cat_row["Nombre"])
            actualizar = st.form_submit_button("Actualizar nombre")
        if actualizar:
            if not nuevo_nombre.strip():
                alerta("error", "El nombre no puede estar vacío.")
            else:
                idx = df_cat.index[df_cat["ID"] == cat_id_sel][0]
                df_cat.loc[idx, "Nombre"] = nuevo_nombre.strip()
                xio.save_categorias(df_cat)
                queue_alert("success", "Categoría actualizada.")
                st.rerun()

        n_actividades = int((df_act["ID_Categoria"] == cat_id_sel).sum()) if not df_act.empty else 0
        if st.button("Eliminar categoría"):
            if n_actividades > 0:
                alerta(
                    "error",
                    f"No se puede eliminar: {n_actividades} actividad(es) usan esta categoría. "
                    "Reasigna o elimina esas actividades primero.",
                    toast=False,
                )
            else:
                df_cat = df_cat[df_cat["ID"] != cat_id_sel]
                xio.save_categorias(df_cat)
                queue_alert("success", "Categoría eliminada.")
                st.rerun()

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
if active_tab == "Configuración":
    config = xio.load_config()
    st.subheader("Configuración del proyecto")
    st.caption(f"El cronograma es anual: todas las fechas usan el año {calc.hoy().year}.")

    with st.form("form_config"):
        fecha_inicio_proj = fecha_input_anual(
            "Fecha inicio del proyecto", config["Fecha_Inicio_Proyecto"], key="config_fecha_inicio"
        )
        fecha_fin_proj = fecha_input_anual(
            "Fecha fin del proyecto", config["Fecha_Fin_Proyecto"], key="config_fecha_fin"
        )
        col_d1, col_d2 = st.columns(2)
        dia_excl_1 = col_d1.selectbox(
            "Día no laborable 1", calc.WEEKDAYS, index=calc.WEEKDAYS.index(config["Dia_Excluido_1"])
        )
        dia_excl_2 = col_d2.selectbox(
            "Día no laborable 2", calc.WEEKDAYS, index=calc.WEEKDAYS.index(config["Dia_Excluido_2"])
        )
        guardar_config = st.form_submit_button("Guardar configuración")

    if guardar_config:
        if fecha_fin_proj < fecha_inicio_proj:
            alerta("error", "La fecha fin del proyecto no puede ser anterior a la fecha inicio.")
        else:
            xio.save_config({
                "Fecha_Inicio_Proyecto": fecha_inicio_proj,
                "Fecha_Fin_Proyecto": fecha_fin_proj,
                "Dia_Excluido_1": dia_excl_1,
                "Dia_Excluido_2": dia_excl_2,
            })
            queue_alert("success", "Configuración guardada.")
            st.rerun()

# ---------------------------------------------------------------------------
# Histórico
# ---------------------------------------------------------------------------
if active_tab == "Histórico":
    st.subheader("Cronogramas de años anteriores")

    df_hist = xio.load_historico()
    if df_hist.empty:
        alerta(
            "info",
            "Todavía no hay cronogramas archivados. Esto se llena automáticamente "
            "cuando termina un año y comienza el siguiente.",
            toast=False,
        )
    else:
        for anio, grupo in sorted(df_hist.groupby("Año"), key=lambda x: x[0], reverse=True):
            total = len(grupo)
            completadas = int((grupo["Status"] == "Completado").sum())
            avance_prom = round(float(grupo["Avance_Real"].astype(float).mean()), 0)
            st.markdown(
                render.render_historico_card(int(anio), total, completadas, avance_prom),
                unsafe_allow_html=True,
            )
            with st.expander(f"Ver actividades de {int(anio)}"):
                detalle = grupo.rename(columns={
                    "Nombre": "Actividad", "Categoria_Nombre": "Categoría",
                    "Fecha_Inicio": "Fecha inicio", "Fecha_Fin": "Fecha fin",
                    "Avance_Real": "% Avance real", "Status": "Estado",
                })[["Actividad", "Categoría", "Responsable", "Fecha inicio", "Fecha fin",
                    "% Avance real", "Estado"]]
                st.dataframe(detalle, use_container_width=True, hide_index=True)