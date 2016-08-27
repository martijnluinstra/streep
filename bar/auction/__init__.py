from flask import Blueprint

auction = Blueprint('auction', __name__, url_prefix='/auction')

import views
