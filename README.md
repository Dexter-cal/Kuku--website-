# 🍗 Hope Kuku Shop - Ultimate Restaurant Suite

A complete enterprise-grade restaurant management and e-commerce platform.

## 🌟 Key Features
- **Semantic Search**: Intelligent product discovery (e.g., 'kuku' finds chicken).
- **Table Booking**: Real-time restaurant reservation system.
- **Scheduled Delivery**: Customers can pick a future time for their order.
- **Financial Analytics**: Admin dashboard with Revenue and **Profit** tracking.
- **Customer Management**: View customer directory and order history.
- **User Authentication**: Secure Login/Signup with **Forgot Password** recovery.
- **Role-Based Access**: 3-Tier security (Customer, Admin, Super Admin).
- **Cross-Platform**: Ready to run on Windows, Linux, and macOS.

## 🚀 Deployment

### Windows
```cmd
run.bat
```

### Linux / macOS
```bash
chmod +x run.sh
./run.sh
```

### Docker
```bash
docker-compose up --build
```

## 🔐 Credentials
Default access details are in `CREDENTIALS.md`.

## 🛠 Tech Stack
- **Backend**: Flask, SQLAlchemy, Flask-Login, Flask-WTF.
- **Database**: SQLite (managed via SQLAlchemy).
- **Frontend**: Responsive HTML5, CSS3, Vanilla JavaScript.
- **Security**: PBKDF2 Password Hashing, CSRF Tokens, RBAC.

---
Developed by Jules Engineer.
