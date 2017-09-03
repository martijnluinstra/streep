from __future__ import division

from urlparse import urlparse, urljoin

from urlparse import urlparse, urljoin
from datetime import datetime
from dateutil.relativedelta import relativedelta

from flask import request, g
from flask_login import current_user

from . import app
from .services.secretary import SecretaryAPI


@app.template_test()
def equalto(value, other):
    return value == other


@app.context_processor
def utility_processor():
    def format_exchange(amount):
        if not amount:
            amount = 0
        return format_price(amount/100)
    def format_price(amount, currency=u"\u20AC"):
        return u'{1} {0:.2f}'.format(amount, currency)
    def is_eligible(birthdate, product_age_limit):
        if not birthdate:
            return True
        age = relativedelta(datetime.now(), birthdate).years
        return not (product_age_limit and age<current_user.age_limit)
    return dict(format_exchange=format_exchange, format_price=format_price, is_eligible=is_eligible)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def get_secretary_api():
    if not g.get('_secretary_api'):
        g._secretary_api = SecretaryAPI(app)
    return g.get('_secretary_api')
