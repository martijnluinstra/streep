from flask_wtf import Form
from wtforms import TextField, IntegerField, validators

class AuctionForm(Form):
    description = TextField('Product description (optional)', validators=[
    	validators.Optional(strip_whitespace=True)
    ])
    price = IntegerField('Price (in Euro cent)', validators=[
    	validators.InputRequired(message='Price is required')
    ])
    participant = TextField('Participant', validators=[
    	validators.InputRequired(message='Participant is required')
    ])
