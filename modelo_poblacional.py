# ======================================================
# MODELO POBLACIONAL DE CARRERAS
# Este archivo genera las tablas necesarias para Streamlit
# sin guardar archivos Excel.
# ======================================================

import os
import sys
import copy
import urllib.parse
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.preprocessing import MinMaxScaler


# ======================================================
# 1. Parámetros principales
# ======================================================

ULTIMO_PERIODO = 202610
PRIMER_PERIODO_PROYECCION = 202620
ANIOS_PROYECCION = 10
N_SIMULACIONES = 200


# ======================================================
# 2. Crear conexión a SQL Server
# ======================================================

def crear_engine_sql():
    """
    Crea la conexión a SQL Server.

    Por ahora usa los mismos datos que ya probaste:
    servidor: SGCN05
    base: BDD_Proyectos
    autenticación Windows.
    """

    servidor = "SGCN05"
    base_datos = "BDD_Proyectos"

    params = urllib.parse.quote_plus(
        "DRIVER={SQL Server};"
        f"SERVER={servidor};"
        f"DATABASE={base_datos};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )

    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

    return engine


# ======================================================
# 3. Descargar datos desde SQL Server
# ======================================================

def descargar_datos_sql(engine):
    """
    Descarga las tres bases principales desde SQL Server:
    1. Histórico de enrollment
    2. Retención
    3. Catálogo de carreras
    """

    query_enrollment = """
    SELECT [IdSemestre] 
          ,[Semestre] AS Periodo
          ,[IdCarrera] 
          ,[IdEspecialidad]
          ,[CodCarrera]
          ,[CodEspecialidad]
          ,[PlanCarrera]
          ,[DesCarreraUnificado]
          ,[CarreraHomologada]
          ,[FacultadAlumno]
          ,[Regimen]
          ,[Jornada]
          ,[Modalidad]
          ,[IdPersona]
          ,[IDMatricula]
          ,[IdPlan]
          ,[Genero]
          ,[Edad]
          ,[RangoEdad]
          ,[CargaAcademica]
          ,[Vigente]
          ,[TieneMatricula]
          ,[TieneColegiatura]
          ,[EsReingreso]
          ,[EsCambio]
          ,[EsPracticas]
          ,[FinMalla]
          ,[Nivel]
          ,[EsGraduado]
          ,[TipoAdm]
          ,[FechaMatricula]
          ,[FechaInicioSemestre]
          ,[SemestreIngresoN] AS SemestreIngreso
          ,[FechaInicio]
          ,[FechaRetiro]
          ,[Retiro]
          ,[IdTipoAlumno]
          ,[PerfilAlumno]
          ,[PGA_Institucional]
          ,[PGA_Carrera]
          ,[PosibleBajaCarga]
          ,[TotMateriasAprobadas]
          ,[PorcAvanceMalla]
    FROM [BDD_Proyectos].[dbo].[Vw_HistoricoEnrollment]
    WHERE [Regimen] IN ('TECNOLOGICO SUPERIOR', 'PREGRADO', 'TECNICO SUPERIOR')
    """

    query_retencion = """
    SELECT [Semestre]
          ,[IDMatricula]
          ,[CodCarrera]
          ,[Regimen]
          ,[EstadoRetencion]
    FROM [BDD_Proyectos].[dbo].[TotalEnrollmentEC]
    """

    query_carreras = """
    SELECT *
    FROM [BDD_Proyectos].[dbo].[Vw_CarreraFacultadArea_New]
    WHERE [PeriodoFinPrograma] = '999999'
    """

    df_enrollment = pd.read_sql(query_enrollment, engine)
    df_retencion = pd.read_sql(query_retencion, engine)
    df_carreras = pd.read_sql(query_carreras, engine)

    df_retencion = df_retencion.rename(columns={"Semestre": "Periodo"})

    return df_enrollment, df_retencion, df_carreras


# ======================================================
# 4. Funciones de limpieza y preparación
# ======================================================

def homologar_carreras_catalogo(df_carreras):
    """
    Aplica correcciones manuales al catálogo de carreras.
    """

    df_carreras = df_carreras.copy()

    df_carreras["CarreraHomologada"] = np.where(
        df_carreras["CodNuevo"] == "UDLA4P053",
        "TECNOLOGÍA SUPERIOR UNIVERSITARIA EN GASTRONOMÍA",
        df_carreras["CarreraHomologada"]
    )

    df_carreras["CarreraHomologada"] = np.where(
        df_carreras["CodNuevo"] == "UDLA1H082",
        "PSICOLOGIA EDUCATIVA",
        df_carreras["CarreraHomologada"]
    )

    df_carreras["CarreraHomologada"] = np.where(
        df_carreras["CodNuevo"] == "UDLA1H791",
        "INGENIERIA DE SOFTWARE",
        df_carreras["CarreraHomologada"]
    )

    return df_carreras


def homologar_carreras_base(df_ret):
    """
    Estandariza nombres de carreras para que el dashboard no tenga duplicados.
    """

    df_ret = df_ret.copy()

    df_ret["CarreraHomologada"] = np.where(
        df_ret["DesCarreraUnificado"] == "PSICOLOGÍA EDUCATIVA",
        "PSICOLOGÍA EDUCATIVA",
        df_ret["CarreraHomologada"]
    )

    df_ret["CarreraHomologada"] = np.where(
        df_ret["CarreraHomologada"].isin([
            "TECNOLOGIA EN REDES Y TELECOMUNICACIONES",
            "TELECOMUNICACIONES"
        ]),
        "NETWORKING Y TELECOMUNICACIONES",
        df_ret["CarreraHomologada"]
    )

    df_ret["CarreraHomologada"] = np.where(
        df_ret["CarreraHomologada"].isin([
            "HOSPITALIDAD Y HOTELERÍA",
            "TURISMO Y HOTELERÍA",
            "TURISMO"
        ]),
        "HOTELERÍA Y TURISMO",
        df_ret["CarreraHomologada"]
    )

    df_ret["CarreraHomologada"] = np.where(
        df_ret["CarreraHomologada"].isin(["ADMINISTRACION DE EMPRESAS"]),
        "ADMINISTRACIÓN DE EMPRESAS",
        df_ret["CarreraHomologada"]
    )

    df_ret["CarreraHomologada"] = np.where(
        df_ret["CarreraHomologada"].isin([
            "TECNOLOGIA EN PRODUCCION Y SEGURIDAD INDUSTRIAL",
            "INGENIERÍA INDUSTRIAL"
        ]),
        "INGENIERÍA INDUSTRIAL",
        df_ret["CarreraHomologada"]
    )

    df_ret["CarreraHomologada"] = np.where(
        df_ret["CarreraHomologada"].isin([
            "TECNOLOGIAS DE LA INFORMACION",
            "CIBERSEGURIDAD"
        ]),
        "CIBERSEGURIDAD",
        df_ret["CarreraHomologada"]
    )

    df_ret["CarreraHomologada"] = np.where(
        df_ret["CarreraHomologada"].isin([
            "DISEÑO GRAFICO",
            "DISEÑO GRAFICO Y COMUNICACION VISUAL"
        ]),
        "DISEÑO GRAFICO",
        df_ret["CarreraHomologada"]
    )

    df_ret["CarreraHomologada"] = np.where(
        df_ret["CarreraHomologada"].isin([
            "GESTION DEPORTIVA",
            "NEGOCIOS DEPORTIVOS"
        ]),
        "NEGOCIOS DEPORTIVOS",
        df_ret["CarreraHomologada"]
    )

    df_ret["CarreraHomologada"] = np.where(
        df_ret["CarreraHomologada"].isin([
            "CIENCIAS POLÍTICAS",
            "RELACIONES INTERNACIONALES"
        ]),
        "RELACIONES INTERNACIONALES",
        df_ret["CarreraHomologada"]
    )

    df_ret["CarreraHomologada"] = np.where(
        df_ret["CarreraHomologada"].isin([
            "EDUCACION INICIAL BILINGUE CON MENCION EN GESTION Y ADMINISTRACION DE CENTROS INFANTILES"
        ]),
        "EDUCACION",
        df_ret["CarreraHomologada"]
    )

    return df_ret


def estado_exacto(row):
    """
    Clasifica el estado del estudiante considerando si es nuevo o no.
    """

    if row["EstadoRetencion"] == "d) Graduación":
        return "Graduación"
    elif row["EstadoRetencion"] == "c) Egresos":
        return "Egreso"
    elif row["EstadoRetencion"] == "f) Deserción":
        if row["PerfilAlumno"] == "NUEVO":
            return "Nuevo"
        else:
            return "Deserción"
    elif row["EstadoRetencion"] == "b) Retención":
        if row["PerfilAlumno"] == "NUEVO":
            return "Nuevo"
        else:
            return "Activo"
    else:
        return "Sin información"


def estado_desercion(row):
    """
    Clasifica el estado del estudiante para cálculos de deserción,
    retención, graduación y egreso.
    """

    if row["EstadoRetencion"] == "d) Graduación":
        return "Graduación"
    elif row["EstadoRetencion"] == "c) Egresos":
        return "Egreso"
    elif row["EstadoRetencion"] == "f) Deserción":
        return "Deserción"
    elif row["EstadoRetencion"] == "b) Retención":
        return "Activo"
    else:
        return "Sin información"


def calcular_semestre_relativo(row):
    """
    Calcula en qué semestre relativo está un estudiante.
    """

    if pd.isna(row["SemestreIngreso"]) or pd.isna(row["Periodo"]):
        return np.nan

    anio_ing = int(row["SemestreIngreso"]) // 100
    sem_ing = int(row["SemestreIngreso"]) % 100

    anio_per = int(row["Periodo"]) // 100
    sem_per = int(row["Periodo"]) % 100

    return (anio_per - anio_ing) * 2 + (sem_per - sem_ing) // 10


def preparar_base_retencion(df_enrollment, df_retencion, df_carreras):
    """
    Une enrollment con retención y catálogo de carreras.
    Deja la base lista para calcular históricos, tasas y proyecciones.
    """

    df_carreras = homologar_carreras_catalogo(df_carreras)

    data = df_enrollment.merge(
        df_retencion,
        on=["Periodo", "IDMatricula", "CodCarrera"],
        how="left"
    )

    # Quitar intersemestrales.
    data = data[data["Periodo"].astype(str).str.endswith(("10", "20"))].copy()

    data["Periodo"] = pd.to_numeric(data["Periodo"], errors="coerce")
    data["SemestreIngreso"] = pd.to_numeric(data["SemestreIngreso"], errors="coerce")

    # Tomar histórico hasta 202610.
    data = data[data["Periodo"] <= ULTIMO_PERIODO].copy()

    df_ret = data[[
        "IDMatricula",
        "DesCarreraUnificado",
        "CodCarrera",
        "CarreraHomologada",
        "Periodo",
        "PerfilAlumno",
        "Nivel",
        "EstadoRetencion",
        "SemestreIngreso"
    ]].copy()

    df_ret = df_ret.rename(columns={"CarreraHomologada": "Carrera"})

    df_ret = df_ret.merge(
        df_carreras[["CodNuevo", "CarreraHomologada", "Modalidad", "Jornada"]],
        left_on="CodCarrera",
        right_on="CodNuevo",
        how="left"
    )

    df_ret = homologar_carreras_base(df_ret)

    # Solo modalidad presencial.
    df_ret = df_ret[df_ret["Modalidad"] == "PRESENCIAL"].copy()

    df_ret["Periodo"] = pd.to_numeric(df_ret["Periodo"], errors="coerce")
    df_ret["SemestreIngreso"] = pd.to_numeric(df_ret["SemestreIngreso"], errors="coerce")
    df_ret["Nivel"] = pd.to_numeric(df_ret["Nivel"], errors="coerce")
    df_ret["EstadoRetencion"] = df_ret["EstadoRetencion"].astype(str).str.strip()

    df_ret["Estado"] = df_ret.apply(estado_exacto, axis=1)
    df_ret["Estado_deser"] = df_ret.apply(estado_desercion, axis=1)

    df_ret = df_ret[
        (df_ret["Estado"] != "Sin información") &
        (df_ret["Estado_deser"] != "Sin información")
    ].copy()

    df_ret["Semestre_Num"] = df_ret.apply(calcular_semestre_relativo, axis=1)
    df_ret["Semestre_Acum"] = df_ret["Semestre_Num"] + 1

    df_ret["EsNuevo"] = np.where(df_ret["PerfilAlumno"] == "NUEVO", 1, 0)

    df_ret = df_ret.sort_values(by=["IDMatricula", "Periodo"])
    df_ret["Estado_Siguiente"] = df_ret.groupby("IDMatricula")["Estado"].shift(-1)

    df_ret.loc[
        (df_ret["Estado"] == "Nuevo") & (df_ret["Estado_Siguiente"].isna()),
        "Estado_Siguiente"
    ] = "Deserción"

    df_ret.loc[
        df_ret["Estado"] == "Graduación",
        "Estado_Siguiente"
    ] = np.nan

    df_ret["Cohorte"] = df_ret["SemestreIngreso"]

    return df_ret


# ======================================================
# 5. Por ahora dejamos esta función principal lista
# ======================================================

def generar_datos():
    """
    Esta será la función que Streamlit llamará desde app.py.

    Retorna:
    - df_completo
    - alertas_df
    - df_score

    En el siguiente paso vamos a completar esta función con toda la lógica
    de proyección, alertas y score.
    """

    engine = crear_engine_sql()

    # Prueba de conexión.
    with engine.connect() as conn:
        resultado = conn.execute(
            text("SELECT @@SERVERNAME AS servidor, DB_NAME() AS base_actual")
        )
        for fila in resultado:
            print("Conexión OK:", fila)

    df_enrollment, df_retencion, df_carreras = descargar_datos_sql(engine)

    df_ret = preparar_base_retencion(
        df_enrollment=df_enrollment,
        df_retencion=df_retencion,
        df_carreras=df_carreras
    )

    # ==================================================
    # ATENCIÓN:
    # Esta versión todavía no genera la proyección final.
    # Solo prueba conexión + descarga + limpieza base.
    # En el siguiente paso agregamos:
    # - df_completo
    # - alertas_df
    # - df_score
    # ==================================================

    return df_ret
