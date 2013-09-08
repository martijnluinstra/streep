from streep import db
from streep.models import User

# Create the database
db.create_all()

# Add a demo user
u_demo = User('Demo User')
db.session.add(u_demo)
db.session.commit()