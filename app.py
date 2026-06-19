# ======================================================
# DASHBOARD STREAMLIT - PROYECCIÓN POBLACIONAL
# ======================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata
from pathlib import Path

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
# 2. Constantes
# ======================================================

OPCION_TODAS = "TODAS LAS CARRERAS"
ARCHIVO_MERCADO = "Crecimiento New Enrollment Porcentajes (1).xlsx"


# ======================================================
# 3. Funciones auxiliares
# ======================================================

def normalizar_texto(texto):
    """
    Normaliza textos para cruzar nombres de carreras aunque tengan tildes,
    mayúsculas, espacios extra o diferencias menores.
    """
    if pd.isna(texto):
        return ""

    texto = str(texto).upper().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join([c for c in texto if not unicodedata.combining(c)])
    texto = " ".join(texto.split())

    return texto


def buscar_columna(df, posibles_nombres):
    """
    Busca una columna en un DataFrame usando nombres normalizados.
    """
    columnas_normalizadas = {
        normalizar_texto(col): col
        for col in df.columns
    }

    for nombre in posibles_nombres:
        nombre_norm = normalizar_texto(nombre)
        if nombre_norm in columnas_normalizadas:
            return columnas_normalizadas[nombre_norm]

    return None


def formatear_periodo(periodo):
    """
    Convierte periodos tipo 202610 en 2026.10.
    También corrige valores tipo 203120.0.
    """
    if pd.isna(periodo):
        return "No aplica"

    periodo = int(float(periodo))
    anio = periodo // 100
    ciclo = periodo % 100

    return f"{anio}.{ciclo:02d}"


def formatear_numero(valor):
    """
    Formatea números para tarjetas KPI.
    """
    if pd.isna(valor):
        return "0"

    return f"{float(valor):,.0f}"


def clasificar_alerta_por_proporcion(p):
    """
    Clasifica alerta a partir de proporción final/base.
    """
    if pd.isna(p):
        return "Sin información"
    elif p >= 1.0:
        return "Sin caída"
    elif 0.75 <= p < 1.0:
        return "Caída leve"
    elif 0.5 < p < 0.75:
        return "Caída moderada"
    else:
        return "Caída severa"


def categorizar_score_por_valor(score):
    """
    Categoriza score numérico.
    """
    if pd.isna(score):
        return "Sin score"
    elif score < 33.33:
        return "Score Bajo"
    elif score < 66.66:
        return "Score Medio"
    else:
        return "Score Alto"


# ======================================================
# 4. Funciones de colores para KPIs
# ======================================================

def color_tipo_alerta(tipo_alerta):
    """
    Semáforo para tipo de alerta.
    """
    if tipo_alerta == "Caída severa":
        return "#C62828"
    elif tipo_alerta == "Caída moderada":
        return "#EF6C00"
    elif tipo_alerta == "Caída leve":
        return "#F9A825"
    elif tipo_alerta == "Sin caída":
        return "#2E7D32"
    else:
        return "#616161"


def color_score(categoria_score):
    """
    Semáforo para score de salud.
    """
    if categoria_score == "Score Bajo":
        return "#C62828"
    elif categoria_score == "Score Medio":
        return "#EF6C00"
    elif categoria_score == "Score Alto":
        return "#2E7D32"
    else:
        return "#616161"


def color_periodo_caida(periodo):
    """
    Semáforo para el periodo de primera caída al 75%.

    Rojo: hasta 2030.20
    Naranja: desde 2031.10 hasta 2040.20
    Verde: desde 2041.10 en adelante
    """
    if pd.isna(periodo):
        return "#2E7D32"

    periodo = int(float(periodo))

    if periodo <= 203020:
        return "#C62828"
    elif 203110 <= periodo <= 204020:
        return "#EF6C00"
    elif periodo >= 204110:
        return "#2E7D32"
    else:
        return "#616161"


def color_categoria_mercado(categoria):
    """
    Semáforo para categoría de mercado UDLA vs competencia.
    """
    categoria_norm = normalizar_texto(categoria)

    if categoria_norm in ["SIN INFORMACION", "SIN INFORMACIÓN", ""]:
        return "#616161"

    if "UDLA CRECE" in categoria_norm and "MERCADO CAE" in categoria_norm:
        return "#2E7D32"

    if "UDLA CRECE" in categoria_norm and "MERCADO CRECE" in categoria_norm:
        return "#1565C0"

    if "UDLA SE MANTIENE" in categoria_norm:
        return "#F9A825"

    if "LOS DOS CAEN" in categoria_norm:
        return "#C62828"

    if "UDLA CAE" in categoria_norm and "MERCADO CRECE" in categoria_norm:
        return "#C62828"

    if "UDLA CAE" in categoria_norm:
        return "#EF6C00"

    return "#616161"


def tarjeta_kpi(titulo, valor, color="#262730", subtitulo=None):
    """
    Crea una tarjeta KPI con color personalizado.
    """
    subtitulo_html = ""

    if subtitulo is not None:
        subtitulo_html = f"""
        <div style="
            font-size: 0.85rem;
            color: #6B7280;
            margin-top: 4px;
        ">
            {subtitulo}
        </div>
        """

    st.markdown(
        f"""
        <div style="
            background-color: #FFFFFF;
            border-radius: 14px;
            padding: 18px 20px;
            border-left: 8px solid {color};
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            min-height: 130px;
            margin-bottom: 12px;
        ">
            <div style="
                font-size: 0.95rem;
                color: #374151;
                margin-bottom: 10px;
                font-weight: 500;
            ">
                {titulo}
            </div>
            <div style="
                font-size: 2.1rem;
                color: {color};
                font-weight: 700;
                line-height: 1.1;
                overflow-wrap: anywhere;
            ">
                {valor}
            </div>
            {subtitulo_html}
        </div>
        """,
        unsafe_allow_html=True
    )


# ======================================================
# 5. Cargar datos
# ======================================================

@st.cache_data(show_spinner="Generando datos del modelo poblacional...")
def cargar_datos():
    df_completo, alertas_df, df_score = generar_datos()
    return df_completo, alertas_df, df_score


@st.cache_data(show_spinner="Cargando información de mercado...")
def cargar_datos_mercado():
    """
    Carga el Excel de mercado que está en la raíz del proyecto.
    Debe contener una columna de carrera y una columna llamada Categoria/Categoría.
    """
    ruta_base = Path(__file__).resolve().parent
    ruta_excel = ruta_base / ARCHIVO_MERCADO

    if not ruta_excel.exists():
        posibles = list(ruta_base.glob("*Crecimiento*Enrollment*.xlsx"))
        if posibles:
            ruta_excel = posibles[0]
        else:
            return pd.DataFrame(columns=["Carrera", "Categoria_Mercado", "Carrera_Key"])

    df_mercado = pd.read_excel(ruta_excel)

    col_carrera = buscar_columna(
        df_mercado,
        ["carrera", "Carrera", "CarreraHomologada", "Carrera Homologada"]
    )

    col_categoria = buscar_columna(
        df_mercado,
        ["categoria", "categoría", "Categoria", "Categoría"]
    )

    if col_carrera is None or col_categoria is None:
        return pd.DataFrame(columns=["Carrera", "Categoria_Mercado", "Carrera_Key"])

    df_mercado = df_mercado[[col_carrera, col_categoria]].copy()

    df_mercado = df_mercado.rename(columns={
        col_carrera: "Carrera",
        col_categoria: "Categoria_Mercado"
    })

    df_mercado["Carrera"] = df_mercado["Carrera"].astype(str)
    df_mercado["Categoria_Mercado"] = df_mercado["Categoria_Mercado"].astype(str)
    df_mercado["Carrera_Key"] = df_mercado["Carrera"].apply(normalizar_texto)

    df_mercado = df_mercado.drop_duplicates(subset=["Carrera_Key"])

    return df_mercado


df_completo, alertas_df, df_score = cargar_datos()
df_mercado = cargar_datos_mercado()


# ======================================================
# 6. Preparar columnas
# ======================================================

df_completo = df_completo.copy()
alertas_df = alertas_df.copy()
df_score = df_score.copy()
df_mercado = df_mercado.copy()

df_completo["Periodo"] = pd.to_numeric(df_completo["Periodo"], errors="coerce")
df_completo = df_completo.dropna(subset=["Periodo"]).copy()
df_completo["Periodo"] = df_completo["Periodo"].astype(int)

df_completo["Periodo_Label"] = df_completo["Periodo"].apply(formatear_periodo)
df_completo["Carrera"] = df_completo["Carrera"].astype(str)
df_completo["Carrera_Key"] = df_completo["Carrera"].apply(normalizar_texto)

periodos_globales = sorted(df_completo["Periodo"].dropna().astype(int).unique())
periodo_a_orden = {periodo: i for i, periodo in enumerate(periodos_globales)}

df_completo["Periodo_Orden"] = df_completo["Periodo"].map(periodo_a_orden)

alertas_df["Carrera"] = alertas_df["Carrera"].astype(str)
alertas_df["Carrera_Key"] = alertas_df["Carrera"].apply(normalizar_texto)

if "CarreraHomologada" in df_score.columns:
    df_score = df_score.rename(columns={"CarreraHomologada": "Carrera"})

df_score["Carrera"] = df_score["Carrera"].astype(str)
df_score["Carrera_Key"] = df_score["Carrera"].apply(normalizar_texto)


# ======================================================
# 7. Título principal
# ======================================================

st.title("📊 Dashboard de Proyección Poblacional de Carreras")

st.markdown(
    """
    Este dashboard muestra el histórico y la proyección futura de enrollment, 
    nuevos ingresos, desertores, graduados, alertas de caída, score de salud 
    y categoría de mercado frente a la competencia.
    """
)


# ======================================================
# 8. Sidebar de filtros
# ======================================================

st.sidebar.header("Filtros")

carreras_disponibles = [OPCION_TODAS] + sorted(
    df_completo["Carrera"].dropna().unique()
)

carrera_seleccionada = st.sidebar.selectbox(
    "Selecciona una carrera",
    carreras_disponibles
)

es_general = carrera_seleccionada == OPCION_TODAS

origenes_disponibles = sorted(df_completo["Origen"].dropna().unique())

origenes_seleccionados = st.sidebar.multiselect(
    "Origen de datos",
    origenes_disponibles,
    default=origenes_disponibles
)

rango_periodos = st.sidebar.select_slider(
    "Rango de periodos",
    options=periodos_globales,
    value=(periodos_globales[0], periodos_globales[-1]),
    format_func=formatear_periodo
)


# ======================================================
# 9. Filtrar información
# ======================================================

df_base_filtrada = df_completo[
    (df_completo["Origen"].isin(origenes_seleccionados)) &
    (df_completo["Periodo"] >= rango_periodos[0]) &
    (df_completo["Periodo"] <= rango_periodos[1])
].copy()

if es_general:
    columnas_sumar = [
        "Nuevos_Ingresos",
        "Total_Desertores",
        "Total_Graduados",
        "Total_Vivos",
        "Total_Enrollment",
        "Sobrevivientes"
    ]

    columnas_sumar = [
        c for c in columnas_sumar
        if c in df_base_filtrada.columns
    ]

    df_filtrado = (
        df_base_filtrada
        .groupby(
            ["Periodo", "Periodo_Label", "Periodo_Orden", "Origen"],
            as_index=False
        )[columnas_sumar]
        .sum()
    )

    alerta_carrera = alertas_df.copy()
    score_carrera = df_score.copy()

else:
    df_filtrado = df_base_filtrada[
        df_base_filtrada["Carrera"] == carrera_seleccionada
    ].copy()

    alerta_carrera = alertas_df[
        alertas_df["Carrera"] == carrera_seleccionada
    ].copy()

    score_carrera = df_score[
        df_score["Carrera"] == carrera_seleccionada
    ].copy()

df_filtrado = df_filtrado.sort_values("Periodo")


# ======================================================
# 10. KPIs superiores
# ======================================================

titulo_vista = (
    "TODAS LAS CARRERAS"
    if es_general
    else carrera_seleccionada
)

st.subheader(f"Vista seleccionada: {titulo_vista}")

if es_general:
    enrollment_base = alertas_df["Enrollment_Base"].sum()
    enrollment_proyectado = alertas_df["Enrollment_Proyectado"].sum()
    incremento_necesario = alertas_df["Incremento_Necesario"].sum()

    ingresos_c10 = alertas_df.get(
        "Ingresos_Adicionales_C10_Total",
        pd.Series([0])
    ).sum()

    ingresos_c20 = alertas_df.get(
        "Ingresos_Adicionales_C20_Total",
        pd.Series([0])
    ).sum()

    if enrollment_base > 0:
        proporcion_general = enrollment_proyectado / enrollment_base
    else:
        proporcion_general = None

    tipo_alerta = clasificar_alerta_por_proporcion(proporcion_general)

    df_eval_general = df_filtrado[
        df_filtrado["Origen"] == "Proyección"
    ].copy()

    if not df_eval_general.empty and enrollment_base > 0:
        df_eval_general["Prop_Enrollment"] = (
            df_eval_general["Total_Enrollment"] / enrollment_base
        )

        periodos_caida = df_eval_general[
            df_eval_general["Prop_Enrollment"] < 0.75
        ]["Periodo"]

        if len(periodos_caida) > 0:
            periodo_caida_75_raw = periodos_caida.min()
            periodo_caida_75 = formatear_periodo(periodo_caida_75_raw)
        else:
            periodo_caida_75_raw = None
            periodo_caida_75 = "No aplica"
    else:
        periodo_caida_75_raw = None
        periodo_caida_75 = "No aplica"

    if "Score_Salud_Final" in df_score.columns:
        score_salud = df_score["Score_Salud_Final"].mean()
        categoria_score = categorizar_score_por_valor(score_salud)
    else:
        score_salud = None
        categoria_score = "Sin score"

    if not df_mercado.empty and "Categoria_Mercado" in df_mercado.columns:
        categoria_mercado = (
            df_mercado["Categoria_Mercado"]
            .dropna()
            .astype(str)
            .value_counts()
        )

        if not categoria_mercado.empty:
            categoria_mercado = categoria_mercado.idxmax()
        else:
            categoria_mercado = "Sin información"
    else:
        categoria_mercado = "Sin información"

else:
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
            periodo_caida_75_raw = alerta_carrera[col_periodo_caida[0]].iloc[0]
        else:
            periodo_caida_75_raw = None

        if pd.isna(periodo_caida_75_raw):
            periodo_caida_75 = "No aplica"
        else:
            periodo_caida_75 = formatear_periodo(periodo_caida_75_raw)

    else:
        tipo_alerta = "Sin información"
        enrollment_base = 0
        enrollment_proyectado = 0
        incremento_necesario = 0
        ingresos_c10 = 0
        ingresos_c20 = 0
        periodo_caida_75_raw = None
        periodo_caida_75 = "No aplica"

    if not score_carrera.empty:
        score_salud = score_carrera["Score_Salud_Final"].iloc[0]
        categoria_score = score_carrera["Categoria_Score"].iloc[0]
    else:
        score_salud = None
        categoria_score = "Sin score"

    carrera_key_actual = normalizar_texto(carrera_seleccionada)

    mercado_carrera = df_mercado[
        df_mercado["Carrera_Key"] == carrera_key_actual
    ]

    if not mercado_carrera.empty:
        categoria_mercado = mercado_carrera["Categoria_Mercado"].iloc[0]
    else:
        categoria_mercado = "Sin información"


color_alerta = color_tipo_alerta(tipo_alerta)
color_score_salud = color_score(categoria_score)
color_caida_75 = color_periodo_caida(periodo_caida_75_raw)
color_mercado = color_categoria_mercado(categoria_mercado)


# ======================================================
# 11. Tarjetas KPI
# ======================================================

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    tarjeta_kpi(
        titulo="Tipo de alerta",
        valor=tipo_alerta,
        color=color_alerta
    )

with kpi2:
    tarjeta_kpi(
        titulo="Enrollment base",
        valor=formatear_numero(enrollment_base),
        color="#374151"
    )

with kpi3:
    tarjeta_kpi(
        titulo="Enrollment proyectado",
        valor=formatear_numero(enrollment_proyectado),
        color="#374151"
    )

with kpi4:
    tarjeta_kpi(
        titulo="Incremento necesario",
        valor=formatear_numero(incremento_necesario),
        color=color_alerta
    )

with kpi5:
    if score_salud is not None and not pd.isna(score_salud):
        tarjeta_kpi(
            titulo=categoria_score,
            valor=f"{float(score_salud):,.2f}",
            color=color_score_salud,
            subtitulo="Score de salud"
        )
    else:
        tarjeta_kpi(
            titulo="Score de salud",
            valor="Sin datos",
            color="#616161"
        )


kpi6, kpi7, kpi8, kpi9 = st.columns(4)

with kpi6:
    tarjeta_kpi(
        titulo="Ingresos adicionales Ciclo 10",
        valor=formatear_numero(ingresos_c10),
        color="#1565C0"
    )

with kpi7:
    tarjeta_kpi(
        titulo="Ingresos adicionales Ciclo 20",
        valor=formatear_numero(ingresos_c20),
        color="#1565C0"
    )

with kpi8:
    tarjeta_kpi(
        titulo="Periodo primera caída 75%",
        valor=periodo_caida_75,
        color=color_caida_75
    )

with kpi9:
    tarjeta_kpi(
        titulo="Categoría de mercado",
        valor=categoria_mercado,
        color=color_mercado,
        subtitulo="UDLA vs competencia"
    )


# ======================================================
# 12. Gráfico principal: histórico y proyección
# ======================================================

st.subheader("Histórico y proyección por carrera")

df_plot = df_filtrado[[
    "Periodo",
    "Periodo_Label",
    "Periodo_Orden",
    "Origen",
    "Nuevos_Ingresos",
    "Total_Desertores",
    "Total_Graduados",
    "Total_Enrollment"
]].copy()

df_plot = df_plot.sort_values("Periodo")

df_plot = df_plot.rename(columns={
    "Nuevos_Ingresos": "Nuevos ingresos",
    "Total_Desertores": "Desertores",
    "Total_Graduados": "Graduados y egresados",
    "Total_Enrollment": "Enrollment total"
})

df_long = df_plot.melt(
    id_vars=["Periodo", "Periodo_Label", "Periodo_Orden", "Origen"],
    value_vars=[
        "Nuevos ingresos",
        "Desertores",
        "Graduados y egresados",
        "Enrollment total"
    ],
    var_name="Indicador",
    value_name="Valor"
)

periodos_ticks = (
    df_plot[["Periodo", "Periodo_Label", "Periodo_Orden"]]
    .drop_duplicates()
    .sort_values("Periodo")
)

fig_principal = px.line(
    df_long,
    x="Periodo_Orden",
    y="Valor",
    color="Indicador",
    line_shape="spline",
    markers=False,
    custom_data=["Periodo_Label", "Origen"],
    title=f"Evolución histórica y proyectada - {titulo_vista}"
)

if 202620 in periodo_a_orden:
    orden_202620 = periodo_a_orden[202620]

    if not df_long.empty:
        if df_long["Periodo_Orden"].min() <= orden_202620 <= df_long["Periodo_Orden"].max():
            fig_principal.add_vline(
                x=orden_202620,
                line_width=2,
                line_dash="dash",
                line_color="gray"
            )

            fig_principal.add_annotation(
                x=orden_202620,
                y=df_long["Valor"].max(),
                text="Inicio proyección",
                showarrow=False,
                yshift=15
            )

fig_principal.update_traces(
    line=dict(width=3),
    opacity=0.90,
    hovertemplate=(
        "Periodo: %{customdata[0]}<br>"
        "Origen: %{customdata[1]}<br>"
        "Valor: %{y:,.0f}<extra></extra>"
    )
)

fig_principal.update_xaxes(
    tickmode="array",
    tickvals=periodos_ticks["Periodo_Orden"],
    ticktext=periodos_ticks["Periodo_Label"],
    tickangle=-45
)

fig_principal.update_layout(
    height=520,
    xaxis_title="Periodo",
    yaxis_title="Cantidad de estudiantes",
    legend_title="Indicador",
    hovermode="x unified",
    plot_bgcolor="white",
    paper_bgcolor="white"
)

fig_principal.update_yaxes(
    gridcolor="rgba(0,0,0,0.10)"
)

st.plotly_chart(fig_principal, use_container_width=True)


# ======================================================
# 13. Gráficos secundarios
# ======================================================

col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("Enrollment total")

    df_enrollment_plot = df_filtrado.copy()
    df_enrollment_plot = df_enrollment_plot.sort_values("Periodo")

    periodos_ticks_bar = (
        df_enrollment_plot[["Periodo", "Periodo_Label", "Periodo_Orden"]]
        .drop_duplicates()
        .sort_values("Periodo")
    )

    fig_enrollment = px.bar(
        df_enrollment_plot,
        x="Periodo_Orden",
        y="Total_Enrollment",
        color="Origen",
        custom_data=["Periodo_Label"],
        title="Enrollment histórico y proyectado",
        text_auto=True
    )

    fig_enrollment.update_traces(
        hovertemplate=(
            "Periodo: %{customdata[0]}<br>"
            "Enrollment total: %{y:,.0f}<extra></extra>"
        )
    )

    fig_enrollment.update_xaxes(
        tickmode="array",
        tickvals=periodos_ticks_bar["Periodo_Orden"],
        ticktext=periodos_ticks_bar["Periodo_Label"],
        tickangle=-45
    )

    fig_enrollment.update_layout(
        height=430,
        xaxis_title="Periodo",
        yaxis_title="Enrollment total",
        legend_title="Origen",
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    st.plotly_chart(fig_enrollment, use_container_width=True)


with col_g2:
    st.subheader("Composición por periodo")

    df_comp = df_filtrado[[
        "Periodo",
        "Periodo_Label",
        "Periodo_Orden",
        "Nuevos_Ingresos",
        "Total_Desertores",
        "Total_Graduados"
    ]].copy()

    df_comp = df_comp.sort_values("Periodo")

    df_comp = df_comp.rename(columns={
        "Nuevos_Ingresos": "Nuevos ingresos",
        "Total_Desertores": "Desertores",
        "Total_Graduados": "Graduados y egresados"
    })

    df_comp_long = df_comp.melt(
        id_vars=["Periodo", "Periodo_Label", "Periodo_Orden"],
        var_name="Indicador",
        value_name="Valor"
    )

    periodos_ticks_comp = (
        df_comp[["Periodo", "Periodo_Label", "Periodo_Orden"]]
        .drop_duplicates()
        .sort_values("Periodo")
    )

    fig_comp = px.bar(
        df_comp_long,
        x="Periodo_Orden",
        y="Valor",
        color="Indicador",
        barmode="group",
        custom_data=["Periodo_Label"],
        title="Nuevos ingresos, desertores y graduados"
    )

    fig_comp.update_traces(
        hovertemplate=(
            "Periodo: %{customdata[0]}<br>"
            "Valor: %{y:,.0f}<extra></extra>"
        )
    )

    fig_comp.update_xaxes(
        tickmode="array",
        tickvals=periodos_ticks_comp["Periodo_Orden"],
        ticktext=periodos_ticks_comp["Periodo_Label"],
        tickangle=-45
    )

    fig_comp.update_layout(
        height=430,
        xaxis_title="Periodo",
        yaxis_title="Cantidad",
        legend_title="Indicador",
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    st.plotly_chart(fig_comp, use_container_width=True)


# ======================================================
# 14. Alertas generales por carrera
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
    xaxis_tickangle=-45,
    plot_bgcolor="white",
    paper_bgcolor="white"
)

st.plotly_chart(fig_alertas, use_container_width=True)


# ======================================================
# 15. Score de salud de carreras
# ======================================================

st.subheader("Score de salud de carreras")

if "Score_Salud_Final" in df_score.columns:
    df_score_plot = df_score.sort_values(
        "Score_Salud_Final",
        ascending=False
    ).copy()

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
        xaxis_tickangle=-45,
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    st.plotly_chart(fig_score, use_container_width=True)
else:
    st.warning("No se encontró la columna Score_Salud_Final en df_score.")


# ======================================================
# 16. Tabla resumen de la vista seleccionada
# ======================================================

st.subheader("Detalle de la vista seleccionada")

with st.expander("Ver histórico y proyección"):
    st.dataframe(
        df_filtrado.sort_values("Periodo"),
        use_container_width=True
    )

with st.expander("Ver alertas"):
    st.dataframe(
        alerta_carrera,
        use_container_width=True
    )

with st.expander("Ver score"):
    st.dataframe(
        score_carrera,
        use_container_width=True
    )

with st.expander("Ver datos de mercado"):
    st.dataframe(
        df_mercado,
        use_container_width=True
    )


# ======================================================
# 17. Botón para refrescar datos
# ======================================================

st.sidebar.markdown("---")

if st.sidebar.button("Actualizar datos"):
    st.cache_data.clear()
    st.rerun()
