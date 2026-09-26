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


# --- TASKS ROUTES ---

@app.route("/tasks", methods=["GET", "POST"])
@login_required
def tasks():
    db = get_db()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        due_date = request.form.get("due_date") or None
        priority = request.form.get("priority", "Medium")

        if not title:
            flash("Task title is required.", "danger")
        else:
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO tasks (user_id, title, description, due_date, priority) VALUES (%s, %s, %s, %s, %s)",
                (current_user.id, title, description, due_date, priority)
            )
            db.commit()
            cursor.close()
            flash("Task added!", "success")

        db.close()
        return redirect(url_for("tasks"))

    # GET request: just show the tasks
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM tasks WHERE user_id = %s ORDER BY due_date ASC",
        (current_user.id,)
    )
    all_tasks = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("tasks.html", tasks=all_tasks)


@app.route("/tasks/<int:task_id>/complete", methods=["POST"])
@login_required
def complete_task(task_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tasks WHERE id = %s AND user_id = %s", (task_id, current_user.id))
    task = cursor.fetchone()

    if task:
        new_status = not task["completed"]
        update_cursor = db.cursor()
        update_cursor.execute("UPDATE tasks SET completed = %s WHERE id = %s", (new_status, task_id))
        db.commit()
        update_cursor.close()

    cursor.close()
    db.close()
    return redirect(url_for("tasks"))


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = %s AND user_id = %s", (task_id, current_user.id))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("tasks"))

# --- BUDGET ROUTES ---

@app.route("/budget", methods=["GET", "POST"])
@login_required
def budget():
    db = get_db()

    if request.method == "POST":
        form_type = request.form.get("form_type")

        if form_type == "set_allowance":
            amount = request.form.get("amount")
            week_start = request.form.get("week_start")
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO allowances (user_id, amount, week_start) VALUES (%s, %s, %s)",
                (current_user.id, amount, week_start)
            )
            db.commit()
            cursor.close()
            flash("Allowance set!", "success")

        elif form_type == "log_expense":
            description = request.form.get("description", "").strip()
            amount = request.form.get("amount")
            expense_date = request.form.get("expense_date")
            category = request.form.get("category", "Other")

            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "SELECT id FROM allowances WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
                (current_user.id,)
            )
            latest_allowance = cursor.fetchone()
            allowance_id = latest_allowance["id"] if latest_allowance else None
            cursor.close()

            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO expenses (user_id, allowance_id, description, amount, expense_date, category) VALUES (%s, %s, %s, %s, %s, %s)",
                (current_user.id, allowance_id, description, amount, expense_date, category)
            )
            db.commit()
            cursor.close()
            flash("Expense logged!", "success")

        db.close()
        return redirect(url_for("budget"))

    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM allowances WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
        (current_user.id,)
    )
    allowance = cursor.fetchone()

    expenses = []
    remaining = 0
    category_totals = {}
    if allowance:
        cursor.execute(
            "SELECT * FROM expenses WHERE allowance_id = %s ORDER BY expense_date DESC",
            (allowance["id"],)
        )
        expenses = cursor.fetchall()
        total_spent = sum(e["amount"] for e in expenses)
        remaining = allowance["amount"] - total_spent

        for e in expenses:
            cat = e.get("category") or "Other"
            category_totals[cat] = category_totals.get(cat, 0) + e["amount"]

    cursor.close()
    db.close()
    return render_template(
        "budget.html",
        allowance=allowance,
        expenses=expenses,
        remaining=remaining,
        category_totals=category_totals
    )

# --- SCHEDULE ROUTES ---

@app.route("/schedule", methods=["GET", "POST"])
@login_required
def schedule():
    db = get_db()

    if request.method == "POST":
        form_type = request.form.get("form_type")
        cursor = db.cursor()

        if form_type == "add_subject":
            name = request.form.get("name", "").strip()

            if not name:
                flash("Subject name is required.", "danger")
            else:
                cursor.execute(
                    "INSERT INTO subjects (user_id, name) VALUES (%s, %s)",
                    (current_user.id, name)
                )
                db.commit()
                flash("Subject added!", "success")

        elif form_type == "add_class":
            subject_id = request.form.get("subject_id")
            day = request.form.get("day")
            start_time = request.form.get("start_time")
            end_time = request.form.get("end_time")
            room = request.form.get("room", "").strip()

            if not subject_id or not day or not start_time or not end_time:
                flash("Subject, day, start time, and end time are all required.", "danger")
            else:
                cursor.execute(
                    "INSERT INTO class_schedules (user_id, subject_id, day, start_time, end_time, room) VALUES (%s, %s, %s, %s, %s, %s)",
                    (current_user.id, subject_id, day, start_time, end_time, room)
                )
                db.commit()
                flash("Class added!", "success")

        cursor.close()
        db.close()
        return redirect(url_for("schedule"))

    # GET: fetch subjects (for the dropdown) + full weekly schedule
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM subjects WHERE user_id = %s", (current_user.id,))
    subjects = cursor.fetchall()

    cursor.execute("""
        SELECT class_schedules.*, subjects.name AS subject_name
        FROM class_schedules
        JOIN subjects ON class_schedules.subject_id = subjects.id
        WHERE class_schedules.user_id = %s
        ORDER BY FIELD(day, 'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'), start_time
    """, (current_user.id,))
    classes = cursor.fetchall()

    cursor.close()
    db.close()
    return render_template("schedule.html", subjects=subjects, classes=classes)


@app.route("/schedule/<int:class_id>/delete", methods=["POST"])
@login_required
def delete_class(class_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM class_schedules WHERE id = %s AND user_id = %s", (class_id, current_user.id))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("schedule"))


# --- NOTES ROUTES ---

@app.route("/notes", methods=["GET", "POST"])
@login_required
def notes():
    db = get_db()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()

        if not title:
            flash("Note title is required.", "danger")
        else:
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO notes (user_id, title, content) VALUES (%s, %s, %s)",
                (current_user.id, title, content)
            )
            db.commit()
            cursor.close()
            flash("Note saved!", "success")

        db.close()
        return redirect(url_for("notes"))

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM notes WHERE user_id = %s ORDER BY updated_at DESC", (current_user.id,))
    all_notes = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("notes.html", notes=all_notes)


@app.route("/notes/<int:note_id>/edit", methods=["POST"])
@login_required
def edit_note(note_id):
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()

    db = get_db()

    if not title:
        flash("Note title is required.", "danger")
        db.close()
        return redirect(url_for("notes"))

    cursor = db.cursor()
    cursor.execute(
        "UPDATE notes SET title = %s, content = %s WHERE id = %s AND user_id = %s",
        (title, content, note_id, current_user.id)
    )
    db.commit()
    affected = cursor.rowcount
    cursor.close()
    db.close()

    if affected == 0:
        flash("Note not found or you don't have permission to edit it.", "danger")
    else:
        flash("Note updated!", "success")

    return redirect(url_for("notes"))


@app.route("/notes/<int:note_id>/delete", methods=["POST"])
@login_required
def delete_note(note_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM notes WHERE id = %s AND user_id = %s", (note_id, current_user.id))
    db.commit()
    affected = cursor.rowcount
    cursor.close()
    db.close()

    if affected == 0:
        flash("Note not found or you don't have permission to delete it.", "danger")
    else:
        flash("Note deleted.", "success")

    return redirect(url_for("notes"))

# --- FLASHCARD ROUTES ---

@app.route("/flashcards", methods=["GET", "POST"])
@login_required
def flashcards():
    db = get_db()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        subject = request.form.get("subject", "").strip()

        if not title:
            flash("Deck title is required.", "danger")
        else:
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO flashcard_decks (user_id, title, subject) VALUES (%s, %s, %s)",
                (current_user.id, title, subject)
            )
            db.commit()
            cursor.close()
            flash("Deck created!", "success")

        db.close()
        return redirect(url_for("flashcards"))

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM flashcard_decks WHERE user_id = %s", (current_user.id,))
    decks = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("flashcards.html", decks=decks)


@app.route("/flashcards/<int:deck_id>", methods=["GET", "POST"])
@login_required
def deck_detail(deck_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Always verify ownership first, before doing anything else
    cursor.execute("SELECT * FROM flashcard_decks WHERE id = %s AND user_id = %s", (deck_id, current_user.id))
    deck = cursor.fetchone()

    if not deck:
        cursor.close()
        db.close()
        flash("Deck not found or you don't have permission to view it.", "danger")
        return redirect(url_for("flashcards"))

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        answer = request.form.get("answer", "").strip()

        if not question or not answer:
            flash("Both a question and an answer are required.", "danger")
        else:
            insert_cursor = db.cursor()
            insert_cursor.execute(
                "INSERT INTO flashcards (deck_id, question, answer) VALUES (%s, %s, %s)",
                (deck_id, question, answer)
            )
            db.commit()
            insert_cursor.close()
            flash("Flashcard added!", "success")

        cursor.close()
        db.close()
        return redirect(url_for("deck_detail", deck_id=deck_id))

    # GET: deck already confirmed to exist and belong to this user
    cursor.execute("SELECT * FROM flashcards WHERE deck_id = %s", (deck_id,))
    cards = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("deck_detail.html", deck=deck, cards=cards)


@app.route("/flashcards/<int:deck_id>/delete", methods=["POST"])
@login_required
def delete_deck(deck_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Verify ownership BEFORE deleting anything
    cursor.execute("SELECT * FROM flashcard_decks WHERE id = %s AND user_id = %s", (deck_id, current_user.id))
    deck = cursor.fetchone()

    if not deck:
        cursor.close()
        db.close()
        flash("Deck not found or you don't have permission to delete it.", "danger")
        return redirect(url_for("flashcards"))

    delete_cursor = db.cursor()
    delete_cursor.execute("DELETE FROM flashcards WHERE deck_id = %s", (deck_id,))
    delete_cursor.execute("DELETE FROM flashcard_decks WHERE id = %s AND user_id = %s", (deck_id, current_user.id))
    db.commit()
    delete_cursor.close()
    cursor.close()
    db.close()

    flash("Deck deleted.", "success")
    return redirect(url_for("flashcards"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5001)