from flask_wtf import FlaskForm
from wtforms.validators import InputRequired
from wtforms import StringField, PasswordField


class LoginForm(FlaskForm):
    """
    WTF form class for validating the login API request.
    """

    class Meta:
        csrf = False

    username = StringField('username', validators=[InputRequired()])
    password = PasswordField('password', validators=[InputRequired()])
