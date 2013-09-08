from flask import render_template, redirect, url_for, request
from streep import app, db
from models import User

@app.route('/', methods=['GET'])
def view_home():
    """ View all users, ordered by name """
    users = User.query.order_by(User.name).all()
    return render_template('index.html', users=users)


@app.route('/add', methods=['GET', 'POST'])
def add_user():
    """ 
    Try to create a new user. 
    For more complex projects, I recommend using WTForms (Flask WTF) to create forms and process formdata.
    """
    error = None
    if request.method == 'POST':
        # Check if the name already exists
        user = User.query.filter_by(name=request.form['name']).first()
        if user is None:
            user = User(request.form['name'])
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('view_home'))
        else:
            error = 'Non unique name'
    return render_template('add.html', error=error)


@app.route('/<int:user_id>/consume', methods=['GET'])
def consume(user_id):
    """
    Increase the amount of consumed credits for *user_id* with a certain value.
    """
    amount = request.args.get('amount', 1, type=int)
    user = User.query.filter_by(id = user_id).first_or_404()
    user.consume(amount)
    db.session.commit()
    return redirect(url_for('view_home'))