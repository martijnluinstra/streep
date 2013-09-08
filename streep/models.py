from streep import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    credits = db.Column(db.Integer)

    def __init__(self, name, credits=0):
        self.name = name
        self.credits = credits

    def consume(self, amount):
        self.credits += amount