from flask_wtf import Form
from wtforms import TextField, BooleanField, validators

class ActivityForm(Form):
    name = TextField('Name', [validators.InputRequired(message='Name is required')])
    passcode = TextField('Passcode', [validators.InputRequired(message='Passcode is required')])
    active = BooleanField('Active')
