from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import SubmitField
from wtforms.validators import DataRequired


class ShopsForm(FlaskForm):
    title = StringField('Название магазина', validators=[DataRequired()])
    coordinats = StringField("Адрес")
    content = TextAreaField("Товары и услуги")
    submit = SubmitField('Опубликовать')
