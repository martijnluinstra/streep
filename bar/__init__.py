from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_misaka import Misaka

# Init app
app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

md = Misaka(skip_html=True)
md.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'pos.login'

from .admin import admin
from .auction import auction
from .pos import pos

app.register_blueprint(admin)
app.register_blueprint(auction)
app.register_blueprint(pos)

from .pos.models import Activity

@login_manager.user_loader
def load_activity(activity_id):
    return Activity.query.get(activity_id)

from . import utils
