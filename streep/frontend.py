from flask import render_template, redirect, url_for, make_response, request, Response
from sqlalchemy.exc import IntegrityError

from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
import re


from streep import app, db
from models import User, Purchase, Product
from forms import UserForm, ProductForm, BirthdayForm


def jsonify(data):
    """ Create a json response from data """
    response = make_response(json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8'))
    response.content_type = 'application/json'
    return response


@app.context_processor
def utility_processor():
    def format_price(amount, currency=u"\u20AC"):
        return u'{1} {0:.2f}'.format(amount, currency)
    def is_eligible(birthdate, product_age_limit):
        age = relativedelta(datetime.now(), birthdate).years
        return not (product_age_limit and age<app.config.get('AGE_LIMIT'))
    return dict(format_price=format_price, is_eligible=is_eligible)


@app.route('/export.csv')
def generate_csv():
    spend_subq = db.session.query(Purchase.user_id.label("user_id"), db.func.sum(Product.price).label("spend")).join(Product, Purchase.product_id==Product.id).filter(Purchase.undone == False).group_by(Purchase.user_id).subquery()
    users =  db.session.query(User.name,User.address,User.city, User.email, User.iban, spend_subq.c.spend).outerjoin(spend_subq, spend_subq.c.user_id==User.id).order_by(User.name).filter(spend_subq.c.spend!=0).all()
    def generate(data):
        for row in data:
            my_row = list(row)
            my_row[-1] = float(row[-1]) / 100
            my_row[-2] = re.sub(r'\s+', '', row[-2])
            yield ','.join(['"' + unicode(field).encode('utf-8') + '"' for field in my_row]) + '\n'
    return Response(generate(users), mimetype='text/csv')

@app.route('/', methods=['GET'])
@app.route('/users', methods=['GET'])
def view_home():
    """ View all users, ordered by name """
    spend_subq = db.session.query(Purchase.user_id.label("user_id"), db.func.sum(Product.price).label("spend")).join(Product, Purchase.product_id==Product.id).filter(Purchase.undone == False).group_by(Purchase.user_id).subquery()
    users =  db.session.query(User, spend_subq.c.spend).outerjoin(spend_subq, spend_subq.c.user_id==User.id).order_by(User.name).all()
    # users = User.query.order_by(User.name).all()
    products = Product.query.order_by(Product.priority.desc()).all()
    return render_template('index.html', users=users, products=products)


@app.route('/faq', methods=['GET'])
def faq():
    return render_template('faq.html')


@app.route('/users/add', methods=['GET', 'POST'])
def add_user():
    """ 
    Try to create a new user.
    """
    form = UserForm()
    if form.validate_on_submit():
        user = User(form.name.data, form.address.data, form.city.data, form.email.data, form.iban.data, form.birthday.data)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            form.name.errors.append('Please provide a unique name!')
            return render_template('user_add.html', form=form, mode='add')
        else:
            return redirect(url_for('view_home'))
    return render_template('user_add.html', form=form, mode='add')


@app.route('/users/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.filter_by(id = user_id).first_or_404()
    form = UserForm(request.form, user)
    if form.validate_on_submit():
        form.populate_obj(user)
        try:
            db.session.commit()
        except IntegrityError:
            form.name.errors.append('Please provide a unique name!')
            return render_template('user_add.html', form=form, mode='edit', id=user.id)
        else:
            return redirect(url_for('view_home'))
    return render_template('user_add.html', form=form, mode='edit', id=user.id)


@app.route('/users/<int:user_id>/history', methods=['GET'])
def history(user_id):
    purchase_query = db.session.query(Purchase, Product.name, Product.price).join(Product, Purchase.product_id==Product.id).filter(Purchase.user_id == user_id).order_by(Purchase.id.desc())
    try:
        show = request.args.get('show', type=int)
    except KeyError:
        purchases = purchase_query.all();
    else:
        purchases = purchase_query.limit(show).all();
    user = User.query.filter_by(id = user_id).first_or_404()
    return render_template('user_history.html', purchases=purchases, user=user)


@app.route('/users/names', methods=['GET'])
def list_users():
    """ List all users """
    users = db.session.query(User.name).all()
    return jsonify([user[0] for user in users])


@app.route('/users/birthday', methods=['GET', 'POST'])
def add_birthdays():
    """ 
    Try to create a new user.
    """
    form = BirthdayForm()
    if form.validate_on_submit():
        user = User.query.filter_by(name = form.name.data).first()
        if user is not None:
            user.birthday = form.birthday.data
            db.session.commit()
            return redirect(url_for('add_birthdays'))
        else:
            form.name.errors.append('Username can not be found')
    return render_template('user_birthday.html', form=form)


@app.route('/purchase', methods=['POST'])
def batch_consume():
    data = request.get_json()
    for row in data:
        purchase = Purchase(row['user_id'], row['product_id'])
        db.session.add(purchase)
    db.session.commit()
    return 'Purchases created', 201


@app.route('/purchase/undo', methods=['POST'])
def batch_undo():
    data = request.get_json()
    for row in data:
        purchase = Purchase.query.filter_by(id = row['purchase_id']).first_or_404()
        purchase.undone = True
    db.session.commit()
    return 'Purchases undone', 201


@app.route('/purchase/<int:purchase_id>/undo', methods=['GET'])
def undo(purchase_id):
    purchase = Purchase.query.filter_by(id = purchase_id).first_or_404()
    purchase.undone = True
    db.session.commit()
    return redirect(url_for('history', user_id = purchase.user_id))


@app.route('/products', methods=['GET', 'POST'])
def view_products():
    """ 
    View all products.
    """
    products = Product.query.order_by(Product.priority.desc()).all()
    return render_template('products.html', products=products)


@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    """ 
    Try to create a new product.
    """
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(form.name.data, form.price.data, form.priority.data, form.age_limit.data)
        db.session.add(product)
        db.session.commit()
        return redirect(url_for('view_products'))
    return render_template('product_add.html', form=form, mode='add')


@app.route('/products/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.filter_by(id = product_id).first_or_404()
    form = ProductForm(request.form, product)
    if form.validate_on_submit():
        form.populate_obj(product)
        db.session.commit()
        return redirect(url_for('view_products'))
    return render_template('product_add.html', form=form, mode='edit', id=product.id)