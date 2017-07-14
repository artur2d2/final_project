from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import gettempdir
from datetime import datetime

from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")

## Routes go here
# A route should be of the form

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    
    if request.method == "POST":
        if not request.form.get("phonogram"):
            return render_template("index.html")
        
        sequence = request.form.get("phonogram")
        sequence = sequence.replace(",", "")
        sequence = sequence.split(" ")
        hiero = db.execute("SELECT * FROM characters WHERE (letter LIKE :sq)", sq=sequence[0])
        hiero = chr(int (hiero[0]["character"], 0))
        return render_template("translation.html", hiero=hiero)
    else:
        return render_template("index.html")
    
# where "project/templates/index.html" is a file created automatically by Pagedraw.
# Within the respective Pagedraw document, you can do {{ name }} which will print 'Garfunkel'

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock."""
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method =="POST":
        
        # ensure stock_symbol and number of shares were submitted
        if not request.form.get("stock_symbol") and not request.form.get("shares"):
            return apology("must provide stock_symbol and number of shares")
        
        # ensure stock_symbol was submitted
        elif not request.form.get("stock_symbol"):
            return apology("must provide stock_symbol")
        
        # ensure number of shares was submitted    
        elif not request.form.get("shares"):
            return apology("must provide number of shares")
        
        # ensure number of shares is greater than cero
        elif int(request.form.get("shares")) < 1:
            return apology("must provide a positive number for number of shares")
            
        # assignment of stock_symbol to stock
        stock = lookup(request.form.get("stock_symbol"))
        
        # money result of buying shares
        money_buy = int(request.form.get("shares")) * stock["price"]
        
        # rendering of quoted page with name, price and symbol
        if stock:
            row = db.execute("SELECT cash FROM users WHERE id=:id", id = session["user_id"])
            if money_buy <= row[0]["cash"]:
                db.execute("INSERT INTO history (id, symbol, name, shares, price) VALUES (:id, :symbol, :name, :shares, :price)", id=session["user_id"], symbol= stock["symbol"], name=stock["name"], shares=request.form.get("shares"), price=stock["price"])
                db.execute("UPDATE users SET cash = :cash_row - :money_buy WHERE id=:id", cash_row= row[0]["cash"], money_buy= money_buy, id=session["user_id"])
                
                # redirect user to home page
                return redirect(url_for("index"))
            else:
                return apology("shares bought exceeds user's available cash")
        else:
            return apology("stock_symbol doesn't exist")    
    
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:    
        return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    
     # selection of name, symbol, shares and cash of user stocks
    stocks = db.execute("SELECT * FROM history WHERE id=:id", id = session["user_id"])
    return render_template("history.html", stocks=stocks)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # ensure stock_symbol was submitted
        if not request.form.get("stock_symbol"):
            return apology("must sumbmit a stock_symbol")
        
        # assignment of stock_symbol to quote
        quote = lookup(request.form.get("stock_symbol"))
        
        # rendering of quoted page with name, price and symbol
        if quote:
            return render_template("quoted.html", quote=quote)
        else:
            return apology("stock_symbol doesn't exist")
    
    # else if user reached route via GET (as clicking a link or via redirect)
    else:        
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    
    # forget any user_id
    session.clear()
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # ensure username and password were submited
        
        if not request.form.get("username") and not request.form.get("password"):
            return apology("must provide username and password")
            
        # ensure username was submitted
        elif not request.form.get("username"):
            return apology("must provide username")
        
        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")
        
        # ensure password and password_confirmation are equal
        elif request.form.get("password") != request.form.get("password_confirmation"):
            return apology("password and password_confirmation must be equal")
        
        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        
        # ensure username doesn't exist in the database
        if rows:
            return apology("username already exists")
            
        # password encryption
        hash = pwd_context.encrypt(request.form.get("password"))
        
        # registration of username and password
        db.execute("INSERT INTO users(username,hash) VALUES (:username, :hash)", username=request.form.get("username"), hash=hash)
        
        # selecting users data
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        
        # remember which user has logged in
        session["user_id"] = rows[0]["id"]
        
        # redirect user to home page
        return redirect(url_for("index"))
        
    # else if user reached route via GET (as by clicking a link or via redirect)    
    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock."""
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method =="POST":
        
        # ensure stock_symbol and number of shares were submitted
        if not request.form.get("stock_symbol") and not request.form.get("shares"):
            return apology("must provide stock_symbol and number of shares")
        
        # ensure stock_symbol was submitted
        elif not request.form.get("stock_symbol"):
            return apology("must provide stock_symbol")
        
        # ensure number of shares was submitted    
        elif not request.form.get("shares"):
            return apology("must provide number of shares")
        
        # ensure number of shares is greater than cero
        elif int(request.form.get("shares")) < 1:
            return apology("must provide a positive number for number of shares")
            
        # assignment of stock_symbol to stock
        stock = lookup(request.form.get("stock_symbol"))
        
        # money result of buying shares
        money_sell = int(request.form.get("shares")) * stock["price"]
        
        # negative value of shares sold
        neg_shares = - int(request.form.get("shares"))
        
        # rendering of quoted page with name, price and symbol
        if stock:
            row = db.execute("SELECT name, symbol, SUM(shares) AS shares FROM history WHERE id=:id AND symbol=:symbol GROUP BY name", id = session["user_id"], symbol=request.form.get("stock_symbol"))
            row2 = db.execute("SELECT cash FROM users WHERE id=:id", id = session["user_id"])
            if int(request.form.get("shares")) <= row[0]["shares"]:
                db.execute("INSERT INTO history (id, symbol, name, shares, price) VALUES (:id, :symbol, :name, :shares, :price)", id=session["user_id"], symbol= stock["symbol"], name=stock["name"], shares=neg_shares, price=stock["price"])
                db.execute("UPDATE users SET cash = :cash_row + :money_sell WHERE id=:id", cash_row= row2[0]["cash"], money_sell= money_sell, id=session["user_id"])
                
                # redirect user to home page
                return redirect(url_for("index"))
            else:
                return apology("shares sold exceeds user's available shares")
        else:
            return apology("stock_symbol doesn't exist")    
    
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:    
        return render_template("sell.html")
        
@app.route("/password_change", methods=["GET", "POST"])
@login_required
def password_change():
    """Change user's password"""
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method =="POST":
        
        # select user's old password
        row = db.execute("SELECT * FROM users WHERE id=:id", id=session["user_id"])
        
        if request.form.get("password") and request.form.get("new_password") and request.form.get("new_password_confirmation"):
            
            # ensure new_password and new_password_confirmation are equal
            if request.form.get("new_password") == request.form.get("new_password_confirmation"):
                
                # ensure password entered by user is equal to current password
                if not pwd_context.verify(request.form.get("password"), row[0]["hash"]):
                    return apology("password don't match user's actual password")
                
                else:
                    # password encryption
                    new = pwd_context.encrypt(request.form.get("new_password"))
                    
                    # update of user's password
                    db.execute("UPDATE users SET hash = :new WHERE id=:id", new=new, id=session["user_id"])
                    # redirect user to home page
                    return redirect(url_for("index"))
            else:
                return apology("new_password and new_password_confirmation must be equal")
        
        else:
            return apology("must provide password, new_password and new password confirmation")
            
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("password_change.html")