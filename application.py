import os
from functools import wraps
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import requests
from tempfile import mkdtemp
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure CS50 Library to use SQLite database
db = SQL(os.getenv("DATABASE_URL"))

# Login required decorator
def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Get the username for template
@app.context_processor
def get_username():
    a = session.get("user_id")
    name = db.execute("SELECT name FROM users WHERE id=?", a)
    if len(name) == 1:
        name = name[0]["name"]
        return dict(name=name)
    else:
        return dict(name='')


# Connect with bank api

def get_rate(currency, date):

    try:
        url = f"https://bank.gov.ua/NBUStatService/v1/statdirectory/exchangenew?valcode={currency}&date={date}&json"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None
    # Parse response
    try:
        rate = response.json()
        return float(rate[0]["rate"])
    except (KeyError, TypeError, ValueError):
        return None
#main page
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    #GET just renders the template
    if request.method == "GET":
        return render_template ("index.html")
    else:
        #if all data prest do
        if request.form.get("sum") and request.form.get("currency") and request.form.get("date"):
            sum = request.form.get("sum")
            currency = request.form.get("currency")
            date = datetime.strptime(request.form.get("date"), "%Y-%m-%d")

            if currency == 'UAH':
                rate = 1
            else:
                #get rate by connecting to the bank api
                rate = get_rate(currency, datetime.strftime(date, "%Y%m%d"))
            uah = round(float(sum)*rate, 2)
            db.execute("INSERT INTO transactions (user_id, sum, currency, rate, uah, date) VALUES (?, ?, ?, ?, ?, ?)", session.get("user_id"), sum, currency, rate, uah, date.strftime("%Y-%m-%d"))
            flash("The transaction is successfully submited")
            return redirect("/transactions")

        else:
            #if some required data aren't present
            flash('Please fill up the form')
            return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted

        # Ensure username was submitted
        if not request.form.get("name"):
            flash('Must provide a username')
            return render_template("login.html"), 400

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash('Must provide a password')
            return render_template("login.html"), 400

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE name = ?", request.form.get("name"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            flash('Invalid username and/or password')
            return render_template("login.html"), 400

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        name = request.form.get("name")
        row = len(db.execute("SELECT * FROM users WHERE name=?", name))
        #Check if the username is in db
        if not name or row == 1:
            flash('Username is not unique')
            return render_template("register.html")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        #check if the password mathes confirmation
        if not password or not confirmation or password != confirmation:
            flash('Passwords do not match')
            return render_template("register.html"), 400
        #hash password
        password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        #insert new user to the table
        db.execute("INSERT INTO users (name, password) VALUES (?, ?)", name, password)
        return redirect("/")

#allows user to logout from the session
@app.route("/logout")
def logout():
    return redirect("/login")


@app.route("/transactions", methods=["POST", "GET"])
@login_required
def transactions():
    #render table from transactions
    if request.method == "GET":
        transactions = db.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY date DESC", session.get("user_id"))
        return render_template("transactions.html", transactions=transactions)
    else:
        #delete the row from the table
        id = request.form.get("id")
        db.execute("DELETE FROM transactions WHERE id=?", id)
        return redirect("/transactions")

@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "GET":
        return render_template("chp.html")
    else:
        #old password
        op = request.form.get("opass")
        #new password
        np = request.form.get("npass")
        #confirm
        cp = request.form.get("cpass")
        #current password
        cup = db.execute("SELECT password FROM users WHERE id=?", session.get("user_id"))
        cup = cup[0]["password"]
        #check if entered old password mathes the current password
        if not check_password_hash(cup, op):
            flash("Wrong current password")
            return redirect("/changepassword")
        else:

            if np == cp:
                #hash new password
                np = generate_password_hash(np, method='pbkdf2:sha256', salt_length=8)
                #update table
                db.execute("UPDATE users SET password=? WHERE id=?", np, session.get("user_id"))
                flash("Password successfully updated")
                return redirect("/changepassword")
            else:
                flash('Passwords do not match')
                return redirect("/changepassword")
@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    if request.method == "GET":
        return render_template("report.html")
    else:
        start = request.form.get("start")
        finish = request.form.get("finish")
        id = session.get("user_id")
        #selec the transactions sum
        uah = db.execute("SELECT SUM(uah) as sum FROM transactions WHERE user_id = ? AND date BETWEEN ? AND ?", id, start, finish)
        #check if there are transactions
        if len(uah) > 0 and uah[0]["SUM"] != None:
            #count the sum
            uah = round(float(uah[0]["SUM"]), 2)
            #count tax
            tax = round(uah*0.05)
            #formate string to data object
            start = datetime.strptime(request.form.get("start"), "%Y-%m-%d")
            finish = datetime.strptime(request.form.get("finish"), "%Y-%m-%d")
            #list of dates
            dates = []
            #get the list of dates(1 month one date)
            while start <= finish:
                #append start date to the list
                dates.append(start)
                #add one month the start date
                start += relativedelta(months=1, day=1)
            #convert dates in the list to string
            dates = [x.strftime("%Y-%m-%d") for x in dates]
            uscarray = []
            #get a list of dict with usc values for dates
            for x in dates:
                value = db.execute("SELECT value FROM USC WHERE ? BETWEEN start_date AND finish_date", x)
                uscarray.append(value[0])
            usc = 0
            #Sum all the values of usc
            for i in uscarray:
                usc += i['value']
            #count net income
            net = round(uah - tax - usc, 2)
            start = request.form.get("start")
            finish=request.form.get("finish")
            a = f"The report for date period {start} - {finish} is generated"
            flash(a)
            return render_template("report.html", uah=uah, tax=tax, usc=usc, net=net)
        else:
            flash("There is no records for this period")
            return redirect("/report")

@app.route("/ref")
@login_required
def ref():
    return render_template ("ref.html")

if __name__ == '__main__':
    app.run(threaded=True, port=5000)