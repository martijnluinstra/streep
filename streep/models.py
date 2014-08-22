from streep import db
from datetime import datetime


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    iban = db.Column(db.String(34), nullable=False)
    birthday = db.Column(db.DateTime(), nullable=True)
    purchases = db.relationship('Purchase', backref='user',
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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    timestamp = db.Column(db.DateTime(), nullable=False)
    undone = db.Column(db.Boolean())

    def __init__(self, user_id, product_id):
        self.user_id = user_id
        self.product_id = product_id
        self.timestamp = datetime.now()
        self.undone = False


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Integer(), nullable=False)
    age_limit = db.Column(db.Boolean())

    def __init__(self, name, price=1, age_limit=False):
        self.name = name
        self.price = price
        self.age_limit = age_limit