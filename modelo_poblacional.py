# ======================================================
# MODELO POBLACIONAL DE CARRERAS
# Este archivo genera las tablas necesarias para Streamlit
# sin guardar archivos Excel.
# ======================================================

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
# 2. Parámetros de conexión SQL Server
# ======================================================

SERVIDOR_SQL = "SNBI03"          # Servidor 03
BASE_DATOS_SQL = "BDD_Proyectos" # Cambia solo si en el 03 la base tiene otro nombre


# ======================================================
# 3. Crear conexión a SQL Server
# ======================================================

def crear_engine_sql():
    """
    Crea la conexión a SQL Server.

    Ajuste:
    - Antes apuntaba al servidor 05.
    - Ahora apunta al servidor 03.
    """

    params = urllib.parse.quote_plus(
        "DRIVER={SQL Server};"
        f"SERVER={SERVIDOR_SQL};"
        f"DATABASE={BASE_DATOS_SQL};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )

    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

    return engine


# ======================================================
# 4. Descargar datos desde SQL Server
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
# 5. Limpieza y preparación de datos
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

    data = data[data["Periodo"].astype(str).str.endswith(("10", "20"))].copy()

    data["Periodo"] = pd.to_numeric(data["Periodo"], errors="coerce")
    data["SemestreIngreso"] = pd.to_numeric(data["SemestreIngreso"], errors="coerce")

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
# 6. Funciones de tasas, crecimiento y simulación
# ======================================================

def calcular_desviaciones_tasas(df_ret: pd.DataFrame) -> pd.DataFrame:
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
    pivot["Tasa_Graduación"] = (pivot["Graduación"] + pivot["Egreso"]) / pivot["Total"]

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

        tasas_sim["Tasa_Deserción_Sim"] = tasas_sim["Tasa_Deserción_Sim"].clip(0, 1).fillna(0)
        tasas_sim["Tasa_Graduación_Sim"] = tasas_sim["Tasa_Graduación_Sim"].clip(0, 1).fillna(0)

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
    if p >= 1.0:
        return "Sin caída"
    elif 0.75 <= p < 1.0:
        return "Caída leve"
    elif 0.5 < p < 0.75:
        return "Caída moderada"
    else:
        return "Caída severa"


def calcular_cagr_objetivo(adicional_total, base, ciclos):
    if base <= 0 or adicional_total <= 0:
        return np.nan

    return (1 + (adicional_total / base)) ** (1 / ciclos) - 1


def detectar_caida(df, columna_prop, umbral):
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
    if pd.isna(score):
        return np.nan
    elif score < 33.33:
        return "Score Bajo"
    elif score < 66.66:
        return "Score Medio"
    else:
        return "Score Alto"


# ======================================================
# 7. Función principal
# ======================================================

def generar_datos():
    """
    Ejecuta todo el modelo poblacional y devuelve:
    - df_completo
    - alertas_df
    - df_score
    """

    engine = crear_engine_sql()

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

    estados_muerte = ["Graduación", "Egreso", "Deserción"]

    excluyentes = [
        "CONTABILIDAD Y AUDITORÍA",
        "INTELIGENCIA ARTIFICIAL",
        "PSICOLOGÍA EDUCATIVA",
        "TECNOLOGÍA SUPERIOR UNIVERSITARIA EN GASTRONOMÍA"
    ]

    df_ret_sorted = df_ret[df_ret["Periodo"] >= 201820].copy()

    df_final = df_ret_sorted[
        df_ret_sorted["Estado"].isin(["Graduación", "Egreso"])
    ].copy()

    vida_util_promedio = (
        df_final
        .groupby("CarreraHomologada")["Nivel"]
        .mean()
        .round(1)
        .reset_index()
    )

    vida_util_promedio.rename(
        columns={"Nivel": "VidaUtil_Semestres"},
        inplace=True
    )

    vida_util_dict = {
        carrera: round(vida_util)
        for carrera, vida_util in vida_util_promedio
        .set_index("CarreraHomologada")["VidaUtil_Semestres"]
        .to_dict()
        .items()
    }

    df_filtrado = df_ret[df_ret["SemestreIngreso"] >= 201820].copy()

    tabla_vida = (
        df_filtrado
        .groupby(["CarreraHomologada", "Nivel", "Cohorte", "Estado_deser"])["IDMatricula"]
        .nunique()
        .reset_index()
    )

    pivot = tabla_vida.pivot_table(
        index=["CarreraHomologada", "Nivel", "Cohorte"],
        columns="Estado_deser",
        values="IDMatricula",
        fill_value=0
    ).reset_index()

    for col in ["Activo", "Deserción", "Graduación", "Egreso"]:
        if col not in pivot.columns:
            pivot[col] = 0

    pivot["Total"] = pivot[["Activo", "Graduación", "Deserción", "Egreso"]].sum(axis=1)
    pivot = pivot[pivot["Total"] > 0].copy()

    pivot["Tasa_Deserción"] = pivot["Deserción"] / pivot["Total"]
    pivot["Tasa_Graduación"] = (pivot["Graduación"] + pivot["Egreso"]) / pivot["Total"]
    pivot["Tasa_Retención"] = pivot["Activo"] / pivot["Total"]

    tasas_por_semestre = (
        pivot
        .groupby(["CarreraHomologada", "Nivel"])[
            ["Tasa_Deserción", "Tasa_Graduación", "Tasa_Retención"]
        ]
        .mean()
        .round(3)
        .reset_index()
    )

    desv_tasas = calcular_desviaciones_tasas(df_ret)

    df_ingresos = df_ret[df_ret["EsNuevo"] == 1].copy()
    df_ingresos["Ciclo"] = df_ingresos["SemestreIngreso"] % 100

    ingresos_por_ciclo = (
        df_ingresos
        .groupby(["CarreraHomologada", "SemestreIngreso", "Ciclo"])["IDMatricula"]
        .nunique()
        .reset_index()
    )

    ingresos_por_ciclo.rename(
        columns={"IDMatricula": "Ingresos"},
        inplace=True
    )

    ingresos_por_ciclo = ingresos_por_ciclo[
        ingresos_por_ciclo["SemestreIngreso"] >= 201820
    ].copy()

    ingresos_por_ciclo.sort_values(
        by=["CarreraHomologada", "Ciclo", "SemestreIngreso"],
        inplace=True
    )

    df_cagr_completo = calcular_cagr_todas_versiones(
        df=ingresos_por_ciclo,
        alpha=0.3,
        ventana=3,
        umbral_ingreso_inicial=5
    )

    df_cagr_completo = df_cagr_completo[[
        "CarreraHomologada",
        "Ciclo",
        "CAGR_EMA"
    ]].copy()

    df_cagr_completo.rename(
        columns={"CAGR_EMA": "Tasa_Crecimiento_Compuesta"},
        inplace=True
    )

    cagr_dict = {
        (row["CarreraHomologada"], row["Ciclo"]): row["Tasa_Crecimiento_Compuesta"]
        for _, row in df_cagr_completo.dropna().iterrows()
    }

    desv_cagr_dict = calcular_desviacion_cagr(ingresos_por_ciclo)

    df_ultimo = df_ret[df_ret["Periodo"] == ULTIMO_PERIODO].copy()

    if df_ultimo.empty:
        periodos_disponibles = sorted(df_ret["Periodo"].dropna().unique())
        raise ValueError(
            f"No hay datos para ULTIMO_PERIODO={ULTIMO_PERIODO}. "
            f"Últimos periodos disponibles: {periodos_disponibles[-10:]}"
        )

    df_vivos = df_ultimo[
        ~df_ultimo["Estado_deser"].isin(estados_muerte)
    ].copy()

    estado_base = (
        df_vivos
        .groupby(["CarreraHomologada", "Nivel"])["IDMatricula"]
        .nunique()
        .reset_index()
    )

    estado_base.rename(
        columns={"IDMatricula": "Cantidad"},
        inplace=True
    )

    estado_base = estado_base[
        ~estado_base["CarreraHomologada"].isin(excluyentes)
    ].copy()

    Poblacion = {}

    for carrera, grupo in estado_base.groupby("CarreraHomologada"):
        vida_util = int(vida_util_dict.get(carrera, grupo["Nivel"].max()))

        if vida_util <= 0:
            vida_util = 10

        cohorte = [0] * vida_util

        for _, row in grupo.iterrows():
            nivel = int(row["Nivel"])

            if 1 <= nivel <= vida_util:
                cohorte[nivel - 1] = int(row["Cantidad"])

        Poblacion[carrera] = cohorte

    df_nuevos = df_ret[df_ret["EsNuevo"] == 1].copy()
    df_nuevos["Ciclo"] = df_nuevos["Periodo"] % 100

    ultimo_por_ciclo = (
        df_nuevos
        .groupby(["CarreraHomologada", "Ciclo"])["Periodo"]
        .max()
        .reset_index()
    )

    df_ingresos_base = df_nuevos.merge(
        ultimo_por_ciclo,
        on=["CarreraHomologada", "Ciclo", "Periodo"],
        how="inner"
    )

    ingresos_base = (
        df_ingresos_base
        .groupby(["CarreraHomologada", "Ciclo"])["IDMatricula"]
        .nunique()
        .reset_index()
    )

    ingresos_base.rename(
        columns={"IDMatricula": "Ingresos_Ultimo"},
        inplace=True
    )

    Ingresos = {}

    for _, row in ingresos_base.iterrows():
        carrera = row["CarreraHomologada"]
        ciclo = int(row["Ciclo"])
        valor = int(row["Ingresos_Ultimo"])

        if carrera not in Ingresos:
            Ingresos[carrera] = {}

        Ingresos[carrera][ciclo] = valor

    for carrera in Poblacion.keys():
        Ingresos.setdefault(carrera, {})
        Ingresos[carrera].setdefault(10, 0)
        Ingresos[carrera].setdefault(20, 0)

    anio_base = ULTIMO_PERIODO // 100

    periodos_futuros = [PRIMER_PERIODO_PROYECCION]

    for i in range(1, ANIOS_PROYECCION + 1):
        anio = anio_base + i
        periodos_futuros.append(anio * 100 + 10)
        periodos_futuros.append(anio * 100 + 20)

    resultados_con_ic = simular_proyecciones_montecarlo(
        Poblacion=Poblacion,
        Ingresos=Ingresos,
        cagr_dict=cagr_dict,
        tasas_por_semestre=tasas_por_semestre,
        desv_tasas=desv_tasas,
        vida_util_dict=vida_util_dict,
        periodos_futuros=periodos_futuros,
        desv_cagr_dict=desv_cagr_dict,
        n_simulaciones=N_SIMULACIONES
    )

    variables_a_suavizar = [
        "Total_Vivos_Prom",
        "Nuevos_Ingresos_Prom",
        "Total_Desertores_Prom",
        "Total_Graduados_Prom"
    ]

    resumen_ic_suav = suavizar_proyeccion(
        resultados_con_ic,
        variables_a_suavizar,
        metodo="ema",
        alpha=0.4
    )

    resumen_ic_suav = resumen_ic_suav.drop(columns=[
        "Total_Vivos_Prom",
        "Nuevos_Ingresos_Prom",
        "Total_Graduados_Prom",
        "Total_Desertores_Prom"
    ])

    resumen_ic_suav = resumen_ic_suav.rename(columns={
        "Total_Vivos_Prom_Suav": "Total_Vivos",
        "Nuevos_Ingresos_Prom_Suav": "Nuevos_Ingresos",
        "Total_Graduados_Prom_Suav": "Total_Graduados",
        "Total_Desertores_Prom_Suav": "Total_Desertores"
    })

    resultados_con_ic = resumen_ic_suav.copy()

    periodos_historicos = df_ret[df_ret["Periodo"] >= 201820].copy()

    df_hist = periodos_historicos.groupby([
        "Periodo",
        "CarreraHomologada"
    ])

    df_historico = df_hist.agg(
        Nuevos_Ingresos=("EsNuevo", lambda x: (x == 1).sum()),
        Total_Desertores=("Estado_deser", lambda x: (x == "Deserción").sum()),
        Total_Graduados=("Estado_deser", lambda x: ((x == "Graduación") | (x == "Egreso")).sum()),
        Total_Vivos=("Estado_deser", lambda x: (~x.isin(estados_muerte)).sum())
    ).reset_index()

    df_historico["Sobrevivientes"] = (
        df_historico["Total_Vivos"] -
        df_historico["Nuevos_Ingresos"]
    )

    df_historico["Ciclo"] = df_historico["Periodo"] % 100

    df_historico.rename(
        columns={"CarreraHomologada": "Carrera"},
        inplace=True
    )

    resultados_con_ic["Sobrevivientes"] = (
        resultados_con_ic["Total_Vivos"] -
        resultados_con_ic["Nuevos_Ingresos"]
    )

    resultados_con_ic["Ciclo"] = resultados_con_ic["Periodo"] % 100

    carreras_proy = resultados_con_ic["Carrera"].unique()

    df_historico = df_historico[
        df_historico["Carrera"].isin(carreras_proy)
    ].copy()

    df_historico["Origen"] = "Histórico"
    resultados_con_ic["Origen"] = "Proyección"

    df_completo = pd.concat(
        [df_historico, resultados_con_ic],
        ignore_index=True
    )

    df_completo = df_completo.sort_values(
        by=["Carrera", "Periodo"]
    )

    df_completo["Total_Enrollment"] = (
        df_completo["Total_Desertores"] +
        df_completo["Total_Graduados"] +
        df_completo["Total_Vivos"]
    )

    periodo_hist_max = (
        df_completo[df_completo["Origen"] == "Histórico"]
        .groupby("Carrera")["Periodo"]
        .max()
        .reset_index()
    )

    periodo_proj_max = (
        df_completo[df_completo["Origen"] == "Proyección"]
        .groupby("Carrera")["Periodo"]
        .max()
        .reset_index()
    )

    enrollment_base = pd.merge(
        periodo_hist_max,
        df_completo,
        on=["Carrera", "Periodo"]
    )[["Carrera", "Total_Enrollment"]]

    enrollment_base.rename(
        columns={"Total_Enrollment": "Enrollment_Base"},
        inplace=True
    )

    enrollment_final = pd.merge(
        periodo_proj_max,
        df_completo,
        on=["Carrera", "Periodo"]
    )[["Carrera", "Total_Enrollment"]]

    enrollment_final.rename(
        columns={"Total_Enrollment": "Enrollment_Proyectado"},
        inplace=True
    )

    alertas_df = pd.merge(
        enrollment_base,
        enrollment_final,
        on="Carrera"
    )

    alertas_df["Proporcion_Final_vs_Base"] = (
        alertas_df["Enrollment_Proyectado"] /
        alertas_df["Enrollment_Base"]
    ).round(3)

    alertas_df["Tipo_Alerta"] = alertas_df[
        "Proporcion_Final_vs_Base"
    ].apply(clasificar_alerta)

    alertas_df["Incremento_Necesario"] = (
        alertas_df["Enrollment_Base"] -
        alertas_df["Enrollment_Proyectado"]
    ).apply(lambda x: max(0, round(x)))

    ciclos_interes = [10, 20]

    df_hist_ciclos = df_completo[
        (df_completo["Origen"] == "Histórico") &
        (df_completo["Ciclo"].isin(ciclos_interes))
    ].copy()

    ingresos_ciclo = (
        df_hist_ciclos
        .groupby(["Carrera", "Ciclo"])["Nuevos_Ingresos"]
        .sum()
        .reset_index()
    )

    ingresos_totales = (
        ingresos_ciclo
        .groupby("Carrera")["Nuevos_Ingresos"]
        .sum()
        .reset_index()
        .rename(columns={"Nuevos_Ingresos": "Total_Ingresos"})
    )

    proporciones = pd.merge(
        ingresos_ciclo,
        ingresos_totales,
        on="Carrera"
    )

    proporciones["Proporcion_Ciclo"] = (
        proporciones["Nuevos_Ingresos"] /
        proporciones["Total_Ingresos"]
    )

    proporciones_pivot = (
        proporciones
        .pivot(index="Carrera", columns="Ciclo", values="Proporcion_Ciclo")
        .reset_index()
        .fillna(0)
    )

    proporciones_pivot.columns.name = None

    proporciones_pivot.rename(
        columns={
            10: "Prop_Ciclo_10",
            20: "Prop_Ciclo_20"
        },
        inplace=True
    )

    alertas_df = pd.merge(
        alertas_df,
        proporciones_pivot,
        on="Carrera",
        how="left"
    )

    alertas_df["Prop_Ciclo_10"] = alertas_df["Prop_Ciclo_10"].fillna(0)
    alertas_df["Prop_Ciclo_20"] = alertas_df["Prop_Ciclo_20"].fillna(0)

    n_periodos_futuros = len(periodos_futuros)

    alertas_df["Ingresos_Adicionales_C10_Total"] = (
        alertas_df["Incremento_Necesario"] *
        alertas_df["Prop_Ciclo_10"]
    ).round(1)

    alertas_df["Ingresos_Adicionales_C20_Total"] = (
        alertas_df["Incremento_Necesario"] *
        alertas_df["Prop_Ciclo_20"]
    ).round(1)

    alertas_df["Ingresos_Adicionales_C10_xPeriodo"] = (
        alertas_df["Ingresos_Adicionales_C10_Total"] /
        n_periodos_futuros
    ).round(1)

    alertas_df["Ingresos_Adicionales_C20_xPeriodo"] = (
        alertas_df["Ingresos_Adicionales_C20_Total"] /
        n_periodos_futuros
    ).round(1)

    n_ciclos = df_completo[
        df_completo["Origen"] == "Proyección"
    ]["Ciclo"].nunique()

    alertas_df["CAGR_Ciclo10_Necesario"] = alertas_df.apply(
        lambda row: calcular_cagr_objetivo(
            row["Ingresos_Adicionales_C10_Total"],
            row["Enrollment_Proyectado"],
            n_ciclos
        ),
        axis=1
    ).round(4)

    alertas_df["CAGR_Ciclo20_Necesario"] = alertas_df.apply(
        lambda row: calcular_cagr_objetivo(
            row["Ingresos_Adicionales_C20_Total"],
            row["Enrollment_Proyectado"],
            n_ciclos
        ),
        axis=1
    ).round(4)

    df_hist = df_completo[
        df_completo["Origen"] == "Histórico"
    ].copy()

    ultimo_ciclo_hist = (
        df_hist
        .groupby("Carrera")["Periodo"]
        .max()
        .reset_index()
    )

    df_base = pd.merge(
        df_hist,
        ultimo_ciclo_hist,
        on=["Carrera", "Periodo"]
    )[["Carrera", "Periodo", "Total_Enrollment", "Nuevos_Ingresos"]]

    df_base.rename(
        columns={
            "Total_Enrollment": "Enrollment_Base",
            "Nuevos_Ingresos": "Ingresos_Base"
        },
        inplace=True
    )

    df_proy = df_completo[
        df_completo["Origen"] == "Proyección"
    ].copy()

    df_proy = df_proy[[
        "Carrera",
        "Periodo",
        "Total_Enrollment",
        "Nuevos_Ingresos"
    ]]

    df_eval = pd.merge(
        df_proy,
        df_base,
        on="Carrera",
        how="left",
        suffixes=("", "_base")
    )

    df_eval["Prop_Enrollment"] = (
        df_eval["Total_Enrollment"] /
        df_eval["Enrollment_Base"]
    )

    df_eval["Prop_Ingresos"] = (
        df_eval["Nuevos_Ingresos"] /
        df_eval["Ingresos_Base"]
    )

    caida_75_enrollment = detectar_caida(df_eval, "Prop_Enrollment", 0.75)
    caida_50_enrollment = detectar_caida(df_eval, "Prop_Enrollment", 0.50)
    caida_25_enrollment = detectar_caida(df_eval, "Prop_Enrollment", 0.25)

    alertas_df = alertas_df.merge(
        caida_75_enrollment,
        on="Carrera",
        how="left"
    )

    alertas_df = alertas_df.merge(
        caida_50_enrollment,
        on="Carrera",
        how="left"
    )

    alertas_df = alertas_df.merge(
        caida_25_enrollment,
        on="Carrera",
        how="left"
    )

    df_ret_filtrado = df_ret[df_ret["Periodo"] >= 201820].copy()

    df_ret_filtrado["Ciclo"] = (
        df_ret_filtrado["Periodo"]
        .astype(str)
        .str[-2:]
    )

    ingresos_totales_score = (
        ingresos_por_ciclo
        .groupby(["CarreraHomologada", "Ciclo"])["Ingresos"]
        .sum()
        .reset_index(name="Total_Ingresos")
    )

    ingresos_totales_score["Ciclo"] = pd.to_numeric(
        ingresos_totales_score["Ciclo"],
        errors="coerce"
    )

    cagr_ponderado = df_cagr_completo.merge(
        ingresos_totales_score,
        on=["CarreraHomologada", "Ciclo"],
        how="inner"
    )

    cagr_ponderado_total = (
        cagr_ponderado
        .groupby("CarreraHomologada")
        .apply(
            lambda x: np.average(
                x["Tasa_Crecimiento_Compuesta"],
                weights=x["Total_Ingresos"]
            )
            if x["Total_Ingresos"].sum() > 0
            else np.nan
        )
        .reset_index(name="CAGR")
    )

    retencion_por_periodo = (
        df_ret_filtrado
        .groupby(["CarreraHomologada", "Periodo"])["Estado_deser"]
        .value_counts()
        .unstack()
        .fillna(0)
    )

    if "Activo" not in retencion_por_periodo.columns:
        retencion_por_periodo["Activo"] = 0

    retencion_por_periodo["Total"] = retencion_por_periodo.sum(axis=1)

    retencion_por_periodo = retencion_por_periodo[
        retencion_por_periodo["Total"] > 0
    ].copy()

    retencion_por_periodo["Tasa_Retencion_Periodo"] = (
        retencion_por_periodo["Activo"] /
        retencion_por_periodo["Total"]
    )

    retencion_promedio = (
        retencion_por_periodo
        .reset_index()
        .groupby("CarreraHomologada")["Tasa_Retencion_Periodo"]
        .mean()
        .reset_index()
    )

    retencion_promedio.rename(
        columns={"Tasa_Retencion_Periodo": "Tasa_Retencion"},
        inplace=True
    )

    retencion_promedio = retencion_promedio[
        retencion_promedio["Tasa_Retencion"] > 0.4
    ].copy()

    df_ret_filtrado_dt = df_ret[
        df_ret["Cohorte"].between(201820, 202410)
    ].copy()

    ingresos_dt = df_ret_filtrado_dt[
        df_ret_filtrado_dt["EsNuevo"] == 1
    ][["IDMatricula", "CarreraHomologada", "Cohorte"]].drop_duplicates()

    desertores_tempranos = df_ret_filtrado_dt[
        (df_ret_filtrado_dt["Estado_deser"] == "Deserción") &
        (df_ret_filtrado_dt["Nivel"].isin([1, 2]))
    ][["IDMatricula", "CarreraHomologada", "Cohorte"]].drop_duplicates()

    reingresaron = df_ret[df_ret["Nivel"] > 2]["IDMatricula"].unique()

    desertores_definitivos = desertores_tempranos[
        ~desertores_tempranos["IDMatricula"].isin(reingresaron)
    ]

    ingresos_dt["Desercion_Temprana_Real"] = ingresos_dt[
        "IDMatricula"
    ].isin(desertores_definitivos["IDMatricula"])

    tasa_dt_real = (
        ingresos_dt
        .groupby(["CarreraHomologada", "Cohorte"])["Desercion_Temprana_Real"]
        .mean()
        .reset_index()
    )

    tasa_dt_final = (
        tasa_dt_real
        .groupby("CarreraHomologada")["Desercion_Temprana_Real"]
        .mean()
        .reset_index()
    )

    tasa_dt_final = tasa_dt_final[
        tasa_dt_final["Desercion_Temprana_Real"] != 0
    ].copy()

    cagr_ponderado_total = cagr_ponderado_total[
        ~cagr_ponderado_total["CarreraHomologada"].isin(excluyentes)
    ].copy()

    df_indicadores = (
        cagr_ponderado_total
        .merge(retencion_promedio, on="CarreraHomologada", how="outer")
        .merge(tasa_dt_final, on="CarreraHomologada", how="outer")
    )

    df_indicadores = df_indicadores[
        ~df_indicadores["CarreraHomologada"].isin(excluyentes)
    ].copy()

    scaler = MinMaxScaler()

    df_scaled = df_indicadores.copy()

    cols_norm = [
        "CAGR",
        "Tasa_Retencion",
        "Desercion_Temprana_Real"
    ]

    for col in cols_norm:
        if col not in df_scaled.columns:
            df_scaled[col] = np.nan

    df_scaled[cols_norm] = pd.DataFrame(
        scaler.fit_transform(df_scaled[cols_norm]),
        columns=cols_norm,
        index=df_scaled.index
    )

    df_scaled["Score_Salud"] = df_scaled.apply(
        calcular_score_flexible,
        axis=1
    )

    df_scaled["Score_Salud"] = (
        df_scaled["Score_Salud"] * 100
    ).round(2)

    df_scaled = df_scaled[df_scaled["Score_Salud"] > 0].copy()

    scaler_score = MinMaxScaler()

    df_scaled["Score_Salud_Norm"] = scaler_score.fit_transform(
        df_scaled[["Score_Salud"]]
    )

    df_scaled["Score_Salud_Final"] = (
        df_scaled["Score_Salud_Norm"] * 100
    ).round(2)

    df_scaled["Categoria_Score"] = df_scaled[
        "Score_Salud_Final"
    ].apply(categorizar_score)

    df_score = df_scaled.copy()

    df_completo = df_completo.reset_index(drop=True)
    alertas_df = alertas_df.reset_index(drop=True)
    df_score = df_score.reset_index(drop=True)

    print("Modelo terminado correctamente.")
    print("Servidor:", SERVIDOR_SQL)
    print("Base:", BASE_DATOS_SQL)
    print("df_completo:", df_completo.shape)
    print("alertas_df:", alertas_df.shape)
    print("df_score:", df_score.shape)

    return df_completo, alertas_df, df_score
