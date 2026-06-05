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
# 5. Funciones de tasas, crecimiento y simulación
# ======================================================

def calcular_desviaciones_tasas(df_ret: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula la variabilidad histórica de las tasas de deserción y graduación.
    Esto sirve para que Monte Carlo no use siempre una tasa fija,
    sino una tasa con variación realista.
    """

    df = df_ret.copy()
    df = df[df["SemestreIngreso"] >= 201820]

    pivot = (
        df
        .groupby(["CarreraHomologada", "Nivel", "Cohorte", "Estado_deser"])["IDMatricula"]
        .nunique()
        .reset_index()
    )

    pivot = pivot.pivot_table(
        index=["CarreraHomologada", "Nivel", "Cohorte"],
        columns="Estado_deser",
        values="IDMatricula",
        fill_value=0
    )

    for col in ["Activo", "Deserción", "Graduación", "Egreso"]:
        if col not in pivot.columns:
            pivot[col] = 0

    pivot["Total"] = pivot[["Activo", "Graduación", "Deserción", "Egreso"]].sum(axis=1)
    pivot = pivot[pivot["Total"] > 0].copy()

    pivot["Tasa_Deserción"] = pivot["Deserción"] / pivot["Total"]
    pivot["Tasa_Graduación"] = (
        pivot["Graduación"] + pivot["Egreso"]
    ) / pivot["Total"]

    resumen = (
        pivot
        .groupby(["CarreraHomologada", "Nivel"])
        .agg(
            Desv_Desercion=("Tasa_Deserción", "std"),
            Media_Desercion=("Tasa_Deserción", "mean"),
            Desv_Graduacion=("Tasa_Graduación", "std"),
            Media_Graduacion=("Tasa_Graduación", "mean")
        )
        .reset_index()
    )

    resumen["Desv_Desercion"] = resumen["Desv_Desercion"].fillna(0)
    resumen["Desv_Graduacion"] = resumen["Desv_Graduacion"].fillna(0)

    return resumen


def calcular_cagr(x):
    """
    Calcula la tasa de crecimiento anual compuesta.
    En este caso se usa sobre ingresos por carrera y ciclo.
    """

    x = x.dropna()

    if len(x) < 2:
        return np.nan

    inicial = x.iloc[0]
    final = x.iloc[-1]
    n = len(x) - 1

    if inicial == 0:
        return np.nan

    return (final / inicial) ** (1 / n) - 1


def tasa_geom_media(x):
    """
    Calcula una tasa geométrica media a partir de una serie.
    """

    x = x.dropna()

    if len(x) < 2 or (x <= 0).any():
        return np.nan

    retornos = x.pct_change().dropna() + 1

    return retornos.prod() ** (1 / len(retornos)) - 1


def calcular_cagr_todas_versiones(
    df,
    alpha=0.3,
    ventana=3,
    umbral_ingreso_inicial=5
):
    """
    Calcula varias versiones de CAGR.
    Para la proyección usaremos CAGR_EMA porque suaviza cambios extremos.
    """

    resultados = []

    for (carrera, ciclo), grupo in df.groupby(["CarreraHomologada", "Ciclo"]):
        serie = grupo.sort_values("SemestreIngreso")["Ingresos"].dropna()

        idx_inicio_valido = serie[serie >= umbral_ingreso_inicial].index.min()

        if pd.isna(idx_inicio_valido):
            continue

        serie_filtrada = serie.loc[idx_inicio_valido:]

        if len(serie_filtrada) < 2:
            continue

        ingresos_iniciales = serie_filtrada.iloc[0]

        cagr_clasico = calcular_cagr(serie_filtrada)

        suavizado_ema = serie_filtrada.ewm(alpha=alpha, adjust=False).mean()
        cagr_ema = tasa_geom_media(suavizado_ema)

        suavizado_rolling_mean = serie_filtrada.rolling(
            window=ventana,
            min_periods=1
        ).mean()

        cagr_rolling_mean = tasa_geom_media(suavizado_rolling_mean)

        suavizado_rolling_median = serie_filtrada.rolling(
            window=ventana,
            min_periods=1
        ).median()

        cagr_rolling_median = tasa_geom_media(suavizado_rolling_median)

        resultados.append({
            "CarreraHomologada": carrera,
            "Ciclo": ciclo,
            "CAGR_Original": round(cagr_clasico, 4),
            "CAGR_EMA": round(cagr_ema, 4),
            "CAGR_RollingMean": round(cagr_rolling_mean, 4),
            "CAGR_RollingMedian": round(cagr_rolling_median, 4),
            "IngresoInicialUsado": ingresos_iniciales,
            "NumPeriodosUsados": len(serie_filtrada)
        })

    return pd.DataFrame(resultados)


def calcular_desviacion_cagr(df_ciclo: pd.DataFrame) -> Dict[Tuple[str, int], float]:
    """
    Calcula la desviación histórica de los crecimientos de ingresos.
    Esto permite que Monte Carlo simule variaciones en los nuevos ingresos.
    """

    df = df_ciclo.copy()

    df["SemestreIngreso"] = pd.to_numeric(df["SemestreIngreso"], errors="coerce")
    df["Ingresos"] = pd.to_numeric(df["Ingresos"], errors="coerce")

    df.dropna(subset=["SemestreIngreso", "Ingresos"], inplace=True)

    desviaciones = {}

    for (carrera, ciclo), grupo in df.groupby(["CarreraHomologada", "Ciclo"]):
        grupo = grupo.sort_values("SemestreIngreso")
        grupo = grupo[grupo["Ingresos"] > 0]

        if len(grupo) < 3:
            continue

        grupo["Tasa_Var"] = grupo["Ingresos"].pct_change()
        desv = grupo["Tasa_Var"].std()

        if not np.isnan(desv) and desv < 1:
            desviaciones[(carrera, ciclo)] = round(desv, 4)

    return desviaciones


def simular_proyecciones_montecarlo(
    Poblacion: Dict[str, List[int]],
    Ingresos: Dict[str, Dict[int, int]],
    cagr_dict: Dict[Tuple[str, int], float],
    tasas_por_semestre: pd.DataFrame,
    desv_tasas: pd.DataFrame,
    vida_util_dict: Dict[str, int],
    periodos_futuros: List[int],
    desv_cagr_dict: Dict[Tuple[str, int], float],
    n_simulaciones: int = 1000
) -> pd.DataFrame:
    """
    Ejecuta la proyección Monte Carlo.

    Para cada carrera y periodo futuro calcula:
    - nuevos ingresos
    - desertores
    - graduados
    - sobrevivientes
    - total vivos

    Al final devuelve promedios e intervalos de confianza.
    """

    resultados_simulacion = []

    for sim in range(n_simulaciones):
        Poblacion_sim = copy.deepcopy(Poblacion)
        Ingresos_sim = copy.deepcopy(Ingresos)

        Resultados = []

        tasas_sim = tasas_por_semestre.merge(
            desv_tasas,
            on=["CarreraHomologada", "Nivel"],
            how="left"
        )

        tasas_sim["Media_Desercion"] = tasas_sim["Media_Desercion"].fillna(
            tasas_sim["Tasa_Deserción"]
        )

        tasas_sim["Media_Graduacion"] = tasas_sim["Media_Graduacion"].fillna(
            tasas_sim["Tasa_Graduación"]
        )

        tasas_sim["Desv_Desercion"] = tasas_sim["Desv_Desercion"].fillna(0)
        tasas_sim["Desv_Graduacion"] = tasas_sim["Desv_Graduacion"].fillna(0)

        tasas_sim["Tasa_Deserción_Sim"] = np.random.normal(
            tasas_sim["Media_Desercion"],
            tasas_sim["Desv_Desercion"]
        )

        tasas_sim["Tasa_Graduación_Sim"] = np.random.normal(
            tasas_sim["Media_Graduacion"],
            tasas_sim["Desv_Graduacion"]
        )

        tasas_sim["Tasa_Deserción_Sim"] = (
            tasas_sim["Tasa_Deserción_Sim"]
            .clip(0, 1)
            .fillna(0)
        )

        tasas_sim["Tasa_Graduación_Sim"] = (
            tasas_sim["Tasa_Graduación_Sim"]
            .clip(0, 1)
            .fillna(0)
        )

        exceso = (
            tasas_sim["Tasa_Deserción_Sim"] +
            tasas_sim["Tasa_Graduación_Sim"]
        ) > 1

        tasas_sim.loc[exceso, "Tasa_Deserción_Sim"] *= 0.5
        tasas_sim.loc[exceso, "Tasa_Graduación_Sim"] *= 0.5

        for periodo in periodos_futuros:
            ciclo = periodo % 100

            for carrera in Poblacion_sim.keys():
                vida_util = int(vida_util_dict.get(carrera, 10))

                if vida_util <= 0:
                    vida_util = 10

                cohorte_actual = Poblacion_sim[carrera]

                if len(cohorte_actual) < vida_util:
                    cohorte_actual += [0] * (vida_util - len(cohorte_actual))
                elif len(cohorte_actual) > vida_util:
                    cohorte_actual = cohorte_actual[:vida_util]

                nueva_cohorte = [0] * vida_util

                Ingresos_sim.setdefault(carrera, {})

                ingreso_anterior = Ingresos_sim[carrera].get(ciclo, 0)
                tasa_cagr_base = cagr_dict.get((carrera, ciclo), 0)
                desv_cagr = desv_cagr_dict.get((carrera, ciclo), 0.01)

                tasa_cagr_sim = np.random.normal(tasa_cagr_base, desv_cagr)

                nuevos = max(
                    0,
                    int(round(ingreso_anterior * (1 + tasa_cagr_sim)))
                )

                nueva_cohorte[0] = nuevos
                Ingresos_sim[carrera][ciclo] = nuevos

                desertores = 0
                graduados = 0

                for i in range(1, vida_util):
                    prev = cohorte_actual[i - 1]
                    nivel_actual = i + 1

                    tasas = tasas_sim[
                        (tasas_sim["CarreraHomologada"] == carrera) &
                        (tasas_sim["Nivel"] == nivel_actual)
                    ]

                    if not tasas.empty:
                        tasa_des = tasas["Tasa_Deserción_Sim"].values[0]
                        tasa_grad = tasas["Tasa_Graduación_Sim"].values[0]
                    else:
                        tasa_des = 0
                        tasa_grad = 0

                    des = max(0, prev * tasa_des)
                    grad = max(0, prev * tasa_grad)
                    surv = max(0, prev - des - grad)

                    nueva_cohorte[i] = max(0, int(round(surv)))

                    desertores += des
                    graduados += grad

                Poblacion_sim[carrera] = nueva_cohorte

                Resultados.append({
                    "Simulacion": sim,
                    "Periodo": periodo,
                    "Carrera": carrera,
                    "Ciclo": ciclo,
                    "Nuevos_Ingresos": max(0, nuevos),
                    "Total_Desertores": max(0, int(round(desertores))),
                    "Total_Graduados": max(0, int(round(graduados))),
                    "Sobrevivientes": max(0, sum(nueva_cohorte[1:])),
                    "Total_Vivos": max(0, sum(nueva_cohorte))
                })

        resultados_simulacion.append(pd.DataFrame(Resultados))

    df_simulaciones = pd.concat(resultados_simulacion, ignore_index=True)

    indicadores = [
        "Total_Vivos",
        "Nuevos_Ingresos",
        "Total_Desertores",
        "Total_Graduados"
    ]

    resumen_list = []

    for var in indicadores:
        resumen_var = (
            df_simulaciones
            .groupby(["Carrera", "Periodo"])[var]
            .agg([
                (f"{var}_Prom", "mean"),
                (f"{var}_IC_2.5%", lambda x: np.percentile(x, 2.5)),
                (f"{var}_IC_97.5%", lambda x: np.percentile(x, 97.5))
            ])
        )

        resumen_list.append(resumen_var)

    resumen_ic = pd.concat(resumen_list, axis=1).reset_index()

    return resumen_ic


def suavizar_proyeccion(
    df: pd.DataFrame,
    variables: list,
    metodo: str = "rolling",
    alpha: float = 0.3,
    window: int = 2
) -> pd.DataFrame:
    """
    Suaviza la proyección para evitar saltos muy bruscos.
    """

    df = df.copy()
    df = df.sort_values(["Carrera", "Periodo"])

    for var in variables:
        if metodo == "rolling":
            df[f"{var}_Suav"] = df.groupby("Carrera")[var].transform(
                lambda x: x.rolling(window=window, min_periods=1).mean()
            )
        elif metodo == "ema":
            df[f"{var}_Suav"] = df.groupby("Carrera")[var].transform(
                lambda x: x.ewm(alpha=alpha, adjust=False).mean()
            )
        else:
            raise ValueError("Método no reconocido. Usa 'rolling' o 'ema'.")

    return df


def clasificar_alerta(p):
    """
    Clasifica el nivel de alerta según la caída del enrollment.
    """

    if p >= 1.0:
        return "Sin caída"
    elif 0.75 <= p < 1.0:
        return "Caída leve"
    elif 0.5 < p < 0.75:
        return "Caída moderada"
    else:
        return "Caída severa"


def calcular_cagr_objetivo(adicional_total, base, ciclos):
    """
    Calcula el crecimiento necesario para compensar una caída futura.
    """

    if base <= 0 or adicional_total <= 0:
        return np.nan

    return (1 + (adicional_total / base)) ** (1 / ciclos) - 1


def detectar_caida(df, columna_prop, umbral):
    """
    Identifica el primer periodo donde una carrera cae bajo cierto umbral.
    """

    caidas = (
        df[df[columna_prop] < umbral]
        .groupby("Carrera")["Periodo"]
        .min()
        .reset_index()
    )

    caidas.rename(
        columns={
            "Periodo": f"Periodo_Caida_{int(umbral * 100)}_{columna_prop}"
        },
        inplace=True
    )

    return caidas


def calcular_score_flexible(row):
    """
    Calcula el score de salud usando:
    - CAGR
    - tasa de retención
    - deserción temprana real
    """

    score = 0
    peso_total = 0

    pesos = {
        "CAGR": 0.50,
        "Tasa_Retencion": 0.25,
        "Desercion_Temprana_Real": 0.25
    }

    for var, peso in pesos.items():
        if not pd.isna(row[var]):
            if var == "Desercion_Temprana_Real":
                score += peso * (1 - row[var])
            else:
                score += peso * row[var]

            peso_total += peso

    if peso_total > 0:
        return score / peso_total
    else:
        return np.nan


def categorizar_score(score):
    """
    Convierte el score numérico en categoría.
    """

    if pd.isna(score):
        return np.nan
    elif score < 33.33:
        return "Score Bajo"
    elif score < 66.66:
        return "Score Medio"
    else:
        return "Score Alto"
