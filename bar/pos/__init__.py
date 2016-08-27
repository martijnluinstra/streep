from flask import Blueprint

pos = Blueprint('pos', __name__, url_prefix='')

import views
