from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional

class EDPForm(FlaskForm):
    numero = StringField('N° EDP', validators=[DataRequired()])
    proyecto = StringField('Proyecto', validators=[DataRequired()])
    cliente = StringField('Cliente', validators=[DataRequired()])
    jefe_proyecto = StringField('Jefe de Proyecto', validators=[DataRequired()])
    mes = StringField('Mes', validators=[DataRequired()])
    fecha_emision = DateField('Fecha Emisión', validators=[DataRequired()], format='%Y-%m-%d')
    fecha_envio = DateField('Fecha Envío al Cliente', validators=[DataRequired()], format='%Y-%m-%d')
    monto = DecimalField('Monto', validators=[DataRequired()])
    fecha_estimada_pago = DateField('Fecha Estimada de Pago', validators=[Optional()], format='%Y-%m-%d')
    conformidad_enviada = SelectField('Conformidad Enviada', choices=[('Sí', 'Sí'), ('No', 'No')], validators=[DataRequired()])
    fecha_conformidad = DateField('Fecha Conformidad', validators=[Optional()], format='%Y-%m-%d')
    estado = SelectField('Estado', choices=[
        ('revisión', 'revisión'),
        ('enviado', 'enviado'),
        ('pagado', 'pagado'),
        ('validado', 'validado')
    ], validators=[DataRequired()])
    observaciones = StringField('Observaciones', validators=[Optional()])
    registrado_por = StringField('Registrado Por', validators=[DataRequired()])
    fecha_registro = DateField('Fecha Registro', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('Guardar')
