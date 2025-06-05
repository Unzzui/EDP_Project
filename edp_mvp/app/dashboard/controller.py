from flask import Blueprint, render_template, request, redirect, url_for, flash,jsonify
from ..utils.gsheet import read_sheet, update_row,log_cambio_edp, read_log, crear_incidencia, leer_incidencias, actualizar_incidencia, agregar_comentario_incidencia
from pandas import isna
from datetime import datetime, timedelta
import pandas as pd
from ..extensions import socketio
from flask import session  # arriba del archivo
from flask import make_response
import numpy as np



controller_bp = Blueprint("controller_bp", __name__,url_prefix="/controller")



METAS_ENCARGADOS = {
    "Diego Bravo": 375_000_000,
    "Carolina López": 375_000_000,
    "Pedro Rojas": 375_000_000,
    "Ana Pérez": 375_000_000,
}


    # === Meta Financiera Global ===
META_GLOBAL = 1_500_000_000


def enriquecer_df_con_estado_detallado(df_edp, df_log):
    """
    Enriquece el DataFrame de EDPs con el estado detallado más reciente de cada EDP
    extrayendo esta información del log de cambios.
    
    Args:
        df_edp: DataFrame de EDPs
        df_log: DataFrame del log de cambios
    
    Returns:
        DataFrame de EDPs enriquecido con la columna 'Estado Detallado'
    """
    # Crear una copia para no modificar el original
    df_enriquecido = df_edp.copy()
    
    # Asegurar que existe la columna 'Estado Detallado'
    if 'Estado Detallado' not in df_enriquecido.columns:
        df_enriquecido['Estado Detallado'] = ''
    
    # Filtrar los registros de log que son cambios de 'Estado Detallado'
    cambios_estado = df_log[df_log['Campo'] == 'Estado Detallado'].copy()
    
    # Si no hay registros, devolver el DataFrame original
    if cambios_estado.empty:
        print("No se encontraron registros de 'Estado Detallado' en el log")
        return df_enriquecido
    
    # Convertir la columna 'Fecha y Hora' a datetime para ordenar por fecha
    cambios_estado['Fecha y Hora'] = pd.to_datetime(cambios_estado['Fecha y Hora'], errors='coerce')
    
    # Para cada EDP, obtener el último estado detallado
    for num_edp in df_enriquecido['N° EDP'].unique():
        # Filtrar cambios para este EDP
        cambios_edp = cambios_estado[cambios_estado['N° EDP'] == str(num_edp)]
        
        if not cambios_edp.empty:
            # Ordenar por fecha descendente y tomar el más reciente
            ultimo_cambio = cambios_edp.sort_values('Fecha y Hora', ascending=False).iloc[0]
            ultimo_estado = ultimo_cambio['Después']
            
            # Actualizar el estado en el DataFrame enriquecido
            df_enriquecido.loc[df_enriquecido['N° EDP'] == num_edp, 'Estado Detallado'] = ultimo_estado
    
    # También identificar re-trabajos por campos relacionados como "Motivo No-aprobado"
    motivos_rechazo = df_log[df_log['Campo'] == 'Motivo No-aprobado'].copy()
    if not motivos_rechazo.empty:
        for num_edp in motivos_rechazo['N° EDP'].unique():
            # Si hay un motivo de rechazo pero no hay estado detallado, asumir "re-trabajo solicitado"
            mask = (df_enriquecido['N° EDP'] == num_edp) & (df_enriquecido['Estado Detallado'] == '')
            if mask.any():
                df_enriquecido.loc[mask, 'Estado Detallado'] = 're-trabajo solicitado'
    
    return df_enriquecido

def obtener_meses_ordenados(df):
    """
    Obtiene los meses únicos del DataFrame y los ordena cronológicamente.
    
    Args:
        df (DataFrame): DataFrame con una columna 'Mes'
        
    Returns:
        list: Lista de meses ordenados cronológicamente
    """
    try:
        # Verificar que la columna existe
        if "Mes" not in df.columns:
            print("WARNING: Columna 'Mes' no encontrada en el DataFrame")
            return []
            
        # Obtener meses únicos y eliminar valores nulos
        meses = df["Mes"].dropna().unique()
        
        # Si no hay meses, devolver lista vacía
        if len(meses) == 0:
            return []
            
        # Función para convertir nombres de mes a números para ordenamiento
        def mes_a_numero(mes_str):
            try:
                # Si el mes tiene formato YYYY-MM
                if "-" in mes_str:
                    year, month = mes_str.split("-")
                    return int(year) * 100 + int(month)
                
                # Si el mes incluye año (ej: "Enero 2023")
                partes = mes_str.split()
                if len(partes) >= 2 and partes[-1].isdigit():
                    mes_nombre = " ".join(partes[:-1]).lower()
                    año = int(partes[-1])
                    
                    # Mapeo de nombres de meses a números
                    mapeo_meses = {
                        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
                    }
                    
                    mes_num = mapeo_meses.get(mes_nombre, 0)
                    return año * 100 + mes_num  # 202301, 202302, etc.
                else:
                    # Si solo es el nombre del mes
                    mes_nombre = mes_str.lower()
                    mapeo_meses = {
                        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
                    }
                    return mapeo_meses.get(mes_nombre, 0)
            except Exception as e:
                print(f"Error procesando mes '{mes_str}': {str(e)}")
                return 0
                
        # Ordenar meses
        return sorted(meses, key=mes_a_numero)
        
    except Exception as e:
        import traceback
        print(f"Error en obtener_meses_ordenados: {str(e)}")
        print(traceback.format_exc())
        return []

def clean_nat_values(data):
    """
    Limpia valores NaT (Not a Time) de pandas convirtiéndolos en None
    para que puedan ser serializados a JSON.
    
    Funciona tanto con diccionarios como con listas de diccionarios.
    """
    if isinstance(data, list):
        # Si recibimos una lista de diccionarios, procesarla iterativamente
        return [clean_nat_values(item) for item in data]
    
    # Caso base: data es un diccionario
    if not isinstance(data, dict):
        return data
        
    result = {}
    for key, value in data.items():
        if pd.isna(value) or value == 'NaT' or str(value) == 'NaT':
            result[key] = None
        elif isinstance(value, dict):
            result[key] = clean_nat_values(value)  # Recursivamente para sub-diccionarios
        elif isinstance(value, list):
            result[key] = [clean_nat_values(item) if isinstance(item, dict) else item for item in value]
        else:
            result[key] = value
    return result

def calcular_dias_espera(df):
    """Calcula correctamente los días de espera según las reglas de negocio"""
    now = datetime.now()
    
    # Crear la columna de días de espera correctamente
    df['Días Espera'] = None
    
    for idx, row in df.iterrows():
        # Verificar si hay fecha de envío
        if pd.notna(row.get('Fecha Envío al Cliente')):
            fecha_envio = row['Fecha Envío al Cliente']
            
            # Si tiene conformidad enviada, contar días hasta la fecha de conformidad
            if row.get('Conformidad Enviada') == 'Sí' and pd.notna(row.get('Fecha Conformidad')):
                df.at[idx, 'Días Espera'] = (row['Fecha Conformidad'] - fecha_envio).days
            # Si no tiene conformidad, contar días hasta hoy
            else:
                df.at[idx, 'Días Espera'] = (now - fecha_envio).days
    
    return df

def calcular_dias_habiles(fecha_inicio, fecha_fin):
    """
    Calcula días hábiles entre dos fechas, sin incluir la fecha de inicio.
    """
    if pd.isna(fecha_inicio) or pd.isna(fecha_fin):
        return "—"
    dias = pd.bdate_range(start=fecha_inicio, end=fecha_fin)
    return max(len(dias) - 1, 0)

@controller_bp.route("/dashboard")
def dashboard_controller():
    """
    Dashboard principal del controlador con KPIs, métricas financieras y análisis de EDPs.
    Optimizado para rendimiento y claridad.
    """
    # === CARGA Y PREPARACIÓN DE DATOS ===
    df_full = read_sheet("edp!A1:V")
    df_log = read_sheet("log!A1:G")
    
    # Enriquecer con datos del log
    df_full = enriquecer_df_con_estado_detallado(df_full, df_log)
    
    # Ahora puedes usar la columna Estado Detallado con seguridad
    total_retrabajos = len(df_full[df_full["Estado Detallado"] == "re-trabajo solicitado"])
    
    # Preparar opciones para filtros
    filter_options = {
        "meses": sorted(df_full["Mes"].dropna().unique()),
        "clientes": sorted(df_full["Cliente"].dropna().unique()),
        "encargados": sorted(df_full["Jefe de Proyecto"].dropna().unique()),
        "estados_detallados": sorted(df_full["Estado Detallado"].dropna().unique()) if "Estado Detallado" in df_full.columns else []
    }
    
    # === APLICAR FILTROS ===
    filters = {
        "mes": request.args.get("mes"),
        "encargado": request.args.get("encargado"),
        "cliente": request.args.get("cliente"),
        "estado": request.args.get("estado"),
        "estado_detallado": request.args.get("estado_detallado")
    }
    
    # Aplicar filtros al dataframe
    df = df_full.copy()
    if filters["mes"]:
        df = df[df["Mes"] == filters["mes"]]
    if filters["encargado"]:
        df = df[df["Jefe de Proyecto"] == filters["encargado"]]
    if filters["cliente"]:
        df = df[df["Cliente"] == filters["cliente"]]

    # Aplicar filtro de estado con nueva lógica
    if filters["estado"] == "pendientes":
        # Filtro "Pendientes" - solo muestra estados de revisión y enviado
        df = df[df["Estado"].isin(["revisión", "enviado"])]
    elif filters["estado"] == "todos":  # Nueva opción explícita para "Todos"
        # No aplicar filtro de estado, mostrar todo
        pass
    elif filters["estado"]:
        # Filtro específico (validado, pagado, etc)
        df = df[df["Estado"] == filters["estado"]]
    elif not filters["estado_detallado"]:
        # Filtro predeterminado al cargar la página
        df = df[df["Estado"].isin(["revisión", "enviado"])]
    
    # === KPIs GLOBALES ===
    kpis_globales = {
        "total_edp_global": df_full.shape[0],
        "total_validados_global": df_full[df_full["Validado"]].shape[0],
        "dias_espera_promedio_global": round(df_full["Días Espera"].mean() or 0, 1)
    }
    
    # Cálculos derivados
    validados_rapidos_global = df_full[(df_full["Validado"]) & (df_full["Días Espera"] <= 30)].shape[0]
    kpis_globales["porcentaje_validacion_rapida_global"] = (
        round(validados_rapidos_global / kpis_globales["total_validados_global"] * 100, 1)
        if kpis_globales["total_validados_global"] > 0 else 0
    )
    
    # === KPIs FILTRADOS ===
    kpis_filtrados = {
        "total_filtrados": df.shape[0],
        "total_criticos_filtrados": df[df["Crítico"]].shape[0],
        "dias_espera_promedio_filtrado": round(df["Días Espera"].mean() or 0, 1),
        "dias_habiles_promedio_filtrado": round(df["Días Hábiles"].mean() or 0, 1)
    }
    
    # === MÉTRICAS FINANCIERAS ===
    metricas_financieras = {
        "total_pagado_global": df_full[df_full["Estado"] == "pagado"]["Monto Aprobado"].sum(),
        "total_propuesto_global": df_full["Monto Propuesto"].sum(),
        "total_aprobado_global": df_full["Monto Aprobado"].sum(),
        "meta_global": META_GLOBAL
    }
    
        # === KPIs FINANCIEROS FILTRADOS ===
    dso_filtrado = calcular_dso_para_dataset(df) if not df.empty else 0
    total_pendiente_filtrado = df[df["Estado"].isin(["enviado", "pendiente", "revisión"])]["Monto Propuesto"].sum()
    total_pagado_filtrado = df[df["Estado"].isin(["pagado", "validado"])]["Monto Aprobado"].sum()
    
    # Cálculos financieros derivados
    metricas_financieras["diferencia_montos"] = metricas_financieras["total_aprobado_global"] - metricas_financieras["total_propuesto_global"]
    metricas_financieras["porcentaje_diferencia"] = round(
        (metricas_financieras["diferencia_montos"] / metricas_financieras["total_propuesto_global"] * 100), 1
    ) if metricas_financieras["total_propuesto_global"] > 0 else 0
    metricas_financieras["avance_global"] = round(
        metricas_financieras["total_pagado_global"] / META_GLOBAL * 100, 1
    ) if META_GLOBAL > 0 else 0
    
    # === VARIACIONES MENSUALES ===
    variaciones = calcular_variaciones_mensuales(
        df_full, filters["mes"], filter_options["meses"], 
        metricas_financieras["total_pagado_global"], 
        META_GLOBAL
    )
    
    # === META POR ENCARGADO ===
    info_encargado = {
        "meta_por_encargado": METAS_ENCARGADOS.get(filters["encargado"], 0),
        "monto_pagado_encargado": 0,
        "avance_encargado": 0,
        "monto_pendiente_encargado": 0
    }
    
    if filters["encargado"]:
        info_encargado["monto_pagado_encargado"] = df[df["Estado"] == "pagado"]["Monto Aprobado"].sum()
        pendiente_por_pago = df[df["Estado"].isin(["pendiente", "revisión", 'enviado'])]["Monto Aprobado"].sum() or 0
        
        if info_encargado["meta_por_encargado"] > 0:
            info_encargado["avance_encargado"] = round(
                info_encargado["monto_pagado_encargado"] / info_encargado["meta_por_encargado"] * 100, 1
            )
            info_encargado["monto_pendiente_encargado"] = pendiente_por_pago
    
    # === KPIs DE CONFORMIDAD ===
    kpis_conformidad = {
        "total_con_conformidad": df_full[df_full["Conformidad Enviada"] == "Sí"].shape[0],
    }
    
    kpis_conformidad["porcentaje_conformidad"] = round(
        (kpis_conformidad["total_con_conformidad"] / kpis_globales["total_edp_global"] * 100), 1
    ) if kpis_globales["total_edp_global"] > 0 else 0
    
    # Tiempo promedio hasta conformidad (optimizado con vectorización)
    mask_fechas_validas = (~pd.isna(df_full["Fecha Envío al Cliente"])) & (~pd.isna(df_full["Fecha Conformidad"]))
    if any(mask_fechas_validas):
        tiempos_conformidad = (df_full.loc[mask_fechas_validas, "Fecha Conformidad"] - 
                              df_full.loc[mask_fechas_validas, "Fecha Envío al Cliente"]).dt.days
        kpis_conformidad["tiempo_promedio_conformidad"] = round(tiempos_conformidad.mean(), 1) if not tiempos_conformidad.empty else 0
    else:
        kpis_conformidad["tiempo_promedio_conformidad"] = 0
    
    # === ANÁLISIS DE RETRABAJOS ===
    analisis_retrabajos = {
        "total_retrabajos": df_full[df_full["Estado Detallado"] == "re-trabajo solicitado"].shape[0],
    }
    
    analisis_retrabajos["porcentaje_retrabajos"] = round(
        (analisis_retrabajos["total_retrabajos"] / kpis_globales["total_edp_global"] * 100), 1
    ) if kpis_globales["total_edp_global"] > 0 else 0
    
    # Distribución de motivos y fallas
    analisis_retrabajos["motivos_rechazo"] = df_full["Motivo No-aprobado"].value_counts().to_dict() if "Motivo No-aprobado" in df_full.columns else {}
    analisis_retrabajos["tipos_falla"] = df_full["Tipo_falla"].value_counts().to_dict() if "Tipo_falla" in df_full.columns else {}
    
    # === DATOS DE REGISTROS (para tabla y KPIs específicos) ===
    registros = df.to_dict(orient="records")
    registros_full = df_full.to_dict(orient="records")
    
    # === PROCESAMIENTO DE DATOS PARA KPIs DE PAGOS Y COBROS ===
    # Análisis de EDPs pagados/conformados
    edps_pagados_conformados = [
        edp for edp in registros_full
        if edp.get('Estado') in ['pagado', 'validado'] 
    ]
    
    pagos_data = {
        "total_edp_pagados_conformados": len(edps_pagados_conformados),
        "total_pagado_global_kpi": sum(float(edp.get('Monto Aprobado', 0)) for edp in edps_pagados_conformados),
    }
    
    # Desglose por antigüedad de pagados
    pagos_data["pagado_reciente"] = sum(float(edp.get('Monto Aprobado', 0)) for edp in edps_pagados_conformados if edp.get('Días Espera', 0) <= 30)
    pagos_data["pagado_medio"] = sum(float(edp.get('Monto Aprobado', 0)) for edp in edps_pagados_conformados if 30 < edp.get('Días Espera', 0) <= 60)
    pagos_data["pagado_critico"] = sum(float(edp.get('Monto Aprobado', 0)) for edp in edps_pagados_conformados if edp.get('Días Espera', 0) > 60)
    
    
    # Análisis de EDPs pendientes por cobrar
    edps_por_cobrar = [
        edp for edp in registros_full  # Usar registros_full en vez de registros
        if edp.get('Estado') in ['enviado', 'pendiente', 'revisión']
    ]

    pendientes_data = {
        "total_edps_por_cobrar": len(edps_por_cobrar),
        "total_pendiente_por_cobrar": sum(float(edp.get('Monto Propuesto', 0)) for edp in edps_por_cobrar),
    }
    # Desglose por antigüedad de pendientes
    pendientes_data["pendiente_reciente"] = sum(float(edp.get('Monto Propuesto', 0)) for edp in edps_por_cobrar if edp.get('Días Espera', 0) <= 30)
    pendientes_data["pendiente_medio"] = sum(float(edp.get('Monto Propuesto', 0)) for edp in edps_por_cobrar if 30 < edp.get('Días Espera', 0) <= 60)
    pendientes_data["pendiente_critico"] = sum(float(edp.get('Monto Propuesto', 0)) for edp in edps_por_cobrar if edp.get('Días Espera', 0) > 60)
    
        # === CALCULAR DSO (Días de Venta Pendientes de Cobro) ===
    mes_anterior = None
    df_mes_anterior = None
    if filters["mes"] and len(filter_options["meses"]) > 1:
        try:
            idx_mes_actual = filter_options["meses"].index(filters["mes"])
            mes_anterior = filter_options["meses"][idx_mes_actual - 1] if idx_mes_actual > 0 else None
            if mes_anterior:
                df_mes_anterior = df_full[df_full["Mes"] == mes_anterior]
        except ValueError:
            pass
    
    dso_global, dso_var, top_dso_proyectos = calcular_dso(df_full, mes_anterior, df_mes_anterior)
    
    
    # === RENDERIZAR TEMPLATE CON TODOS LOS DATOS ===
    return render_template(
        "controller/controller_dashboard.html",
        # Datos base
        registros=registros,
        filtros=filters,
        
        
        
        # Opciones para filtros
        meses=filter_options["meses"],
        encargados=filter_options["encargados"],
        clientes=filter_options["clientes"],
        estados_detallados=filter_options["estados_detallados"],
        
        # DSO - Días de Venta Pendientes de Cobro
        dso_global=dso_global,
        dso_var=dso_var,
        top_dso_proyectos=top_dso_proyectos,
        # Nuevos parámetros de KPIs financieros filtrados
        dso_filtrado=dso_filtrado,
        total_pendiente_filtrado=total_pendiente_filtrado,
        total_pagado_filtrado=total_pagado_filtrado,
    
        
        # Todos los KPIs y métricas
        **kpis_globales,
        **kpis_filtrados,
        **metricas_financieras,
        **variaciones,
        **info_encargado,
        **kpis_conformidad,
        **analisis_retrabajos,
        **pagos_data,
        **pendientes_data,
        
    )


def calcular_variaciones_mensuales(df_full, mes_actual_param, meses_disponibles, total_pagado_global, META_GLOBAL):
    """
    Calcula las variaciones de métricas respecto al mes anterior.
    Extrae esta lógica para mejorar la legibilidad del código principal.
    """
    variaciones = {
        "meta_var_porcentaje": 0,
        "pagado_var_porcentaje": 0,
        "pendiente_var_porcentaje": 0,
        "avance_var_porcentaje": 0
    }
    
    mes_actual = mes_actual_param if mes_actual_param else max(meses_disponibles)
    mes_anterior = None
    
    if mes_actual and len(meses_disponibles) > 1:
        try:
            idx_mes_actual = meses_disponibles.index(mes_actual)
            mes_anterior = meses_disponibles[idx_mes_actual - 1] if idx_mes_actual > 0 else None
        except ValueError:
            pass
    
    if mes_anterior:
        df_mes_anterior = df_full[df_full["Mes"] == mes_anterior]
        
        # Métricas del mes anterior
        meta_mes_anterior = META_GLOBAL  # Asumiendo META_GLOBAL constante
        pagado_mes_anterior = df_mes_anterior[df_mes_anterior["Estado"] == "pagado"]["Monto Aprobado"].sum()
        avance_mes_anterior = round(pagado_mes_anterior / meta_mes_anterior * 100, 1) if meta_mes_anterior > 0 else 0
        
        # Cálculo de variaciones
        variaciones["pagado_var_porcentaje"] = round(
            ((total_pagado_global - pagado_mes_anterior) / pagado_mes_anterior * 100) if pagado_mes_anterior else 0, 1
        )
        
        # Variaciones de pendientes
        pendiente_actual = META_GLOBAL - total_pagado_global
        pendiente_anterior = meta_mes_anterior - pagado_mes_anterior
        variaciones["pendiente_var_porcentaje"] = round(
            ((pendiente_actual - pendiente_anterior) / pendiente_anterior * 100) if pendiente_anterior else 0, 1
        )
        
        # Variación de avance (en puntos porcentuales)
        avance_global = round(total_pagado_global / META_GLOBAL * 100, 1) if META_GLOBAL > 0 else 0
        variaciones["avance_var_porcentaje"] = round(avance_global - avance_mes_anterior, 1)
    
    return variaciones


# Añadir después de la función calcular_variaciones_mensuales()
def calcular_dso_para_dataset(df_datos):
    """
    Calcula el DSO (Days Sales Outstanding) para un dataset específico
    """
    # Check if the required columns exist
    fecha_pago_exists = "Fecha Pago" in df_datos.columns
    fecha_conformidad_exists = "Fecha Conformidad" in df_datos.columns
    fecha_emision_exists = "Fecha Emisión" in df_datos.columns
    
    if not fecha_emision_exists:
        return 0
    
    # Create a mask based on available columns
    mask_conditions = []
    
    if fecha_pago_exists:
        mask_conditions.append(~pd.isna(df_datos["Fecha Pago"]))
    
    if fecha_conformidad_exists:
        mask_conditions.append(~pd.isna(df_datos["Fecha Conformidad"]))
    
    if not mask_conditions:
        return 0
    
    # Combine conditions with OR (|)
    mask = mask_conditions[0]
    for condition in mask_conditions[1:]:
        mask = mask | condition
    
    df_calculable = df_datos[
        (~pd.isna(df_datos["Fecha Emisión"])) & mask
    ].copy()
    
    if df_calculable.empty:
        return 0
    
    # Create Fecha Final column based on available data
    if fecha_pago_exists and fecha_conformidad_exists:
        df_calculable["Fecha Final"] = df_calculable.apply(
            lambda x: x["Fecha Pago"] if not pd.isna(x["Fecha Pago"]) else x["Fecha Conformidad"], 
            axis=1
        )
    elif fecha_pago_exists:
        df_calculable["Fecha Final"] = df_calculable["Fecha Pago"]
    elif fecha_conformidad_exists:
        df_calculable["Fecha Final"] = df_calculable["Fecha Conformidad"]
    
    df_calculable["Días Cobro"] = (df_calculable["Fecha Final"] - df_calculable["Fecha Emisión"]).dt.days
    df_calculable = df_calculable[df_calculable["Días Cobro"] >= 0]
    
    montos = df_calculable["Monto Aprobado"].values
    dias = df_calculable["Días Cobro"].values
    
    if len(montos) == 0 or sum(montos) == 0:
        return 0
    
    dso = np.average(dias, weights=montos)
    return round(dso, 1)
def calcular_dso(df_datos, mes_anterior=None, df_mes_anterior=None):
    """
    Calcula el DSO (Days Sales Outstanding) y metrics relacionadas
    
    Args:
        df_datos: DataFrame con datos de EDPs
        mes_anterior: Mes anterior para comparación
        df_mes_anterior: DataFrame filtrado por mes anterior
        
    Returns:
        Tuple con (dso_global, dso_var, top_dso_proyectos)
    """
    # Check if the required columns exist
    fecha_pago_exists = "Fecha Pago" in df_datos.columns
    fecha_conformidad_exists = "Fecha Conformidad" in df_datos.columns
    fecha_emision_exists = "Fecha Emisión" in df_datos.columns
    
    if not fecha_emision_exists:
        print("WARNING: Column 'Fecha Emisión' not found in DataFrame")
        return 0, 0, []
    
    # Create a mask based on available columns
    mask_conditions = []
    
    if fecha_pago_exists:
        mask_conditions.append(~pd.isna(df_datos["Fecha Pago"]))
    
    if fecha_conformidad_exists:
        mask_conditions.append(~pd.isna(df_datos["Fecha Conformidad"]))
    
    # If no date columns available for comparison, return defaults
    if not mask_conditions:
        print("WARNING: Neither 'Fecha Pago' nor 'Fecha Conformidad' columns found")
        return 0, 0, []
    
    # Combine conditions with OR (|)
    mask = mask_conditions[0]
    for condition in mask_conditions[1:]:
        mask = mask | condition
    
    # Filter dataframe based on emission date and payment/conformity dates
    df_calculable = df_datos[
        (~pd.isna(df_datos["Fecha Emisión"])) & mask
    ].copy()
    
    if df_calculable.empty:
        return 0, 0, []
    
    # Create Fecha Final column based on available data
    if fecha_pago_exists and fecha_conformidad_exists:
        df_calculable["Fecha Final"] = df_calculable.apply(
            lambda x: x["Fecha Pago"] if not pd.isna(x["Fecha Pago"]) else x["Fecha Conformidad"], 
            axis=1
        )
    elif fecha_pago_exists:
        df_calculable["Fecha Final"] = df_calculable["Fecha Pago"]
    elif fecha_conformidad_exists:
        df_calculable["Fecha Final"] = df_calculable["Fecha Conformidad"]
    
    # Calculate days between emission and payment/conformity
    df_calculable["Días Cobro"] = (df_calculable["Fecha Final"] - df_calculable["Fecha Emisión"]).dt.days
    
    # Filter negative or outlier values
    df_calculable = df_calculable[df_calculable["Días Cobro"] >= 0]
    
    # Calculate DSO weighted by amount
    montos = df_calculable["Monto Aprobado"].values
    dias = df_calculable["Días Cobro"].values
    
    if len(montos) == 0 or sum(montos) == 0:
        return 0, 0, []
    
    # Use numpy for weighted average
    import numpy as np
    dso_global = np.average(dias, weights=montos)
    
    dso_var = 0
    if mes_anterior and df_mes_anterior is not None:
        # NUEVO: Verificar columnas en df_mes_anterior
        mes_anterior_fecha_pago_exists = "Fecha Pago" in df_mes_anterior.columns
        mes_anterior_fecha_conformidad_exists = "Fecha Conformidad" in df_mes_anterior.columns
        
        # Construir condición dinámica
        filter_conditions = [~pd.isna(df_mes_anterior["Fecha Emisión"])]
        
        if mes_anterior_fecha_pago_exists:
            filter_conditions.append(~pd.isna(df_mes_anterior["Fecha Pago"]))
        
        if mes_anterior_fecha_conformidad_exists:
            filter_conditions.append(~pd.isna(df_mes_anterior["Fecha Conformidad"]))
        
        # Combinar condiciones
        combined_condition = filter_conditions[0]
        if len(filter_conditions) > 1:
            for i in range(1, len(filter_conditions)):
                combined_condition = combined_condition | filter_conditions[i]
        
        df_calculable_anterior = df_mes_anterior[combined_condition].copy()
        
        if not df_calculable_anterior.empty:
            # Definir "Fecha Final" basada en las columnas disponibles
            if mes_anterior_fecha_pago_exists and mes_anterior_fecha_conformidad_exists:
                df_calculable_anterior["Fecha Final"] = df_calculable_anterior.apply(
                    lambda x: x["Fecha Pago"] if not pd.isna(x["Fecha Pago"]) else x["Fecha Conformidad"], 
                    axis=1
                )
            elif mes_anterior_fecha_pago_exists:
                df_calculable_anterior["Fecha Final"] = df_calculable_anterior["Fecha Pago"]
            elif mes_anterior_fecha_conformidad_exists:
                df_calculable_anterior["Fecha Final"] = df_calculable_anterior["Fecha Conformidad"]
            else:
                # Sin columnas de fecha disponibles, no se puede calcular DSO anterior
                return dso_global, 0, top_proyectos
         
    
    # Top 3 proyectos con mayor tiempo pendiente
    top_proyectos = []
    df_pendientes = df_datos[df_datos["Estado"].isin(["enviado", "pendiente", "revisión"])].copy()
    
    if not df_pendientes.empty and fecha_emision_exists:
        df_pendientes["Días Pendiente"] = (pd.Timestamp.now().normalize() - df_pendientes["Fecha Emisión"]).dt.days
        top_3 = df_pendientes.sort_values("Días Pendiente", ascending=False).head(3)
        
        top_proyectos = [
            {
                "id": row.get("N° EDP", ""), 
                "nombre": row.get("Proyecto", "Sin nombre"), 
                "dias": int(row.get("Días Pendiente", 0)),
                "monto": row.get("Monto Aprobado", 0),
                "encargado": row.get("Jefe de Proyecto", "")  # Add project manager
            }
            for _, row in top_3.iterrows() if not pd.isna(row.get("Días Pendiente", None))
        ]
    return round(dso_global, 1), round(dso_var, 1), top_proyectos
    


 
@controller_bp.route("api/export-all-csv")
def export_all_csv():
    """
    Exportar todos los datos de EDPs a CSV sin aplicar filtros.
    """
    try:
        # Leer todos los datos
        df = read_sheet("edp!A1:V")
        
        # Formatear fechas para CSV
        for col in df.select_dtypes(include=['datetime64']).columns:
            df[col] = df[col].dt.strftime('%d-%m-%Y')
        
        # Convertir a CSV
        csv_data = df.to_csv(index=False)
        
        # Crear respuesta
        response = make_response(csv_data)
        response.headers["Content-Disposition"] = "attachment; filename=edp_completo.csv"
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        
        return response
    except Exception as e:
        import traceback
        print(f"Error exportando CSV completo: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@controller_bp.route("api/get-edp/<edp_id>", methods=["GET"])
def get_edp_data(edp_id):
    """Obtener datos de un EDP específico para mostrar en modales"""
    try:
        df = read_sheet("edp!A1:V")
        edp = df[df["N° EDP"] == str(edp_id)]
        
        if edp.empty:
            return jsonify({"error": f"EDP {edp_id} no encontrado"}), 404
            
        # Convertir a diccionario para la respuesta JSON
        edp_data = edp.iloc[0].to_dict()
        
        # Asegurar que las fechas estén en formato YYYY-MM-DD para campos de fecha
        for campo in ['Fecha Emisión', 'Fecha Envío al Cliente', 'Fecha Estimada de Pago', 'Fecha Conformidad']:
            if campo in edp_data and edp_data[campo]:
                try:
                    # Intentar convertir a formato de fecha estándar
                    fecha = pd.to_datetime(edp_data[campo])
                    edp_data[campo] = fecha.strftime('%Y-%m-%d')
                except:
                    # Si falla la conversión, mantener el valor original
                    pass
        
        return jsonify(edp_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@controller_bp.route("/api/edp-details/<n_edp>", methods=["GET"])
def api_get_edp_details(n_edp):
    """API para obtener detalles de un EDP en formato JSON"""
    df = read_sheet("edp!A1:V")
    edp = df[df["N° EDP"] == n_edp]
    
    if edp.empty:
        return jsonify({"error": "EDP no encontrado"}), 404
        
    edp_data = edp.iloc[0].to_dict()
    
    # Limpiar valores NaT/NaN y formatear fechas
    for key, value in edp_data.items():
        if pd.isna(value):
            edp_data[key] = None
        elif isinstance(value, pd.Timestamp):
            edp_data[key] = value.strftime("%Y-%m-%d")
    
    return jsonify(edp_data)

@controller_bp.route("api/update-edp/<n_edp>", methods=["POST"])
def api_update_edp(n_edp):
    """API para actualizar un EDP desde el modal"""
    try:
        # 1. Obtener datos del EDP
        df = read_sheet("edp!A1:V")
        edp = df[df["N° EDP"] == n_edp]
      
        if edp.empty:
            return jsonify({"success": False, "message": "EDP no encontrado"}), 404
        
        row_idx = edp.index[0] + 2  # +1 por header, +1 porque Sheets arranca en 1
        
        # 2. Preparar actualizaciones
        updates = {
            "Estado": request.form.get("estado") or "",
            "Estado Detallado": request.form.get("estado_detallado") or "",
            "Conformidad Enviada": request.form.get("conformidad_enviada") or "",
            "N° Conformidad": request.form.get("n_conformidad") or "",
            "Monto Propuesto": request.form.get("monto_propuesto") or "",
            "Monto Aprobado": request.form.get("monto_aprobado") or "",
            "Fecha Estimada de Pago": request.form.get("fecha_estimada_pago") or "",
            "Crítico": request.form.get("critico") == "true",
            "Observaciones": request.form.get("observaciones") or "",
        }
        
        # 3. Incluir campos condicionales
        if updates["Estado Detallado"] == "re-trabajo solicitado":
            updates["Motivo No-aprobado"] = request.form.get("motivo_no_aprobado") or ""
            updates["Tipo_falla"] = request.form.get("tipo_falla") or ""
        
        # 4. Aplicar reglas automáticas
        if updates["Estado"] in ["pagado", "validado"]:
            updates["Conformidad Enviada"] = "Sí"
        
        # 5. Registrar cambios en log
        usuario = session.get("usuario", "Sistema")
        edp_data = edp.iloc[0].to_dict()
        
        for campo, nuevo in updates.items():
            viejo = str(edp_data.get(campo, ""))
            if nuevo != "" and nuevo != viejo:
                log_cambio_edp(n_edp=n_edp, proyecto=edp_data.get('Proyecto'), campo=campo, 
                               antes=viejo, despues=nuevo, usuario=usuario)        
        # 6. CORREGIDO: Pasar correctamente los argumentos
        update_row(row_idx, updates,"edp",  usuario=usuario, force_update=True)
        
        return jsonify({"success": True, "message": "EDP actualizado correctamente"})
        
    except Exception as e:
        import traceback
        print(f"Error en api_update_edp: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@controller_bp.route("id/<n_edp>", methods=["GET", "POST"])
def detalle_edp(n_edp):
    """
    Vista detallada de un EDP, ahora usando el ID único como parámetro
    aunque manteniendo la compatibilidad con la ruta existente
    """
    # ----------- LECTURA -----------
    df = read_sheet("edp!A1:V")        # ahora 22 columnas
    edp = get_edp_by_unique_id(n_edp)


    if edp.empty:
        flash("ID no encontrada", "error")
        return redirect(url_for("controller_bp.dashboard_controller"))

    row_idx  = edp.index[0] + 2        # +1 por header, +1 porque Sheets arranca en 1
    edp_data = edp.iloc[0].to_dict()

    # ----------- KPI de tiempo -----------
    fecha_envio       = edp_data.get("Fecha Envío al Cliente")
    fecha_conformidad = edp_data.get("Fecha Conformidad")

    if not isna(fecha_envio):
        fin = fecha_conformidad if not isna(fecha_conformidad) else datetime.today()
        edp_data["dias_espera"]  = (fin - fecha_envio).days
        edp_data["dias_habiles"] = calcular_dias_habiles(fecha_envio, fin)
    else:
        edp_data["dias_espera"] = edp_data["dias_habiles"] = "—"

    # ----------- Fechas a string para los <input type=date> -----------
    edp_data["fecha_conf_str"]      = fecha_conformidad.strftime("%Y-%m-%d") if not isna(fecha_conformidad) else ""
    edp_data["fecha_estimada_pago"] = (
        edp_data["Fecha Estimada de Pago"].strftime("%Y-%m-%d")
        if not isna(edp_data.get("Fecha Estimada de Pago")) else ""
    )
    edp_data["fecha_emision_str"] = (
        edp_data["Fecha Emisión"].strftime("%Y-%m-%d")
        if not isna(edp_data.get("Fecha Emisión")) else ""
    )

    # ==============================================================
    # POST – guardar cambios
    # ==============================================================
    if request.method == "POST":
        f = request.form

        updates = {
            "Estado"                 : f.get("estado")                     or "",
            "Estado Detallado"       : f.get("estado_detallado")           or "",
            "Motivo No-aprobado"     : f.get("motivo_no_aprobado")         or "",
            "Tipo_falla"             : f.get("tipo_falla")                 or "",
            "Fecha Conformidad"      : f.get("fecha_conformidad")          or "",
            "Conformidad Enviada"    : f.get("conformidad_enviada")        or "",
            "N° Conformidad"         : f.get("n_conformidad")              or "",
            "Monto Propuesto"        : f.get("monto_propuesto")            or "",
            "Monto Aprobado"         : f.get("monto_aprobado")             or "",
            "Fecha Estimada de Pago" : f.get("fecha_estimada_pago")        or "",
            "Fecha Emisión"          : f.get("fecha_emision")              or "",
            "Observaciones"          : f.get("observaciones")              or "",
        }

        # ---------- Reglas automáticas ----------
     
        if updates["Estado"] in ["pagado", "validado"]:  
            updates["Conformidad Enviada"] = "Sí"
        # Si no vino nº conformidad y el usuario marcó pagado, dejamos campo vacío pero registrado.

        # Si el usuario marca re-trabajo: exige motivo + tipo de falla
        if updates["Estado Detallado"] == "re-trabajo solicitado":
            if not updates["Motivo No-aprobado"]:
                flash("Debes indicar el motivo del no-aprobado.", "warning")
                return render_template("controller/controller_edp_detalle.html",
                                       edp=edp_data, row=row_idx)
            if not updates["Tipo_falla"]:
                flash("Debes indicar el tipo de falla asociado.", "warning")
                return render_template("controller/controller_edp_detalle.html",
                                       edp=edp_data, row=row_idx)

        # ---------- Auditoría ----------
        usuario = session.get("usuario", "Sistema")  # o correo/name si usas flask-login
        for campo, nuevo in updates.items():
            viejo = str(edp_data.get(campo, ""))
            if nuevo != "" and nuevo != viejo:
                
                log_cambio_edp(
            n_edp=edp_data["N° EDP"], 
            proyecto=edp_data.get("Proyecto", "Sin proyecto"),  # Añadir proyecto
            campo=campo, 
            antes=viejo, 
            despues=nuevo, 
            usuario=usuario
        )

        # ---------- Guardar en Google Sheets ----------
        update_row(row_idx, updates, usuario=usuario, force_update=True)
        flash("EDP actualizado correctamente", "success")
        return redirect(url_for("controller_bp.dashboard_controller"))

    # GET → pintar plantilla
    return render_template(
        "controller/controller_edp_detalle.html",
        edp=edp_data,
        row=row_idx
    )



@controller_bp.route("encargado/<nombre>")
def vista_encargado(nombre):
    df_full = read_sheet("edp!A1:Q")
    df_encargado = df_full[df_full["Jefe de Proyecto"] == nombre]

    if df_encargado.empty:
        flash(f"No hay EDP registrados para {nombre}", "warning")
        return redirect(url_for("controller_bp.dashboard_controller"))

    # numéricos y flag crítico como int
    for col in ["Monto Propuesto", "Monto Aprobado"]:
        df_encargado[col] = pd.to_numeric(df_encargado[col], errors="coerce").fillna(0)
    df_encargado["Crítico"] = df_encargado["Crítico"].astype(int)

    # EDP pagados
    df_pagados = df_encargado[df_encargado["Estado"].isin(["pagado","validado"])]

    # —— resumen por proyecto ——
    resumen = (
        df_encargado.groupby("Proyecto")
        .agg(
            Total_EDP=("N° EDP", "count"),
            Críticos=("Crítico", "sum"),
            Validados=("Validado", "sum"),
            Prom_Días_Espera=("Días Espera", "mean"),
            Monto_Propuesto_Total=("Monto Propuesto", "sum"),  # Renombrado para claridad
            Monto_Aprobado_Total=("Monto Aprobado", "sum"),    # Añadido para referencia
        )
    )

    # pagado & pendiente - usando los montos APROBADOS
    monto_pagado = (
        df_pagados.groupby("Proyecto")["Monto Aprobado"].sum().rename("Monto_Pagado")
    )
    resumen = resumen.merge(monto_pagado, left_index=True, right_index=True, how="left")
    resumen["Monto_Pagado"] = resumen["Monto_Pagado"].fillna(0)
    
    # Calcular pendiente usando Monto Aprobado (para coherencia)
    resumen["Monto_Pendiente"] = resumen["Monto_Aprobado_Total"] - resumen["Monto_Pagado"]

    # % avance basado en montos aprobados (más coherente)
    resumen["%_Avance"] = (resumen["Monto_Pagado"] / resumen["Monto_Aprobado_Total"]).replace(
        [np.inf, np.nan], 0
    ) * 100
    resumen["%_Avance"] = resumen["%_Avance"].round(1)
    resumen["Prom_Días_Espera"] = resumen["Prom_Días_Espera"].round(1)

    proyectos = resumen.reset_index().to_dict(orient="records")
    
    # Totales globales
    meta_por_encargado = METAS_ENCARGADOS.get(nombre, 0)
    monto_aprobado_global = resumen["Monto_Aprobado_Total"].sum()
    monto_propuesto_global = resumen["Monto_Propuesto_Total"].sum()
    monto_pagado_global = resumen["Monto_Pagado"].sum()
    
    # Cálculos financieros basados en montos aprobados
    avance_global = (monto_pagado_global / meta_por_encargado * 100) if meta_por_encargado else 0
    monto_pendiente_global = monto_aprobado_global - monto_pagado_global
    
    
    registros_full = df_full.to_dict(orient="records")

    
        # Calcular DSO específico para este encargado
    df_encargado = df_full[df_full["Jefe de Proyecto"] == nombre]
    dso_encargado = calcular_dso_para_dataset(df_encargado) if not df_encargado.empty else 0
    dso_global = calcular_dso_para_dataset(df_full) if not df_full.empty else 0
    
    # Análisis de EDPs pagados/conformados para este encargado
    edps_pagados = [
        edp for edp in registros_full
        if edp.get('Estado') in ['pagado', 'validado'] and edp.get('Jefe de Proyecto') == nombre
    ]
    
    pagado_reciente = sum(float(edp.get('Monto Aprobado', 0)) for edp in edps_pagados if edp.get('Días Espera', 0) <= 30)
    pagado_medio = sum(float(edp.get('Monto Aprobado', 0)) for edp in edps_pagados if 30 < edp.get('Días Espera', 0) <= 60)
    pagado_critico = sum(float(edp.get('Monto Aprobado', 0)) for edp in edps_pagados if edp.get('Días Espera', 0) > 60)
    
    # Análisis de EDPs pendientes por cobrar para este encargado
    edps_pendientes = [
        edp for edp in registros_full
        if edp.get('Estado') in ['enviado', 'pendiente', 'revisión'] and edp.get('Jefe de Proyecto') == nombre
    ]
    
    pendiente_reciente = sum(float(edp.get('Monto Propuesto', 0)) for edp in edps_pendientes if edp.get('Días Espera', 0) <= 30)
    pendiente_medio = sum(float(edp.get('Monto Propuesto', 0)) for edp in edps_pendientes if 30 < edp.get('Días Espera', 0) <= 60)
    pendiente_critico = sum(float(edp.get('Monto Propuesto', 0)) for edp in edps_pendientes if edp.get('Días Espera', 0) > 60)
    
        # === MÉTRICAS PARA KPIs DINÁMICOS ===
    
    # Tendencia de cobro (últimos 3 meses)
    meses_analisis = obtener_ultimos_meses(3)
    tendencia_cobro = []
    
    for mes in meses_analisis:
        df_mes = df_full[(df_full["Mes"] == mes) & (df_full["Jefe de Proyecto"] == nombre) & 
                         (df_full["Estado"] == "pagado")]
        monto_cobrado = df_mes["Monto Aprobado"].sum()
        tendencia_cobro.append((mes, monto_cobrado))
    
    monto_cobrado_ultimo_mes = tendencia_cobro[-1][1] if tendencia_cobro else 0
    monto_cobrado_penultimo_mes = tendencia_cobro[-2][1] if len(tendencia_cobro) > 1 else 1
    
    # Variación mensual y promedio
    variacion_mensual_cobro = ((monto_cobrado_ultimo_mes - monto_cobrado_penultimo_mes) / monto_cobrado_penultimo_mes * 100) if monto_cobrado_penultimo_mes > 0 else 0
    promedio_cobro_mensual = sum(monto for _, monto in tendencia_cobro) / len(tendencia_cobro) if tendencia_cobro else 0
    maximo_cobro_mensual = max(monto for _, monto in tendencia_cobro) if tendencia_cobro else 1
    
    # Efectividad de aprobación
    edps_propuestos = df_full[df_full["Jefe de Proyecto"] == nombre].shape[0]
    edps_aprobados = df_full[(df_full["Jefe de Proyecto"] == nombre) & 
                           (df_full["Estado"].isin(["pagado", "validado"]))].shape[0]
    
    tasa_aprobacion = (edps_aprobados / edps_propuestos * 100) if edps_propuestos > 0 else 0
    tasa_aprobacion_global = (df_full[df_full["Estado"].isin(["pagado", "validado"])].shape[0] / 
                             df_full.shape[0] * 100) if df_full.shape[0] > 0 else 0
    
    # Tiempo promedio de aprobación
    mask_fechas_completas = (~pd.isna(df_full["Fecha Envío al Cliente"])) & (~pd.isna(df_full["Fecha Conformidad"]))    
    
    df_con_fechas = df_full[mask_fechas_completas & (df_full["Jefe de Proyecto"] == nombre)]
        
    if not df_con_fechas.empty:
        # Fix column names here too - they need to match what we checked in the mask
        df_con_fechas["Tiempo Aprobación"] = (df_con_fechas["Fecha Conformidad"] - df_con_fechas["Fecha Envío al Cliente"]).dt.days
        dias_promedio_aprobacion = df_con_fechas["Tiempo Aprobación"].mean()
    else:
        dias_promedio_aprobacion = 0
    
    # EDPs próximos a cobrar (hasta 15 días)
# Use datetime instead of date for pandas compatibility
    hoy = datetime.now()  # datetime object
    fecha_limite = hoy + timedelta(days=15)

    # First check if the column exists to avoid KeyError
    if "Fecha Estimada de Pago" in df_full.columns:
        # Use proper column name "Fecha Estimada de Pago" instead of "Fecha Esperada Pago"
        df_proximos = df_full[(df_full["Jefe de Proyecto"] == nombre) & 
                            (df_full["Estado"] == "validado") &
                            (~pd.isna(df_full["Fecha Estimada de Pago"])) &
                            (df_full["Fecha Estimada de Pago"] <= fecha_limite)]
    else:
        # Fallback: just filter by project manager and status if date column is missing
        df_proximos = df_full[(df_full["Jefe de Proyecto"] == nombre) & 
                            (df_full["Estado"] == "validado")]
        print("WARNING: 'Fecha Estimada de Pago' column not found, proximity filter disabled")

    monto_proximo_cobro = df_proximos["Monto Aprobado"].sum()
    cantidad_edp_proximos = df_proximos.shape[0]
    # EDPs prioritarios y con cliente
        # Replace lines 952-953 with this code:
    
    # EDPs prioritarios y con cliente - with column existence check
    if "Prioridad" in df_proximos.columns:
        cantidad_edp_prioritarios = df_proximos[df_proximos["Prioridad"] == "Alta"].shape[0]
    else:
        cantidad_edp_prioritarios = 0  # Default value if column doesn't exist
        print("WARNING: 'Prioridad' column not found in DataFrame")
        
    if "Con Cliente" in df_proximos.columns:
        cantidad_edp_con_cliente = df_proximos[df_proximos["Con Cliente"] == "Sí"].shape[0]
    else:
        cantidad_edp_con_cliente = 0  # Default value if column doesn't exist
        print("WARNING: 'Con Cliente' column not found in DataFrame")
        
    METAS_MENSUALES = {}
    # Proyección para el mes actual
    mes_actual = datetime.now().strftime('%B').lower()
    meta_mes_actual = METAS_MENSUALES.get(mes_actual, METAS_ENCARGADOS.get(nombre, 0))
    proyeccion_cobro_mes = monto_proximo_cobro + (monto_cobrado_ultimo_mes * 0.7)  # Estimación basada en próximos cobros + tendencia
    
    # Pendientes críticos (+30 días)
    df_criticos = df_full[(df_full["Jefe de Proyecto"] == nombre) &
                        (df_full["Estado"].isin(["enviado", "revisión"])) &
                        (df_full["Días Espera"] > 30)]
    
    monto_pendiente_critico = df_criticos["Monto Propuesto"].sum()
    cantidad_edp_criticos = df_criticos.shape[0]
    
    if monto_pendiente_global > 0:
        porcentaje_pendientes_criticos = round(monto_pendiente_critico / monto_pendiente_global * 100, 1)
    else:
        porcentaje_pendientes_criticos = 0
    
    # Top proyectos con pendientes críticos
    proyectos_criticos = df_criticos.groupby("Proyecto")["Monto Propuesto"].sum().reset_index()
    proyectos_criticos = proyectos_criticos.sort_values("Monto Propuesto", ascending=False)
    
    top_proyectos_criticos = [
        {"nombre": row["Proyecto"], "monto": row["Monto Propuesto"]}
        for _, row in proyectos_criticos.head(3).iterrows()
    ]
    
    
    return render_template(
        "controller/controller_encargado.html",
        nombre=nombre,
        proyectos=proyectos,
        meta_por_encargado=meta_por_encargado,
        monto_pendiente_global=monto_pendiente_global,
        monto_pagado_global=monto_pagado_global,
        monto_propuesto_global=monto_propuesto_global,
        monto_aprobado_global=monto_aprobado_global,
        avance_global=round(avance_global, 1),
        now=datetime.now(),
               # Nuevas variables para KPIs financieros
        dso_encargado=dso_encargado,
        dso_global=dso_global,
        pagado_reciente=pagado_reciente, 
        pagado_medio=pagado_medio,
        pagado_critico=pagado_critico,
        pendiente_reciente=pendiente_reciente,
        pendiente_medio=pendiente_medio,
        pendiente_critico=pendiente_critico,
        
        # Nuevas variables para KPIs dinámicos
        tendencia_cobro=tendencia_cobro,
        monto_cobrado_ultimo_mes=monto_cobrado_ultimo_mes,
        variacion_mensual_cobro=variacion_mensual_cobro,
        promedio_cobro_mensual=promedio_cobro_mensual,
        maximo_cobro_mensual=maximo_cobro_mensual,
        
        tasa_aprobacion=tasa_aprobacion,
        tasa_aprobacion_global=tasa_aprobacion_global,
        dias_promedio_aprobacion=dias_promedio_aprobacion,
        
        monto_proximo_cobro=monto_proximo_cobro,
        cantidad_edp_proximos=cantidad_edp_proximos,
        cantidad_edp_prioritarios=cantidad_edp_prioritarios,
        cantidad_edp_con_cliente=cantidad_edp_con_cliente,
        proyeccion_cobro_mes=proyeccion_cobro_mes,
        meta_mes_actual=meta_mes_actual,
        
        monto_pendiente_critico=monto_pendiente_critico,
        cantidad_edp_criticos=cantidad_edp_criticos,
        porcentaje_pendientes_criticos=porcentaje_pendientes_criticos,
        top_proyectos_criticos=top_proyectos_criticos
    )

def obtener_ultimos_meses(n_meses):
    """
    Obtiene los nombres de los últimos n_meses disponibles en los datos.
    
    Args:
        n_meses (int): Número de meses a obtener
        
    Returns:
        list: Lista con los nombres de los últimos meses disponibles.
              Si hay menos meses que los solicitados, devuelve todos los disponibles.
              Si hay error, devuelve una lista vacía.
    """
    try:
        # Leer datos de Sheets para obtener la columna de meses
        df = read_sheet("edp!A1:V")
        
        # Verificar que la columna existe
        if "Mes" not in df.columns:
            print("WARNING: Columna 'Mes' no encontrada en los datos")
            return []
        
        # Obtener meses únicos, eliminar valores nulos y ordenar
        meses_disponibles = sorted(df["Mes"].dropna().unique())
        
        if len(meses_disponibles) == 0:
            print("WARNING: No hay datos de meses en el dataframe")
            return []
            
        # Si hay menos meses disponibles que los solicitados, usar todos
        if len(meses_disponibles) <= n_meses:
            print(f"NOTA: Se solicitaron {n_meses} meses pero solo hay {len(meses_disponibles)} disponibles")
            return meses_disponibles
        
        # Devolver los últimos n_meses
        return meses_disponibles[-n_meses:]
        
    except Exception as e:
        import traceback
        print(f"ERROR en obtener_ultimos_meses: {str(e)}")
        print(traceback.format_exc())
        return []  # En caso de cualquier error, devolver lista vacía

@controller_bp.route("encargado/<nombre>/<proyecto>")
def vista_proyecto_de_encargado(nombre, proyecto):
    df_full = read_sheet("edp!A1:Q")
    # Convert numeric columns
    for col in ["Monto Propuesto", "Monto Aprobado"]:
        df_full[col] = pd.to_numeric(df_full[col], errors="coerce").fillna(0)
    
    df_filtrado = df_full[
        (df_full["Jefe de Proyecto"] == nombre) &
        (df_full["Proyecto"] == proyecto)
    ]

    if df_filtrado.empty:
        flash(f"No hay EDP registrados para {nombre} en el proyecto {proyecto}", "warning")
        return redirect(url_for("controller_bp.vista_encargado", nombre=nombre))

    registros = df_filtrado.to_dict(orient="records")
    
    # KPIs locales para el proyecto
    total_edp = df_filtrado.shape[0]
    total_criticos = df_filtrado[df_filtrado["Crítico"]].shape[0]
    total_validados = df_filtrado[df_filtrado["Validado"]].shape[0]
    promedio_dias_espera = round(df_filtrado["Días Espera"].mean() or 0, 1)
    promedio_dias_habiles = round(df_filtrado["Días Hábiles"].mean() or 0, 1)
    
    # KPIs financieros del proyecto
    monto_propuesto = df_filtrado["Monto Propuesto"].sum()
    monto_aprobado = df_filtrado["Monto Aprobado"].sum()
    
    # Considerar pagado y validado como estados válidos para pago
    df_pagados = df_filtrado[df_filtrado["Estado"].isin(["pagado", "validado"])]
    monto_pagado = df_pagados["Monto Aprobado"].sum()
    
    # Calcular diferencia entre propuesto y aprobado
    diferencia = monto_aprobado - monto_propuesto
    porcentaje_diferencia = round((diferencia / monto_propuesto * 100), 1) if monto_propuesto > 0 else 0
    
    # Avance financiero basado en monto aprobado
    avance_financiero = (monto_pagado / monto_aprobado * 100) if monto_aprobado > 0 else 0

    return render_template(
        "controller/controller_encargado_proyecto.html",
        nombre=nombre,
        proyecto=proyecto,
        registros=registros,
        total_edp=total_edp,
        total_criticos=total_criticos,
        total_validados=total_validados,
        promedio_dias_espera=promedio_dias_espera,
        promedio_dias_habiles=promedio_dias_habiles,
        monto_propuesto=monto_propuesto,
        monto_aprobado=monto_aprobado,
        diferencia=diferencia,
        porcentaje_diferencia=porcentaje_diferencia,
        monto_pagado=monto_pagado,
        avance_financiero=round(avance_financiero, 1)
    )
 
# Ruta para visualizar el log de un EDP específico desde la hoja "log"

@controller_bp.route("log/<n_edp>")
def ver_log_edp(n_edp):
    """
    Muestra el historial completo de cambios de un EDP.
    Utiliza read_log() para mantener la lógica centralizada.
    """
    df_log = read_log(n_edp=n_edp)          # ← ya filtra por N° EDP

    if df_log.empty:
        flash(f"No hay registros de cambios para el EDP {n_edp}.", "info")
        return redirect(url_for("controller_bp.dashboard_controller"))

    registros = df_log.to_dict(orient="records")

    return render_template(
        "controller/controller_log_edp.html",
        n_edp=n_edp,
        registros=registros
    )

    
@controller_bp.route("kanban")
def vista_kanban():
    """
    Vista del tablero Kanban con optimizaciones para grandes conjuntos de datos:
    - Filtrado inteligente de registros antiguos
    - Soporte para lazy loading
    - Métricas de eficiencia de datos
    - Procesamiento optimizado en un solo bucle
    """
    try:
        # Leer datos completos
        print("Leyendo datos de EDP...")
        df = read_sheet("edp!A1:V")
        df = calcular_dias_espera(df)
        
        # Convertir fechas explícitamente para evitar problemas de formato
        date_columns = ["Fecha Emisión", "Fecha Envío al Cliente", "Fecha Conformidad", "Fecha Estimada de Pago"]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Obtener parámetros de filtro
        mes = request.args.get("mes")
        encargado = request.args.get("encargado")
        cliente = request.args.get("cliente")
        estado_detallado = request.args.get("estado_detallado")
        mostrar_validados_antiguos = request.args.get("mostrar_validados_antiguos", "false").lower() == "true"

        # Capturar tamaño original para métricas
        total_registros_original = len(df)
        
        # Aplicar filtros si existen
        if mes:
            df = df[df["Mes"] == mes]
        if encargado:
            df = df[df["Jefe de Proyecto"] == encargado]
        if cliente:
            df = df[df["Cliente"] == cliente]
        if estado_detallado:
            df = df[df["Estado Detallado"] == estado_detallado]

        # Filtrar EDPs validados antiguos (más de 10 días desde conformidad)
        fecha_limite = datetime.now() - pd.Timedelta(days=10)
        
        # Contar cuántos validados antiguos hay antes de filtrar
        validados_antiguos = df[
            (df["Estado"] == "validado") & 
            (pd.notna(df["Fecha Conformidad"])) & 
            (df["Fecha Conformidad"] < fecha_limite)
        ]
        total_validados_antiguos = len(validados_antiguos)
        
        # Filtrar solo si no se solicitó mostrar todos
        if not mostrar_validados_antiguos:
            df = df[~(
                (df["Estado"] == "validado") & 
                (pd.notna(df["Fecha Conformidad"])) & 
                (df["Fecha Conformidad"] < fecha_limite)
            )]
        
        # Métricas para optimización
        total_registros_filtrados = len(df)
        porcentaje_reduccion = ((total_registros_original - total_registros_filtrados) / total_registros_original * 100) if total_registros_original > 0 else 0
        
        # Convert numeric columns for consistent calculations
        for col in ["Monto Propuesto", "Monto Aprobado"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
        # Agrupar por estado (SOLO UN BUCLE)
        estados = ["revisión", "enviado", "pagado", "validado"]
        columnas = {estado: [] for estado in estados}
        
        # Variables para análisis de carga de datos
        total_items = 0
        items_por_estado = {}
        
        # Un solo bucle que procesa todas las tarjetas con sus campos adicionales
        for _, row in df.iterrows():
            estado = row["Estado"]
            if estado in columnas:
                # Crear el diccionario base con los campos necesarios
                item = row.to_dict()
                total_items += 1
                items_por_estado[estado] = items_por_estado.get(estado, 0) + 1
                
                # Añadir campo para optimización de lazy loading
                item["lazy_index"] = items_por_estado[estado]
                
                # Procesar fechas para formato adecuado
                try:
                    if not pd.isna(row.get("Fecha Estimada de Pago")):
                        item["dias_para_pago"] = (row["Fecha Estimada de Pago"] - datetime.today()).days
                    else:
                        item["dias_para_pago"] = None
                except Exception as e:
                    item["dias_para_pago"] = None
                    print(f"Error calculando dias_para_pago: {e}")
                    
                # Añadir diferencia entre monto propuesto y aprobado
                try:
                    if not pd.isna(row.get("Monto Propuesto")) and not pd.isna(row.get("Monto Aprobado")):
                        item["diferencia_montos"] = row["Monto Aprobado"] - row["Monto Propuesto"]
                        item["porcentaje_diferencia"] = (item["diferencia_montos"] / row["Monto Propuesto"] * 100) if row["Monto Propuesto"] > 0 else 0
                    else:
                        item["diferencia_montos"] = 0
                        item["porcentaje_diferencia"] = 0
                except Exception as e:
                    item["diferencia_montos"] = 0
                    item["porcentaje_diferencia"] = 0
                    print(f"Error calculando diferencia_montos: {e}")
                
                # Clasificación de validados antiguos vs nuevos (para destacar visualmente)
                if estado == "validado" and not pd.isna(row.get("Fecha Conformidad")):
                    dias_desde_conformidad = (datetime.now() - row["Fecha Conformidad"]).days
                    item["antiguedad_validado"] = "antiguo" if dias_desde_conformidad > 10 else "reciente"
                
                # Verificar si es crítico para destacarlo visualmente
                item["es_critico"] = bool(row.get("Crítico", False))
                    
                # Agregar una sola vez a la columna correspondiente
                columnas[estado].append(item)

        # Listas únicas para los dropdowns de filtros
        meses_disponibles = sorted(df["Mes"].dropna().unique())
        encargados_disponibles = sorted(df["Jefe de Proyecto"].dropna().unique())
        clientes_disponibles = sorted(df["Cliente"].dropna().unique())
        estados_detallados = sorted(df["Estado Detallado"].dropna().unique()) if "Estado Detallado" in df.columns else []
        
        # Clean NaT values before sending to template - use helper function
        for estado, edps in columnas.items():
            for i in range(len(edps)):
                edps[i] = clean_nat_values(edps[i])
        
        # Análisis de distribución de datos para optimización
        distribucion_cards = {estado: len(items) for estado, items in columnas.items()}
        
        # Estadísticas globales para toma de decisiones
        estadisticas = {
            "total_registros": total_registros_original,
            "registros_filtrados": total_registros_filtrados,
            "porcentaje_reduccion": round(porcentaje_reduccion, 1),
            "distribucion_cards": distribucion_cards,
            "total_validados_antiguos": total_validados_antiguos
        }
                
        return render_template(
            "controller/controller_kanban.html",
            columnas=columnas,
            filtros={
                "mes": mes, 
                "encargado": encargado, 
                "cliente": cliente,
                "estado_detallado": estado_detallado,
                "mostrar_validados_antiguos": mostrar_validados_antiguos
            },
            meses=meses_disponibles,
            encargados=encargados_disponibles,
            clientes=clientes_disponibles,
            estados_detallados=estados_detallados,
            now=datetime.now(),
            total_validados_antiguos=total_validados_antiguos,
            estadisticas=estadisticas
        )
    
    except Exception as e:
        import traceback
        print(f"Error en vista_kanban: {str(e)}")
        print(traceback.format_exc())
        flash(f"Error al cargar tablero Kanban: {str(e)}", "error")
        return redirect(url_for("controller_bp.dashboard_controller"))


@controller_bp.route("kanban/update_estado", methods=["POST"])
def actualizar_estado_kanban():
    data = request.get_json()
    edp_id = data.get("edp_id")
    nuevo_estado = data.get("nuevo_estado").lower()
    conformidad_enviada = data.get("conformidad_enviada", False)

    if not edp_id or not nuevo_estado:
        return jsonify({"error": "Datos incompletos"}), 400

    # Usar el mismo rango que en otras partes del código
    df = read_sheet("edp!A1:V")
    # Asegurarse que el EDP ID sea string para comparación correcta
    edp = df[df["N° EDP"] == str(edp_id)]

    if edp.empty:
        return jsonify({"error": f"EDP {edp_id} no encontrado"}), 404

    row_idx = edp.index[0] + 2  # +2 por encabezado y 0-indexado
    edp_data = edp.iloc[0].to_dict()
    
    # Preparar cambios con estado mayor prioridad
    cambios = {"Estado": nuevo_estado + " "}  # Agregamos un espacio temporal
    
    # Usar el valor enviado desde frontend si existe
    if conformidad_enviada:
        cambios["Conformidad Enviada"] = "Sí"
    # Mantener regla de negocio como respaldo
    elif nuevo_estado == "pagado" or nuevo_estado == "validado":
        cambios["Conformidad Enviada"] = "Sí"

    # Registrar todos los cambios
    usuario = session.get("usuario", "Kanban")

    if nuevo_estado != edp_data.get("Estado"):
        log_cambio_edp(
    n_edp=edp_id,
    proyecto=edp_data.get("Proyecto", "Sin proyecto"),  # Añadir proyecto
    campo="Estado", 
    antes=edp_data.get("Estado"), 
    despues=nuevo_estado, 
    usuario=usuario
)

    
    if cambios.get("Conformidad Enviada") == "Sí" and edp_data.get("Conformidad Enviada") != "Sí":
        log_cambio_edp(
    n_edp=edp_id,
    proyecto=edp_data.get("Proyecto", "Sin proyecto"),  # Añadir proyecto
    campo="Conformidad Enviada", 
    antes=edp_data.get("Conformidad Enviada"), 
    despues="Sí", 
    usuario=usuario
)
    
   
    
    # Hacer la actualización pasando el usuario para auditoría
    update_row(row_idx, cambios, "edp", usuario, force_update=True)
    # Leer los datos actualizados después de la modificación
    df_actualizado = read_sheet("edp!A1:V")
    edp_actualizado = df_actualizado[df_actualizado["N° EDP"] == str(edp_id)].iloc[0].to_dict() 
    
    # Formatear fechas para evitar problemas de serialización
    for campo in ['Fecha Emisión', 'Fecha Envío al Cliente', 'Fecha Estimada de Pago', 'Fecha Conformidad']:
        if campo in edp_actualizado and pd.notna(edp_actualizado[campo]):
            try:
                fecha = pd.to_datetime(edp_actualizado[campo])
                edp_actualizado[campo] = fecha.strftime('%Y-%m-%d')
            except:
                pass
    # Emitir evento más completo
    socketio.emit("estado_actualizado", {
        "edp_id": edp_id,
        "nuevo_estado": nuevo_estado,
        "cambios": cambios
    })

    return jsonify({
        "success": True, 
        "message": f"EDP {edp_id} actualizado correctamente",
        "cambios": cambios,
        'edp_data': edp_actualizado  # Devolver datos actuales del EDP
    }), 200


@controller_bp.route("kanban/update_estado_detallado", methods=["POST"])
def actualizar_estado_detallado():
    """
    Procesa actualizaciones detalladas de estado con campos adicionales 
    específicos para cada transición de estado.
    """
    try:
        # Obtener datos del formulario
        edp_id = request.form.get("edp_id")
        nuevo_estado = request.form.get("nuevo_estado", "").lower()
        
        if not edp_id or not nuevo_estado:
            return jsonify({"success": False, "message": "Datos incompletos"}), 400
        
        # Leer datos actuales
        df = read_sheet("edp!A1:V")
        edp = df[df["N° EDP"] == str(edp_id)]
        
        if edp.empty:
            return jsonify({"success": False, "message": f"EDP {edp_id} no encontrado"}), 404
            
        row_idx = edp.index[0] + 2  # +2 por encabezado y 0-indexado
        edp_data = edp.iloc[0].to_dict()
        
        # Preparar cambios base
        cambios = {"Estado": nuevo_estado}
        
        # Procesar campos especiales según el estado
        if nuevo_estado == "pagado":
            cambios["Fecha Conformidad"] = request.form.get("fecha_pago")
            cambios["N° Conformidad"] = request.form.get("n_conformidad")
            cambios["Conformidad Enviada"] = "Sí"
            
        elif nuevo_estado == "validado":
            cambios["Fecha Estimada de Pago"] = request.form.get("fecha_estimada_pago")
            cambios["Conformidad Enviada"] = "Sí"
            
        elif nuevo_estado == "revision" and request.form.get("contacto_cliente"):
            # Campos para revisión de cliente
            # (opcional: estos campos no existen en el modelo original,
            # puedes decidir si añadirlos o no)
            # cambios["Contacto Cliente"] = request.form.get("contacto_cliente")
            # cambios["Fecha Estimada Respuesta"] = request.form.get("fecha_estimada_respuesta")
            pass
        
        # Quitar campos vacíos
        cambios = {k: v for k, v in cambios.items() if v is not None and v != ""}
        
        # Registrar cambios en log
        usuario = session.get("usuario", "Kanban Modal")
        for campo, nuevo_valor in cambios.items():
            valor_anterior = edp_data.get(campo)
            if str(nuevo_valor) != str(valor_anterior):
                log_cambio_edp(
    n_edp=edp_id,
    proyecto=edp_data.get("Proyecto", "Sin proyecto"),  # Añadir proyecto
    campo=campo, 
    antes=valor_anterior, 
    despues=nuevo_valor, 
    usuario=usuario
)
        
       
        
        # Actualizar en Google Sheets
        update_row(row_idx, cambios, "edp", usuario, force_update=True)
        
        # Notificar via Socket.IO
        socketio.emit("estado_actualizado", {
            "edp_id": edp_id,
            "nuevo_estado": nuevo_estado,
            "cambios": cambios
        })
        
        return jsonify({
            "success": True, 
            "message": f"EDP {edp_id} actualizado correctamente con detalles adicionales"
        })
        
    except Exception as e:
        import traceback
        print(f"Error en actualizar_estado_detallado: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Error al actualizar: {str(e)}"
        }), 500
@controller_bp.route("log/<n_edp>/csv")
def descargar_log_csv(n_edp):
    """
    Devuelve el historial de cambios de un EDP como archivo CSV descargable.
    """
    df_log = read_log(n_edp=n_edp)
    if df_log.empty:
        flash(f"No hay registros de cambios para el EDP {n_edp}.", "info")
        return redirect(url_for("controller_bp.ver_log_edp", n_edp=n_edp))

    csv_data = df_log.to_csv(index=False)
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = (
        f"attachment; filename=log_edp_{n_edp}.csv"
    )
    response.headers["Content-Type"] = "text/csv"
    return response



@controller_bp.route("encargados")
def vista_global_encargados():
    """
    Vista global de todos los encargados con métricas comparativas.
    Permite visualizar, comparar y analizar el rendimiento de todos los encargados.
    """
    # Cargar datos completos
    df_full = read_sheet("edp!A1:V")
    df_full = calcular_dias_espera(df_full)
    
    # Aplicar filtros si existen
    filtros = {
        "mes": request.args.get("mes"),
        "cliente": request.args.get("cliente"),
        "ordenar_por": request.args.get("ordenar_por", "pagado_desc")  # Default: ordenar por monto pagado descendente
    }
    
    df_filtrado = df_full.copy()
    if filtros["mes"]:
        df_filtrado = df_filtrado[df_filtrado["Mes"] == filtros["mes"]]
    if filtros["cliente"]:
        df_filtrado = df_filtrado[df_filtrado["Cliente"] == filtros["cliente"]]
    
    # Obtener lista única de encargados
    encargados = sorted(df_filtrado["Jefe de Proyecto"].dropna().unique())
    
    # Lista para almacenar datos de cada encargado
    datos_encargados = []
    for encargado in encargados:
        df_encargado = df_filtrado[df_filtrado["Jefe de Proyecto"] == encargado]
        
        # Calcular métricas financieras
        meta = METAS_ENCARGADOS.get(encargado, 0)
        monto_pagado = df_encargado[df_encargado["Estado"].isin(["pagado", "validado"])]["Monto Aprobado"].sum()
        monto_pendiente = df_encargado[df_encargado["Estado"].isin(["enviado", "pendiente", "revisión"])]["Monto Propuesto"].sum()
        monto_propuesto = df_encargado["Monto Propuesto"].sum()
        monto_aprobado = df_encargado["Monto Aprobado"].sum()
        
        # Calcular avance
        avance = (monto_pagado / meta * 100) if meta > 0 else 0
        
        # Calcular DSO
        dso = calcular_dso_para_dataset(df_encargado) if not df_encargado.empty else 0
        
        # Calcular tasa de aprobación
        total_edps = df_encargado.shape[0]
        edps_aprobados = df_encargado[df_encargado["Estado"].isin(["pagado", "validado"])].shape[0]
        tasa_aprobacion = (edps_aprobados / total_edps * 100) if total_edps > 0 else 0
        
        # Calcular EDPs críticos
        edps_criticos = df_encargado[(df_encargado["Crítico"]) | 
                                     (df_encargado["Estado"].isin(["enviado", "revisión"]) & 
                                      (df_encargado["Días Espera"] > 30))].shape[0]
        
        # Calcular tendencia (último mes vs. promedio)
        if "Mes" in df_encargado.columns:
            meses_disponibles = sorted(df_encargado["Mes"].dropna().unique())
            if meses_disponibles:
                ultimo_mes = meses_disponibles[-1]
                df_ultimo_mes = df_encargado[(df_encargado["Mes"] == ultimo_mes) & 
                                             (df_encargado["Estado"] == "pagado")]
                monto_ultimo_mes = df_ultimo_mes["Monto Aprobado"].sum()
                
                # Calcular promedio mensual (excluyendo el último mes)
                promedios_meses = []
                for mes in meses_disponibles[:-1]:
                    df_mes = df_encargado[(df_encargado["Mes"] == mes) & 
                                         (df_encargado["Estado"] == "pagado")]
                    promedios_meses.append(df_mes["Monto Aprobado"].sum())
                
                promedio_mensual = sum(promedios_meses) / len(promedios_meses) if promedios_meses else 0
                tendencia = ((monto_ultimo_mes - promedio_mensual) / promedio_mensual * 100) if promedio_mensual > 0 else 0
            else:
                monto_ultimo_mes = 0
                tendencia = 0
        else:
            monto_ultimo_mes = 0
            tendencia = 0
        
        # Añadir datos a la lista
        datos_encargados.append({
            "nombre": encargado,
            "meta": meta,
            "monto_pagado": monto_pagado,
            "monto_pendiente": monto_pendiente,
            "monto_propuesto": monto_propuesto,
            "monto_aprobado": monto_aprobado,
            "avance": round(avance, 1),
            "dso": round(dso, 1),
            "tasa_aprobacion": round(tasa_aprobacion, 1),
            "total_edps": total_edps,
            "edps_aprobados": edps_aprobados,
            "edps_criticos": edps_criticos,
            "monto_ultimo_mes": monto_ultimo_mes,
            "tendencia": round(tendencia, 1)
        })
    for encargado in datos_encargados:
        for key, value in encargado.items():
            # Convert NumPy integers to Python int
            if hasattr(value, 'dtype') and np.issubdtype(value.dtype, np.integer):
                encargado[key] = int(value)
            # Convert NumPy floats to Python float
            elif hasattr(value, 'dtype') and np.issubdtype(value.dtype, np.floating):
                encargado[key] = float(value)
    # Ordenar datos según el parámetro
    ordenar_por = filtros["ordenar_por"]
    reverse = True if ordenar_por.endswith("_desc") else False
    campo = ordenar_por.replace("_desc", "").replace("_asc", "")
    
    campos_validos = ["nombre", "meta", "monto_pagado", "avance", "dso", 
                      "tasa_aprobacion", "edps_criticos", "tendencia"]
    
    if campo in campos_validos:
        datos_encargados = sorted(datos_encargados, 
                                  key=lambda x: x[campo] if x[campo] is not None else 0, 
                                  reverse=reverse)
    
    # Opciones para filtros
    meses_disponibles = sorted(df_full["Mes"].dropna().unique())
    clientes_disponibles = sorted(df_full["Cliente"].dropna().unique())
    
    # Calcular totales y promedios para comparación
    total_meta = sum(encargado["meta"] for encargado in datos_encargados)
    total_pagado = sum(encargado["monto_pagado"] for encargado in datos_encargados)
    total_pendiente = sum(encargado["monto_pendiente"] for encargado in datos_encargados)
    avance_global = (total_pagado / total_meta * 100) if total_meta > 0 else 0
    
    promedio_dso = sum(encargado["dso"] for encargado in datos_encargados) / len(datos_encargados) if datos_encargados else 0
    promedio_tasa_aprobacion = sum(encargado["tasa_aprobacion"] for encargado in datos_encargados) / len(datos_encargados) if datos_encargados else 0
    
    
        # Preparar datos para el gráfico de evolución mensual
    datos_mensuales = {
        "meses": [],             # Lista de meses ["Ene 2023", "Feb 2023", etc.]
        "total_por_mes": [],     # Total global pagado por mes
        "encargados": []         # Lista de objetos con datos por encargado
    }
    
    # Obtener lista de meses únicos ordenados cronológicamente
    meses_ordenados = obtener_meses_ordenados(df_full)
    datos_mensuales["meses"] = meses_ordenados
    
    # Calcular totales globales por mes
    for mes in meses_ordenados:
        df_mes = df_full[df_full["Mes"] == mes]
        total_mes = df_mes[df_mes["Estado"].isin(["pagado", "validado"])]["Monto Aprobado"].sum()
        datos_mensuales["total_por_mes"].append(float(total_mes))
    
    # Calcular datos por encargado
    # Calcular datos por encargado
    for encargado_nombre in encargados:
        datos_encargado = {
            "nombre": encargado_nombre,  # El nombre del encargado es el string directamente
            "montos_por_mes": []
        }
        
        for mes in meses_ordenados:
            df_mes_enc = df_full[(df_full["Mes"] == mes) & (df_full["Jefe de Proyecto"] == encargado_nombre)]
            monto_mes = df_mes_enc[df_mes_enc["Estado"].isin(["pagado", "validado"])]["Monto Aprobado"].sum()
            datos_encargado["montos_por_mes"].append(float(monto_mes))
        
        datos_mensuales["encargados"].append(datos_encargado)
    
    
    
    resumen_global = {
        "total_meta": total_meta,
        "total_pagado": total_pagado,
        "total_pendiente": total_pendiente,
        "avance_global": round(avance_global, 1),
        "promedio_dso": round(promedio_dso, 1),
        "promedio_tasa_aprobacion": round(promedio_tasa_aprobacion, 1)
    }
    
    return render_template(
        "controller/controller_encargados_global.html",
        encargados=datos_encargados,
        filtros=filtros,
        meses=meses_disponibles,
        clientes=clientes_disponibles,
        resumen_global=resumen_global,
        now=datetime.now(),
        datos_mensuales=datos_mensuales

    )
    
    
# Añadir estas rutas al final del archivo

@controller_bp.route("issues")
def vista_issues():
    """
    Vista principal del gestor de incidencias.
    Muestra todas las incidencias con opciones de filtrado.
    """
    # Obtener parámetros de filtro
    filtros = {
        "estado": request.args.get("estado"),
        "tipo": request.args.get("tipo"),
        "edp_relacionado": request.args.get("edp_relacionado"),
        "proyecto_relacionado": request.args.get("proyecto_relacionado")
    }
    
    # Leer incidencias con filtros
    df_issues = leer_incidencias(filtros)
    
    # Convertir a lista de diccionarios para la plantilla
    incidencias = df_issues.to_dict(orient="records")
    
    # Limpiar valores NaT para evitar problemas en la plantilla
    incidencias = clean_nat_values(incidencias)
    
    # Obtener opciones para filtros
    opciones = {}
    if not df_issues.empty:
        opciones["tipos"] = sorted(df_issues["Tipo"].dropna().unique())
        opciones["estados"] = sorted(df_issues["Estado"].dropna().unique())
        opciones["proyectos"] = sorted(df_issues["Proyecto_Relacionado"].dropna().unique())
    else:
        # Valores predeterminados si no hay datos
        opciones["tipos"] = ["bug", "mejora", "soporte", "pregunta"]
        opciones["estados"] = ["abierta", "en progreso", "resuelta", "cerrada"]
        opciones["proyectos"] = []
    
    # Obtener lista de EDPs para el selector
    df_edps = read_sheet("edp!A:B")  # Solo necesitamos el N° EDP
    edps = sorted(df_edps["N° EDP"].dropna().unique()) if not df_edps.empty else []
    
    return render_template(
        "controller/controller_issues.html",
        incidencias=incidencias,
        filtros=filtros,
        opciones=opciones,
        edps=edps,
        now=datetime.now()
    )


@controller_bp.route("issues/nueva", methods=["GET", "POST"])
def nueva_incidencia():
    """
    Formulario para crear una nueva incidencia.
    """
    if request.method == "POST":
        try:
            # Obtener datos del formulario
            tipo = request.form.get("tipo")
            severidad = request.form.get("severidad")
            descripcion = request.form.get("descripcion")
            edp_relacionado = request.form.get("edp_relacionado")
            proyecto_relacionado = request.form.get("proyecto_relacionado")
            usuario_asignado = request.form.get("usuario_asignado")
            
            # Validaciones básicas
            if not tipo or not severidad or not descripcion:
                flash("Debes completar todos los campos obligatorios.", "warning")
                return redirect(url_for("controller_bp.nueva_incidencia"))
            
            # Crear la incidencia
            usuario_reporta = session.get("usuario", "Sistema")
            issue_id = crear_incidencia(
                tipo=tipo,
                severidad=severidad,
                estado="abierta",  # Estado inicial
                descripcion=descripcion,
                edp_relacionado=edp_relacionado,
                proyecto_relacionado=proyecto_relacionado,
                usuario_reporta=usuario_reporta,
                usuario_asignado=usuario_asignado
            )
            
            flash(f"Incidencia #{issue_id} creada correctamente.", "success")
            return redirect(url_for("controller_bp.vista_issues"))
            
        except Exception as e:
            flash(f"Error al crear la incidencia: {str(e)}", "error")
            return redirect(url_for("controller_bp.nueva_incidencia"))
    
    # Para GET: Mostrar formulario
    # Obtener lista de EDPs para el selector
    df_edps = read_sheet("edp!A:C")  # Necesitamos N° EDP y Proyecto
    edps = df_edps[["N° EDP", "Proyecto"]].dropna(subset=["N° EDP"]).to_dict(orient="records") if not df_edps.empty else []
    
    # Obtener lista de proyectos únicos
    proyectos = sorted(df_edps["Proyecto"].dropna().unique()) if not df_edps.empty else []
    
    # Obtener lista de usuarios (encargados)
    usuarios = list(METAS_ENCARGADOS.keys())
    
    return render_template(
        "controller/controller_issue_nueva.html",
        edps=edps,
        proyectos=proyectos,
        usuarios=usuarios
    )


@controller_bp.route("issues/<int:issue_id>")
def detalle_incidencia(issue_id):
    """
    Vista detallada de una incidencia específica.
    """
    # Buscar la incidencia por ID
    df_issues = leer_incidencias({"id": issue_id})
    
    if df_issues.empty:
        flash(f"Incidencia #{issue_id} no encontrada.", "warning")
        return redirect(url_for("controller_bp.vista_issues"))
    
    # Convertir a diccionario para la plantilla
    incidencia = df_issues.iloc[0].to_dict()
    
    # Limpiar valores NaT para evitar problemas en la plantilla
    incidencia = clean_nat_values(incidencia)
    
    # Parsear comentarios si existen
    comentarios = []
    if incidencia.get("Solución/Comentarios"):
        # Dividir por líneas en blanco (separador de comentarios)
        comentarios_raw = incidencia["Solución/Comentarios"].split("\n\n")
        for comentario in comentarios_raw:
            if comentario.startswith("[") and "]" in comentario:
                # Extraer metadatos del comentario
                meta_end = comentario.find("]") + 1
                meta = comentario[1:meta_end-1]  # Sin los corchetes
                
                try:
                    fecha, autor = meta.split(" - ", 1)
                    texto = comentario[meta_end:].strip()
                    comentarios.append({
                        "fecha": fecha,
                        "autor": autor,
                        "texto": texto
                    })
                except:
                    # Si no tiene el formato esperado, añadirlo como está
                    comentarios.append({
                        "fecha": "",
                        "autor": "Sistema",
                        "texto": comentario
                    })
            else:
                # Comentario sin formato estándar
                comentarios.append({
                    "fecha": "",
                    "autor": "Sistema",
                    "texto": comentario
                })
    
    # Obtener lista de usuarios para asignación
    usuarios = list(METAS_ENCARGADOS.keys())
    
    return render_template(
        "controller/controller_issue_detalle.html",
        incidencia=incidencia,
        comentarios=comentarios,
        usuarios=usuarios
    )


@controller_bp.route("issues/<int:issue_id>/actualizar", methods=["POST"])
def actualizar_issue(issue_id):
    """
    Actualiza el estado o detalles de una incidencia.
    """
    try:
        # Recopilar actualizaciones del formulario
        actualizaciones = {}
        
        # Campos que pueden ser actualizados
        campos_permitidos = [
            "Estado", "Severidad", "Descripción", 
            "EDP Relacionado", "Proyecto Relacionado", "Usuario asignado"
        ]
        
        for campo in campos_permitidos:
            valor = request.form.get(campo.lower().replace(" ", "_"))
            if valor is not None:
                actualizaciones[campo] = valor
        
        # Obtener usuario actual
        usuario = session.get("usuario", "Sistema")
        
        # Actualizar la incidencia
        exito = actualizar_incidencia(issue_id, actualizaciones, usuario)
        
        if exito:
            flash(f"Incidencia #{issue_id} actualizada correctamente.", "success")
        else:
            flash(f"No se pudo actualizar la incidencia #{issue_id}.", "warning")
            
        return redirect(url_for("controller_bp.detalle_incidencia", issue_id=issue_id))
        
    except Exception as e:
        flash(f"Error al actualizar la incidencia: {str(e)}", "error")
        return redirect(url_for("controller_bp.detalle_incidencia", issue_id=issue_id))


@controller_bp.route("issues/<int:issue_id>/comentar", methods=["POST"])
def comentar_issue(issue_id):
    """
    Añade un comentario a una incidencia.
    """
    try:
        comentario = request.form.get("comentario")
        if not comentario:
            flash("El comentario no puede estar vacío.", "warning")
            return redirect(url_for("controller_bp.detalle_incidencia", issue_id=issue_id))
        
        usuario = session.get("usuario", "Sistema")
        exito = agregar_comentario_incidencia(issue_id, comentario, usuario)
        
        if exito:
            flash("Comentario añadido correctamente.", "success")
        else:
            flash("No se pudo añadir el comentario.", "warning")
            
        return redirect(url_for("controller_bp.detalle_incidencia", issue_id=issue_id))
        
    except Exception as e:
        flash(f"Error al añadir comentario: {str(e)}", "error")
        return redirect(url_for("controller_bp.detalle_incidencia", issue_id=issue_id))
    
    
@controller_bp.route("issues/analisis")
def analisis_issues():
    """
    Vista de análisis de incidencias para mejora de procesos.
    Muestra estadísticas sobre tipos de incidencias, causas comunes y tendencias.
    """
    # Obtener todas las incidencias
    df_issues = leer_incidencias()
    
    if df_issues.empty:
        flash("No hay suficientes datos para realizar análisis.", "warning")
        return redirect(url_for("controller_bp.vista_issues"))
    
    # 1. Análisis por tipo de incidencia
    if 'Tipo' in df_issues.columns:
        tipo_counts = df_issues['Tipo'].value_counts().to_dict()
    else:
        tipo_counts = {}
        
    # 2. Análisis por tipo de falla
    if 'Tipo_falla' in df_issues.columns:
        falla_counts = df_issues['Tipo_falla'].value_counts().to_dict()
        # Calcular porcentajes
        total_fallas = sum(falla_counts.values())
        falla_pcts = {k: round(v/total_fallas*100, 1) for k, v in falla_counts.items()}
    else:
        falla_counts = {}
        falla_pcts = {}
    
    # 3. Análisis por proyecto
    if 'Proyecto Relacionado' in df_issues.columns:
        proyecto_counts = df_issues['Proyecto Relacionado'].value_counts().to_dict()
    else:
        proyecto_counts = {}
    
    # 4. Tendencias temporales (agrupando por semana)
    if 'Timestamp' in df_issues.columns:
        df_issues['Semana'] = df_issues['Timestamp'].dt.isocalendar().week
        tendencia_semanal = df_issues.groupby('Semana').size().to_dict()
    else:
        tendencia_semanal = {}
    
        # 5. Tiempo promedio de resolución
    tiempo_resolucion = None
    if 'Timestamp' in df_issues.columns and 'Fecha resolución' in df_issues.columns:
        resueltas = df_issues.dropna(subset=['Fecha resolución'])
        if not resueltas.empty:
            # Normalizar zonas horarias antes de restar
            timestamp_col = pd.to_datetime(resueltas['Timestamp'])
            resolucion_col = pd.to_datetime(resueltas['Fecha resolución'])
            
            # Convertir ambas a formato naive (sin zona horaria)
            if hasattr(timestamp_col.dt, 'tz'):
                timestamp_col = timestamp_col.dt.tz_localize(None)
            if hasattr(resolucion_col.dt, 'tz'):
                resolucion_col = resolucion_col.dt.tz_localize(None)
                
            # Calcular diferencia
            diferencia = resolucion_col - timestamp_col
            tiempo_resolucion = diferencia.dt.total_seconds() / (60 * 60 * 24)  # convertir a días
            tiempo_resolucion = tiempo_resolucion.mean()
    
    # Preparar datos para gráficos
    charts_data = {
        'tipos': {
            'labels': list(tipo_counts.keys()),
            'data': list(tipo_counts.values())
        },
        'fallas': {
            'labels': list(falla_pcts.keys()),
            'data': list(falla_pcts.values())
        },
        'tendencia': {
            'labels': [f"Semana {w}" for w in tendencia_semanal.keys()],
            'data': list(tendencia_semanal.values())
        }
    }
    
    return render_template(
        "controller/controller_issues_analisis.html",
        tipo_counts=tipo_counts,
        falla_counts=falla_counts,
        falla_pcts=falla_pcts,
        proyecto_counts=proyecto_counts,
        tendencia_semanal=tendencia_semanal,
        tiempo_resolucion=tiempo_resolucion,
        charts_data=charts_data
    )
    
def get_edp_by_id(n_edp):
    """
    Obtiene los datos de un EDP específico por su ID y los prepara para formato JSON.
    
    Args:
        n_edp (int): ID del EDP a buscar
        
    Returns:
        dict: Datos del EDP limpios y formateados para JSON, o None si no se encuentra
    """
    try:
        # Leer datos de la hoja
        df = read_sheet("edp!A1:V")
        
        # Convertir el ID a string para comparación consistente
        n_edp_str = str(n_edp)
        
        # Filtrar por ID de EDP
        edp = df[df["N° EDP"] == n_edp_str]
        
        if edp.empty:
            return None
            
        # Convertir a diccionario
        edp_data = edp.iloc[0].to_dict()
        
        # Limpiar valores NaT/NaN para JSON
        edp_data = clean_nat_values(edp_data)
        
        # Formatear fechas específicamente para los campos de fecha
        for campo in ['Fecha Emisión', 'Fecha Envío al Cliente', 'Fecha Estimada de Pago', 'Fecha Conformidad']:
            if campo in edp_data and edp_data[campo]:
                try:
                    # Convertir a formato ISO para campos de fecha
                    fecha = pd.to_datetime(edp_data[campo])
                    edp_data[campo] = fecha.strftime('%Y-%m-%d')
                except:
                    # Si falla la conversión, mantener el valor original
                    pass
        
        return edp_data
        
    except Exception as e:
        import traceback
        print(f"Error en get_edp_by_id({n_edp}): {str(e)}")
        print(traceback.format_exc())
        return None
    
@controller_bp.route('detalle_edp/<string:n_edp>/json')
def detalle_edp_json(n_edp):
    """Devuelve los datos de un EDP en formato JSON para el modal de edición rápida"""
    edp = get_edp_by_unique_id(n_edp)
    if edp.empty:
        return jsonify({"error": "EDP no encontrado"}), 404
    
    # Convertir DataFrame a diccionario
    edp_data = edp.iloc[0].to_dict()
    return jsonify(edp_data)




def get_edp_by_unique_id(unique_id):
    """
    Obtiene un EDP usando su ID único, devolviendo el DataFrame filtrado
    para mantener compatibilidad con el código existente.
    
    Args:
        unique_id (str or int): ID único del EDP
        
    Returns:
        DataFrame: DataFrame filtrado con el EDP solicitado (o vacío si no existe)
    """
    try:
        df = read_sheet("edp!A1:V")
        
        # Asegurar que unique_id sea string para comparación consistente
        str_id = str(unique_id)
        
        # Filtrar por el ID único
        edp_match = df[df["ID"] == str_id]
        
        # Si no encuentra por ID, intentar buscar por N° EDP (compatibilidad)
        if edp_match.empty:
            edp_match = df[df["N° EDP"] == str_id]
            
            if not edp_match.empty:
                print(f"ADVERTENCIA: EDP encontrado por N° EDP ({str_id}) en lugar de ID")
        
        return edp_match
        
    except Exception as e:
        import traceback
        print(f"Error en get_edp_by_unique_id({unique_id}): {str(e)}")
        print(traceback.format_exc())
        return pd.DataFrame()  # Devolver DataFrame vacío en caso de error


@controller_bp.route('api/edp-details/<edp_id>')
def api_edp_details(edp_id):
    """API endpoint para obtener detalles de EDP por ID único"""
    # Usar la función que busca por ID único pero mantiene compatibilidad
    edp = get_edp_by_unique_id(edp_id)
    
    if edp.empty:
        return jsonify({"error": "EDP no encontrado"}), 404
        
    edp_data = edp.iloc[0].to_dict()
    return jsonify(edp_data)


@controller_bp.route('api/update-edp/<edp_id>', methods=['POST'])
def update_edp_api(edp_id):
    """Actualiza un EDP mediante API (usado por el modal)"""
    try:
        # Encontrar el EDP por ID único 
        edp = get_edp_by_unique_id(edp_id)
        
        if edp.empty:
            return jsonify({"success": False, "message": "EDP no encontrado"}), 404
            
        row_idx = edp.index[0] + 2  # +1 por header, +1 porque Sheets arranca en 1
        
        # Procesar datos del formulario
        updates = {
            "Estado": request.form.get("estado") or "",
            "Estado Detallado": request.form.get("estado_detallado") or "",
            # ... otros campos ...
        }
        
        # Realizar actualización
        update_row(row_idx, updates, usuario=session.get("usuario", "Sistema"), force_update=True)
        
        return jsonify({"success": True})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
# Función de compatibilidad para rutas antiguas
@controller_bp.route('api/edp-details-by-number/<string:edp_number>')
def api_edp_details_by_number(edp_number):
    """Compatibilidad con rutas antiguas que usan número de EDP"""
    # Buscar el primer EDP que coincida con ese número 
    df = read_sheet("edp!A1:Z")
    matches = df[df["N° EDP"] == str(edp_number)]
    
    if matches.empty:
        return jsonify({"error": "EDP no encontrado"}), 404
    
    # Redirigir a la ruta que usa ID único
    edp_id = matches.iloc[0]["ID"]
    return redirect(url_for('controller_bp.api_edp_details', edp_id=edp_id))


@controller_bp.route("retrabajos")
def analisis_retrabajos():
    """Dashboard especializado en análisis de re-trabajos basado en el historial completo de logs"""
    try:
        # Obtener datos de EDP y LOG
        df_edp = read_sheet("edp!A1:V")
        df_log = read_sheet("log!A1:G")
        
        # Obtener parámetros de filtro
        filtros = {
            "mes": request.args.get("mes"),
            "encargado": request.args.get("encargado"),
            "cliente": request.args.get("cliente"),
            "tipo_falla": request.args.get("tipo_falla"),
            "fecha_desde": request.args.get("fecha_desde"),
            "fecha_hasta": request.args.get("fecha_hasta")
        }
        
        # ====== MODIFICACIÓN PRINCIPAL: ANÁLISIS BASADO EN LOG HISTÓRICO ======
        # Filtrar todos los cambios a re-trabajo solicitado en el log
        df_log_retrabajos = df_log[
            (df_log["Campo"] == "Estado Detallado") & 
            (df_log["Después"] == "re-trabajo solicitado")
        ]
        
        # Convertir fechas para filtrado temporal
        df_log_retrabajos = df_log_retrabajos.copy()

        df_log_retrabajos.loc[:, "Fecha y Hora"] = pd.to_datetime(df_log_retrabajos["Fecha y Hora"])        
        # Aplicar filtros temporales si existen
        if filtros["fecha_desde"]:
            fecha_desde = pd.to_datetime(filtros["fecha_desde"])
            df_log_retrabajos = df_log_retrabajos[df_log_retrabajos["Fecha y Hora"] >= fecha_desde]
        
        if filtros["fecha_hasta"]:
            fecha_hasta = pd.to_datetime(filtros["fecha_hasta"])
            df_log_retrabajos = df_log_retrabajos[df_log_retrabajos["Fecha y Hora"] <= fecha_hasta]
        
        
        if "Proyecto" in df_log_retrabajos.columns:
            df_log_retrabajos = df_log_retrabajos.drop(columns=["Proyecto"], axis=1)
        # Enriquecer log con información de EDP para poder filtrar por encargado y cliente
        df_log_enriquecido = pd.merge(
            df_log_retrabajos,
            df_edp[["N° EDP", "Proyecto", "Jefe de Proyecto", "Cliente", "Mes", "Tipo_falla", "Motivo No-aprobado","Monto Aprobado"]],
            on="N° EDP",
            how="left"
        )
        
   
        # Aplicar filtros de EDP también al log
        if filtros["encargado"]:
            df_log_enriquecido = df_log_enriquecido[df_log_enriquecido["Jefe de Proyecto"] == filtros["encargado"]]
        
        if filtros["cliente"]:
            df_log_enriquecido = df_log_enriquecido[df_log_enriquecido["Cliente"] == filtros["cliente"]]
        
        if filtros["mes"]:
            df_log_enriquecido = df_log_enriquecido[df_log_enriquecido["Mes"] == filtros["mes"]]
        
        if filtros["tipo_falla"]:
            df_log_enriquecido = df_log_enriquecido[df_log_enriquecido["Tipo_falla"] == filtros["tipo_falla"]]
        
        # Estadísticas basadas en el log
        total_retrabajos_log = len(df_log_enriquecido)
        edps_unicos_con_retrabajo = df_log_enriquecido["N° EDP"].nunique()
        
        # Buscar motivos y tipos asociados a cada ocurrencia de re-trabajo
        retrabajos_completos = []
        
        for _, row in df_log_enriquecido.iterrows():
            edp_id = row["N° EDP"]
            fecha_cambio = row["Fecha y Hora"]
            
            # Buscar registros de motivo y tipo de falla cercanos (mismo día, mismo EDP)
            fecha_inicio = fecha_cambio - pd.Timedelta(hours=1)
            fecha_fin = fecha_cambio + pd.Timedelta(hours=1)
            
            # Buscar motivo cercano
            motivo_cercano = df_log[
                (df_log["N° EDP"] == edp_id) &
                (df_log["Campo"] == "Motivo No-aprobado") &
                (pd.to_datetime(df_log["Fecha y Hora"]) >= fecha_inicio) &
                (pd.to_datetime(df_log["Fecha y Hora"]) <= fecha_fin)
            ]
            
            # Buscar tipo de falla cercano
            tipo_cercano = df_log[
                (df_log["N° EDP"] == edp_id) &
                (df_log["Campo"] == "Tipo_falla") &
                (pd.to_datetime(df_log["Fecha y Hora"]) >= fecha_inicio) &
                (pd.to_datetime(df_log["Fecha y Hora"]) <= fecha_fin)
            ]
            
            # Crear registro enriquecido
            registro = {
                "N° EDP": edp_id,
                "Proyecto": row.get("Proyecto", ""),
                "Cliente": row.get("Cliente", ""),
                "Jefe de Proyecto": row.get("Jefe de Proyecto", ""),
                "Fecha": fecha_cambio,
                "Estado Anterior": row["Antes"],
                "Motivo No-aprobado": motivo_cercano["Después"].iloc[0] if not motivo_cercano.empty else row.get("Motivo No-aprobado", ""),
                "Tipo_falla": tipo_cercano["Después"].iloc[0] if not tipo_cercano.empty else row.get("Tipo_falla", ""),
                "Usuario": row["Usuario"]
            }
            
            retrabajos_completos.append(registro)
        
        # Crear DataFrame para análisis detallado
        df_analisis = pd.DataFrame(retrabajos_completos)
        # ====== ANÁLISIS DETALLADO DE RETRABAJOS ======
        # 1. Análisis por motivo de rechazo
        if not df_analisis.empty and "Motivo No-aprobado" in df_analisis.columns:
            motivos_rechazo = df_analisis["Motivo No-aprobado"].value_counts().to_dict()
        else:
            motivos_rechazo = {}
        
        # 2. Análisis por tipo de falla
        if not df_analisis.empty and "Tipo_falla" in df_analisis.columns:
            tipos_falla = df_analisis["Tipo_falla"].value_counts().to_dict()
        else:
            tipos_falla = {}
        
        # 3. Análisis por encargado
        if not df_analisis.empty and "Jefe de Proyecto" in df_analisis.columns:
            retrabajos_por_encargado = df_analisis["Jefe de Proyecto"].value_counts().to_dict()
        else:
            retrabajos_por_encargado = {}
        
        # 4. Análisis temporal
        if not df_analisis.empty and "Fecha" in df_analisis.columns:
            df_analisis["mes"] = df_analisis["Fecha"].dt.strftime("%Y-%m")
            tendencia_por_mes = df_analisis["mes"].value_counts().sort_index().to_dict()
        else:
            tendencia_por_mes = {}
            
        # 5. Análisis por proyecto
        if not df_analisis.empty and "Proyecto" in df_analisis.columns:
            retrabajos_por_proyecto_raw = df_analisis["Proyecto"].value_counts().to_dict()
            
            # Estructura correcta para cada proyecto
            proyectos_problematicos = {}
            for proyecto, cantidad in retrabajos_por_proyecto_raw.items():
                # Buscar el total de EDPs para este proyecto
                total_edps_proyecto = len(df_edp[df_edp["Proyecto"] == proyecto]) if "Proyecto" in df_edp.columns else 0
                
                # Calcular el porcentaje
                porcentaje = round((cantidad / total_edps_proyecto * 100), 1) if total_edps_proyecto > 0 else 0
                
                # Crear estructura de datos correcta
                proyectos_problematicos[proyecto] = {
                    "total": total_edps_proyecto,
                    "retrabajos": cantidad,
                    "porcentaje": porcentaje
                }
        else:
            proyectos_problematicos = {}
        # 6. Análisis por usuario solicitante
        if not df_analisis.empty and "Usuario" in df_analisis.columns:
            usuarios_solicitantes = df_analisis["Usuario"].value_counts().to_dict()
        else:
            usuarios_solicitantes = {}
        
        # Calcular estadísticas globales
        total_edps = len(df_edp)
        porcentaje_edps_afectados = round((edps_unicos_con_retrabajo / total_edps * 100), 1) if total_edps > 0 else 0
        
        # ====== CALCULAR PORCENTAJES ======
        porcentaje_motivos = {}
        for motivo, cantidad in motivos_rechazo.items():
            porcentaje_motivos[motivo] = round((cantidad / total_retrabajos_log * 100), 1) if total_retrabajos_log > 0 else 0
            
        porcentaje_tipos = {}  
        for tipo, cantidad in tipos_falla.items():
            porcentaje_tipos[tipo] = round((cantidad / total_retrabajos_log * 100), 1) if total_retrabajos_log > 0 else 0
            
        # ====== PREPARAR DATOS PARA GRÁFICOS ======
        chart_data = {
            "motivos_labels": list(motivos_rechazo.keys()),
            "motivos_data": list(motivos_rechazo.values()),
            "tipos_labels": list(tipos_falla.keys()),
            "tipos_data": list(tipos_falla.values()),
            "tendencia_meses": list(tendencia_por_mes.keys()),
            "tendencia_valores": list(tendencia_por_mes.values()),
            "encargados": list(retrabajos_por_encargado.keys()),
            "retrabajos_encargado": list(retrabajos_por_encargado.values()),
            # Add missing 'eficiencia' key to chart_data
            "eficiencia": []  # Initialize with empty list
        }
        # Calculate efficiency metrics if we have data for encargados
        if chart_data["encargados"]:
            
            for encargado in chart_data["encargados"]:
                # Find total EDPs for this encargado in the original dataset
                total_edps_encargado = len(df_edp[df_edp["Jefe de Proyecto"] == encargado]) 
                # Find retrabajos count for this encargado
                retrabajos_count = retrabajos_por_encargado.get(encargado, 0)
                
                if total_edps_encargado > 0:
                    # Efficiency = 100 - (retrabajos/total_edps * 100)
                    # Higher is better - fewer retrabajos per EDP means higher efficiency
                    eficiencia = 100 - (retrabajos_count / total_edps_encargado * 100)
                    # Cap at 0 to avoid negative efficiency
                    eficiencia = max(0, round(eficiencia, 1))
                else:
                    eficiencia = 0
                    
                chart_data["eficiencia"].append(eficiencia)
        # ====== Calcular Impacto Financiero ====== 
        
  
        
        
        # ====== PREPARAR DATOS PARA LA TABLA DE REGISTROS ======
        registros = retrabajos_completos
        registros = clean_nat_values(registros)
        
        # ====== OPCIONES PARA FILTROS ======
        filter_options = {
            "meses": sorted(df_edp["Mes"].dropna().unique()),
            "encargados": sorted(df_edp["Jefe de Proyecto"].dropna().unique()),
            "clientes": sorted(df_edp["Cliente"].dropna().unique()),
            "tipos_falla": sorted(df_edp["Tipo_falla"].dropna().unique()) if "Tipo_falla" in df_edp.columns else []
        }
        
        # ====== ESTADÍSTICAS RESUMEN ======
        stats = {
            "total_edps": total_edps,
            "total_retrabajos": total_retrabajos_log,  # Total de ocurrencias de re-trabajo
            "edps_con_retrabajo": edps_unicos_con_retrabajo,  # Número de EDPs únicos con re-trabajo
            "porcentaje_edps_afectados": porcentaje_edps_afectados,
            "porcentaje_retrabajos": porcentaje_edps_afectados,  # Añadir este campo para compatibilidad
            "promedio_retrabajos_por_edp": round(total_retrabajos_log / edps_unicos_con_retrabajo, 2) if edps_unicos_con_retrabajo > 0 else 0
        }
        
        # ====== RETORNAR TEMPLATE CON TODOS LOS DATOS ======
        return render_template(
            "controller/controller_retrabajos.html",
            stats=stats,
            motivos_rechazo=motivos_rechazo,
            porcentaje_motivos=porcentaje_motivos,
            tipos_falla=tipos_falla,
            porcentaje_tipos=porcentaje_tipos,
            retrabajos_por_encargado=retrabajos_por_encargado,
            tendencia_por_mes=tendencia_por_mes,
            impacto_financiero=0,  # Calcular si es necesario
            proyectos_problematicos=proyectos_problematicos,
            registros=registros,
            chart_data=chart_data,
            filtros=filtros,
            filter_options=filter_options,
            usuarios_solicitantes=usuarios_solicitantes
        )
    except Exception as e:
        import traceback
        print(f"Error en analisis_retrabajos: {str(e)}")
        print(traceback.format_exc())
        flash(f"Error al cargar el análisis de re-trabajos: {str(e)}", "error")
        return redirect(url_for("controller_bp.dashboard_controller"))