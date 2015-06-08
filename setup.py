from bar import db
from bar.models import Activity, Participant, Product
from datetime import datetime
from unicodedata import normalize
import csv


def read_date(date):
    try:
        return datetime.strptime(date, "%d-%m-%Y")
    except ValueError:
        print "Error: invalid date provided! (" + date + ")"
        return None


def create_demo_data():
    # Add a demo participant
    p_demo = Participant('Demo Participant', 'Nijenborgh 9', 'Groningen', 'martijn@svcover.nl', 'NL54RABO0103796940')
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


def import_users(file):
    with open(file, 'rb') as csvfile:
        user_data = csv.reader(csvfile, delimiter=',', quotechar='"')
        for (line, row) in enumerate(user_data):
            try:
                user = User(row[0],row[1],row[2],row[3],row[4],(read_date(row[5]) if len(row)>5 else None))
            except IndexError:
                print "Error: not enough columns provided" + (" for "+ row[0] if len(row)>0 else "") + " on line "+ str(line+1) +"!"
                continue
            else:
                db.session.add(user)
        db.session.commit()


# Create the database
db.create_all()
# Add some data
create_demo_data()
# Import files