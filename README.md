
# 🛒 GroceryFlow — Grocery Ordering & Management System

GroceryFlow is a Python-based grocery ordering and management web application built with Streamlit and SQLite. It helps customers browse grocery products, place orders, and track their purchases, while store administrators can manage products, inventory, orders, and sales.

## ✨ Features

### 🛍️ Customer Store
- Browse grocery products by category
- Search for products
- View product images, descriptions, and prices
- Add products to a shopping cart
- Update quantities and remove items
- Checkout with customer details
- Cash on Delivery payment option
- Automatic delivery fee calculation
- Track orders using an order number and phone number

### 📦 Inventory Management
- View available stock
- Add new grocery products
- Edit product details and prices
- Update stock quantities
- Restock existing products
- Receive low-stock alerts
- Automatically deduct stock after successful orders

### 📊 Admin Dashboard
- Password-protected admin access
- View total sales and order statistics
- Monitor pending orders
- Manage products and categories
- Update order statuses
- View customer order details
- Generate daily sales reports
- Download order data as a CSV file

### 💾 Database
- SQLite database
- Persistent local product and order records
- Separate tables for products, orders, and order items
- Order items preserve their purchase-time prices

## 🧰 Technologies Used

- Python
- Streamlit
- SQLite
- Pandas
- HTML and CSS styling

## 📁 Project Structure

```text
GroceryFlow/
├── app.py
├── requirements.txt
├── README.md
└── groceryflow.db
```

The `groceryflow.db` database is created automatically when the application runs for the first time.

## ⚙️ Installation

### Prerequisites

- Python 3.11 or newer
- Visual Studio Code (recommended)
- An internet connection for externally hosted product images

### Step 1: Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd GroceryFlow
```

Alternatively, download the repository ZIP and extract it.

### Step 2: Create a virtual environment

On Windows:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run the application

```bash
streamlit run app.py
```

Open the local URL displayed in your terminal. It is usually:

http://localhost:8501

## 🔐 Admin Access

For local demonstration, the default admin password is:

`admin1234`

To change it for your current PowerShell session:

```powershell
$env:GROCERYFLOW_ADMIN_PASSWORD = "your-strong-password"
streamlit run app.py
```

**Security notice:** The default password is for testing only. Change it before deployment. This demo login is not a substitute for a production authentication system.

## 🚚 Delivery and Payments

- Currency: Pakistani Rupees (PKR)
- Delivery fee: PKR 150
- Free delivery: Orders of PKR 3,000 or more
- Payment method: Cash on Delivery

Delivery charges can be customized in the application code.

No real online payment processing is integrated.

## 🧪 Testing Checklist

- [ ] Browse and search products
- [ ] Add products to the cart
- [ ] Change quantities and remove items
- [ ] Place a test order
- [ ] Confirm that stock decreases
- [ ] Find the order using its number and phone
- [ ] Update the order status as an administrator
- [ ] Restock a product
- [ ] Export the order report

Test cancellation and inventory-restoration behavior carefully before using the app for real orders.

## 🚀 Future Improvements

- Customer registration and login
- Secure, role-based authentication
- Product image uploads
- Product reviews and ratings
- Discount codes and coupons
- Delivery staff dashboard
- Email or SMS notifications
- Real payment gateway integration
- Advanced sales analytics
- Hosted database for multi-user deployment
- Responsive, mobile-first user interface

## ⚠️ Deployment Notes

SQLite is suitable for learning, local testing, and small demonstrations. A hosted application may not retain local files across all deployments, and a local SQLite database is not ideal for a busy multi-user store.

For a real business, use reliable persistent storage, a hosted database, secure authentication, regular backups, and proper input validation.

## 👨‍💻 Author

**Ahmed Faisal**

Python Developer | Streamlit App Developer | AI Automation Student

GitHub: https://github.com/AhmedFaisalCareer

## 📄 License

This project is available for learning, portfolio demonstration, and customization. Add a specific open-source license if you want to define formal reuse and distribution permissions.
```

**Important:** Replace `YOUR_GITHUB_REPOSITORY_URL` with your actual repository URL before publishing. Keep `app.py`, `requirements.txt`, and `README.md` in the repository root so deployment tools can find them easily.