import json
import os
import secrets
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from models import db, User, Order, OrderItem, Product, Setting, Reservation, Feedback, Report
from functools import wraps
from dotenv import load_dotenv
from sqlalchemy import or_, func

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///kuku_shop.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key_change_me')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB limit

# Mail Configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

csrf = CSRFProtect(app)
db.init_app(app)
mail = Mail(app)

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def seed_data():
    if Product.query.first() is None:
        products = [
            Product(name='Full Roast Chicken', price=800, cost_price=450, category='chicken', image_url='images/kuku full.jpg', tags='kuku, chicken, roast, meal, family'),
            Product(name='Drumstick (1kg)', price=550, cost_price=300, category='chicken', image_url='images/drumstick.jpg', tags='kuku, chicken, leg, meat'),
            Product(name='Chicken Wings (1kg)', price=600, cost_price=350, category='chicken', image_url='images/chicken wings.jpg', tags='kuku, chicken, wings, snack'),
            Product(name='Gizzards (Portion)', price=250, cost_price=120, category='chicken', image_url='images/gizzards.png', tags='kuku, gizzards, kima, offal'),
            Product(name='Chicken Liver', price=200, cost_price=100, category='chicken', image_url='images/liver.png', tags='kuku, liver, kima, offal'),
            Product(name='Chicken Neck', price=150, cost_price=50, category='chicken', image_url='images/neck.png', tags='kuku, neck, meat'),
            Product(name='Golden Chips (Large)', price=150, cost_price=60, category='sides', image_url='images/chips.jpg', tags='fries, potatoes, starchy, side'),
            Product(name='Smokes', price=50, cost_price=20, category='sides', image_url='images/smokes.jpg', tags='sausage, snack, side'),
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

# --- PUBLIC ROUTES ---

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

# --- AUTH ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
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

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            db.session.commit()

            reset_url = url_for('reset_password', token=token, _external=True)

            # Send Email
            msg = Message("Hope Kuku Shop - Password Reset", recipients=[user.email])
            msg.body = f"Hello {user.first_name},\n\nYou requested a password reset. Click the link below to continue:\n\n{reset_url}\n\nIf you did not request this, please ignore this email."
            try:
                mail.send(msg)
                flash('Password reset link sent to your email.')
            except Exception as e:
                app.logger.error(f"Mail error: {e}")
                flash(f'Error sending email. Development Reset Link: {reset_url}')
        else:
            flash('Email not found.')
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first_or_404()
    if request.method == 'POST':
        user.password_hash = generate_password_hash(request.form.get('password'))
        user.reset_token = None
        db.session.commit()
        flash('Password updated!')
        return redirect(url_for('login'))
    return render_template('reset_password.html', token=token)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --- CUSTOMER ROUTES ---

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'POST':
        try:
            cart_data_raw = request.form.get('cart_data')
            scheduled_time_raw = request.form.get('scheduled_time')
            if not cart_data_raw or cart_data_raw == '[]':
                flash('Cart empty.')
                return redirect(url_for('menu'))

            cart_items = json.loads(cart_data_raw)
            total_amount = 0
            total_cost = 0
            verified_items = []

            for item in cart_items:
                product = Product.query.get(item['id'])
                if not product or not product.is_active:
                    continue
                total_amount += product.price * item['quantity']
                total_cost += product.cost_price * item['quantity']
                verified_items.append({'id': product.id, 'name': product.name, 'price': product.price, 'cost': product.cost_price, 'qty': item['quantity']})

            new_order = Order(
                user_id=current_user.id,
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                address=request.form.get('address'),
                city=request.form.get('city'),
                country=request.form.get('country'),
                payment_method=request.form.get('payment_method'),
                total_amount=total_amount,
                total_cost=total_cost,
                scheduled_delivery_time=datetime.fromisoformat(scheduled_time_raw) if scheduled_time_raw else None
            )
            db.session.add(new_order)

            # Loyalty Points: 1 point for every 100 KES spent
            current_user.loyalty_points += int(total_amount / 100)

            db.session.flush()
            for item in verified_items:
                db.session.add(OrderItem(order_id=new_order.id, product_id=item['id'], name=item['name'], price=item['price'], cost_at_time=item['cost'], quantity=item['qty']))
            db.session.commit()
            return render_template('success.html', order=new_order)
        except Exception as e:
            db.session.rollback()
            flash('Error processing order.')
    return render_template('checkout.html')

@app.route('/book', methods=['GET', 'POST'])
@login_required
def book_table():
    if request.method == 'POST':
        new_res = Reservation(user_id=current_user.id, guest_count=request.form.get('guest_count'), reservation_time=datetime.fromisoformat(request.form.get('reservation_time')), special_requests=request.form.get('special_requests'))
        db.session.add(new_res)
        db.session.commit()
        flash('Table booked!')
        return redirect(url_for('user_dashboard'))
    return render_template('booking.html')

@app.route('/dashboard')
@login_required
def user_dashboard():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    reservations = Reservation.query.filter_by(user_id=current_user.id).order_by(Reservation.reservation_time.desc()).all()
    return render_template('user_dashboard.html', orders=orders, reservations=reservations)

@app.route('/feedback', methods=['POST'])
@login_required
def leave_feedback():
    product_id = request.form.get('product_id')
    order_id = request.form.get('order_id')
    rating = int(request.form.get('rating', 5))
    comment = request.form.get('comment')

    new_fb = Feedback(user_id=current_user.id, product_id=product_id, order_id=order_id, rating=rating, comment=comment)
    db.session.add(new_fb)
    db.session.commit()
    flash('Thank you for your feedback!')
    return redirect(url_for('user_dashboard'))

@app.route('/report', methods=['POST'])
@login_required
def report_item():
    item_type = request.form.get('item_type')
    item_id = request.form.get('item_id')
    reason = request.form.get('reason')

    new_report = Report(user_id=current_user.id, item_type=item_type, item_id=item_id, reason=reason)
    db.session.add(new_report)
    db.session.commit()
    flash('Report submitted. We will investigate.')
    return redirect(url_for('user_dashboard'))

# --- ADMIN ROUTES ---

@app.route('/admin/orders')
@role_required(['Admin', 'SuperAdmin'])
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    stats = {
        'revenue': db.session.query(func.sum(Order.total_amount)).filter(Order.status != 'Cancelled').scalar() or 0,
        'profit': (db.session.query(func.sum(Order.total_amount)).filter(Order.status != 'Cancelled').scalar() or 0) - (db.session.query(func.sum(Order.total_cost)).filter(Order.status != 'Cancelled').scalar() or 0),
        'pending': Order.query.filter_by(status='Pending').count()
    }
    return render_template('orders.html', orders=orders, stats=stats)

@app.route('/admin/order/<int:order_id>/status', methods=['POST'])
@role_required(['Admin', 'SuperAdmin'])
def update_status(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = request.form.get('status')
    order.payment_status = request.form.get('payment_status')
    db.session.commit()
    flash('Order updated.')
    return redirect(url_for('admin_orders'))

@app.route('/admin/customers')
@role_required(['Admin', 'SuperAdmin'])
def admin_customers():
    customers = User.query.filter_by(role='Customer').all()
    return render_template('admin_customers.html', customers=customers)

@app.route('/admin/products')
@role_required(['Admin', 'SuperAdmin'])
def admin_products():
    products = Product.query.all()
    return render_template('admin_products.html', products=products)

@app.route('/admin/product/add', methods=['GET', 'POST'])
@role_required(['Admin', 'SuperAdmin'])
def add_product():
    if request.method == 'POST':
        image_url = request.form.get('image_url') # Default

        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_url = f'uploads/{filename}'

        db.session.add(Product(
            name=request.form.get('name'),
            price=float(request.form.get('price')),
            cost_price=float(request.form.get('cost_price')),
            category=request.form.get('category'),
            image_url=image_url,
            tags=request.form.get('tags'),
            description=request.form.get('description'),
            stock_level=int(request.form.get('stock_level', 100))
        ))
        db.session.commit()
        flash('Product added!')
        return redirect(url_for('admin_products'))
    return render_template('product_form.html', action="Add")

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@role_required(['Admin', 'SuperAdmin'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                product.image_url = f'uploads/{filename}'
        elif request.form.get('image_url'):
             product.image_url = request.form.get('image_url')

        product.name, product.price, product.cost_price, product.category, product.tags, product.description, product.is_active = request.form.get('name'), float(request.form.get('price')), float(request.form.get('cost_price')), request.form.get('category'), request.form.get('tags'), request.form.get('description'), 'is_active' in request.form
        product.stock_level = int(request.form.get('stock_level', 100))
        db.session.commit()
        return redirect(url_for('admin_products'))
    return render_template('product_form.html', product=product, action="Edit")

# --- SUPER ADMIN ---

@app.route('/super-admin')
@role_required('SuperAdmin')
def super_admin():
    return render_template('super_admin.html',
                           settings=Setting.query.all(),
                           users=User.query.all(),
                           feedbacks=Feedback.query.order_by(Feedback.created_at.desc()).all(),
                           reports=Report.query.order_by(Report.created_at.desc()).all())

@app.route('/super-admin/user/<int:user_id>/role', methods=['POST'])
@role_required('SuperAdmin')
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    user.role = request.form.get('role')
    db.session.commit()
    return redirect(url_for('super_admin'))

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))
