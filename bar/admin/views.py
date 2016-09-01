from flask import request, render_template, redirect, url_for, current_app
from flask_login import login_user
from flask_coverapi import admin_required

from bar import db
from bar.pos.models import Activity

from . import admin
from .forms import ActivityForm


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
    return redirect(url_for('pos.view_home'))


@admin.route('/activities/<int:activity_id>/activate', methods=['GET', 'POST'])
@admin_required
def activate_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    activity.active = request.args.get('activate') != 'False'
    db.session.commit()
    return redirect(url_for('admin.list_activities'))
