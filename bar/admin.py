from flask import request, render_template, redirect, url_for, abort, get_flashed_messages

from bar import app login_manager
from models import Activity
from view import is_safe_url


def get_user(username=None):
    if not username:
        username = session['username']
    for user in app.config['ADMINS']:
        if user[0] == username:
            return user
    return None


@app.route("/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == 'POST':
        if not any(field in request.form for field in ('username', 'password')):
                return abort(400)
        user = get_user(request.form['username'])
        if user and check_password_hash(user[2], request.form['password']):
            session['username'] = user[0]

            next = request.args.get('next')
            if not is_safe_url(next):
                return abort(400)
            return redirect(next or url_for('view_home'))
        else:
            error = 'Username and password do not match!'
    flashes = get_flashed_messages()
    return render_template('login.html', error=error)


@app.route('/admin/logout', methods=['GET'])
def admin_logout():
    session.pop('username', None)
    return redirect(url_for('login'))
