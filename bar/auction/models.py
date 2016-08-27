from datetime import datetime

from bar import db

class AuctionPurchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Integer(), nullable=False)
    timestamp = db.Column(db.DateTime(), nullable=False)
    undone = db.Column(db.Boolean(), default=False, nullable=False)

    participant = db.relationship('Participant', backref=db.backref('auction_purchases', lazy='dynamic'))
    activity = db.relationship('Activity')

    def __init__(self, **kwargs):
        self.timestamp = datetime.now()
        super(AuctionPurchase, self).__init__(**kwargs)
