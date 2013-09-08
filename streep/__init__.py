from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

# Init app
app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

from streep import models, frontend