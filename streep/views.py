from flask import request, render_template, redirect, url_for, abort, flash
from flask.ext.login import login_user, logout_user, login_required, current_user
from urlparse import urlparse, urljoin

from streep import app, db, login_manager
from models import Activity, Participant, Purchase, Product, activities_participants_table
from forms import ParticipantForm, ProductForm, BirthdayForm


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
    """ View all participants attending the activity, ordered by name """
    spend_subq = db.session.query(Purchase.participant_id.label("participant_id"), db.func.sum(Product.price).label("spend")).join(Product, Purchase.product_id==Product.id).filter(Purchase.undone == False).filter(Purchase.activity_id==current_user.id).group_by(Purchase.participant_id).subquery()
    parti_subq = current_user.participants.subquery()
    participants = db.session.query(parti_subq, spend_subq.c.spend).outerjoin(spend_subq, spend_subq.c.participant_id==parti_subq.c.id).order_by(parti_subq.c.name).all()
    # users = User.query.order_by(User.name).all()
    products = Product.query.order_by(Product.priority.desc()).all()
    print  "1 aapje "+str(participants)
    return render_template('index.html', participants=participants, products=products)


@app.route('/participant', methods=['GET'])
@login_required
def list_participants():
    """ List all participants in the system by name """
    registered_subq = current_user.participants.add_column(db.bindparam("activity", current_user.id)).subquery()
    participants = db.session.query(Participant, registered_subq.c.activity).outerjoin(registered_subq, Participant.id==registered_subq.c.id).all()
    return render_template('participants.html', participants=participants)


@app.route('/participant/add', methods=['GET', 'POST'])
def add_participant():
    """ Try to create a new participant. """
    form = ParticipantForm()
    if form.validate_on_submit():
        participant = Participant(
            form.name.data, form.address.data, form.city.data, form.email.data, form.iban.data, form.birthday.data)
        db.session.add(participant)
        current_user.participants.append(participant)
        try:
            db.session.commit()
        except IntegrityError:
            form.name.errors.append('Please provide a unique name!')
            return render_template('participant_add.html', form=form, mode='add')
        else:
            return redirect(url_for('view_home'))
    return render_template('participant_add.html', form=form, mode='add')



@app.route('/participant/<int:participant_id>/register', methods=['GET'])
@login_required
def register_participant(participant_id):
    """ Add a participant to an activity """
    participant = Participant.query.filter_by(id=participant_id).first_or_404()
    current_user.participants.append(participant)
    db.session.commit()
    return redirect(url_for('list_participants'))

@app.route('/participant/<int:participant_id>/deregister', methods=['GET'])
@login_required
def deregister_participant(participant_id):
    """ Remove a participant from an activity """
    participant = Participant.query.filter_by(id=participant_id).first_or_404()
    purchases = participant.purchases.filter_by(activity_id=current_user.id).first()
    if purchases:
        flash("Cannot remove this participant, this participant has purchases!")
    else:
        current_user.participants.remove(participant)
        db.session.commit()
    return redirect(url_for('list_participants'))