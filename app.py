import json
import os
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Order, OrderItem, Product
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///kuku_shop.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key_change_me')

# Enable CSRF Protection
csrf = CSRFProtect(app)

db.init_app(app)

# Hashed Admin Password (Default: kuku_admin_2024)
DEFAULT_HASH = generate_password_hash("kuku_admin_2024")
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', DEFAULT_HASH)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def seed_products():
    if Product.query.first() is None:
        products = [
            Product(name='Full Roast Chicken', price=800, category='chicken', image_url='images/kuku full.jpg'),
            Product(name='Drumstick (1kg)', price=550, category='chicken', image_url='images/drumstick.jpg'),
            Product(name='Chicken Wings (1kg)', price=600, category='chicken', image_url='images/chicken wings.jpg'),
            Product(name='Gizzards (Portion)', price=250, category='chicken', image_url='images/gizzards.png'),
            Product(name='Chicken Liver', price=200, category='chicken', image_url='images/liver.png'),
            Product(name='Chicken Neck', price=150, category='chicken', image_url='images/neck.png'),
            Product(name='Golden Chips (Large)', price=150, category='sides', image_url='images/chips.jpg'),
            Product(name='Smokes', price=50, category='sides', image_url='images/smokes.jpg'),
        ]
        db.session.bulk_save_objects(products)
        db.session.commit()

with app.app_context():
    db.create_all()
    seed_products()

@app.route('/')
def index():
    featured_products = Product.query.limit(3).all()
    return render_template('index.html', featured_products=featured_products)

@app.route('/menu')
def menu():
    products = Product.query.all()
    return render_template('menu.html', products=products)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        try:
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            address = request.form.get('address')
            city = request.form.get('city')
            country = request.form.get('country')
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
                if not product:
                    flash(f"Product {item['name']} not found.")
                    return redirect(url_for('menu'))

                # Server-side price calculation
                item_total = product.price * item['quantity']
                total_amount += item_total
                verified_items.append({
                    'product_id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'quantity': item['quantity']
                })

            new_order = Order(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                address=address,
                city=city,
                country=country,
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
            app.logger.error(f"Error processing order: {e}")
            flash('There was an error processing your order.')
            return redirect(url_for('checkout'))

    return render_template('checkout.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_orders'))
        else:
            flash('Invalid password')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin/orders')
@login_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=orders)

@app.route('/admin/order/<int:order_id>/status', methods=['POST'])
@login_required
def update_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    if new_status:
        order.status = new_status
        db.session.commit()
        flash(f'Order #{order_id} status updated to {new_status}')
    return redirect(url_for('admin_orders'))

@app.route('/about')
def about():
    return "About Us page coming soon!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true', port=port)
