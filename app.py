import json
import os
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Order, OrderItem, Product, Setting
from functools import wraps
from dotenv import load_dotenv
from sqlalchemy import or_

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///kuku_shop.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key_change_me')

csrf = CSRFProtect(app)
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Intelligent Search Alias Mapping
SYNONYMS = {
    "kuku": ["chicken", "poultry", "roast"],
    "chips": ["fries", "potatoes", "fried"],
    "fries": ["chips", "potatoes"],
    "kima": ["liver", "gizzards"],
    "meat": ["chicken", "wings", "drumstick", "liver", "gizzards", "neck"],
    "starchy": ["chips", "fries"],
    "poultry": ["chicken", "kuku"]
}

def get_search_terms(query):
    query = query.lower().strip()
    terms = {query}
    for key, values in SYNONYMS.items():
        if query == key or query in values:
            terms.add(key)
            terms.update(values)
    return list(terms)

def role_required(roles):
    if isinstance(roles, str):
        roles = [roles]
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def seed_data():
    if Product.query.first() is None:
        products = [
            Product(name='Full Roast Chicken', price=800, category='chicken', image_url='images/kuku full.jpg', tags='kuku, chicken, roast, meal, family'),
            Product(name='Drumstick (1kg)', price=550, category='chicken', image_url='images/drumstick.jpg', tags='kuku, chicken, leg, meat'),
            Product(name='Chicken Wings (1kg)', price=600, category='chicken', image_url='images/chicken wings.jpg', tags='kuku, chicken, wings, snack'),
            Product(name='Gizzards (Portion)', price=250, category='chicken', image_url='images/gizzards.png', tags='kuku, gizzards, kima, offal'),
            Product(name='Chicken Liver', price=200, category='chicken', image_url='images/liver.png', tags='kuku, liver, kima, offal'),
            Product(name='Chicken Neck', price=150, category='chicken', image_url='images/neck.png', tags='kuku, neck, meat'),
            Product(name='Golden Chips (Large)', price=150, category='sides', image_url='images/chips.jpg', tags='fries, potatoes, starchy, side'),
            Product(name='Smokes', price=50, category='sides', image_url='images/smokes.jpg', tags='sausage, snack, side'),
        ]
        db.session.bulk_save_objects(products)

    if User.query.filter_by(role='SuperAdmin').first() is None:
        super_admin = User(
            first_name="Super",
            last_name="Admin",
            email="superadmin@hopekuku.com",
            password_hash=generate_password_hash("super_admin_2024"),
            role="SuperAdmin"
        )
        db.session.add(super_admin)

        admin = User(
            first_name="Store",
            last_name="Manager",
            email="admin@hopekuku.com",
            password_hash=generate_password_hash("admin_2024"),
            role="Admin"
        )
        db.session.add(admin)

    db.session.commit()

with app.app_context():
    db.create_all()
    seed_data()

# --- ROUTES ---

@app.route('/')
def index():
    featured_products = Product.query.filter_by(is_active=True).limit(3).all()
    return render_template('index.html', featured_products=featured_products)

@app.route('/menu')
def menu():
    query = request.args.get('q', '').strip()
    if query:
        search_terms = get_search_terms(query)
        filters = []
        for term in search_terms:
            filters.append(Product.name.contains(term))
            filters.append(Product.category.contains(term))
            filters.append(Product.tags.contains(term))

        products = Product.query.filter(Product.is_active == True).filter(or_(*filters)).all()
    else:
        products = Product.query.filter_by(is_active=True).all()

    return render_template('menu.html', products=products, query=query)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid email or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return redirect(url_for('signup'))

        new_user = User(
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            email=email,
            password_hash=generate_password_hash(request.form.get('password')),
            role='Customer'
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Account created! Please login.')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'POST':
        try:
            payment_method = request.form.get('payment_method')
            cart_data_raw = request.form.get('cart_data')

            if not cart_data_raw or cart_data_raw == '[]':
                flash('Your cart is empty.')
                return redirect(url_for('menu'))

            cart_items = json.loads(cart_data_raw)
            total_amount = 0
            verified_items = []

            for item in cart_items:
                product = Product.query.get(item['id'])
                if not product or not product.is_active:
                    flash(f"Product {item['name']} not available.")
                    return redirect(url_for('menu'))

                total_amount += product.price * item['quantity']
                verified_items.append({
                    'product_id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'quantity': item['quantity']
                })

            new_order = Order(
                user_id=current_user.id,
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                address=request.form.get('address'),
                city=request.form.get('city'),
                country=request.form.get('country'),
                payment_method=payment_method,
                total_amount=total_amount,
                status='Pending'
            )
            db.session.add(new_order)
            db.session.flush()

            for item in verified_items:
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=item['product_id'],
                    name=item['name'],
                    price=item['price'],
                    quantity=item['quantity']
                )
                db.session.add(order_item)

            db.session.commit()
            return render_template('success.html', order=new_order)

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error: {e}")
            flash('Error processing your order.')
            return redirect(url_for('checkout'))

    return render_template('checkout.html')

@app.route('/dashboard')
@login_required
def user_dashboard():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('user_dashboard.html', orders=orders)

@app.route('/admin/orders')
@role_required(['Admin', 'SuperAdmin'])
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=orders)

@app.route('/admin/order/<int:order_id>/status', methods=['POST'])
@role_required(['Admin', 'SuperAdmin'])
def update_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    if new_status:
        order.status = new_status
        db.session.commit()
        flash(f'Order #{order_id} updated.')
    return redirect(url_for('admin_orders'))

@app.route('/super-admin')
@role_required('SuperAdmin')
def super_admin():
    products = Product.query.all()
    settings = Setting.query.all()
    return render_template('super_admin.html', products=products, settings=settings)

@app.route('/super-admin/product/add', methods=['POST'])
@role_required('SuperAdmin')
def add_product():
    new_product = Product(
        name=request.form.get('name'),
        price=float(request.form.get('price')),
        category=request.form.get('category'),
        image_url=request.form.get('image_url'),
        tags=request.form.get('tags'),
        description=request.form.get('description')
    )
    db.session.add(new_product)
    db.session.commit()
    flash('Product added!')
    return redirect(url_for('super_admin'))

@app.route('/super-admin/setting/update', methods=['POST'])
@role_required('SuperAdmin')
def update_setting():
    key = request.form.get('key')
    value = request.form.get('value')
    setting = Setting.query.filter_by(key=key).first()
    if setting:
        setting.value = value
    else:
        setting = Setting(key=key, value=value)
        db.session.add(setting)
    db.session.commit()
    flash('Setting updated!')
    return redirect(url_for('super_admin'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true', port=port)
