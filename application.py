from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp

from helpers import *

# configure application
app = Flask(__name__)

app.jinja_env.globals.update(usd=usd)

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
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    
    if request.method == "POST":
        if not request.form.get("phonogram"):
            return render_template("index.html")
        
        translation = []
        translation2 = []
        translation3 = [""]
        string = ""
        hieroglyph = 0
        sequence = request.form.get("phonogram")
        sequence = sequence.replace(",", "")
        length = len(sequence)
        letter_ch = 0
        i = 0
        while i < length:
            hiero_row = db.execute("SELECT * FROM characters WHERE (letter LIKE :sq)", sq=sequence[i]+"%")
            if hiero_row:
                if hiero_row[0]["character"] == "0x1337F":
                    hieroglyph = int (hiero_row[0]["character"], 0)
                    translation.append(hieroglyph)
                    letter_ch += 1
                    i += 2
                else:
                    hieroglyph = int (hiero_row[0]["character"], 0)
                    translation.append(hieroglyph)
                    i += 1
            else:
                return apology("One of the characters isn't in the dictionary")
            hiero_row = None
        
        if letter_ch >= 1:
            for j in range(length - letter_ch):
                translation2.append(chr(translation[j]))
        else:
            for j in range(length):
                translation2.append(chr(translation[j]))
        
        translation2 = " ".join(translation2)
        translation3.append(translation2)
        translation = None
        translation2 = None
        db.execute("INSERT INTO history (id, phonogram) VALUES (:id, :phonogram)", id=session["user_id"], phonogram= request.form.get("phonogram"))
        
        return render_template("translation.html", hieroglyphs=translation3)
    else:
        return render_template("index.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    
     # selection of name, symbol, shares and cash of user stocks
    hist = db.execute("SELECT * FROM history WHERE id=:id", id = session["user_id"])
    return render_template("history.html", hist=hist)

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