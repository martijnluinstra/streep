from datetime import datetime
import flask_login as login

from bar import db


class Activity(db.Model, login.UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    passcode = db.Column(db.String(40), nullable=False, unique=True)
    active = db.Column(db.Boolean(), nullable=False, default=True)
    # settings
    trade_credits = db.Column(db.Boolean(), nullable=False, default=False)
    credit_value = db.Column(db.Integer, nullable=True)
    age_limit = db.Column(db.Integer, nullable=False, default=18)
    stacked_purchases = db.Column(db.Boolean(), nullable=False, default=True)
    require_terms = db.Column(db.Boolean(), nullable=False, default=False)
    terms = db.Column(db.String(2048), nullable=True)
    participants = db.relationship('Participant', backref='activity', lazy='dynamic')

    def is_active(self):
        return self.active


class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cover_id = db.Column(db.Integer(), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    iban = db.Column(db.String(34), nullable=False)
    bic = db.Column(db.String(11), nullable=True)
    birthday = db.Column(db.DateTime(), nullable=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False)
    has_agreed_to_terms = db.Column(db.Boolean(), nullable=False, default=False)

    __table_args__ = (
        db.UniqueConstraint('cover_id', 'activity_id'),
        db.UniqueConstraint('name', 'activity_id'),
    )


class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    timestamp = db.Column(db.DateTime(), nullable=False)
    undone = db.Column(db.Boolean(), default=False, nullable=False)

    participant = db.relationship('Participant', backref=db.backref('pos_purchases', lazy='dynamic'))
    activity = db.relationship('Activity')
    product = db.relationship('Product')

    def __init__(self, **kwargs):
        self.timestamp = datetime.now()
        super(Purchase, self).__init__(**kwargs)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Integer(), nullable=False, default=1)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False)
    priority = db.Column(db.Integer(), nullable=False, default=0)
    age_limit = db.Column(db.Boolean(), nullable=False, default=False)

    activity = db.relationship('Activity')
