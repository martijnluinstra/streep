from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, IntegerField, DateTimeField, validators


class UserForm(Form):
    name = TextField('Name', [validators.InputRequired(message='Name is required')])
    address = TextField('Address', [validators.InputRequired(message='Address is required')])
    city = TextField('Place of residence', [validators.InputRequired(message='Place of residence is required')])
    email = TextField('Email address', [validators.InputRequired(message='Email is required'), validators.Email(message='Invalid email address')])
    iban = TextField('IBAN')
    birthday  = DateTimeField('Birthday', format='%d-%m-%Y', validators=[validators.Optional(strip_whitespace=True)])


class ProductForm(Form):
    name = TextField('Name', [validators.InputRequired(message='Name is required')])
    price = IntegerField('Price (credits)', [validators.InputRequired(message='Price is required')])
    age_limit = BooleanField('Age limit')