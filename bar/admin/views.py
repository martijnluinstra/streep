from functools import wraps

from flask import request, render_template, redirect, url_for, current_app, has_request_context, jsonify
from flask_login import login_user
from flask_coverapi import current_user

import json
from sqlalchemy.exc import IntegrityError

from bar import db
from bar.pos.models import Activity, Product, Participant, Purchase
from bar.auction.models import AuctionPurchase

from . import admin
from .forms import ActivityForm, ImportForm


def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_app.config.get('STAND_ALONE', False):
            return func(*args, **kwargs)
        elif not current_user.is_authenticated:
            return redirect(login_url())
        elif not current_user.is_admin:
            abort(403)
        return func(*args, **kwargs)
    return decorated_view


@admin.route('/', methods=['GET'])
@admin.route('/activities', methods=['GET'])
@admin_required
def list_activities():
    activities = Activity.query.all()
    return render_template('admin/activity_list.html', activities=activities)


@admin.route('/activities/add', methods=['GET', 'POST'])
@admin_required
def add_activity():
    """ Try to create a new activity. """
    form = ActivityForm()
    if form.validate_on_submit():
        activity = Activity(
            name=form.name.data, 
            passcode=form.passcode.data, 
            active=form.active.data
        )
        db.session.add(activity)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            form.passcode.errors.append('Please provide a unique passcode!')
            return render_template('activity_form.html', form=form, mode='add')
        else:
            return redirect(url_for('admin.list_activities'))
    return render_template('admin/activity_form.html', form=form, mode='add')


@admin.route('/activities/import', methods=['GET', 'POST'])
@admin_required
def import_activity():
    form = ImportForm()
    if form.validate_on_submit():
        try: 
            data = json.load(form.import_file.data)
            if not form.name.data:
                form.name.data = data['name']
            if not form.passcode.data:
                form.passcode.data = data['passcode']
            _load_activity(data, form.name.data, form.passcode.data)
        except IntegrityError:
            db.session.rollback()
            form.passcode.errors.append('Please provide a unique passcode!')
        except Exception as e:
            db.session.rollback()
            form.import_file.errors.append(str(e))
        else:
            return redirect(url_for('admin.list_activities'))
    return render_template('admin/activity_import_form.html', form=form)


def _load_activity(data, name=None, passcode=None):
    if not name:
        name = data['name']
    if not passcode:
        passcode = data['passcode']

    activity = Activity(
            name=name,
            passcode=passcode,
            **data['settings']
        )
    
    db.session.add(activity)
    db.session.flush()

    products = {}
    participants = {}

    for product in data['products']:
        p_id = str(product['id'])
        del product['id']
        product['activity_id'] = activity.id
        products[p_id] = Product(**product)
        db.session.add(products[p_id])

    for participant in data['participants']:
        p_id = str(participant['id'])
        del participant['id']
        participant['activity_id'] = activity.id
        participants[p_id] = Participant(**participant)
        db.session.add(participants[p_id])

    db.session.flush()

    for purchase in data['pos_purchases']:
        p = Purchase(
            participant_id=participants[str(purchase['participant_id'])].id,
            activity_id=activity.id,
            product_id=products[str(purchase['product_id'])].id,
            timestamp=purchase['timestamp'],
            undone=purchase['undone']
        )
        db.session.add(p)

    for purchase in data['auction_purchases']:
        p = AuctionPurchase(
            participant_id=participants[str(purchase['participant_id'])].id,
            activity_id=activity.id,
            description=purchase['description'],
            price=purchase['price'],
            timestamp=purchase['timestamp'],
            undone=purchase['undone']
        )
        db.session.add(p)

    db.session.commit()


@admin.route('/activities/<int:activity_id>', methods=['GET', 'POST'])
@admin_required
def edit_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    form = ActivityForm(request.form, activity)
    if form.validate_on_submit():
        form.populate_obj(activity)
        try:
            db.session.commit()
        except IntegrityError:
            form.name.errors.append('Please provide a unique name!')
            return render_template('activity_form.html', form=form, mode='edit', id=activity.id)
        else:
            return redirect(url_for('admin.list_activities'))
    return render_template('admin/activity_form.html', form=form, mode='edit', id=activity.id)


@admin.route('/activities/<int:activity_id>/impersonate', methods=['GET', 'POST'])
@admin_required
def impersonate_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    login_user(activity, force=True)
    return redirect(url_for('pos.view_home'))


@admin.route('/activities/<int:activity_id>/activate', methods=['GET', 'POST'])
@admin_required
def activate_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    activity.active = request.args.get('activate') != 'False'
    db.session.commit()
    return redirect(url_for('admin.list_activities'))


@admin.route('/activities/<int:activity_id>/export.json', methods=['GET'])
@admin_required
def export_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    return jsonify(activity.to_dict())
