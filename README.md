# 🍗 Hope Kuku Shop - Premium Roasted Chicken

A modern, secure, and professional e-commerce platform for a local chicken shop. Built with Flask, SQLAlchemy, and a clean frontend.

## 🚀 Quick Start

### Option 1: Standard Setup
```bash
chmod +x setup.sh
./setup.sh
source venv/bin/activate
python app.py
```

### Option 2: Docker
```bash
docker build -t kuku-shop .
docker run -p 5000:5000 kuku-shop
```

Access the application at `http://localhost:5000`.

## 🛠 Features
- **Dynamic Menu**: Fully database-driven menu with categories (Chicken, Sides).
- **Secure Ordering**: Server-side price verification to prevent manipulation.
- **Cart Management**: Persistent shopping cart using browser LocalStorage.
- **Payment Integration**: Simulated M-Pesa STK push and Bitcoin payment flows.
- **Admin Dashboard**: Secure interface to manage orders and delivery status.
- **Responsive Design**: Optimized for mobile and desktop customers.

## 🔐 Admin Access
- **URL**: `http://localhost:5000/admin/orders`
- **Default Password**: `kuku_admin_2024`
*(Note: In production, change the password in `app.py` or use environment variables)*

## 📂 Project Structure
- `app.py`: Main application logic and routes.
- `models.py`: Database schema (Product, Order, OrderItem).
- `templates/`: HTML templates (Jinja2).
- `static/`: CSS, Images, and JavaScript.
- `instance/`: SQLite database storage.

## 📝 Security Features
- **Price Guard**: The server looks up item prices in the database during checkout; it never trusts the price sent from the client.
- **Admin Auth**: Orders are protected by a login session.
- **PII Protection**: Sensitive customer data is only visible to authenticated admins.

---
Developed by Jules Engineer.
