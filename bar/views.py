from __future__ import division

from flask import request, render_template, redirect, url_for, abort, make_response, flash, Response, get_flashed_messages
from flask.ext.login import login_user, logout_user, login_required, current_user
from urlparse import urlparse, urljoin
from sqlalchemy.exc import IntegrityError, InvalidRequestError

from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
import re
import csv

from pprint import pprint

from bar import app, db, login_manager
from models import Activity, Participant, Purchase, Product, activities_participants_table
from forms import ParticipantForm, ProductForm, BirthdayForm, SettingsForm, ImportForm, AuctionForm


def jsonify(data):
    """ Create a json response from data """
    response = make_response(json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8'))
    response.content_type = 'application/json'
    return response


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

@app.template_test()
def equalto(value, other):
    return value == other


@app.context_processor
def utility_processor():
    def format_exchange(amount):
        if(current_user.trade_credits):
            return amount
        return format_price(amount/100)
    def format_price(amount, currency=u"\u20AC"):
        return u'{1} {0:.2f}'.format(amount, currency)
    def is_eligible(birthdate, product_age_limit):
        if not birthdate:
            return True
        age = relativedelta(datetime.now(), birthdate).years
        return not (product_age_limit and age<current_user.age_limit)
    return dict(format_exchange=format_exchange, format_price=format_price, is_eligible=is_eligible)


@login_manager.user_loader
def load_activity(activity_id):
    return Activity.query.get(activity_id)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == 'POST':
        activity = Activity.query.filter_by(passcode = request.form['passcode']).first()
        if not activity or not activity.is_active():
            error = 'Invalid code!'
        else:
            login_user(activity)

            next = request.args.get('next')
            if not is_safe_url(next):
                return abort(400)
            return redirect(next or url_for('view_home'))
    flashes = get_flashed_messages()
    return render_template('login.html', error=error)


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/', methods=['GET'])
@login_required
def view_home():
    """ View all participants attending the activity, ordered by name """
    spend_subq = db.session.query(Purchase.participant_id.label("participant_id"), db.func.sum(Product.price).label("spend")).join(Product, Purchase.product_id==Product.id).filter(Purchase.undone == False).filter(Purchase.activity_id==current_user.id).filter(Purchase.category==Purchase.CATEGORY_BAR).group_by(Purchase.participant_id).subquery()
    parti_subq = current_user.participants.subquery()
    participants = db.session.query(parti_subq, spend_subq.c.spend).outerjoin(spend_subq, spend_subq.c.participant_id==parti_subq.c.id).order_by(parti_subq.c.name).all()
    products = Product.query.filter_by(activity_id=current_user.id).order_by(Product.priority.desc()).all()
    return render_template('main.html', participants=participants, products=products)

 
@app.route('/faq', methods=['GET'])
def faq():
    return render_template('faq.html')


@app.route('/participants', methods=['GET'])
@login_required
def list_participants():
    """ List all participants in the system by name """
    registered_subq = current_user.participants.add_column(db.bindparam("activity", current_user.id)).subquery()
    participants = db.session.query(Participant, registered_subq.c.activity).outerjoin(registered_subq, Participant.id==registered_subq.c.id).all()
    return render_template('participant_list.html', participants=participants)


@app.route('/participants/import', methods=['GET', 'POST'])
@login_required
def import_participants():
    form = ImportForm()
    if form.validate_on_submit():
        return import_process_csv(form)
    elif request.method == 'POST':
        return import_process_data(request.get_json())
    return render_template('import_upload_form.html', form=form)


def import_process_csv(form):
    data = []
    participant_data = csv.reader(form.import_file.data, delimiter=form.delimiter.data.encode('ascii', 'ignore'))
    for line, row in enumerate(participant_data):
        if line==0:
            for column, value in enumerate(row):
                data.append({
                    'header': value if form.header.data else ('Column_%d' % (column+1)),
                    'rows': []
                    })
            if form.header.data:
                continue
        for column, value in enumerate(row):
            data[column]["rows"].append(value)
    return render_template('import_select_form.html', json_data=json.dumps(data, ensure_ascii=False).encode('utf-8'))


def import_report_error(errors, key, err):
    if  errors.has_key(key):
        errors[key].update(err)
        print errors
    else:
        errors[key] = err


def import_validate_row(key, row, errors):
    birthday = None
    if row['birthday']:
        try:
            birthday = datetime.strptime(row['birthday'], "%d-%m-%Y")
        except ValueError:
            import_report_error(errors,key,{'birthday': ['type']})
    row['birthday'] = birthday
    for prop in ['name', 'address', 'city', 'email', 'iban']:
        if not row[prop].strip():
            import_report_error(errors,key,{prop: ['nonblank']})
    if len(row['iban']) > 34:
        import_report_error(errors,key,{'iban': ['type']})
    if len(row['bic']) > 11:
        import_report_error(errors,key,{'bic': ['type']})
    return (row, errors)


def import_process_data(data):
    errors = {}
    for key, row in data.iteritems():
        row, errors = import_validate_row(key, row, errors)
        participant = Participant(row['name'],row['address'],row['city'],row['email'],row['iban'], row['bic'], row['birthday'])
        db.session.add(participant)
        current_user.participants.append(participant)
        try: 
            db.session.flush()
        except IntegrityError:
            import_report_error(errors,key,{'name': ['nonunique']})
            db.session.rollback()
    if not errors:
        db.session.commit()
        return "", 200
    else:
        db.session.rollback()
        return jsonify(errors)


@app.route('/participants/add', methods=['GET', 'POST'])
@login_required
def add_participant():
    """ Try to create a new participant. """
    form = ParticipantForm()
    if form.validate_on_submit():
        participant = Participant(
            form.name.data, form.address.data, form.city.data, form.email.data, form.iban.data, form.bic.data, form.birthday.data)
        db.session.add(participant)
        current_user.participants.append(participant)
        try:
            db.session.commit()
        except IntegrityError:
            form.name.errors.append('Please provide a unique name!')
            return render_template('participant_form.html', form=form, mode='add')
        else:
            return redirect(url_for('view_home'))
    return render_template('participant_form.html', form=form, mode='add')


@app.route('/participants/<int:participant_id>', methods=['GET', 'POST'])
@login_required
def edit_participant(participant_id):
    participant = Participant.query.get_or_404(participant_id)
    form = ParticipantForm(request.form, participant)
    if form.validate_on_submit():
        form.populate_obj(participant)
        try:
            db.session.commit()
        except IntegrityError:
            form.name.errors.append('Please provide a unique name!')
            return render_template('participant_form.html', form=form, mode='edit', id=participant.id)
        else:
            return redirect(url_for('list_participants'))
    return render_template('participant_form.html', form=form, mode='edit', id=participant.id)


@app.route('/participants/<int:participant_id>/register', methods=['GET'])
@login_required
def register_participant(participant_id):
    """ Add a participant to an activity """
    participant = Participant.query.get_or_404(participant_id)
    current_user.participants.append(participant)
    db.session.commit()
    return redirect(url_for('list_participants'))


@app.route('/participants/<int:participant_id>/deregister', methods=['GET'])
@login_required
def deregister_participant(participant_id):
    """ Remove a participant from an activity """
    participant = Participant.query.get_or_404(participant_id)
    purchases = participant.purchases.filter_by(activity_id=current_user.id).first()
    if purchases:
        flash("Cannot remove this participant, this participant has purchases!")
    else:
        current_user.participants.remove(participant)
        db.session.commit()
    return redirect(url_for('list_participants'))


@app.route('/participants/<int:participant_id>/history', methods=['GET'])
@login_required
def participant_history(participant_id):
    purchase_query = db.session.query(Purchase, Product.name, Product.price).join(Product, Purchase.product_id==Product.id).filter(Purchase.participant_id == participant_id).filter(Purchase.activity_id==current_user.id).filter(Purchase.category==Purchase.CATEGORY_BAR).order_by(Purchase.id.desc())
    try:
        show = request.args.get('show', type=int)
    except KeyError:
        purchases = purchase_query.all();
    else:
        purchases = purchase_query.limit(show).all();
    participant = Participant.query.get_or_404(participant_id)
    return render_template('participant_history.html', purchases=purchases, participant=participant)


@app.route('/participants/birthday', methods=['GET', 'POST'])
@login_required
def add_participant_birthday():
    """ 
    Edit a participant's birthday
    """
    form = BirthdayForm()
    if form.validate_on_submit():
        participant = Participant.query.filter_by(name=form.name.data).first()
        if participant:
            participant.birthday = form.birthday.data
            db.session.commit()
            return redirect(url_for('add_participant_birthday'))
        else:
            form.name.errors.append('Participant\'s name can not be found')
    return render_template('participant_birthday.html', form=form)


@app.route('/participants/names', methods=['GET'])
@login_required
def list_participant_names():
    """ List all participants """
    # users = db.session.query(User.name).all()
    participants = current_user.participants.all()
    return jsonify([participant.name for participant in participants])


@app.route('/purchases', methods=['POST'])
@login_required
def batch_consume():
    data = request.get_json()
    for row in data:
        purchase = Purchase(category=Purchase.CATEGORY_BAR, participant_id=row['participant_id'], activity_id=current_user.id, product_id=row['product_id'])
        db.session.add(purchase)
    db.session.commit()
    return 'Purchases created', 201


@app.route('/purchases/undo', methods=['POST'])
@login_required
def batch_undo():
    data = request.get_json()
    for row in data:
        purchase = Purchase.query.get_or_404(row['purchase_id'])
        if purchase.activity_id != current_user.id:
            return 'Purchase not in current activity', 401
        purchase.undone = True
    db.session.commit()
    return 'Purchases undone', 201


@app.route('/purchases/<int:purchase_id>/undo', methods=['GET'])
@login_required
def undo(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)
    if purchase.activity_id != current_user.id:
        return 'Purchase not in current activity', 401    
    purchase.undone = True
    db.session.commit()
    return redirect(url_for('history', participant_id = purchase.participant_id))


@app.route('/products', methods=['GET', 'POST'])
@login_required
def list_products():
    """ 
    View all products.
    """
    products = Product.query.order_by(Product.priority.desc()).filter_by(activity_id=current_user.id).all()
    return render_template('product_list.html', products=products)


@app.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    """ 
    Create a new product.
    """
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(form.name.data, current_user.id, form.price.data, form.priority.data, form.age_limit.data)
        db.session.add(product)
        db.session.commit()
        return redirect(url_for('list_products'))
    return render_template('product_form.html', form=form, mode='add')


@app.route('/products/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """ Edit a product """
    product = Product.query.get_or_404(product_id)
    if product.activity_id != current_user.id:
        return 'Product not in current activity', 401 
    form = ProductForm(request.form, product)
    if form.validate_on_submit():
        form.populate_obj(product)
        db.session.commit()
        return redirect(url_for('list_products'))
    return render_template('product_form.html', form=form, mode='edit', id=product.id)


@app.route('/products/<int:product_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_product(product_id):
    """ Edit a product """
    product = Product.query.get_or_404(product_id)
    if product.activity_id != current_user.id:
        return 'Product not in current activity', 401 
    purchase = Purchase.query.filter_by(product_id=product.id).first()
    if purchase:
        flash('Cannot delete product, as it has been purchased already. Carry on or contact the AC/DCee!')
    else:
        db.session.delete(product)
        db.session.commit()
    return redirect(url_for('list_products'))


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def activity_settings():
    """ Edit settings """
    form = SettingsForm(request.form, current_user)
    if form.validate_on_submit():
        form.populate_obj(current_user)
        db.session.commit()
        flash('Changes are saved!')
    return render_template('activity_settings.html', form=form)


@app.route('/activity/export.csv', methods=['GET'])
@login_required
def activity_export():
    """ Export all purchases of an activity """
    spend_subq = db.session.query(Purchase.participant_id.label("participant_id"), db.func.sum(Product.price).label("spend")).join(Product, Purchase.product_id==Product.id).filter(Purchase.undone == False).filter(Purchase.activity_id==current_user.id).group_by(Purchase.participant_id).subquery()
    parti_subq = current_user.participants.subquery()
    participants = db.session.query(parti_subq.c.name,parti_subq.c.address, parti_subq.c.city, parti_subq.c.email, parti_subq.c.iban, spend_subq.c.spend).outerjoin(spend_subq, spend_subq.c.participant_id==parti_subq.c.id).order_by(parti_subq.c.name).filter(spend_subq.c.spend!=0).all()
    def generate(data, trade_credits, credit_value):
        for row in data:
            my_row = list(row)
            my_row[-1] = float(row[-1]*credit_value) / 100 if trade_credits else float(row[-1]) / 100
            my_row[-2] = re.sub(r'\s+', '', row[-2])
            yield ','.join(['"' + unicode(field).encode('utf-8') + '"' for field in my_row]) + '\n'
    return Response(generate(participants, current_user.trade_credits, current_user.credit_value), mimetype='text/csv')


@app.route('/auction', methods=['GET', 'POST'])
@login_required
def list_auction():
    form = AuctionForm()
    if form.validate_on_submit():
        participant = Participant.query.filter_by(name=form.participant.data).first()
        purchase = Purchase(category=Purchase.CATEGORY_AUCTION, participant_id=participant.id, activity_id=current_user.id, description=form.description.data, price=form.price.data)
        db.session.add(purchase)
        db.session.commit()
        return redirect(url_for('list_auction'))
    purchases = Purchase.query.filter_by(activity_id=current_user.get_id()).filter_by(category=Purchase.CATEGORY_AUCTION).all()
    return render_template('auction.html', form=form, purchases=purchases)
