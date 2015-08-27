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

from bar import app, db, login_manager
from models import Activity, Participant, Purchase, Product, AuctionPurchase, ActivityParticipant
from forms import ParticipantForm, ProductForm, BirthdayForm, SettingsForm, ImportForm, AuctionForm, ExportForm


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
    spend_subq = db.session.query(Purchase.participant_id.label("participant_id"), db.func.sum(Product.price).label("spend")).join(Product, Purchase.product_id==Product.id).filter(Purchase.undone == False).filter(Purchase.activity_id==current_user.id).group_by(Purchase.participant_id).subquery()
    parti_subq = db.session.query(Participant, ActivityParticipant.agree_to_terms.label('agree_to_terms')).join(ActivityParticipant, Participant.id==ActivityParticipant.participant_id).filter(ActivityParticipant.activity_id == current_user.id).subquery()
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
    registered_subq = db.session.query(Participant).join(ActivityParticipant, Participant.id==ActivityParticipant.participant_id).filter(ActivityParticipant.activity_id == current_user.id).add_column(db.bindparam("activity", current_user.id)).subquery()
    participants = db.session.query(Participant, registered_subq.c.activity).outerjoin(registered_subq, Participant.id==registered_subq.c.id).order_by(Participant.name).all()
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
            participant = Participant.query.filter_by(name=value).first()
            if participant:
                value = [value,[participant.name, participant.email, participant.iban]]
            data[column]["rows"].append(value)
    return render_template('import_select_form.html', json_data=json.dumps(data, ensure_ascii=False).encode('utf-8'))


def import_report_error(errors, key, err):
    if  errors.has_key(key):
        errors[key].update(err)
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
        participant = Participant.query.filter_by(name=row['name']).first()
        if participant:
            participant.address = row['address']
            participant.city = row['city']
            participant.email = row['email']
            participant.iban = row['iban']
            participant.bic = row['bic']
            participant.birthday = row['birthday']
        else:
            participant = Participant(row['name'],row['address'],row['city'],row['email'],row['iban'], row['bic'], row['birthday'])
            db.session.add(participant)
        if not participant in current_user.participants:
            current_user.participants.append(participant)
        db.session.flush()
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
    if not participant in current_user.participants:
        current_user.participants.append(participant)
    db.session.commit()
    return redirect(url_for('list_participants'))


@app.route('/participants/<int:participant_id>/deregister', methods=['GET'])
@login_required
def deregister_participant(participant_id):
    """ Remove a participant from an activity """
    participant = Participant.query.get_or_404(participant_id)
    pos_purchases = participant.pos_purchases.filter_by(activity_id=current_user.id).first()
    auction_purchases = participant.auction_purchases.filter_by(activity_id=current_user.id).first()
    if pos_purchases or auction_purchases:
        flash("Cannot remove this participant, this participant has purchases!")
    else:
        current_user.participants.remove(participant)
        db.session.commit()
    return redirect(url_for('list_participants'))


@app.route('/participants/<int:participant_id>/terms', methods=['GET'])
@login_required
def accept_terms_participant(participant_id):
    """ Let a participant accept terms """
    accept = request.args.get('accept') == 'True'
    participant = ActivityParticipant.query.filter_by(participant_id=participant_id).first_or_404()
    products = Product.query.filter_by(activity_id=current_user.id).all()
    if not participant.agree_to_terms:
        participant.agree_to_terms = accept
    db.session.commit()
    if accept:
        return redirect(url_for('view_home'))
    return render_template('terms.html', terms=current_user.terms, participant=participant.participant, products=products)


@app.route('/participants/<int:participant_id>/history', methods=['GET'])
@login_required
def participant_history(participant_id):
    view = request.args.get('view', 'pos')
    
    if view == 'auction':
        purchase_query = AuctionPurchase.query.filter_by(participant_id=participant_id)\
                .filter_by(activity_id=current_user.id)\
                .order_by(AuctionPurchase.timestamp.desc())
    elif view == 'pos':
        purchase_query = db.session.query(Purchase, Product.name, Product.price)\
                .join(Product, Purchase.product_id == Product.id)\
                .filter(Purchase.participant_id == participant_id)\
                .filter(Purchase.activity_id == current_user.id)\
                .order_by(Purchase.timestamp.desc())
    else:
        return 'Invalid view', 400

    try:
        limit = request.args.get('limit', type=int)
    except KeyError:
        purchases = purchase_query.all();
    else:
        purchases = purchase_query.limit(limit).all();

    participant = Participant.query.get_or_404(participant_id)
    return render_template('participant_history.html', purchases=purchases, participant=participant, view=view)


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


@app.route('/participants/names.json', methods=['GET'])
@login_required
def list_participant_names():
    """ List all participants """
    participants = current_user.participants
    return jsonify([participant.name for participant in participants])


@app.route('/purchases', methods=['POST'])
@login_required
def batch_consume():
    data = request.get_json()
    for row in data:
        purchase = Purchase(participant_id=row['participant_id'], activity_id=current_user.id, product_id=row['product_id'])
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
    purchase.undone = request.args.get('undo') != 'False'
    db.session.commit()
    next_url = request.args.get('next')
    return redirect(url_for('participant_history', participant_id = purchase.participant_id))


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


@app.route('/settings/export', methods=['GET'])
@login_required
def activity_export_form():
    """ Edit settings """
    form = ExportForm(csrf_enabled=False)
    return render_template('export_form.html', form=form)


@app.route('/activity/export.csv', methods=['GET'])
@login_required
def activity_export():
    """ Export all purchases of an activity """
    form = ExportForm(request.args, csrf_enabled=False)
    if not form.validate():
        return 'Unexpected error in form', 400

    if not (form.pos.data or form.auction.data):
        return '', 200

    pos_subq = db.session.query(Purchase.participant_id.label('participant_id'), db.func.sum(Product.price).label('spend')).join(Product, Purchase.product_id==Product.id).filter(Purchase.undone == False).filter(Purchase.activity_id==current_user.id).group_by(Purchase.participant_id).subquery()
    auction_subq = db.session.query(AuctionPurchase.participant_id.label('participant_id'), db.func.sum(AuctionPurchase.price).label('spend')).filter(AuctionPurchase.activity_id==current_user.get_id()).group_by(AuctionPurchase.participant_id).subquery()

    participants = db.session.query(Participant).join(ActivityParticipant, Participant.id==ActivityParticipant.participant_id).filter(ActivityParticipant.activity_id == current_user.id).add_columns(pos_subq.c.spend.label('spend_pos'), auction_subq.c.spend.label('spend_auction')).outerjoin(pos_subq, pos_subq.c.participant_id == Participant.id).outerjoin(auction_subq, auction_subq.c.participant_id == Participant.id).order_by(Participant.name).all()

    spend_data = []

    settings={
        'trade_credits': current_user.trade_credits,
        'credit_value': current_user.credit_value,
        'pos': form.pos.data,
        'auction': form.auction.data,
        'description_pos_prefix': form.description_pos_prefix.data,
        'description_auction_prefix': form.description_auction_prefix.data,
        'description': form.description.data
    }

    def generate(data, settings):
        for participant, spend_pos, spend_auction in data:        
            spend_pos = 0 if spend_pos is None else spend_pos
            spend_auction = 0 if spend_auction is None else spend_auction
            
            if settings['pos'] and settings['auction']:
                amount = spend_auction + (spend_pos * settings['credit_value'] if settings['trade_credits'] else spend_pos)
            elif settings['pos']:
                amount = (spend_pos * settings['credit_value'] if settings['trade_credits'] else spend_pos)
            else:
                amount = spend_auction

            if amount == 0:
                continue

            if amount > 0 and settings['description_pos_prefix'] and settings['description_auction_prefix']:
                if spend_pos > 0 and spend_auction > 0:
                    description = settings['description_pos_prefix'] + ' + ' + settings['description_auction_prefix'] + (' ' + settings['description'] if settings['description'] else '')
                elif spend_pos > 0:
                    description = settings['description_pos_prefix'] +  (' ' + settings['description'] if settings['description'] else '')
                else: 
                    description = settings['description_auction_prefix'] +  (' ' + settings['description'] if settings['description'] else '')
            else:
                description = settings['description']

            iban = re.sub(r'\s+', '', participant.iban)
            bic = re.sub(r'\s+', '', participant.bic) if participant.bic else ''

            p_data = [participant.name, participant.address, participant.city, participant.email, iban, bic, float(amount)/100, description]
            yield ','.join(['"' + unicode(field).encode('utf-8') + '"' for field in p_data]) + '\n'

    return Response(generate(participants, settings), mimetype='text/csv')


@app.route('/auction', methods=['GET', 'POST'])
@login_required
def list_auction():
    form = AuctionForm()
    if form.validate_on_submit():
        participant = Participant.query.filter_by(name=form.participant.data).first()
        purchase = AuctionPurchase(participant_id=participant.id, activity_id=current_user.id, description=form.description.data, price=form.price.data)
        db.session.add(purchase)
        db.session.commit()
        return redirect(url_for('list_auction'))
    purchases = AuctionPurchase.query.filter_by(activity_id=current_user.get_id()).all()
    return render_template('auction.html', form=form, purchases=purchases)


@app.route('/auction/purchases/<int:purchase_id>', methods=['GET', 'POST'])
@login_required
def edit_auction_purchase(purchase_id):
    """ Edit a purchase """
    purchase = AuctionPurchase.query.get_or_404(purchase_id)
    if purchase.activity_id != current_user.id:
        return 'Product not in current activity', 401
    form = AuctionForm(request.form, purchase)
    if form.validate_on_submit():
        participant = Participant.query.filter_by(name=form.participant.data).first()
        if participant:
            form.participant.data = participant
            form.populate_obj(purchase)
            db.session.commit()
            return redirect(url_for('list_auction'))
        else:
            form.participant.errors.append('Participant not found!')
    else:
        form.participant.data = purchase.participant.name
    return render_template('auction_form.html', form=form, mode='edit', id=purchase.id)


@app.route('/auction/purchases/<int:purchase_id>/undo', methods=['GET'])
@login_required
def undo_auction_purchase(purchase_id):
    purchase = AuctionPurchase.query.get_or_404(purchase_id)
    if purchase.activity_id != current_user.id:
        return 'Purchase not in current activity', 401    
    purchase.undone = request.args.get('undo') != 'False'
    db.session.commit()
    return redirect(url_for('list_auction'))
