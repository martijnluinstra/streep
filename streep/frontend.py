from flask import render_template, redirect, url_for, request
from datetime import datetime
from dateutil.relativedelta import relativedelta
from streep import app, db
from models import User, Purchase, Product
from forms import UserForm, ProductForm
import csv


@app.context_processor
def utility_processor():
    def format_price(amount, currency=u"\u20AC"):
        return u'{1} {0:.2f}'.format(amount, currency)
    def is_eligible(birthdate, product_age_limit):
        age = relativedelta(datetime.now(), birthdate).years
        return not (product_age_limit and age<18)
    return dict(format_price=format_price, is_eligible=is_eligible)

@app.route('/', methods=['GET'])
def view_home():
    """ View all users, ordered by name """
    spend_subq = db.session.query(Purchase.user_id.label("user_id"), db.func.sum(Product.price).label("spend")).join(Product, Purchase.product_id==Product.id).filter(Purchase.undone == False).group_by(Purchase.user_id).subquery()
    users =  db.session.query(User, spend_subq.c.spend).outerjoin(spend_subq, spend_subq.c.user_id==User.id).all()
    # users = User.query.order_by(User.name).all()
    products = Product.query.all()
    return render_template('index.html', users=users, products=products)


@app.route('/faq', methods=['POST'])
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
        db.session.commit()
        return redirect(url_for('view_home'))
    return render_template('user_add.html', form=form, mode='add')


@app.route('/users/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.filter_by(id = user_id).first_or_404()
    form = UserForm(request.form, user)
    if form.validate_on_submit():
        form.populate_obj(user)
        db.session.commit()
        return redirect(url_for('view_home'))
    return render_template('user_add.html', form=form, mode='edit', id=user.id)


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
        return redirect(url_for('view_home'))
    return render_template('product_add.html', form=form, mode='add')


@app.route('/products/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.filter_by(id = product_id).first_or_404()
    form = ProductForm(request.form, product)
    if form.validate_on_submit():
        form.populate_obj(product)
        db.session.commit()
        return redirect(url_for('view_home'))
    return render_template('product_add.html', form=form, mode='edit', id=product.id)


@app.route('/users/<int:user_id>/history', methods=['GET'])
def history(user_id):
    # purchases = Purchase.query.filter_by(user_id = user_id).all()
    purchases = db.session.query(Purchase, Product.name, Product.price).join(Product, Purchase.product_id==Product.id).filter(Purchase.user_id == user_id).order_by(Purchase.id.desc()).all()
    user = User.query.filter_by(id = user_id).first_or_404()
    return render_template('user_history.html', purchases=purchases, user=user)


@app.route('/purchase/<int:purchase_id>/undo', methods=['GET'])
def undo(purchase_id):
    purchase = Purchase.query.filter_by(id = purchase_id).first_or_404()
    purchase.undone = True
    db.session.commit()
    return redirect(url_for('history', user_id = purchase.user_id))


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