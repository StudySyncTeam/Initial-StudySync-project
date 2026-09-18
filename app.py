from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import mysql.connector
from config import DB_CONFIG
from email_validator import validate_email, EmailNotValidError

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key-for-local-dev")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

# User Class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    if user:
        return User(user["id"], user["username"], user["email"])
    return None

# --- GENERAL ROUTES ---

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

# --- AUTHENTICATION ROUTES ---

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # 1. Validate Form Inputs
        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return redirect(url_for("register"))

        # 2. Strict Real/Official Email Domain Validation
        try:
            # check_deliverability=True verifies real MX records exist on the domain
            valid = validate_email(email, check_deliverability=True)
            email = valid.normalized
        except EmailNotValidError as e:
            flash("Please enter a valid, active official email address.", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, hashed_password)
            )
            db.commit()
            flash("Account created! Please log in.", "success")
            return redirect(url_for("login"))
        except mysql.connector.Error:
            flash("An account with this username or email already exists.", "danger")
            return redirect(url_for("register"))
        finally:
            cursor.close()
            db.close()

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # Basic input check
        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template("login.html")

        # Validate format
        try:
            valid = validate_email(email, check_deliverability=False)
            email = valid.normalized
        except EmailNotValidError:
            flash("Invalid username/email or password.", "danger")
            return render_template("login.html")

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = cursor.fetchone()
        cursor.close()
        db.close()

        # Verify Hashed Password
        if user_data and check_password_hash(user_data["password_hash"], password):
            user_obj = User(user_data["id"], user_data["username"], user_data["email"])
            login_user(user_obj)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username/email or password.", "danger")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

# --- DASHBOARD ROUTE ---

@app.route("/dashboard")
@login_required
def dashboard():
    pending_tasks = 0
    remaining_budget = 0.0

    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT COUNT(*) AS pending_count FROM tasks WHERE user_id = %s AND completed = FALSE", (current_user.id,))
        task_row = cursor.fetchone()
        if task_row:
            pending_tasks = task_row["pending_count"]
    except mysql.connector.Error:
        pending_tasks = 0

    try:
        cursor.execute("SELECT * FROM allowances WHERE user_id = %s ORDER BY created_at DESC LIMIT 1", (current_user.id,))
        allowance = cursor.fetchone()
        if allowance:
            cursor.execute("SELECT SUM(amount) AS total_expenses FROM expenses WHERE user_id = %s AND allowance_id = %s", (current_user.id, allowance["id"]))
            expenses = cursor.fetchone()
            total_expenses = expenses["total_expenses"] or 0
            remaining_budget = allowance["amount"] - total_expenses
    except mysql.connector.Error:
        remaining_budget = 0.0

    cursor.close()
    db.close()
    
    return render_template("dashboard.html", pending_tasks=pending_tasks, remaining_budget=remaining_budget)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5001)