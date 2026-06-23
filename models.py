from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from flask_login import UserMixin
import secrets

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='Customer') # Customer, Admin, SuperAdmin
    reset_token = db.Column(db.String(100), nullable=True)
    loyalty_points = db.Column(db.Integer, default=0) # New Feature
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    orders = db.relationship('Order', backref='customer', lazy=True)
    reservations = db.relationship('Reservation', backref='customer', lazy=True)
    feedbacks = db.relationship('Feedback', backref='customer', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    cost_price = db.Column(db.Float, default=0.0)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(255), nullable=True)
    stock_level = db.Column(db.Integer, default=100) # New Feature
    is_active = db.Column(db.Boolean, default=True)

    items = db.relationship('OrderItem', backref='product_ref', lazy=True)
    feedbacks = db.relationship('Feedback', backref='product', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    payment_status = db.Column(db.String(20), default='Unpaid')
    total_amount = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='Pending') # Pending, Preparing, Out for Delivery, Completed, Cancelled
    scheduled_delivery_time = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    cost_at_time = db.Column(db.Float, default=0.0)
    quantity = db.Column(db.Integer, nullable=False)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    guest_count = db.Column(db.Integer, nullable=False)
    reservation_time = db.Column(db.DateTime, nullable=False)
    special_requests = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Confirmed')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Feedback(db.Model): # New Feature
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    rating = db.Column(db.Integer, default=5)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Report(db.Model): # New Feature
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_type = db.Column(db.String(50), nullable=False) # e.g. "Order", "Product", "Feedback"
    item_id = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Open') # Open, Resolved, Ignored
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
