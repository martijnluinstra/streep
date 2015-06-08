from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, IntegerField, DateTimeField, RadioField, validators


class ParticipantForm(Form):
    name = TextField('Name', [validators.InputRequired(message='Name is required')])
    address = TextField('Address', [validators.InputRequired(message='Address is required')])
    city = TextField('Place of residence', [validators.InputRequired(message='Place of residence is required')])
    email = TextField('Email address', [validators.InputRequired(message='Email is required'), validators.Email(message='Invalid email address')])
    iban = TextField('IBAN')
    birthday  = DateTimeField('Birthday', format='%d-%m-%Y', validators=[validators.Optional(strip_whitespace=True)])


class BirthdayForm(Form):
    name = TextField('Name', [validators.InputRequired(message='Name is required')])
    birthday  = DateTimeField('Birthday', format='%d-%m-%Y', validators=[validators.InputRequired(message='Birthday is required')])


class ProductForm(Form):
    name = TextField('Name', [validators.InputRequired(message='Name is required')])
    price = IntegerField('Price', [validators.InputRequired(message='Price is required')])
    priority = IntegerField('Priority (order)', [validators.InputRequired(message='Priority is required')])
    age_limit = BooleanField('Age limit')


class SettingsForm(Form):
    trade_credits = RadioField('Trading currency', choices=[('True','Credits'),('False','Euro')])
    credit_value = IntegerField('Credit value (in Euro cent)')
    age_limit = IntegerField('Age limit (minimal save age)', [validators.InputRequired(message='Age limit is required')])
    stacked_purchases = BooleanField('Allow stacked purchases')

    def validate_trade_credits(form, field):
        field.data = field.data == 'True'

    def validate_credit_value(form, field):
        if not form.trade_credits:
            return
        if not field.raw_data or not field.raw_data[0]:
            field.errors[:] = []
            raise validators.StopValidation('Credit value is requried!')
