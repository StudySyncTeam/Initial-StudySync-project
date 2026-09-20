import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import mysql.connector
from config import DB_CONFIG
from email_validator import validate_email, EmailNotValidError

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key-for-local-dev")

# Token Serializer for Email Verification Links
serializer = URLSafeTimedSerializer(app.secret_key)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"

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
    try:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user:
            return User(
                user["id"], 
                user["username"], 
                user["email"], 
                bool(user.get("is_verified", False))
            )
        return None
    finally:
        cursor.close()
        db.close()

# --- EMAIL VERIFICATION HELPERS (BREVO API) ---

def send_confirmation_email(user_email):
    token = serializer.dumps(user_email, salt="email-confirm-salt")
    confirm_url = url_for("confirm_email", token=token, _external=True)

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = os.environ.get('BREVO_API_KEY')

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": user_email}],
        sender={"name": "StudySync Support", "email": os.environ.get('BREVO_FROM_EMAIL')},
        subject="StudySync - Verify Your Email Address",
        html_content=f'''
            <h2>Welcome to StudySync!</h2>
            <p>Please click the link below to verify your account:</p>
            <p><a href="{confirm_url}">{confirm_url}</a></p>
            <p>This link expires in 1 hour. If you didn't sign up, you can ignore this email.</p>
        '''
    )

    api_instance.send_transac_email(send_smtp_email)
    return True

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
            return render_template("login.html", form_type="register")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("login.html", form_type="register")

        # 2. Email Validation
        try:
            valid = validate_email(email, check_deliverability=True)
            email = valid.normalized
        except EmailNotValidError:
            flash("Please enter a valid, active email address.", "danger")
            return render_template("login.html", form_type="register")

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
            return render_template("login.html", form_type="register")
        finally:
            cursor.close()
            db.close()

        # 3. Send confirmation email
        try:
            send_confirmation_email(email)
            flash("Account created! Check your email to confirm your address before logging in.", "success")
        except (ApiException, Exception) as e:
            print(f"Brevo API Error during registration: {e}")
            flash("Account created, but confirmation email failed to send. Please use the resend page or contact support.", "warning")

        return redirect(url_for("login"))

    return render_template("login.html", form_type="register")

@app.route("/confirm/<token>")
def confirm_email(token):
    try:
        email = serializer.loads(token, salt="email-confirm-salt", max_age=3600)
    except SignatureExpired:
        flash("That confirmation link has expired. Please request a new one.", "danger")
        return redirect(url_for("login"))
    except BadSignature:
        flash("That confirmation link is invalid.", "danger")
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
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
    finally:
        cursor.close()
        db.close()

    return redirect(url_for("login"))

@app.route("/resend-confirmation", methods=["GET", "POST"])
def resend_confirmation():
    if request.method == "POST":
        email = request.form.get("email", "").strip()

        db = get_db()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
        finally:
            cursor.close()
            db.close()

        if user and not user["is_verified"]:
            try:
                send_confirmation_email(email)
            except Exception as e:
                print(f"Failed to resend email: {e}")

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

        # 1. Reject empty inputs immediately
        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template("login.html", form_type="login")

        # 2. Look up user by email or username
        db = get_db()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE email = %s OR username = %s", (email, email))
            user_data = cursor.fetchone()
        finally:
            cursor.close()
            db.close()

        # 3. Verify user existence & password matching
        if not user_data or not check_password_hash(user_data["password_hash"], password):
            flash("Invalid credentials. Incorrect email, username, or password.", "danger")
            return render_template("login.html", form_type="login")

        # 4. Check verification status
        if not user_data.get("is_verified", False):
            flash("Please confirm your email before logging in. Check your inbox or resend the link.", "warning")
            return render_template("login.html", form_type="login")

        # 5. Success: log in user and send to dashboard
        user_obj = User(user_data["id"], user_data["username"], user_data["email"], True)
        login_user(user_obj)
        return redirect(url_for("dashboard"))

    return render_template("login.html", form_type="login")

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
    finally:
        cursor.close()
        db.close()

    return render_template("dashboard.html", pending_tasks=pending_tasks, remaining_budget=remaining_budget)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5001)