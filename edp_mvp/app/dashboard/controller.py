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
    df_full = read_sheet("edp!A1:Q")
    df_full = calcular_dias_espera(df_full)
    df = df_full.copy()

    # Filtros desde la URL
    mes = request.args.get("mes")
    encargado = request.args.get("encargado")
    cliente = request.args.get("cliente")
    estado = request.args.get("estado")

    if mes:
        df = df[df["Mes"] == mes]
    if encargado:
        df = df[df["Jefe de Proyecto"] == encargado]
    if cliente:
        df = df[df["Cliente"] == cliente]
    if estado:
        df = df[df["Estado"] == estado]
    else:
        df = df[df["Estado"].isin(["revisión", "enviado", "pagado"])]


    total_pagado_global = df_full[df_full["Estado"] == "pagado"]["Monto Aprobado"].sum()
    avance_global = round(total_pagado_global / META_GLOBAL * 100, 1) if META_GLOBAL > 0 else 0

    # === Meta por Encargado (opcional)
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
    # KPIs GLOBALES
    total_edp_global = df_full.shape[0]
    total_validados_global = df_full[df_full["Validado"]].shape[0]
    validados_rapidos_global = df_full[(df_full["Validado"]) & (df_full["Días Espera"] <= 30)].shape[0]
    porcentaje_validacion_rapida_global = (
        round(validados_rapidos_global / total_validados_global * 100, 1)
        if total_validados_global > 0 else 0
    )
    dias_espera_promedio_global = round(df_full["Días Espera"].mean() or 0, 1)

    # KPIs FILTRADOS
    total_filtrados = df.shape[0]
    total_criticos_filtrados = df[df["Crítico"]].shape[0]
    dias_espera_promedio_filtrado = round(df["Días Espera"].mean() or 0, 1)
    dias_habiles_promedio_filtrado = round(df["Días Hábiles"].mean() or 0, 1)

    # Para dropdowns
    meses_disponibles = sorted(df_full["Mes"].dropna().unique())
    clientes_disponibles = sorted(df_full["Cliente"].dropna().unique())
    encargados_disponibles = sorted(df_full["Jefe de Proyecto"].dropna().unique())
    
    registros = df.to_dict(orient="records")
    return render_template(
        "controller/controller_dashboard.html",
        registros=registros,
        filtros={"mes": mes, "encargado": encargado, "cliente": cliente, "estado": estado},
        meses=meses_disponibles,
        encargados=encargados_disponibles,
        clientes=clientes_disponibles,
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
        total_pagado_global=total_pagado_global,
        avance_global=avance_global,
        monto_pagado_encargado=monto_pagado_encargado,
        avance_encargado=avance_encargado,
        meta_global=META_GLOBAL,
        meta_por_encargado=meta_por_encargado,
        monto_pendiente_encargado=monto_pendiente_encargado
    )
    
# dashboard/controller.py
# -----------------------

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
        if updates["Estado"] == "pagado":
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
        update_row(row_idx, updates, usuario=usuario)
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
    df_full = read_sheet("edp!A1:Q")
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
    monto_total = df_filtrado["Monto Aprobado"].sum()
    monto_pagado = df_filtrado[df_filtrado["Estado"] == "pagado"]["Monto Aprobado"].sum()
    avance_financiero = (
        (monto_pagado / monto_total) * 100 if monto_total > 0 else 0
    )

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
        monto_total=monto_total,
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
    df = read_sheet("edp!A1:Q")
    df = calcular_dias_espera(df)
    
    # Obtener parámetros de filtro
    mes = request.args.get("mes")
    encargado = request.args.get("encargado")
    cliente = request.args.get("cliente")

    # Aplicar filtros si existen
    if mes:
        df = df[df["Mes"] == mes]
    if encargado:
        df = df[df["Jefe de Proyecto"] == encargado]
    if cliente:
        df = df[df["Cliente"] == cliente]

    # Agrupar por estado (SOLO UN BUCLE)
    estados = ["revisión", "enviado", "pagado", "validado"]
    columnas = {estado: [] for estado in estados}
    
    # Un solo bucle que procesa todas las tarjetas con sus campos adicionales
    for _, row in df.iterrows():
        estado = row["Estado"]
        if estado in columnas:
            # Crear el diccionario base
            item = row.to_dict()
            
            # Procesar fechas para formato adecuado
            if not pd.isna(row.get("Fecha Estimada de Pago")):
                item["dias_para_pago"] = (row["Fecha Estimada de Pago"] - datetime.today()).days
                
            # Añadir diferencia entre monto propuesto y aprobado
            if not pd.isna(row.get("Monto Propuesto")) and not pd.isna(row.get("Monto Aprobado")):
                item["diferencia_montos"] = row["Monto Aprobado"] - row["Monto Propuesto"]
            
            # Agregar una sola vez a la columna correspondiente
            columnas[estado].append(item)

    # Listas únicas para los dropdowns de filtros
    meses_disponibles = sorted(df["Mes"].dropna().unique())
    encargados_disponibles = sorted(df["Jefe de Proyecto"].dropna().unique())
    clientes_disponibles = sorted(df["Cliente"].dropna().unique())
    
        # Clean NaT values before sending to template
    for estado, edps in columnas.items():
        for edp in edps:
            for key in ['Fecha Conformidad', 'Fecha Emisión', 'Fecha Estimada de Pago', 'Fecha Envío al Cliente']:
                if key in edp and pd.isna(edp[key]):
                    edp[key] = None
    return render_template(
        "controller/controller_kanban.html",
        columnas=columnas,
        filtros={"mes": mes, "encargado": encargado, "cliente": cliente},
        meses=meses_disponibles,
        encargados=encargados_disponibles,
        clientes=clientes_disponibles,
        now=datetime.now()
    )


@controller_bp.route("/controller/kanban/update_estado", methods=["POST"])
def actualizar_estado_kanban():
    data = request.get_json()
    edp_id = data.get("edp_id")
    nuevo_estado = data.get("nuevo_estado")

    if not edp_id or not nuevo_estado:
        return jsonify({"error": "Datos incompletos"}), 400

    df = read_sheet("edp!A1:Q")
    edp = df[df["N° EDP"] == edp_id]

    if edp.empty:
        return jsonify({"error": "EDP no encontrado"}), 404

    row_idx = edp.index[0] + 2
    edp_data = edp.iloc[0].to_dict()
    cambios = {"Estado": nuevo_estado}

    if nuevo_estado == "pagado":
        cambios["Conformidad Enviada"] = "Sí"

    if nuevo_estado != edp_data.get("Estado"):
        log_cambio_edp(edp_id, "Estado", edp_data.get("Estado"), nuevo_estado, edp_data.get("Registrado Por", "Kanban"))

    if nuevo_estado == "pagado" and edp_data.get("Conformidad Enviada") != "Sí":
        log_cambio_edp(edp_id, "Conformidad Enviada", edp_data.get("Conformidad Enviada"), "Sí", "Kanban")

    update_row(row_idx, cambios)

    # Emitir evento por socket
    socketio.emit("estado_actualizado", {
        "edp_id": edp_id,
        "nuevo_estado": nuevo_estado
    })

    return jsonify({"success": True}), 200


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
