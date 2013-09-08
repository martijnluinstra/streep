import os
basedir = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = '\xa3b{\xf2\xa3\xf1\x9aX\xe1\xc2\xe4t\xf7$\xb6tbV\xb0\x1cD\xf5e\xe6'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'database.db')