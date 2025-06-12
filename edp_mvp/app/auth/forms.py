from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    email = StringField('Username/Email', validators=[DataRequired()])  # Cambiado para aceptar username
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Recordar sesión')
    submit = SubmitField('Iniciar sesión')