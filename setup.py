from streep import db
from streep.models import User
from datetime import datetime
import csv


def read_date(date):
    try:
        return datetime.strptime(date, "%d-%m-%Y")
    except ValueError:
        print "Error: invalid date provided! (" + date + ")"
        return None


def create_demo_data():
    # Add a demo user
    u_demo = User('Demo User', 'Nijenborgh 9', 'Groningen', 'martijn@svcover.nl', 'NL54RABO0103796940')
    db.session.add(u_demo)
    db.session.commit()

    # # Add demo products
    # u_demo = User('Demo User', 'Nijenborgh 9', 'Groningen', 'martijn@svcover.nl', 'NL54RABO0103796940')
    # db.session.add(u_demo)
    # db.session.commit()


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
# Import files
import_users("D:\\\\Martijn\\Documents\\GitHub\\streep\\test.csv")