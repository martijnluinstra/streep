from flask import request, render_template, redirect, url_for, abort, get_flashed_messages, session, current_app
from flask_login import login_user
from werkzeug.security import check_password_hash

from functools import wraps

from bar import db
from bar.utils import is_safe_url
from bar.pos.models import Activity

from . import admin
from .forms import ActivityForm


def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not get_user():
            return redirect(url_for('admin.login', next=request.url))
        return func(*args, **kwargs)
    return decorated_view


def get_user(username=None):
    if not username:
        if not 'username' in session:
            return None
        username = session.get('username', None)
    for user in current_app.config['ADMINS']:
        if user[0] == username:
            return user
    return None


@admin.route("/login", methods=["GET", "POST"])
def login():
    errors = []
    if request.method == 'POST':
        if not any(field in request.form for field in ('username', 'password')):
            return abort(400)
        user = get_user(request.form['username'])
        if user and check_password_hash(user[2], request.form['password']):
            session['username'] = user[0]

            next_url = request.args.get('next')
            if not is_safe_url(next_url):
                return abort(400)
            return redirect(url_for('admin.list_activities'))
        else:
            errors.append('Username and password do not match!')
    flashes = get_flashed_messages()
    return render_template('admin/login.html', errors=errors)


@admin.route('/logout', methods=['GET'])
def logout():
    session.pop('username', None)
    return redirect(url_for('admin.login'))


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
            form.name.errors.append('Please provide a unique passcode!')
            return render_template('activity_form.html', form=form, mode='add')
        else:
            return redirect(url_for('admin.list_activities'))
    return render_template('admin/activity_form.html', form=form, mode='add')


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
    return redirect(url_for('view_home'))


@admin.route('/activities/<int:activity_id>/activate', methods=['GET', 'POST'])
@admin_required
def activate_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    activity.active = request.args.get('activate') != 'False'
    db.session.commit()
    return redirect(url_for('admin.list_activities'))
