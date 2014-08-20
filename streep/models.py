from streep import db
from datetime import datetime


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    place_of_residence = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    iban = db.Column(db.String(34), nullable=False)
    date_of_birth = db.Column(db.DateTime(), nullable=True)
    purchases = db.relationship('Purchase', backref='user',
                                lazy='dynamic')

    def __init__(self, name, address, place_of_residence, email, iban, date_of_birth=None):
        self.name = name
        self.address = address
        self.place_of_residence = place_of_residence
        self.email = email
        self.iban = iban
        self.date_of_birth = date_of_birth


class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    timestamp = db.Column(db.DateTime(), nullable=False)
    undone = db.Column(db.Boolean())

    def __init__(self, user_id, product_id):
        self.user_id = user_id
        self.product_id = product_id
        self.timestamp = datetime.utcnow()
        self.undone = True


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Integer(), nullable=False)
    age_limit = db.Column(db.Boolean())

    def __init__(self, name, price=1, age_limit=False):
        self.name = name
        self.price = price
        self.age_limit = false