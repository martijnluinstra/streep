from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, IntegerField, DateTimeField, validators


class AddUserForm(Form):
    name = TextField('Name', [validators.Required(message='Name is required')])
    address = TextField('Address', [validators.Required(message='Address is required')])
    city = TextField('Place of residence', [validators.Required(message='Place of residence is required')])
    email = TextField('Email address', [validators.Required(message='Email is required'), validators.Email(message='Invalid email address')])
    iban = TextField('IBAN')
    birthday  = DateTimeField('Birthday', format='%d-%m-%Y')

class AddProductForm(Form):
    name = TextField('Name', [validators.Required(message='Name is required')])
    price = IntegerField('Price (credits)', [validators.Required(message='Price is required')])
    age_limit = BooleanField('Age limit')