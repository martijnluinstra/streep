from bar import db
from datetime import datetime


activities_participants_table =  db.Table('activities_participants',
    db.Column('activity_id', db.Integer, db.ForeignKey('activity.id')),
    db.Column('participant_id', db.Integer, db.ForeignKey('participant.id'))
)


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    passcode = db.Column(db.String(40), unique=True)
    # settings
    trade_credits = db.Column(db.Boolean(), nullable=False, default=False)
    credit_value = db.Column(db.Integer, nullable=True)
    age_limit = db.Column(db.Integer, nullable=False, default=18)
    stacked_purchases = db.Column(db.Boolean(), nullable=False, default=True)

    participants = db.relationship('Participant', secondary=activities_participants_table,
        lazy='dynamic', backref=db.backref('activities', lazy='dynamic'))

    def __init__(self, name, passcode):
        self.name = name
        self.passcode = passcode

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id


class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    iban = db.Column(db.String(34), nullable=False)
    birthday = db.Column(db.DateTime(), nullable=True)
    purchases = db.relationship('Purchase', backref='participant',
                                lazy='dynamic')

    def __init__(self, name, address, city, email, iban, birthday=None):
        self.name = name
        self.address = address
        self.city = city
        self.email = email
        self.iban = iban
        self.birthday = birthday


class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    timestamp = db.Column(db.DateTime(), nullable=False)
    undone = db.Column(db.Boolean(), nullable=False)

    def __init__(self, participant_id, activity_id, product_id):
        self.participant_id = participant_id
        self.activity_id = activity_id
        self.product_id = product_id
        self.timestamp = datetime.now()
        self.undone = False


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Integer(), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False)
    priority = db.Column(db.Integer(), nullable=False)
    age_limit = db.Column(db.Boolean(), nullable=False)

    def __init__(self, name, activity_id, price=1, priority=0, age_limit=False):
        self.name = name
        self.price = price
        self.activity_id = activity_id
        self.priority = priority
        self.age_limit = age_limit