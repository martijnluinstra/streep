from bar import db
from bar.models import Activity, Participant, Product
from datetime import datetime
from unicodedata import normalize
import csv

def create_demo_data():
    # Add a demo participant
    p_demo = Participant('Demo Participant', 'Nijenborgh 9', 'Groningen', 'martijn@svcover.nl', 'NL37BANK0123456789')
    db.session.add(p_demo)
    db.session.commit()

    # Add a demo activity
    a_demo = Activity('Demo Activity', 'DEMO22')
    db.session.add(a_demo)
    db.session.commit()

    # Add demo products
    p_demo1 = Product('Beer', a_demo.id, 55, True)
    db.session.add(p_demo1)
    p_demo2 = Product('Soft drink', a_demo.id, 27)
    db.session.add(p_demo2)
    db.session.commit()

# Create the database
db.create_all()
# Add some data
create_demo_data()