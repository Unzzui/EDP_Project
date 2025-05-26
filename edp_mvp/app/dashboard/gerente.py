from flask import Blueprint, render_template

gerente_bp = Blueprint('gerente_bp', __name__)

@gerente_bp.route('/gerente')
def dashboard_gerente():
    # TODO: display gerente KPIs
    return render_template('dashboard/gerente.html')
