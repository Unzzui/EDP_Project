from flask import Blueprint, render_template, request, redirect, url_for, flash,jsonify
from app.utils.gsheet import read_sheet, update_row,log_cambio_edp, read_log
from pandas import isna
controller_bp = Blueprint("controller_bp", __name__)
from datetime import datetime
import pandas as pd
from app.extensions import socketio
from flask import session  # arriba del archivo
from flask import make_response
import numpy as np


# Por ejemplo, dentro de controller.py
METAS_ENCARGADOS = {
    "Diego Bravo": 200_000_000,
    "Carolina López": 150_000_000,
    "Pedro Rojas": 100_000_000,
    "Ana Pérez": 180_000_000,
}


    # === Meta Financiera Global ===
META_GLOBAL = 1_000_000_000
def clean_nat_values(data_dict):
    """Clean NaT values from dictionaries before template rendering"""
    import pandas as pd
    
    for key, value in data_dict.items():
        if isinstance(value, dict):
            clean_nat_values(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    clean_nat_values(item)
        elif pd.isna(value):
            data_dict[key] = None
    
    return data_dict

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

@controller_bp.route("/controller")
def dashboard_controller():
    # Siemmpre revisar las columnas de la bd 
    df_full = read_sheet("edp!A1:T")
    df_full = calcular_dias_espera(df_full)
    df = df_full.copy()
    
    # === Para dropdowns y filtros ===
    meses_disponibles = sorted(df_full["Mes"].dropna().unique())
    clientes_disponibles = sorted(df_full["Cliente"].dropna().unique())
    encargados_disponibles = sorted(df_full["Jefe de Proyecto"].dropna().unique())
    estados_detallados = sorted(df_full["Estado Detallado"].dropna().unique()) if "Estado Detallado" in df_full.columns else []
    
    # Filtros desde la URL
    mes = request.args.get("mes")
    encargado = request.args.get("encargado")
    cliente = request.args.get("cliente")
    estado = request.args.get("estado")
    estado_detallado = request.args.get("estado_detallado")

    if mes:
        df = df[df["Mes"] == mes]
    if encargado:
        df = df[df["Jefe de Proyecto"] == encargado]
    if cliente:
        df = df[df["Cliente"] == cliente]
    if estado:
        df = df[df["Estado"] == estado]
    elif not estado_detallado:  # Si no se filtró por estado ni estado detallado, usar filtro predeterminado
        df = df[df["Estado"].isin(["revisión", "enviado", "pagado"])]
    if estado_detallado:
        df = df[df["Estado Detallado"] == estado_detallado]

    # === MÉTRICAS FINANCIERAS GLOBALES ===
    total_pagado_global = df_full[df_full["Estado"] == "pagado"]["Monto Aprobado"].sum()
    avance_global = round(total_pagado_global / META_GLOBAL * 100, 1) if META_GLOBAL > 0 else 0
    print(avance_global)
    # Total montos propuestos y aprobados (para análisis de diferencias)
    total_propuesto_global = df_full["Monto Propuesto"].sum()
    total_aprobado_global = df_full["Monto Aprobado"].sum()
    diferencia_montos = total_aprobado_global - total_propuesto_global
    porcentaje_diferencia = round((diferencia_montos / total_propuesto_global * 100), 1) if total_propuesto_global > 0 else 0

    # === Calcular variaciones mensuales
    mes_actual = mes if mes else max(meses_disponibles)
    if mes_actual and len(meses_disponibles) > 1:
        try:
            idx_mes_actual = meses_disponibles.index(mes_actual)
            mes_anterior = meses_disponibles[idx_mes_actual -1] if idx_mes_actual > 0 else None
        except ValueError:
            mes_anterior = None
    else:
        mes_anterior = None
        
    # Calcular las metricas del mes anterior
    if mes_anterior:
        df_mes_anterior = df_full[df_full["Mes"] == mes_anterior]

        # Previous month metrics
        meta_mes_anterior = META_GLOBAL  # assuming META_GLOBAL is constant across months
        pagado_mes_anterior = df_mes_anterior[df_mes_anterior["Estado"] == "pagado"]["Monto Aprobado"].sum()
        avance_mes_anterior = round(pagado_mes_anterior / meta_mes_anterior * 100, 1) if meta_mes_anterior > 0 else 0

        # Calculate variations
        meta_var_porcentaje = 0  # META_GLOBAL is constant, so no variation
        pagado_var_porcentaje = round(((total_pagado_global - pagado_mes_anterior) / pagado_mes_anterior * 100) if pagado_mes_anterior else 0, 1)

        # Calculate pending amounts
        pendiente_actual = META_GLOBAL - total_pagado_global
        pendiente_anterior = meta_mes_anterior - pagado_mes_anterior
        pendiente_var_porcentaje = round(((pendiente_actual - pendiente_anterior) / pendiente_anterior * 100) if pendiente_anterior else 0, 1)

        # Progress percentage variation (percentage point difference, not percentage change)
        avance_var_porcentaje = round(avance_global - avance_mes_anterior, 1)
    else:
    # Default values when no previous month data is available
        meta_mes_anterior = 0
        pagado_mes_anterior = 0
        avance_mes_anterior = 0
        meta_var_porcentaje = 0
        pagado_var_porcentaje = 0
        pendiente_var_porcentaje = 0
        avance_var_porcentaje = 0


    # === Meta por Encargado (opcional) ===
    meta_por_encargado = METAS_ENCARGADOS.get(encargado, 0)
    monto_pagado_encargado = df[df["Estado"] == "pagado"]["Monto Aprobado"].sum()
    avance_encargado = 0
    monto_pendiente_encargado = 0

    if encargado:
        monto_pagado_encargado = df[df["Estado"] == "pagado"]["Monto Aprobado"].sum()
        pendiente_por_pago = df[df["Estado"].isin(["pendiente", "revisión",'enviado'])]["Monto Aprobado"].sum() or 0
        
        if meta_por_encargado > 0:
            avance_encargado = round(monto_pagado_encargado / meta_por_encargado * 100, 1)
            monto_pendiente_encargado = pendiente_por_pago
    
    # === KPIs GLOBALES ===
    total_edp_global = df_full.shape[0]
    total_validados_global = df_full[df_full["Validado"]].shape[0]
    validados_rapidos_global = df_full[(df_full["Validado"]) & (df_full["Días Espera"] <= 30)].shape[0]
    porcentaje_validacion_rapida_global = (
        round(validados_rapidos_global / total_validados_global * 100, 1)
        if total_validados_global > 0 else 0
    )
    dias_espera_promedio_global = round(df_full["Días Espera"].mean() or 0, 1)

    # === KPIs FILTRADOS ===
    total_filtrados = df.shape[0]
    total_criticos_filtrados = df[df["Crítico"]].shape[0]
    dias_espera_promedio_filtrado = round(df["Días Espera"].mean() or 0, 1)
    dias_habiles_promedio_filtrado = round(df["Días Hábiles"].mean() or 0, 1)
    
    # === NUEVOS KPIs DE CONFORMIDAD ===
    # Porcentaje de EDPs con conformidad enviada
    total_con_conformidad = df_full[df_full["Conformidad Enviada"] == "Sí"].shape[0]
    porcentaje_conformidad = round((total_con_conformidad / total_edp_global * 100), 1) if total_edp_global > 0 else 0
    
    
    
    # Tiempo promedio hasta conformidad (días desde envío hasta conformidad)
    tiempos_hasta_conformidad = []
    for _, row in df_full.iterrows():
        if not pd.isna(row.get("Fecha Envío al Cliente")) and not pd.isna(row.get("Fecha Conformidad")):
            tiempos_hasta_conformidad.append((row["Fecha Conformidad"] - row["Fecha Envío al Cliente"]).days)
    
    tiempo_promedio_conformidad = round(sum(tiempos_hasta_conformidad) / len(tiempos_hasta_conformidad), 1) if tiempos_hasta_conformidad else 0
    
    # === ANÁLISIS DE RETRABAJOS ===
    # Conteo de EDPs en re-trabajo
    total_retrabajos = df_full[df_full["Estado Detallado"] == "re-trabajo solicitado"].shape[0]
    porcentaje_retrabajos = round((total_retrabajos / total_edp_global * 100), 1) if total_edp_global > 0 else 0
    
    # Distribución de motivos de no-aprobación
    if "Motivo No-aprobado" in df_full.columns:
        motivos_rechazo = df_full["Motivo No-aprobado"].value_counts().to_dict()
    else:
        motivos_rechazo = {}
    
    # Distribución de tipos de fallas
    if "Tipo_falla" in df_full.columns:
        tipos_falla = df_full["Tipo_falla"].value_counts().to_dict()
    else:
        tipos_falla = {}


    
    registros = df.to_dict(orient="records")
    
    return render_template(
        "controller/controller_dashboard.html",
        registros=registros,
        filtros={
            "mes": mes, 
            "encargado": encargado, 
            "cliente": cliente, 
            "estado": estado,
            "estado_detallado": estado_detallado
        },
        meses=meses_disponibles,
        encargados=encargados_disponibles,
        clientes=clientes_disponibles,
        estados_detallados=estados_detallados,
        
        # KPIs Globales
        total_edp_global=total_edp_global,
        total_validados_global=total_validados_global,
        porcentaje_validacion_rapida_global=porcentaje_validacion_rapida_global,
        dias_espera_promedio_global=dias_espera_promedio_global,
        
        # KPIs Filtrados
        total_filtrados=total_filtrados,
        total_criticos_filtrados=total_criticos_filtrados,
        dias_espera_promedio_filtrado=dias_espera_promedio_filtrado,
        dias_habiles_promedio_filtrado=dias_habiles_promedio_filtrado,
        
        # KPIs Financieros
        total_pagado_global=total_pagado_global,
        total_propuesto_global=total_propuesto_global,
        total_aprobado_global=total_aprobado_global,
        diferencia_montos=diferencia_montos,
        porcentaje_diferencia=porcentaje_diferencia,
        avance_global=avance_global,
        monto_pagado_encargado=monto_pagado_encargado,
        avance_encargado=avance_encargado,
        meta_global=META_GLOBAL,
        meta_por_encargado=meta_por_encargado,
        monto_pendiente_encargado=monto_pendiente_encargado,
        
        # Variaciones mensuales
        meta_var_porcentaje=meta_var_porcentaje,
        pagado_var_porcentaje=pagado_var_porcentaje,
        pendiente_var_porcentaje=pendiente_var_porcentaje,
        avance_var_porcentaje=avance_var_porcentaje,
        
        # KPIs de Conformidad
        total_con_conformidad=total_con_conformidad,
        porcentaje_conformidad=porcentaje_conformidad,
        tiempo_promedio_conformidad=tiempo_promedio_conformidad,
        
        # Análisis de Retrabajos
        total_retrabajos=total_retrabajos,
        porcentaje_retrabajos=porcentaje_retrabajos,
        motivos_rechazo=motivos_rechazo,
        tipos_falla=tipos_falla
    )


@controller_bp.route("/controller/api/export-all-csv")
def export_all_csv():
    """
    Exportar todos los datos de EDPs a CSV sin aplicar filtros.
    """
    try:
        # Leer todos los datos
        df = read_sheet("edp!A1:T")
        
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


@controller_bp.route("/controller/api/get-edp/<edp_id>", methods=["GET"])
def get_edp_data(edp_id):
    """Obtener datos de un EDP específico para mostrar en modales"""
    try:
        df = read_sheet("edp!A1:T")
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
@controller_bp.route("/controller/api/edp-details/<n_edp>", methods=["GET"])
def api_get_edp_details(n_edp):
    """API para obtener detalles de un EDP en formato JSON"""
    df = read_sheet("edp!A1:T")
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

@controller_bp.route("/controller/api/update-edp/<n_edp>", methods=["POST"])
def api_update_edp(n_edp):
    """API para actualizar un EDP desde el modal"""
    try:
        # 1. Obtener datos del EDP
        df = read_sheet("edp!A1:T")
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
                log_cambio_edp(n_edp, campo, viejo, nuevo, usuario)
        
        # 6. CORREGIDO: Pasar correctamente los argumentos
        update_row(row_idx, updates,"edp",  usuario=usuario, force_update=True)
        
        return jsonify({"success": True, "message": "EDP actualizado correctamente"})
        
    except Exception as e:
        import traceback
        print(f"Error en api_update_edp: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@controller_bp.route("/controller/detalle/<n_edp>", methods=["GET", "POST"])
def detalle_edp(n_edp):
    """
    Vista detalle + edición de un EDP.
    - Lee todas las 20 columnas (A-T) de la hoja.
    - Calcula días corridos y hábiles.
    - Aplica reglas de negocio al guardar:
        • Si Estado = pagado ⇒ Conformidad Enviada = “Sí”.
        • Si Estado Detallado pasa a 'aprobado' y aún no hay Conformidad,
          se sugiere marcar Conformidad Enviada = “Sí”.
        • Si Estado Detallado = 're-trabajo solicitado' se deben
          informar Motivo No-aprobado y Tipo_falla.
    - Registra cada cambio en la hoja log.
    """
    # ----------- LECTURA -----------
    df = read_sheet("edp!A1:T")        # ahora 20 columnas
    edp = df[df["N° EDP"] == n_edp]

    if edp.empty:
        flash("EDP no encontrado", "error")
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
                    edp_data["N° EDP"], campo, viejo, nuevo, usuario
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



@controller_bp.route("/controller/encargado/<nombre>")
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
        now=datetime.now()
    )

@controller_bp.route("/controller/encargado/<nombre>/<proyecto>")
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

@controller_bp.route("/controller/log/<n_edp>")
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

    
@controller_bp.route("/controller/kanban")
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
        df = read_sheet("edp!A1:T")
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
            for edp in edps:
                clean_nat_values(edp)
        
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


@controller_bp.route("/controller/kanban/update_estado", methods=["POST"])
def actualizar_estado_kanban():
    data = request.get_json()
    edp_id = data.get("edp_id")
    nuevo_estado = data.get("nuevo_estado").lower()
    conformidad_enviada = data.get("conformidad_enviada", False)

    if not edp_id or not nuevo_estado:
        return jsonify({"error": "Datos incompletos"}), 400

    # Usar el mismo rango que en otras partes del código
    df = read_sheet("edp!A1:T")
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
    print(f"Actualizando EDP {edp_id}: estado actual={edp_data.get('Estado')}, nuevo={nuevo_estado}")

    # Registrar todos los cambios
    usuario = session.get("usuario", "Kanban")

    if nuevo_estado != edp_data.get("Estado"):
        log_cambio_edp(edp_id, "Estado", edp_data.get("Estado"), nuevo_estado, usuario)
    
    if cambios.get("Conformidad Enviada") == "Sí" and edp_data.get("Conformidad Enviada") != "Sí":
        log_cambio_edp(edp_id, "Conformidad Enviada", edp_data.get("Conformidad Enviada"), "Sí", usuario)
    
   
    
    # Hacer la actualización pasando el usuario para auditoría
    update_row(row_idx, cambios, "edp", usuario, force_update=True)
  # Leer los datos actualizados después de la modificación
    df_actualizado = read_sheet("edp!A1:T")
    edp_actualizado = df_actualizado[df_actualizado["N° EDP"] == str(edp_id)].iloc[0].to_dict() 
    
    if not edp.empty:
        # Convertir a diccionario
        edp_actualizado = edp.iloc[0].to_dict()
        
        # Formatear fechas para evitar problemas de serialización
        for campo in ['Fecha Emisión', 'Fecha Envío al Cliente', 'Fecha Estimada de Pago', 'Fecha Conformidad']:
            if campo in edp_actualizado and pd.notna(edp_actualizado[campo]):
                try:
                    fecha = pd.to_datetime(edp_actualizado[campo])
                    edp_actualizado[campo] = fecha.strftime('%Y-%m-%d')
                except:
                    pass
    else:
        edp_actualizado = {}
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


@controller_bp.route("/controller/kanban/update_estado_detallado", methods=["POST"])
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
        df = read_sheet("edp!A1:T")
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
                log_cambio_edp(edp_id, campo, valor_anterior, nuevo_valor, usuario)
        
        # Debugging
        print(f"Actualizando EDP {edp_id} (detallado): {cambios}")
        
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
@controller_bp.route("/controller/log/<n_edp>/csv")
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
