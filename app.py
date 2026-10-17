import os
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "groceryflow.db"
ADMIN_PASSWORD = os.getenv("GROCERYFLOW_ADMIN_PASSWORD", "admin1234")
DELIVERY_FEE = 150.0
LOW_STOCK_THRESHOLD = 5

st.set_page_config(
    page_title="GroceryFlow | Grocery Store",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background: #f7faf7; }
    [data-testid="stSidebar"] { background: #eef6ef; }
    .hero {
        padding: 1.5rem 1.7rem; border-radius: 18px;
        background: linear-gradient(120deg, #14532d, #16a34a);
        color: white; margin-bottom: 1.2rem;
    }
    .hero h1 { color: white; margin-bottom: .25rem; }
    .hero p { color: #e7fbe9; margin-bottom: 0; }
    .metric-card {
        background: white; border: 1px solid #e1ece2;
        padding: 1rem; border-radius: 14px; min-height: 95px;
    }
    .product-card {
        background: white; border: 1px solid #e1ece2;
        padding: .8rem; border-radius: 14px; margin-bottom: .5rem;
    }
    div.stButton > button[kind="primary"] {
        background: #15803d; border-color: #15803d;
    }
</style>
""", unsafe_allow_html=True)


# -------------------- DATABASE --------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL CHECK(price >= 0),
            stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
            image_url TEXT DEFAULT '',
            description TEXT DEFAULT '',
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            payment_method TEXT NOT NULL DEFAULT 'Cash on Delivery',
            subtotal REAL NOT NULL,
            delivery_fee REAL NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Received',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            unit_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            line_total REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL
        );
        """)

        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sample_products = [
                ("Fresh Apples", "Fruits", 450, 25, "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=600", "Crisp and juicy apples"),
                ("Bananas", "Fruits", 180, 40, "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=600", "Fresh bananas by the dozen"),
                ("Tomatoes", "Vegetables", 160, 30, "https://images.unsplash.com/photo-1546094096-0df4bcaaa337?w=600", "Fresh red tomatoes"),
                ("Potatoes", "Vegetables", 100, 50, "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=600", "Everyday cooking potatoes"),
                ("Milk 1L", "Dairy", 280, 20, "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=600", "Fresh milk"),
                ("Eggs (dozen)", "Dairy", 360, 18, "https://images.unsplash.com/photo-1506976785307-8732e854ad03?w=600", "Farm eggs"),
                ("Basmati Rice 1kg", "Staples", 390, 15, "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=600", "Premium basmati rice"),
                ("Cooking Oil 1L", "Staples", 590, 12, "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=600", "Cooking oil for everyday meals"),
                ("Orange Juice", "Drinks", 250, 14, "https://images.unsplash.com/photo-1600271886742-f049cd451bba?w=600", "Refreshing orange juice"),
                ("Potato Chips", "Snacks", 100, 22, "https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=600", "Crunchy snack"),
                ("Bread Loaf", "Bakery", 170, 16, "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=600", "Fresh bakery bread"),
                ("Dishwashing Liquid", "Household", 320, 8, "https://images.unsplash.com/photo-1585421514284-efb74c2b69ba?w=600", "Kitchen cleaning essential"),
            ]
            conn.executemany("""
                INSERT INTO products
                (name, category, price, stock, image_url, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [(*p, now) for p in sample_products])


init_db()


# -------------------- HELPERS --------------------
def money(value):
    return f"PKR {float(value):,.0f}"


def fetch_products(active_only=True):
    with get_connection() as conn:
        if active_only:
            rows = conn.execute("SELECT * FROM products WHERE active=1 ORDER BY category, name").fetchall()
        else:
            rows = conn.execute("SELECT * FROM products ORDER BY category, name").fetchall()
    return [dict(row) for row in rows]


def fetch_orders():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]


def fetch_order_items(order_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM order_items WHERE order_id=? ORDER BY id", (order_id,)
        ).fetchall()
    return [dict(row) for row in rows]


def clear_cart():
    st.session_state.cart = {}


def add_to_cart(product_id, quantity=1):
    product = next((p for p in fetch_products() if p["id"] == product_id), None)
    if not product:
        st.error("This product is no longer available.")
        return
    current = st.session_state.cart.get(product_id, 0)
    new_quantity = current + quantity
    if new_quantity > product["stock"]:
        st.warning(f"Only {product['stock']} unit(s) are currently in stock.")
        return
    st.session_state.cart[product_id] = new_quantity
    st.toast(f"Added {product['name']} to your cart")


def cart_details():
    products = {p["id"]: p for p in fetch_products()}
    items = []
    for product_id, quantity in st.session_state.cart.items():
        product = products.get(product_id)
        if product and quantity > 0:
            items.append({
                "id": product_id,
                "name": product["name"],
                "price": float(product["price"]),
                "stock": int(product["stock"]),
                "quantity": int(quantity),
                "line_total": float(product["price"]) * int(quantity),
            })
    return items


def place_order(customer_name, phone, address, payment_method):
    items = cart_details()
    if not items:
        return False, "Your cart is empty."

    subtotal = sum(item["line_total"] for item in items)
    delivery_fee = DELIVERY_FEE if subtotal < 3000 else 0.0
    total = subtotal + delivery_fee
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with get_connection() as conn:
            # Check current stock and deduct it within one transaction.
            for item in items:
                row = conn.execute(
                    "SELECT name, price, stock, active FROM products WHERE id=?",
                    (item["id"],),
                ).fetchone()
                if row is None or not row["active"]:
                    raise ValueError(f"{item['name']} is no longer available.")
                if row["stock"] < item["quantity"]:
                    raise ValueError(
                        f"Not enough stock for {row['name']}. Available: {row['stock']}."
                    )

            cursor = conn.execute("""
                INSERT INTO orders
                (customer_name, phone, address, payment_method, subtotal,
                 delivery_fee, total, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Received', ?)
            """, (customer_name.strip(), phone.strip(), address.strip(),
                  payment_method, subtotal, delivery_fee, total, now))
            order_id = cursor.lastrowid

            for item in items:
                row = conn.execute(
                    "SELECT price, name FROM products WHERE id=?", (item["id"],)
                ).fetchone()
                price = float(row["price"])
                conn.execute("""
                    INSERT INTO order_items
                    (order_id, product_id, product_name, unit_price, quantity, line_total)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (order_id, item["id"], row["name"], price,
                      item["quantity"], price * item["quantity"]))
                conn.execute(
                    "UPDATE products SET stock = stock - ? WHERE id=?",
                    (item["quantity"], item["id"]),
                )

        clear_cart()
        return True, str(order_id)
    except (sqlite3.Error, ValueError) as exc:
        return False, str(exc)


def metric(label, value, note=""):
    st.markdown(
        f'<div class="metric-card"><div style="color:#64748b;font-size:.9rem">{label}</div>'
        f'<div style="font-size:1.65rem;font-weight:750;color:#14532d">{value}</div>'
        f'<div style="color:#64748b;font-size:.8rem">{note}</div></div>',
        unsafe_allow_html=True,
    )


# -------------------- SESSION STATE --------------------
if "cart" not in st.session_state:
    st.session_state.cart = {}
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "customer_order_id" not in st.session_state:
    st.session_state.customer_order_id = None


# -------------------- SIDEBAR NAVIGATION --------------------
st.sidebar.markdown("## 🛒 GroceryFlow")
st.sidebar.caption("Fresh groceries. Simple management.")
page = st.sidebar.radio(
    "Navigate",
    ["Customer Store", "My Orders", "Admin Dashboard"],
    label_visibility="visible",
)
st.sidebar.divider()
cart_count = sum(st.session_state.cart.values())
st.sidebar.metric("Cart items", cart_count)
st.sidebar.caption(f"Delivery: {money(DELIVERY_FEE)} under PKR 3,000")
st.sidebar.caption("Demo admin password: `admin1234`")
st.sidebar.caption("Change it before sharing the app.")


# -------------------- CUSTOMER STORE --------------------
if page == "Customer Store":
    st.markdown("""
    <div class="hero">
      <h1>Fresh groceries, delivered simply.</h1>
      <p>Shop daily essentials at GroceryFlow — your neighbourhood grocery store.</p>
    </div>
    """, unsafe_allow_html=True)

    products = fetch_products()
    if not products:
        st.info("No products are available right now.")
    else:
        left, right = st.columns([3, 1])
        with left:
            search = st.text_input("🔎 Search groceries", placeholder="Search apples, milk, rice...")
        with right:
            categories = ["All"] + sorted({p["category"] for p in products})
            category = st.selectbox("Category", categories)

        filtered = [
            p for p in products
            if (category == "All" or p["category"] == category)
            and (search.strip().lower() in p["name"].lower()
                 or search.strip().lower() in p["description"].lower()
                 or search.strip().lower() in p["category"].lower())
        ]

        if not filtered:
            st.warning("No products match your search.")
        else:
            cols = st.columns(3)
            for index, product in enumerate(filtered):
                with cols[index % 3]:
                    st.markdown('<div class="product-card">', unsafe_allow_html=True)
                    if product["image_url"]:
                        st.image(product["image_url"], use_container_width=True)
                    st.subheader(product["name"])
                    st.caption(product["category"])
                    st.write(product["description"] or "Everyday grocery essential.")
                    st.markdown(f"### {money(product['price'])}")
                    if product["stock"] <= LOW_STOCK_THRESHOLD:
                        st.caption(f"⚠️ Only {product['stock']} left")
                    else:
                        st.caption(f"In stock: {product['stock']}")
                    if product["stock"] > 0:
                        if st.button("＋ Add to cart", key=f"add_{product['id']}", use_container_width=True):
                            add_to_cart(product["id"])
                            st.rerun()
                    else:
                        st.button("Out of stock", key=f"out_{product['id']}", disabled=True, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("🛍️ Your cart")
    items = cart_details()
    if not items:
        st.info("Your cart is empty. Add a few groceries to get started.")
    else:
        for item in items:
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            c1.write(f"**{item['name']}**")
            c2.write(money(item["price"]))
            new_qty = c3.number_input(
                "Qty", min_value=0, max_value=item["stock"], value=item["quantity"],
                step=1, key=f"qty_{item['id']}", label_visibility="collapsed"
            )
            c4.write(money(item["line_total"]))
            if new_qty != item["quantity"]:
                if new_qty == 0:
                    st.session_state.cart.pop(item["id"], None)
                else:
                    st.session_state.cart[item["id"]] = int(new_qty)
                st.rerun()

        subtotal = sum(item["line_total"] for item in items)
        delivery_fee = DELIVERY_FEE if subtotal < 3000 else 0.0
        st.write(f"**Subtotal:** {money(subtotal)}")
        st.write(f"**Delivery:** {money(delivery_fee)}" + (" (free over PKR 3,000)" if delivery_fee == 0 else ""))
        st.markdown(f"## Total: {money(subtotal + delivery_fee)}")

        with st.expander("Checkout", expanded=True):
            with st.form("checkout_form"):
                customer_name = st.text_input("Full name")
                phone = st.text_input("Phone number", placeholder="03XXXXXXXXX")
                address = st.text_area("Delivery address")
                payment_method = st.selectbox("Payment method", ["Cash on Delivery"])
                submitted = st.form_submit_button("Place order", type="primary", use_container_width=True)
                if submitted:
                    if not customer_name.strip() or not phone.strip() or not address.strip():
                        st.error("Please fill in your name, phone number and delivery address.")
                    elif len(phone.strip()) < 7:
                        st.error("Please enter a valid phone number.")
                    else:
                        ok, result = place_order(customer_name, phone, address, payment_method)
                        if ok:
                            st.session_state.customer_order_id = int(result)
                            st.success(f"Order placed successfully! Your order number is #{result}.")
                            st.info("Open **My Orders** to view its current status.")
                            st.rerun()
                        else:
                            st.error(result)


# -------------------- MY ORDERS --------------------
elif page == "My Orders":
    st.markdown('<div class="hero"><h1>Track your order</h1><p>Enter your order number and phone number to view order details.</p></div>', unsafe_allow_html=True)
    with st.form("track_order_form"):
        default_order = st.session_state.customer_order_id or 1
        order_id = st.number_input("Order number", min_value=1, value=int(default_order), step=1)
        phone = st.text_input("Phone number used at checkout")
        track = st.form_submit_button("Find order", type="primary")
    if track:
        with get_connection() as conn:
            order = conn.execute(
                "SELECT * FROM orders WHERE id=? AND phone=?", (int(order_id), phone.strip())
            ).fetchone()
            if order:
                order = dict(order)
                st.success(f"Order #{order['id']} — {order['status']}")
                a, b, c = st.columns(3)
                a.metric("Order total", money(order["total"]))
                b.metric("Payment", order["payment_method"])
                c.metric("Placed on", order["created_at"])
                st.write(f"**Deliver to:** {order['customer_name']} — {order['address']}")
                st.subheader("Items")
                order_items = fetch_order_items(order["id"])
                st.dataframe(pd.DataFrame(order_items)[
                    ["product_name", "unit_price", "quantity", "line_total"]
                ].rename(columns={
                    "product_name": "Product", "unit_price": "Unit price (PKR)",
                    "quantity": "Quantity", "line_total": "Line total (PKR)"
                }), use_container_width=True, hide_index=True)
            else:
                st.error("Order not found. Check both the order number and phone number.")


# -------------------- ADMIN DASHBOARD --------------------
elif page == "Admin Dashboard":
    st.markdown('<div class="hero"><h1>Admin Dashboard</h1><p>Manage products, inventory, orders and sales.</p></div>', unsafe_allow_html=True)

    if not st.session_state.admin_logged_in:
        st.info("Sign in to access store management.")
        with st.form("admin_login_form"):
            password = st.text_input("Admin password", type="password")
            login = st.form_submit_button("Sign in", type="primary")
            if login:
                if password == ADMIN_PASSWORD:
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
        st.caption("For local testing, the default password is admin1234. Set GROCERYFLOW_ADMIN_PASSWORD before deploying.")
    else:
        top1, top2 = st.columns([5, 1])
        top1.success("You are signed in as the store administrator.")
        if top2.button("Log out"):
            st.session_state.admin_logged_in = False
            st.rerun()

        admin_tab, products_tab, inventory_tab, orders_tab, reports_tab = st.tabs(
            ["Overview", "Products", "Inventory", "Orders", "Reports"]
        )

        with admin_tab:
            products = fetch_products(active_only=False)
            orders = fetch_orders()
            revenue = sum(o["total"] for o in orders if o["status"] != "Cancelled")
            pending = sum(1 for o in orders if o["status"] in ("Received", "Preparing"))
            low_stock = sum(1 for p in products if p["active"] and p["stock"] <= LOW_STOCK_THRESHOLD)
            m1, m2, m3, m4 = st.columns(4)
            with m1: metric("Total sales*", money(revenue), "*Excludes cancelled orders")
            with m2: metric("Orders", len(orders), "All order statuses")
            with m3: metric("Pending orders", pending, "Received or preparing")
            with m4: metric("Low-stock products", low_stock, f"Threshold: {LOW_STOCK_THRESHOLD} or fewer")

            st.subheader("Recent orders")
            if orders:
                recent = pd.DataFrame(orders[:8])
                st.dataframe(recent[["id", "customer_name", "total", "status", "created_at"]].rename(
                    columns={"id": "Order #", "customer_name": "Customer", "total": "Total (PKR)",
                             "status": "Status", "created_at": "Placed at"}
                ), use_container_width=True, hide_index=True)
            else:
                st.info("No orders yet. Orders will appear here after checkout.")

            st.subheader("Stock alerts")
            alerts = [p for p in products if p["active"] and p["stock"] <= LOW_STOCK_THRESHOLD]
            if alerts:
                st.dataframe(pd.DataFrame(alerts)[["name", "category", "stock", "price"]].rename(
                    columns={"name": "Product", "category": "Category", "stock": "Stock", "price": "Price (PKR)"}
                ), use_container_width=True, hide_index=True)
            else:
                st.success("All active products are above the low-stock threshold.")

        with products_tab:
            st.subheader("Add a product")
            with st.form("add_product_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                name = col1.text_input("Product name")
                category = col2.selectbox("Category", ["Fruits", "Vegetables", "Dairy", "Meat", "Staples", "Drinks", "Snacks", "Bakery", "Household", "Other"])
                price = col1.number_input("Price (PKR)", min_value=0.0, value=100.0, step=10.0)
                stock = col2.number_input("Opening stock", min_value=0, value=10, step=1)
                image_url = st.text_input("Image URL (optional)")
                description = st.text_area("Description (optional)")
                add_product = st.form_submit_button("Add product", type="primary")
                if add_product:
                    if not name.strip():
                        st.error("Product name is required.")
                    else:
                        with get_connection() as conn:
                            conn.execute("""
                                INSERT INTO products
                                (name, category, price, stock, image_url, description, active, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                            """, (name.strip(), category, price, int(stock), image_url.strip(),
                                  description.strip(), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        st.success(f"{name} added.")
                        st.rerun()

            st.divider()
            st.subheader("Edit or deactivate products")
            all_products = fetch_products(active_only=False)
            if all_products:
                choices = {f"#{p['id']} — {p['name']}": p["id"] for p in all_products}
                selected_label = st.selectbox("Choose product", list(choices.keys()))
                selected_id = choices[selected_label]
                product = next(p for p in all_products if p["id"] == selected_id)
                with st.form(f"edit_product_{selected_id}"):
                    edit_name = st.text_input("Name", value=product["name"])
                    edit_category = st.text_input("Category", value=product["category"])
                    edit_price = st.number_input("Price (PKR)", min_value=0.0, value=float(product["price"]), step=10.0)
                    edit_stock = st.number_input("Stock", min_value=0, value=int(product["stock"]), step=1)
                    edit_image = st.text_input("Image URL", value=product["image_url"] or "")
                    edit_description = st.text_area("Description", value=product["description"] or "")
                    active = st.checkbox("Available in customer store", value=bool(product["active"]))
                    save_product = st.form_submit_button("Save product changes", type="primary")
                    if save_product:
                        if not edit_name.strip() or not edit_category.strip():
                            st.error("Name and category are required.")
                        else:
                            with get_connection() as conn:
                                conn.execute("""
                                    UPDATE products SET name=?, category=?, price=?, stock=?,
                                    image_url=?, description=?, active=? WHERE id=?
                                """, (edit_name.strip(), edit_category.strip(), edit_price, int(edit_stock),
                                      edit_image.strip(), edit_description.strip(), int(active), selected_id))
                            st.success("Product updated.")
                            st.rerun()

        with inventory_tab:
            st.subheader("Inventory overview")
            products = [p for p in fetch_products(active_only=False) if p["active"]]
            if products:
                inventory_df = pd.DataFrame(products)[["id", "name", "category", "stock", "price"]].copy()
                inventory_df["Stock value (PKR)"] = inventory_df["stock"] * inventory_df["price"]
                st.dataframe(inventory_df.rename(columns={
                    "id": "ID", "name": "Product", "category": "Category",
                    "stock": "Units in stock", "price": "Unit price (PKR)"
                }), use_container_width=True, hide_index=True)
                st.metric("Total inventory value at selling prices", money(inventory_df["Stock value (PKR)"].sum()))
                st.caption("This is an estimate based on selling prices, not purchase cost.")
            else:
                st.info("No active products.")

            st.divider()
            st.subheader("Restock a product")
            restock_products = fetch_products(active_only=True)
            if restock_products:
                choices = {f"#{p['id']} — {p['name']} (stock: {p['stock']})": p["id"] for p in restock_products}
                with st.form("restock_form"):
                    restock_label = st.selectbox("Product", list(choices.keys()))
                    units = st.number_input("Units to add", min_value=1, value=5, step=1)
                    restock = st.form_submit_button("Add stock", type="primary")
                    if restock:
                        with get_connection() as conn:
                            conn.execute("UPDATE products SET stock=stock+? WHERE id=?", (int(units), choices[restock_label]))
                        st.success("Inventory updated.")
                        st.rerun()

        with orders_tab:
            st.subheader("Manage orders")
            orders = fetch_orders()
            if not orders:
                st.info("No orders have been placed yet.")
            else:
                statuses = ["Received", "Preparing", "Ready for Dispatch", "Out for Delivery", "Completed", "Cancelled"]
                order_choices = {
                    f"Order #{o['id']} — {o['customer_name']} — {money(o['total'])} — {o['status']}": o["id"]
                    for o in orders
                }
                selected_order_label = st.selectbox("Select order", list(order_choices.keys()))
                selected_order_id = order_choices[selected_order_label]
                selected_order = next(o for o in orders if o["id"] == selected_order_id)
                a, b, c = st.columns(3)
                a.metric("Order total", money(selected_order["total"]))
                b.metric("Payment", selected_order["payment_method"])
                c.metric("Placed at", selected_order["created_at"])
                st.write(f"**Customer:** {selected_order['customer_name']} · **Phone:** {selected_order['phone']}")
                st.write(f"**Address:** {selected_order['address']}")
                items = fetch_order_items(selected_order_id)
                if items:
                    st.dataframe(pd.DataFrame(items)[["product_name", "unit_price", "quantity", "line_total"]].rename(
                        columns={"product_name": "Product", "unit_price": "Unit price (PKR)",
                                 "quantity": "Qty", "line_total": "Line total (PKR)"}
                    ), use_container_width=True, hide_index=True)
                with st.form(f"update_order_{selected_order_id}"):
                    current_status = selected_order["status"]
                    status_index = statuses.index(current_status) if current_status in statuses else 0
                    new_status = st.selectbox("Update status", statuses, index=status_index)
                    update_order = st.form_submit_button("Save order status", type="primary")
                    if update_order:
                        with get_connection() as conn:
                            conn.execute("UPDATE orders SET status=? WHERE id=?", (new_status, selected_order_id))
                            # If cancelled, restore stock exactly once.
                            if new_status == "Cancelled" and current_status != "Cancelled":
                                for item in items:
                                    if item["product_id"] is not None:
                                        conn.execute("UPDATE products SET stock=stock+? WHERE id=?",
                                                     (item["quantity"], item["product_id"]))
                            # Do not allow a cancelled order to be reactivated automatically,
                            # because its stock may have been sold again after cancellation.
                            if current_status == "Cancelled" and new_status != "Cancelled":
                                st.warning("Cancelled orders should not be reactivated. Create a new order instead.")
                                conn.execute("UPDATE orders SET status='Cancelled' WHERE id=?", (selected_order_id,))
                        st.success("Order status saved.")
                        st.rerun()

        with reports_tab:
            st.subheader("Sales report")
            orders = fetch_orders()
            completed_or_active = [o for o in orders if o["status"] != "Cancelled"]
            if completed_or_active:
                report = pd.DataFrame(completed_or_active)
                report["created_at"] = pd.to_datetime(report["created_at"], errors="coerce")
                report["date"] = report["created_at"].dt.date.astype(str)
                daily = report.groupby("date", as_index=False).agg(
                    Orders=("id", "count"), Sales_PKR=("total", "sum")
                ).sort_values("date", ascending=False)
                st.dataframe(daily.rename(columns={"date": "Date", "Orders": "Orders", "Sales_PKR": "Sales (PKR)"}),
                             use_container_width=True, hide_index=True)
                csv = report.to_csv(index=False).encode("utf-8")
                st.download_button("Download order report (CSV)", data=csv,
                                   file_name="groceryflow_orders.csv", mime="text/csv")
            else:
                st.info("Sales reports will appear after the first order.")


