# ======================================================
# DASHBOARD STREAMLIT - PROYECCIÓN POBLACIONAL
# ======================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from modelo_poblacional import generar_datos


# ======================================================
# 1. Configuración general de la página
# ======================================================

st.set_page_config(
    page_title="Dashboard Poblacional Carreras",
    page_icon="📊",
    layout="wide"
)


# ======================================================
# 2. Cargar datos desde el modelo
# ======================================================

@st.cache_data(show_spinner="Generando datos del modelo poblacional...")
def cargar_datos():
    """
    Ejecuta el modelo poblacional y trae las tres tablas principales:
    - df_completo
    - alertas_df
    - df_score
    """
    df_completo, alertas_df, df_score = generar_datos()
    return df_completo, alertas_df, df_score


df_completo, alertas_df, df_score = cargar_datos()


# ======================================================
# 3. Preparar columnas
# ======================================================

df_completo = df_completo.copy()
alertas_df = alertas_df.copy()
df_score = df_score.copy()

df_completo["Periodo"] = pd.to_numeric(df_completo["Periodo"], errors="coerce")
df_completo["Carrera"] = df_completo["Carrera"].astype(str)

alertas_df["Carrera"] = alertas_df["Carrera"].astype(str)

if "CarreraHomologada" in df_score.columns:
    df_score = df_score.rename(columns={"CarreraHomologada": "Carrera"})

df_score["Carrera"] = df_score["Carrera"].astype(str)


# ======================================================
# 4. Título principal
# ======================================================

st.title("📊 Dashboard de Proyección Poblacional de Carreras")

st.markdown(
    """
    Este dashboard muestra el histórico y la proyección futura de enrollment, 
    nuevos ingresos, desertores, graduados, alertas de caída y score de salud por carrera.
    """
)


# ======================================================
# 5. Sidebar de filtros
# ======================================================

st.sidebar.header("Filtros")

carreras_disponibles = sorted(df_completo["Carrera"].dropna().unique())

carrera_seleccionada = st.sidebar.selectbox(
    "Selecciona una carrera",
    carreras_disponibles
)

origenes_disponibles = sorted(df_completo["Origen"].dropna().unique())

origenes_seleccionados = st.sidebar.multiselect(
    "Origen de datos",
    origenes_disponibles,
    default=origenes_disponibles
)

periodo_min = int(df_completo["Periodo"].min())
periodo_max = int(df_completo["Periodo"].max())

rango_periodos = st.sidebar.slider(
    "Rango de periodos",
    min_value=periodo_min,
    max_value=periodo_max,
    value=(periodo_min, periodo_max),
    step=10
)


# ======================================================
# 6. Filtrar información
# ======================================================

df_filtrado = df_completo[
    (df_completo["Carrera"] == carrera_seleccionada) &
    (df_completo["Origen"].isin(origenes_seleccionados)) &
    (df_completo["Periodo"] >= rango_periodos[0]) &
    (df_completo["Periodo"] <= rango_periodos[1])
].copy()

alerta_carrera = alertas_df[
    alertas_df["Carrera"] == carrera_seleccionada
].copy()

score_carrera = df_score[
    df_score["Carrera"] == carrera_seleccionada
].copy()


# ======================================================
# 7. KPIs superiores
# ======================================================

st.subheader(f"Carrera seleccionada: {carrera_seleccionada}")

if not alerta_carrera.empty:
    tipo_alerta = alerta_carrera["Tipo_Alerta"].iloc[0]
    enrollment_base = alerta_carrera["Enrollment_Base"].iloc[0]
    enrollment_proyectado = alerta_carrera["Enrollment_Proyectado"].iloc[0]
    incremento_necesario = alerta_carrera["Incremento_Necesario"].iloc[0]

    ingresos_c10 = alerta_carrera.get(
        "Ingresos_Adicionales_C10_Total",
        pd.Series([0])
    ).iloc[0]

    ingresos_c20 = alerta_carrera.get(
        "Ingresos_Adicionales_C20_Total",
        pd.Series([0])
    ).iloc[0]

    col_periodo_caida = [
        c for c in alerta_carrera.columns
        if "Periodo_Caida_75" in c
    ]

    if len(col_periodo_caida) > 0:
        periodo_caida_75 = alerta_carrera[col_periodo_caida[0]].iloc[0]
    else:
        periodo_caida_75 = None

    if pd.isna(periodo_caida_75):
        periodo_caida_75 = "No aplica"
else:
    tipo_alerta = "Sin información"
    enrollment_base = 0
    enrollment_proyectado = 0
    incremento_necesario = 0
    ingresos_c10 = 0
    ingresos_c20 = 0
    periodo_caida_75 = "No aplica"


if not score_carrera.empty:
    score_salud = score_carrera["Score_Salud_Final"].iloc[0]
    categoria_score = score_carrera["Categoria_Score"].iloc[0]
else:
    score_salud = None
    categoria_score = "Sin score"


kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.metric(
        label="Tipo de alerta",
        value=tipo_alerta
    )

with kpi2:
    st.metric(
        label="Enrollment base",
        value=f"{enrollment_base:,.0f}"
    )

with kpi3:
    st.metric(
        label="Enrollment proyectado",
        value=f"{enrollment_proyectado:,.0f}"
    )

with kpi4:
    st.metric(
        label="Incremento necesario",
        value=f"{incremento_necesario:,.0f}"
    )

with kpi5:
    if score_salud is not None:
        st.metric(
            label=f"{categoria_score}",
            value=f"{score_salud:,.2f}"
        )
    else:
        st.metric(
            label="Score de salud",
            value="Sin datos"
        )


# ======================================================
# 8. Segunda fila de KPIs
# ======================================================

kpi6, kpi7, kpi8 = st.columns(3)

with kpi6:
    st.metric(
        label="Ingresos adicionales Ciclo 10",
        value=f"{ingresos_c10:,.0f}"
    )

with kpi7:
    st.metric(
        label="Ingresos adicionales Ciclo 20",
        value=f"{ingresos_c20:,.0f}"
    )

with kpi8:
    st.metric(
        label="Periodo primera caída 75%",
        value=periodo_caida_75
    )


# ======================================================
# 9. Gráfico principal: histórico y proyección
# ======================================================

st.subheader("Histórico y proyección por carrera")

df_plot = df_filtrado[[
    "Periodo",
    "Origen",
    "Nuevos_Ingresos",
    "Total_Desertores",
    "Total_Graduados",
    "Total_Vivos",
    "Total_Enrollment"
]].copy()

df_plot = df_plot.rename(columns={
    "Nuevos_Ingresos": "Nuevos ingresos",
    "Total_Desertores": "Desertores",
    "Total_Graduados": "Graduados y egresados",
    "Total_Vivos": "Estudiantes activos",
    "Total_Enrollment": "Enrollment total"
})

df_long = df_plot.melt(
    id_vars=["Periodo", "Origen"],
    value_vars=[
        "Nuevos ingresos",
        "Desertores",
        "Graduados y egresados",
        "Estudiantes activos",
        "Enrollment total"
    ],
    var_name="Indicador",
    value_name="Valor"
)

fig_principal = px.line(
    df_long,
    x="Periodo",
    y="Valor",
    color="Indicador",
    markers=True,
    title=f"Evolución histórica y proyectada - {carrera_seleccionada}"
)

fig_principal.add_vline(
    x=202610,
    line_width=2,
    line_dash="dash",
    line_color="gray"
)

fig_principal.add_annotation(
    x=202620,
    y=df_long["Valor"].max() if not df_long.empty else 0,
    text="Inicio proyección",
    showarrow=False,
    yshift=15
)

fig_principal.update_layout(
    height=520,
    xaxis_title="Periodo",
    yaxis_title="Cantidad de estudiantes",
    legend_title="Indicador",
    hovermode="x unified"
)

st.plotly_chart(fig_principal, use_container_width=True)


# ======================================================
# 10. Gráfico de enrollment total
# ======================================================

col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("Enrollment total")

    fig_enrollment = px.bar(
        df_filtrado,
        x="Periodo",
        y="Total_Enrollment",
        color="Origen",
        title="Enrollment histórico y proyectado",
        text_auto=True
    )

    fig_enrollment.update_layout(
        height=430,
        xaxis_title="Periodo",
        yaxis_title="Enrollment total",
        legend_title="Origen"
    )

    st.plotly_chart(fig_enrollment, use_container_width=True)


# ======================================================
# 11. Gráfico de composición: nuevos, desertores y graduados
# ======================================================

with col_g2:
    st.subheader("Composición por periodo")

    df_comp = df_filtrado[[
        "Periodo",
        "Nuevos_Ingresos",
        "Total_Desertores",
        "Total_Graduados"
    ]].copy()

    df_comp = df_comp.rename(columns={
        "Nuevos_Ingresos": "Nuevos ingresos",
        "Total_Desertores": "Desertores",
        "Total_Graduados": "Graduados y egresados"
    })

    df_comp_long = df_comp.melt(
        id_vars="Periodo",
        var_name="Indicador",
        value_name="Valor"
    )

    fig_comp = px.bar(
        df_comp_long,
        x="Periodo",
        y="Valor",
        color="Indicador",
        barmode="group",
        title="Nuevos ingresos, desertores y graduados"
    )

    fig_comp.update_layout(
        height=430,
        xaxis_title="Periodo",
        yaxis_title="Cantidad",
        legend_title="Indicador"
    )

    st.plotly_chart(fig_comp, use_container_width=True)


# ======================================================
# 12. Alertas generales por carrera
# ======================================================

st.subheader("Mapa de alertas por carrera")

alertas_resumen = alertas_df.copy()

fig_alertas = px.bar(
    alertas_resumen.sort_values("Proporcion_Final_vs_Base"),
    x="Carrera",
    y="Proporcion_Final_vs_Base",
    color="Tipo_Alerta",
    title="Proporción final vs base por carrera"
)

fig_alertas.update_layout(
    height=520,
    xaxis_title="Carrera",
    yaxis_title="Proporción final vs base",
    legend_title="Tipo de alerta",
    xaxis_tickangle=-45
)

st.plotly_chart(fig_alertas, use_container_width=True)


# ======================================================
# 13. Score de salud de carreras
# ======================================================

st.subheader("Score de salud de carreras")

if "Score_Salud_Final" in df_score.columns:
    df_score_plot = df_score.sort_values("Score_Salud_Final", ascending=False).copy()

    fig_score = px.bar(
        df_score_plot,
        x="Carrera",
        y="Score_Salud_Final",
        color="Categoria_Score",
        title="Score de salud por carrera",
        text="Score_Salud_Final"
    )

    fig_score.update_layout(
        height=520,
        xaxis_title="Carrera",
        yaxis_title="Score de salud",
        legend_title="Categoría",
        xaxis_tickangle=-45
    )

    st.plotly_chart(fig_score, use_container_width=True)
else:
    st.warning("No se encontró la columna Score_Salud_Final en df_score.")


# ======================================================
# 14. Tabla resumen de la carrera seleccionada
# ======================================================

st.subheader("Detalle de la carrera seleccionada")

with st.expander("Ver histórico y proyección"):
    st.dataframe(
        df_filtrado.sort_values("Periodo"),
        use_container_width=True
    )

with st.expander("Ver alerta de la carrera"):
    st.dataframe(
        alerta_carrera,
        use_container_width=True
    )

with st.expander("Ver score de la carrera"):
    st.dataframe(
        score_carrera,
        use_container_width=True
    )


# ======================================================
# 15. Botón para refrescar datos
# ======================================================

st.sidebar.markdown("---")

if st.sidebar.button("Actualizar datos"):
    st.cache_data.clear()
    st.rerun()
