from flask import Blueprint, render_template, request, redirect,url_for,flash

from app.utils.gsheet import read_sheet, append_row
from app.edp.forms import EDPForm

edp_bp = Blueprint('edp', __name__)

@edp_bp.route("/")
def list_edp():
    df = read_sheet("edp!A1:O")
    rows = df.to_dict(orient="records")
    return render_template("edp_list.html", rows=rows)


@edp_bp.route("/nuevo", methods=["GET", "POST"])
def nuevo_edp():
    form = EDPForm()

    if form.validate_on_submit():
        # Crear lista en el mismo orden que las columnas de la hoja
        fila = [
            form.numero.data,
            form.proyecto.data,
            form.cliente.data,
            form.jefe_proyecto.data,
            form.mes.data,
            form.fecha_emision.data.strftime("%Y-%m-%d"),
            form.fecha_envio.data.strftime("%Y-%m-%d"),
            str(form.monto.data),
            form.fecha_estimada_pago.data.strftime("%Y-%m-%d") if form.fecha_estimada_pago.data else "",
            form.conformidad_enviada.data,
            form.fecha_conformidad.data.strftime("%Y-%m-%d") if form.fecha_conformidad.data else "",
            form.estado.data,
            form.observaciones.data or "",
            form.registrado_por.data,
            form.fecha_registro.data.strftime("%Y-%m-%d"),
        ]

        append_row(fila)
        flash("EDP registrado correctamente", "success")
        return redirect(url_for("edp.list_edp"))

    return render_template("edp_form.html", form=form)