from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.misaka import Misaka

# Init app
app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

md = Misaka(skip_html=True)
md.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

from bar import models, views, forms, admin