from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import os
import mysql.connector
from config import DB_CONFIG
from email_validator import validate_email, EmailNotValidError
 
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key-for-local-dev")
 
# --- MAIL CONFIG ---
# Set these as environment variables on Render (or a .env file locally).
# Example for Gmail: use an "App Password", not your normal password.
# Example for SendGrid/Mailgun: use their SMTP relay host + API key as password.
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "True") == "True"
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER", app.config["MAIL_USERNAME"])
 
mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)
 
# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
 
def get_db():
    return mysql.connector.connect(**DB_CONFIG)
 
# User Class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email, is_verified=True):
        self.id = id
        self.username = username
        self.email = email
        self.is_verified = is_verified
 
@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    if user:
        return User(user["id"], user["username"], user["email"], bool(user.get("is_verified", 1)))
    return None
 
# --- EMAIL VERIFICATION HELPERS ---
 
def send_confirmation_email(email):
    token = serializer.dumps(email, salt="email-confirm-salt")
    confirm_url = url_for("confirm_email", token=token, _external=True)
    msg = Message("Confirm your StudelO account", recipients=[email])
    msg.body = (
        f"Welcome to StudelO!\n\n"
        f"Please confirm your email by clicking the link below:\n{confirm_url}\n\n"
        f"This link expires in 1 hour. If you didn't sign up, you can ignore this email."
    )
    mail.send(msg)
 
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
        # Note: this only confirms the DOMAIN can receive mail (valid MX records).
        # It does NOT confirm this specific mailbox exists — that's what the
        # confirmation email below is for.
        try:
            valid = validate_email(email, check_deliverability=True)
            email = valid.normalized
        except EmailNotValidError:
            flash("Please enter a valid, active official email address.", "danger")
            return redirect(url_for("register"))
 
        hashed_password = generate_password_hash(password)
 
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, is_verified) VALUES (%s, %s, %s, %s)",
                (username, email, hashed_password, False)
            )
            db.commit()
        except mysql.connector.Error:
            flash("An account with this username or email already exists.", "danger")
            return redirect(url_for("register"))
        finally:
            cursor.close()
            db.close()
 
        # 3. Send confirmation email. If sending fails, don't leave the user stuck
        # with an unverifiable account -- tell them plainly.
        try:
            send_confirmation_email(email)
            flash("Account created! Check your email to confirm your address before logging in.", "success")
        except Exception:
            flash("Account created, but the confirmation email failed to send. Please contact support.", "warning")
 
        return redirect(url_for("login"))
 
    return render_template("register.html")
 
@app.route("/confirm/<token>")
def confirm_email(token):
    try:
        email = serializer.loads(token, salt="email-confirm-salt", max_age=3600)
    except SignatureExpired:
        flash("That confirmation link has expired. Please register again or request a new one.", "danger")
        return redirect(url_for("login"))
    except BadSignature:
        flash("That confirmation link is invalid.", "danger")
        return redirect(url_for("login"))
 
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
 
    if not user:
        cursor.close()
        db.close()
        flash("No account found for that link.", "danger")
        return redirect(url_for("login"))
 
    if user["is_verified"]:
        flash("Account already verified. Please log in.", "success")
    else:
        update_cursor = db.cursor()
        update_cursor.execute("UPDATE users SET is_verified = %s WHERE id = %s", (True, user["id"]))
        db.commit()
        update_cursor.close()
        flash("Email confirmed! You can now log in.", "success")
 
    cursor.close()
    db.close()
    return redirect(url_for("login"))
 
@app.route("/resend-confirmation", methods=["GET", "POST"])
def resend_confirmation():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
 
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()
 
        # Always show the same message whether or not the email exists,
        # so this endpoint can't be used to check which emails are registered.
        if user and not user["is_verified"]:
            try:
                send_confirmation_email(email)
            except Exception:
                pass
 
        flash("If that account exists and isn't verified yet, a new confirmation email has been sent.", "info")
        return redirect(url_for("login"))
 
    return render_template("resend_confirmation.html")
 
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
            if not user_data.get("is_verified", False):
                flash("Please confirm your email before logging in. Check your inbox, or resend the link.", "warning")
                return render_template("login.html")
 
            user_obj = User(user_data["id"], user_data["username"], user_data["email"], True)
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