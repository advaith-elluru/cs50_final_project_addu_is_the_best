from cs50 import SQL
from flask import Flask, redirect, request, render_template, session
from flask_session import Session
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta
from helpers import apology, credit, login_required

# COnfigure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSiON_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///math.db")


@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=120)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def apology(message, code):
    return render_template("apology.html", message = message, code = code)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return apology("Please provide username", 400)
        elif not password:
            return apology("Please provide password", 403)

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("Invalid username and/or password", 403)

        session["user_id"] = rows[0]["id"]

        return redirect("/")

    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if not username:
            return apology("Please provide username", 400)
        elif not password:
            return apology("Please provide password", 403)
        elif not confirmation:
            return apology("Please retype password", 403)
        elif password != confirmation:
            return apology("Please retype the same password as you typed in the previous field", 403)
        elif len(rows) != 0:
            return apology("Username already exists in database", 400)

        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, generate_password_hash(password))

        lines = db.execute("SELECT * FROM users WHERE username = ?", username)
        session["user_id"] = lines[0]["id"]

        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():

    if request.method == "POST":
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")
        rows = db.execute("SELECT * FROM users WHERE id = ?", session.get("user_id"))

        if not old_password:
            return apology("Please type your old password", 403)
        elif not check_password_hash(rows[0]["hash"], old_password):
            return apology("Please type correct old password", 403)
        elif not new_password:
            return apology("Please type a new password", 403)
        elif not confirmation:
            return apology("Please retype your new password")
        elif new_password != confirmation:
            return apology("Please retype the same password as you typed in the previous field")

        db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(new_password), session.get("user_id"))

        return redirect("/")

    else:
        return render_template("change_password.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/test", methods=["GET", "POST"])
@login_required
def test():
    if request.method == "POST":
        number = request.form.get("number")
        decision = request.form.get("decision")
        min = request.form.get("min")
        max = request.form.get("max")

        if not decision:
            return apology("Please select a choice", 407)
        elif decision not in ["+", "-", "x", "/"]:
            return apology("Please choose valid option", 407)
        elif not number:
            return apology("Please input a number of problems", 407)
        elif not min:
            return apology("Enter a minimum amount", 409)
        elif not max:
            return apology("Enter a maximum amount", 409)

        return render_template("test.html", numbers = int(number), max = int(max), min = int(min), decision = decision)
    else:
        return render_template("decide.html")

@app.route("/past_results", methods=["GET", "POST"])
@login_required
def past_results():
    hi = 0
    if request.method == "POST":
        choice = request.form.get("choice")
        if not choice:
            return apology("Please select an option", 405)
        if choice not in ["all_results", "best_percentage", "best_time"]:
            return apology("Invalid choice", 405)

        amount = request.form.get("amount")

        if choice == "all_results":
            rows = db.execute("SELECT * FROM results WHERE user_id = ?", session.get("user_id"))
        elif choice == "best_percentage":
            if not amount:
                return apology("Please enter amount", 407)
            elif amount > hi:
                return apology("You haven't taken that many tests yet", 407)
            rows = db.execute("SELECT * FROM results WHERE user_id = ? ORDER BY percent_correct DESC LIMIT ?", session.get("user_id"), hi)
        else:
            if not amount:
                return apology("Please enter amount", 407)
            elif amount > hi:
                return apology("You haven't taken that many tests yet", 407)
            rows = db.execute("SELECT * FROM results WHERE user_id = ? ORDER BY time LIMIT ?", session.get("user_id"), hi)

        return render_template("past_results.html", rows = rows)
    else:
        rows = db.execute("SELECT * FROM results WHERE user_id = ?", session.get("user_id"))
        if len(rows) < 1:
            return apology("You didn't take any tests", 404)
        hi = len(rows)
        return render_template("choose.html", rows = len(rows))


@app.route("/credit", methods=["GET", "POST"])
@login_required
def check_credit():
    if request.method == "POST":
        credit_num = request.form.get("credit")
        if not credit or credit.isdigit() == False:
            return apology("Please enter proper credit card number", 400)
        else:
            check = credit(credit_num)
            if check == "INVALID":
                return apology("This number is either incorrect or unaccepted", 400)
            else:
                db.execute("INSERT INTO Credit (id, credit_number) VALUES (?, ?)", session["user_id"], credit_num)
                return render_template("accepted_credit.html")
    else:
        return render_template("credit.html")
