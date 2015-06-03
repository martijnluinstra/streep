from urlparse import urlparse, urljoin
from flask import request, render_template, redirect, url_for, abort
from streep import app, db, login_manager
from models import Activity, Participant, Purchase, Product
from flask.ext.login import login_user, logout_user, login_required, current_user


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


@app.context_processor
def utility_processor():
    def format_price(amount, currency=u"\u20AC"):
        return u'{1} {0:.2f}'.format(amount, currency)
    def is_eligible(birthdate, product_age_limit):
        age = relativedelta(datetime.now(), birthdate).years
        return not (product_age_limit and age<app.config.get('AGE_LIMIT'))
    return dict(format_price=format_price, is_eligible=is_eligible)


@login_manager.user_loader
def load_activity(activity_id):
    return Activity.query.get(activity_id)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == 'POST':
        activity = Activity.query.filter_by(passcode = request.form['passcode']).first()
        if activity is None:
            error = 'Invalid code!'
        else:
            login_user(activity)

            next = request.args.get('next')
            if not is_safe_url(next):
                return abort(400)
            return redirect(next or url_for('view_home'))

    return render_template('login.html', error=error)


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/', methods=['GET'])
# @app.route('/participants', methods=['GET'])
@login_required
def view_home():
    """ View all participants, ordered by name """
    spend_subq = db.session.query(Purchase.participant_id.label("participant_id"), db.func.sum(Product.price).label("spend")).join(Product, Purchase.product_id==Product.id).filter(Purchase.undone == False).group_by(Purchase.participant_id).subquery()
    users =  db.session.query(Participant, spend_subq.c.spend).outerjoin(spend_subq, spend_subq.c.participant_id==Participant.id).order_by(Participant.name).all()
    # users = User.query.order_by(User.name).all()
    products = Product.query.order_by(Product.priority.desc()).all()
    return render_template('index.html', users=users, products=products)
