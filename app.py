#from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import *
import cryptocompare
from helpers import lookup_crypto, login_required, is_valid_crypto,is_valid_stock, lookup_stock
from pyrebase import pyrebase



config = {
    #not to be included in the github repo
  }


firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()
# configure application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'super secret'
# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
# app.config["SESSION_FILE_DIR"] = mkdtemp()
# app.config["SESSION_PERMANENT"] = False
# app.config["SESSION_TYPE"] = "redis"
# app.config["SECRET_KEY"] = "super secret key"
# app.secret_key = 'BAD_SECRET_KEY'

# Session(app)


# configure CS50 Library to use SQLite database
# db = SQL("sqlite:///finance1.db")


@app.route("/register", methods=["GET", "POST"])
def register():

    # forget any user_id
    # session.clear()
    session.pop('user_id', default=None)

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        firstname = request.form.get("fname")
        lastname = request.form.get("lname")
        username = request.form.get("username")
        password = request.form.get("password")
        password2 = request.form.get("password2")

        if password != password2:
            flash("Passwords do not match", "error")
            return render_template("register.html")

        hash = generate_password_hash(password)
        try:
            user = auth.create_user_with_email_and_password(username, password)
            unique_id = auth.get_account_info(user['idToken'])
            unique_id = (unique_id['users'][0]['localId'])
            new_user = {"username": (
                firstname+" "+lastname), "cash": 100,"cash_stocks": 100000, "email": username}
            db.child("users").child(unique_id).set(new_user)
            # new_folio_entry = {"shares": 1,"price": 1 , "last transacted" :datetime.timestamp(datetime.now()) }
            # db.child("portfolio").child(unique_id).child('POWERINDIA').set(new_folio_entry)
            # new_history_entry = {"symbol":'POWERINDIA' , "shares":1, "price" : 1, "Date Transacted" : datetime.timestamp(datetime.now())}
            # db.child("history").child(unique_id).child(int(datetime.timestamp(datetime.now()))).set(new_history_entry)

            # db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", username=username, hash=hash)
        except:
            flash("Username Already Exists", "error")
            return render_template("register.html")
        flash("New user registered", "success")
        return render_template("login.html")

    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    # forget any user_id
    # session.clear()
    session.pop('user_id', default=None)

    if request.method == "POST":
        # query database for username

        # rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        # try:
        user = auth.sign_in_with_email_and_password(
            request.form.get("username"), request.form.get("password"))

            # remember which user has logged in
        unique_id = auth.get_account_info(user['idToken'])
        unique_id = (unique_id['users'][0]['localId'])
        session["user_id"] = unique_id

            # redirect user to home page
        flash("success", "welcome")
        return redirect(url_for("index_crypto"))

        # except:
        #     flash("Invalid Username/Password", "error")
        #     return redirect(url_for("login"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/wallet_crypto", methods=['GET', 'POST'])
@login_required
def wallet_crypto():
    cash = db.child("users").child(
        session['user_id']).child("cash").get().val()
    user = db.child("users").child(
        session['user_id']).child("username").get().val()
    # user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    # cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    if request.method == 'POST':
        amount = request.form.get("amount")
        if float(amount) <= 0:
            flash("Invalid Amount", "error")
            return redirect(url_for("wallet_crypto"))
        else:
            if(float(amount) < 0):
                db.child("users").child(session['user_id']).update(
                    {"cash": float(cash)+float(amount)})
            #db.execute("UPDATE users SET cash=cash+ :amount WHERE id=:x",amount=amount,x=session["user_id"])
                cash = db.child("users").child(
                    session['user_id']).child("cash").get().val()
            #cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
                flash("amount added", "success")
                return render_template("crypto-wallet.html", cash=cash, user=user)
            else:
                flash("Not Allowed by admin, Speak to coordinators", "error")
                return render_template("crypto-wallet.html", cash=cash, user=user)

    else:
        return render_template("crypto-wallet.html", cash=cash, user=user)


@app.route("/changepass", methods=["GET", "POST"])
@login_required
def changepass():
    cash = db.child("users").child(
        session['user_id']).child("cash").get().val()
    user = db.child("users").child(
        session['user_id']).child("username").get().val()
    #user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    #cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    email = db.child("users").child(
        session['user_id']).child("email").get().val()
    try:
        auth.send_password_reset_email(str(email))
        flash("Password Change Email Successfully Sent", "success")
        return redirect(url_for("index_crypto"))
    except:
        flash("The email you provided while signup is not valid", "error")
        return redirect(url_for("changepass"))

    # if request.method == "POST":

    #     oldpasscheck = db.execute("SELECT hash FROM users WHERE id = :id", id= session['user_id'])

    #     if not check_password_hash(oldpasscheck[0]["hash"] ,request.form.get("oldpass")):
    #

    #     if request.form.get("newpass")!=request.form.get("newpass2"):
    #         flash("New password do not match", "error")
    #         return redirect(url_for("changepass"))

    #     hashed = generate_password_hash(request.form.get("newpass"))

    #     db.execute("UPDATE 'users' SET hash=:hash WHERE id=:id", hash=hashed, id= session['user_id'])
    # flash("Password Successfully Changed", "success")

    # return redirect(url_for("index"))

    # else:
    #     return render_template("changepass.html", user=user[0]["username"], cash=cash[0]["cash"])


@app.route("/")
@login_required
def index_crypto():
    cash = db.child("users").child(
        session['user_id']).child("cash").get().val()
    user = db.child("users").child(
        session['user_id']).child("username").get().val()
    # cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    # user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    return render_template("crypto-index.html", cash=cash, user=user)
    # return render_template("index.html", cash=cash[0]["cash"], user=user[0]["username"])


@app.route("/quote_crypto", methods=["GET", "POST"])
@login_required
def quote_crypto():
    cash = db.child("users").child(
        session['user_id']).child("cash").get().val()
    user = db.child("users").child(
        session['user_id']).child("username").get().val()
    # user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    # cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    if request.method == "POST":
        result = is_valid_crypto(request.form.get("symbol"))
        if result is None:
            flash("invalid stock or Trade Ban on this Script", "error")
            return render_template("crypto-quote.html", cash=cash, user=user)
        else:
            return render_template("crypto-quoted.html", symbol=result["symbol"], user=user, cash=cash)
    else:
        return render_template("crypto-quote.html", cash=cash, user=user)
      # return render_template("quote.html", user=user[0]["username"], cash=cash[0]["cash"])

# this will be configured once we build portfolio


@app.route("/trade_crypto")
@login_required
def trade_crypto():
    cash = db.child("users").child(
        session['user_id']).child("cash").get().val()
    user = db.child("users").child(
        session['user_id']).child("username").get().val()
    symbol = list()
    share = list()
    price = list()
    total = list()

    sy = db.child("crypto").child("portfolio").child(session['user_id']).shallow().get().val()
    if(sy != None):
        sy = (list(sy))

        if len(sy) != 0:
            for i in range(len(sy)):

                share.append(db.child("crypto").child("portfolio").child(
                    session['user_id']).child(sy[i]).child("shares").get().val())
                price.append(db.child("crypto").child("portfolio").child(
                    session['user_id']).child(sy[i]).child("price").get().val())
                symbol.append(sy[i])
                total.append(float(db.child("crypto").child("portfolio").child(session['user_id']).child(sy[i]).child("shares").get(
                ).val()) * float(db.child("crypto").child("portfolio").child(session['user_id']).child(sy[i]).child("price").get().val()))
    # sy = db.execute("SELECT symbol FROM portfolio WHERE id = :id", id= session['user_id'])
    # sh = db.execute("SELECT shares FROM portfolio WHERE id = :id", id= session['user_id'])
    # pr = db.execute("SELECT price FROM portfolio WHERE id = :id", id= session['user_id'])
    # for i in range (len(sy)):
    #     symbol.append(sy[i]["symbol"].upper())
    # for i in range (len(sh)):
    #     share.append(sh[i]["shares"])
    # for i in range (len(pr)):
    #     price.append(pr[i]["price"])
    # for i in range(len(symbol)):
    #     total.append(price[i]*share[i])
    # cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    # user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
        data = zip(symbol, share, price, total)
        return render_template("crypto-trade.html", data=data, cash=cash, user=user)
    else:
        data = zip([], [], [], [])
        return render_template("crypto-trade.html", data=data, cash=cash, user=user)


@app.route("/buy_crypto", methods=["GET", "POST"])
@login_required
def buy_crypto():
    cash = db.child("users").child(
        session['user_id']).child("cash").get().val()
    user = db.child("users").child(
        session['user_id']).child("username").get().val()
    user_folio = db.child("crypto").child("portfolio").child(
        session['user_id']).shallow().get().val()
    # user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    # cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    if request.method == "POST":
        symbol = request.form.get("symbol")
        stock = lookup_crypto(request.form.get("symbol"))
        price = stock["price"]
        amount = request.form.get("shares")
        if amount is None:
            return render_template("crypto-buy.html", symbol=symbol, user=user, cash=cash, name=stock["name"], price=stock["price"])
        else:
            if  (float(amount)) <= 0:
                flash("Invalid Shares!", "error")
                return redirect(url_for("quote_crypto"))

        if float(cash) > float(amount)*stock["price"]:

            if(user_folio == None or symbol not in user_folio):
                new_folio_entry = {"shares": amount, "price": price,
                                   "last transacted": datetime.timestamp(datetime.now())}
                db.child("crypto").child("portfolio").child(session['user_id']).child(
                    symbol).set(new_folio_entry)

                # db.execute("INSERT INTO portfolio (id, symbol, shares, price) VALUES(:id, :symbol, :shares, :price)", id= session['user_id'], symbol=symbol, shares=amount, price=stock["price"])
            else:
                already_held = db.child("crypto").child("portfolio").child(
                    session['user_id']).child(symbol).child("shares").get().val()
                last_price = db.child("crypto").child("portfolio").child(
                    session['user_id']).child(symbol).child("price").get().val()
                db.child("crypto").child("portfolio").child(session['user_id']).child(symbol).update({"price": (
                    ((float(last_price)*float(already_held)) + (float(price)*float(amount))) / (float(amount)+float(already_held)))})
                db.child("crypto").child("portfolio").child(session['user_id']).child(
                    symbol).update({"shares": float(amount)+float(already_held)})
                db.child("crypto").child("portfolio").child(session['user_id']).child(symbol).update(
                    {"last transacted": datetime.timestamp(datetime.now())})
                # temp = db.execute("SELECT shares FROM portfolio WHERE id=:id AND symbol=:symbol", id= session['user_id'], symbol=request.form.get("symbol"))
                # db.execute("UPDATE 'portfolio' SET shares=:shares WHERE id=:id AND symbol=:symbol", shares=temp[0]["shares"]+int(request.form.get("shares")), id=session['user_id'], symbol=request.form.get("symbol"))

            transacted = datetime.timestamp(datetime.now())

            new_history_entry = {"symbol": symbol, "shares": amount,
                                 "price": price, "Date Transacted": transacted}
            db.child("crypto").child("history").child(session['user_id']).child(
                int(transacted)).set(new_history_entry)
            # db.execute("INSERT INTO history (id, symbol, shares, price, transacted) VALUES(:id, :symbol, :shares, :price, :transacted)", id= session['user_id'], symbol=request.form.get("symbol"), shares=request.form.get("shares"), price=stock["price"], transacted = transacted)

            db.child("users").child(session['user_id']).update(
                {"cash": float(cash)-(float(price)*float(amount))})
            # db.execute("UPDATE 'users' SET cash=:cash WHERE id=:id", cash=(cash[0]["cash"])-(float(amount)*stock["price"]), id= session['user_id'])

        else:
            flash("Not Enough Balance", "error")
            return redirect(url_for("portfolio_crypto"))
        flash("Shares Bought", "success")
        return redirect(url_for("portfolio_crypto"))

    else:
        return render_template("crypto-buy.html", user=user, cash=cash)


@app.route("/sell_crypto", methods=["GET", "POST"])
@login_required
def sell_crypto():

    cash = db.child("users").child(
        session['user_id']).child("cash").get().val()
    user = db.child("users").child(
        session['user_id']).child("username").get().val()
    user_folio = db.child("crypto").child("portfolio").child(
        session['user_id']).shallow().get().val()
    # user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    # cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    if request.method == "POST":
        symbol = request.form.get("symbol")
        amount = request.form.get("shares")
        already_held = db.child("crypto").child("portfolio").child(
            session['user_id']).child(symbol).child("shares").get().val()
        last_price = db.child("crypto").child("portfolio").child(
            session['user_id']).child(symbol).child("price").get().val()
        stock = lookup_crypto(request.form.get("symbol"))
        if amount is None:
            return render_template("crypto-sell.html", user=user, cash=cash, symbol=symbol, name=stock["name"], price=stock["price"])
        price = stock["price"]
        #sy = db.execute("SELECT shares FROM portfolio WHERE id = :id AND symbol=:symbol", id= session['user_id'], symbol=request.form.get("symbol"))
        if symbol not in user_folio:
            flash("You dont own this Stock", "error")
            return redirect(url_for("trade_crypto"))
        if ((float(amount)) <= 0 or float(amount) > float(already_held)):
            flash("Invalid Shares", "error")
            return redirect(url_for("trade_crypto"))
        if (float(already_held) == float(amount)):
            db.child("crypto").child("portfolio").child(
                session['user_id']).child(symbol).remove()
            #db.execute("DELETE from 'portfolio' WHERE id = :id AND symbol=:symbol",id= session['user_id'], symbol=request.form.get("symbol") )
        else:

            db.child("crypto").child("portfolio").child(session['user_id']).child(symbol).update({"price": (
                ((float(last_price)*float(already_held)) - (float(price)*float(amount))) / (float(already_held)-float(amount)))})
            db.child("crypto").child("portfolio").child(session['user_id']).child(
                symbol).update({"shares": float(already_held)-float(amount)})
            db.child("crypto").child("portfolio").child(session['user_id']).child(symbol).update(
                {"last transacted": datetime.timestamp(datetime.now())})
            # db.execute("UPDATE 'portfolio' SET shares=:shares WHERE id=:id AND symbol=:symbol", shares=sy[0]["shares"]-int(request.form.get("shares")), id=session['user_id'], symbol=request.form.get("symbol"))

        transacted = datetime.timestamp(datetime.now())
        new_history_entry = {"symbol": symbol, "shares": -1 *
                             float(amount), "price": price, "Date Transacted": transacted}
        db.child("crypto").child("history").child(session['user_id']).child(
            int(transacted)).set(new_history_entry)

        # transacted = datetime.timestamp(datetime.now())
        # db.execute("INSERT INTO history (id, symbol, shares, price, transacted) VALUES(:id, :symbol, :shares, :price, :transacted)", id= session['user_id'], symbol=request.form.get("symbol"), shares=-int(request.form.get("shares")), price=stock["price"], transacted = transacted)
        profit = stock["price"]*float(amount)
        db.child("users").child(session['user_id']).update(
            {"cash": float(cash)+float(profit)})
        # temp = db.execute("SELECT cash FROM users WHERE id=:id",id= session['user_id'])
        # db.execute("UPDATE 'users' SET cash=:cash WHERE id=:id", cash=temp[0]["cash"]+profit, id= session['user_id'])
        flash("Shares Sold", "success")
        return redirect(url_for("portfolio_crypto"))

    else:
        return render_template("crypto-sell.html", user=user, cash=cash)


@app.route("/update_quote_crypto", methods=["GET", "POST"])
@login_required
def update_quote_crypto():
    symbol = request.args.get('symbol')
    temp = lookup_crypto(symbol)
    price = temp["price"]
    return jsonify(price)


@app.route("/history_crypto")
@login_required
def history_crypto():
    cash = db.child("users").child(
        session['user_id']).child("cash").get().val()
    user = db.child("users").child(
        session['user_id']).child("username").get().val()
    # user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    # cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    symbol = list()
    share = list()
    price = list()
    transacted = list()
    total = []

    sy = db.child("crypto").child("history").child(session['user_id']).shallow().get().val()
    if(sy != None):
        sy = (list(sy))

        if len(sy) != 0:
            for i in range(len(sy)):

                transacted.append(str(datetime.fromtimestamp(int(sy[i]))))
                share.append(db.child("crypto").child("history").child(
                    session['user_id']).child(sy[i]).child("shares").get().val())
                price.append(db.child("crypto").child("history").child(
                    session['user_id']).child(sy[i]).child("price").get().val())
                symbol.append(db.child("crypto").child("history").child(
                    session['user_id']).child(sy[i]).child("symbol").get().val())
    # sy = db.execute("SELECT symbol FROM history WHERE id = :id", id= session['user_id'])
    # sh = db.execute("SELECT shares FROM history WHERE id = :id", id= session['user_id'])
    # pr = db.execute("SELECT price FROM history WHERE id = :id", id= session['user_id'])
    # tr = db.execute("SELECT transacted FROM history WHERE id = :id", id= session['user_id'])
    # for i in range (len(sy)):
    #     symbol.append(sy[i]["symbol"].upper())
    # for i in range (len(sh)):
    #     share.append(sh[i]["shares"])
    # for i in range (len(pr)):
    #     price.append(pr[i]["price"])
    # for i in range (len(tr)):
    #     transacted.append(tr[i]["transacted"])
        data = zip(symbol, share, price, transacted)
        return render_template("crypto-history.html", data=data, user=user, cash=cash)
    else:
        return render_template("crypto-history.html", user=user, cash=cash)


@app.route("/portfolio_crypto")
@login_required
def portfolio_crypto():
    cash = db.child("users").child(
        session['user_id']).child("cash").get().val()
    user = db.child("users").child(
        session['user_id']).child("username").get().val()
    # user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    symbol = list()
    share = list()
    price = list()
    latest = list()
    invested = list()
    day_gl = list()
    # cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    sy = db.child("crypto").child("portfolio").child(session['user_id']).shallow().get().val()
    if(sy != None):
        sy = (list(sy))
    # sy = db.execute("SELECT symbol FROM portfolio WHERE id = :id", id= session['user_id'])
    # sh = db.execute("SELECT shares FROM portfolio WHERE id = :id", id= session['user_id'])
    # pr = db.execute("SELECT price FROM portfolio WHERE id = :id", id= session['user_id'])
        if len(sy) != 0:
            for i in range(len(sy)):
                # symbol.append(sy[i]["symbol"].upper())
                # prc=lookup(sy[i]["symbol"])
                # latest.append(prc["price"])
                # share.append(sh[i]["shares"])
                # price.append(pr[i]["price"])

                prc = lookup_crypto(sy[i])
                latest.append(prc["price"])
                share.append(db.child("crypto").child("portfolio").child(
                    session['user_id']).child(sy[i]).child("shares").get().val())
                price.append(db.child("crypto").child("portfolio").child(
                    session['user_id']).child(sy[i]).child("price").get().val())
                symbol.append(sy[i])
                invested.append(float(db.child("crypto").child("portfolio").child(session['user_id']).child(sy[i]).child("shares").get(
                ).val()) * float(db.child("crypto").child("portfolio").child(session['user_id']).child(sy[i]).child("price").get().val()))
                day_gl.append((float(prc["price"])-float(db.child("crypto").child("portfolio").child(session['user_id']).child(sy[i]).child(
                    "price").get().val()))*float(db.child("crypto").child("portfolio").child(session['user_id']).child(sy[i]).child("shares").get().val()))
            data = zip(symbol, share, price, latest, invested, day_gl)
            inv_amt = list()
            gl = list()
            for i in range(len(sy)):
                gl.append((float(latest[i])-float(price[i]))*float(share[i]))
                inv_amt.append(float(price[i])*float(share[i]))
            lat_value = sum(inv_amt)+sum(gl)
            top_gain_index = gl.index(max(gl))
            top_loss_index = gl.index(min(gl))
            top_gain_symbol = symbol[top_gain_index]
            top_loss_symbol = symbol[top_loss_index]
            overall_gl = sum(gl)
            return render_template("crypto-portfolio.html", data=data, lat_value=lat_value, top_gain=top_gain_symbol, top_loss=top_loss_symbol, overall_gl=overall_gl, cash=cash, user=user)
        else:
            return render_template("crypto-portfolio.html", lat_value=0, top_gain='-', top_loss='-', overall_gl=0, cash=cash, user=user)

    else:
        return render_template("crypto-portfolio.html", lat_value=0, top_gain='-', top_loss='-', overall_gl=0, cash=cash, user=user)


@app.route("/update_portfolio_crypto", methods=['GET', 'POST'])
@login_required
def update_portfolio_crypto():
    latest = list()
    share = list()
    price = list()

    sy = db.child("crypto").child("portfolio").child(session['user_id']).shallow().get().val()
    if(sy != None):
        sy = (list(sy))
    # sy = db.execute("SELECT symbol FROM portfolio WHERE id = :id", id= session['user_id'])
    # sh = db.execute("SELECT shares FROM portfolio WHERE id = :id", id= session['user_id'])
    # pr = db.execute("SELECT price FROM portfolio WHERE id = :id", id= session['user_id'])
        if len(sy) != 0:
            for i in range(len(sy)):
                prc = lookup_crypto(sy[i])
                latest.append(prc["price"])
                share.append(db.child("crypto").child("portfolio").child(
                    session['user_id']).child(sy[i]).child("shares").get().val())
                price.append(db.child("crypto").child("portfolio").child(
                    session['user_id']).child(sy[i]).child("price").get().val())
            inv_amt = list()
            gl = list()
            for i in range(len(sy)):
                glst = (float(latest[i])-float(price[i]))*float(share[i])
                gl.append(float("%.2f" % glst))
                inv_amt.append(float(price[i])*float(share[i]))
            tot_inv = float("%.2f" % sum(inv_amt))
            overall_gl = float("%.2f" % sum(gl))
            lat_value = tot_inv + overall_gl
            lat_value_final = float("%.2f" % lat_value)

            return jsonify(latest, gl, lat_value_final, overall_gl)
        else:
            return "-1"
    else:
        return "-1"


@app.route("/leaderboard_crypto")
@login_required
def leaderboard_crypto():
    # user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    # cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    cash = db.child("users").child(
        session['user_id']).child("cash").get().val()
    user = db.child("users").child(
        session['user_id']).child("username").get().val()

    # need to find a way to get list of users
    user_list = db.child("users").shallow().get().val()
    userlist = (list(user_list))

    # users = db.execute("SELECT id, username FROM users")
    user_scores = []
    for i in range(len(userlist)):
        folio_list = db.child("crypto").child("portfolio").child(
            userlist[i]).shallow().get().val()

        # portfolio = db.execute("SELECT symbol,shares,price FROM portfolio WHERE id = :id", id= users[i]["id"])
        if (folio_list != None):
            print(1)
            folio_list = (list(folio_list))
            gl = 0
            inv = 0
            for j in range(len(folio_list)):
                latest = lookup_crypto(folio_list[j])
                already_held = db.child("crypto").child("portfolio").child(userlist[i]).child(
                    folio_list[j]).child("shares").get().val()
                last_price = db.child("crypto").child("portfolio").child(userlist[i]).child(
                    folio_list[j]).child("price").get().val()
                inv += float(last_price)*float(already_held)
                gl += (float(latest["price"]) -
                       float(last_price))*float(already_held)
            profit_percent = (gl/inv)*100
            user_scores.append({"username": db.child("users").child(userlist[i]).child("username").get(
            ).val(), "profit": float("%.2f" % gl), "profit_percent": float("%.2f" % profit_percent)})
        else:
            continue

    if(len(user_scores) != 0):
        result = sorted(
            user_scores, key=lambda i: i["profit_percent"], reverse=True)

    else:
        result = []
    return render_template("crypto-leaderboard.html", user_scores=result, user=user, cash=cash)


@app.route("/wallet_stock", methods=['GET', 'POST'])
@login_required
def wallet_stock():
    cash = db.child("users").child(
        session['user_id']).child("cash_stocks").get().val()
    user = db.child("users").child(
        session['user_id']).child("username").get().val()
    # user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    # cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    if request.method == 'POST':
        amount = request.form.get("amount")
        if float(amount) <= 0:
            flash("Invalid Amount", "error")
            return redirect(url_for("wallet_stock"))
        else:
            if(float(amount) < 0):
                db.child("users").child(session['user_id']).update(
                    {"cash": float(cash)+float(amount)})
            #db.execute("UPDATE users SET cash=cash+ :amount WHERE id=:x",amount=amount,x=session["user_id"])
                cash = db.child("users").child(
                    session['user_id']).child("cash_stocks").get().val()
            #cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
                flash("amount added", "success")
                return render_template("stock-wallet.html", cash=cash, user=user)
            else:
                flash("Not Allowed by admin, Speak to coordinators", "error")
                return render_template("stock-wallet.html", cash=cash, user=user)

    else:
        return render_template("stock-wallet.html", cash=cash, user=user)





@app.route("/index_stock")
@login_required
def index_stock():
    cash = db.child("users").child(
        session['user_id']).child("cash_stocks").get().val()
    user = db.child("users").child(
        session['user_id']).child("username").get().val()
    # cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    # user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    return render_template("stock-index.html", cash=cash, user=user)
    # return render_template("index.html", cash=cash[0]["cash"], user=user[0]["username"])


@app.route("/quote_stock", methods=["GET", "POST"])
@login_required
def quote_stock():
    cash = db.child("users").child(
        session['user_id']).child("cash_stocks").get().val()
    user = db.child("users").child(
        session['user_id']).child("username").get().val()
    # user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    # cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    if request.method == "POST":
        result = is_valid_stock(request.form.get("symbol"))
        if result is None:
            flash("invalid stock or Trade Ban on this Script", "error")
            return render_template("stock-quote.html", cash=cash, user=user)
        else:
            return render_template("stock-quoted.html", symbol=result["symbol"], user=user, cash=cash)
    else:
        return render_template("stock-quote.html", cash=cash, user=user)
      # return render_template("quote.html", user=user[0]["username"], cash=cash[0]["cash"])

# this will be configured once we build portfolio


@app.route("/trade_stock")
@login_required
def trade_stock():
    cash = db.child("users").child(
        session['user_id']).child("cash_stocks").get().val()
    user = db.child("users").child(
        session['user_id']).child("username").get().val()
    symbol = list()
    share = list()
    price = list()
    total = list()

    sy = db.child("stock").child("portfolio").child(session['user_id']).shallow().get().val()
    if(sy != None):
        sy = (list(sy))

        if len(sy) != 0:
            for i in range(len(sy)):

                share.append(db.child("stock").child("portfolio").child(
                    session['user_id']).child(sy[i]).child("shares").get().val())
                price.append(db.child("stock").child("portfolio").child(
                    session['user_id']).child(sy[i]).child("price").get().val())
                symbol.append(sy[i])
                total.append(float(db.child("stock").child("portfolio").child(session['user_id']).child(sy[i]).child("shares").get(
                ).val()) * float(db.child("stock").child("portfolio").child(session['user_id']).child(sy[i]).child("price").get().val()))
    # sy = db.execute("SELECT symbol FROM portfolio WHERE id = :id", id= session['user_id'])
    # sh = db.execute("SELECT shares FROM portfolio WHERE id = :id", id= session['user_id'])
    # pr = db.execute("SELECT price FROM portfolio WHERE id = :id", id= session['user_id'])
    # for i in range (len(sy)):
    #     symbol.append(sy[i]["symbol"].upper())
    # for i in range (len(sh)):
    #     share.append(sh[i]["shares"])
    # for i in range (len(pr)):
    #     price.append(pr[i]["price"])
    # for i in range(len(symbol)):
    #     total.append(price[i]*share[i])
    # cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    # user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
        data = zip(symbol, share, price, total)
        return render_template("stock-trade.html", data=data, cash=cash, user=user)
    else:
        data = zip([], [], [], [])
        return render_template("stock-trade.html", data=data, cash=cash, user=user)


@app.route("/buy_stock", methods=["GET", "POST"])
@login_required
def buy_stock():
    cash = db.child("users").child(
        session['user_id']).child("cash_stocks").get().val()
    user = db.child("users").child(
        session['user_id']).child("username").get().val()
    user_folio = db.child("stock").child("portfolio").child(
        session['user_id']).shallow().get().val()
    # user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    # cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    if request.method == "POST":
        symbol = request.form.get("symbol")
        stock = lookup_stock(request.form.get("symbol"))
        price = stock["price"]
        amount = request.form.get("shares")
        if amount is None:
            return render_template("stock-buy.html", symbol=symbol, user=user, cash=cash, name=stock["name"], price=stock["price"])
        else:
            if  (float(amount)) <= 0:
                flash("Invalid Shares!", "error")
                return redirect(url_for("quote_stock"))

        if float(cash) > float(amount)*stock["price"]:

            if(user_folio == None or symbol not in user_folio):
                new_folio_entry = {"shares": amount, "price": price,
                                   "last transacted": datetime.timestamp(datetime.now())}
                db.child("stock").child("portfolio").child(session['user_id']).child(
                    symbol).set(new_folio_entry)

                # db.execute("INSERT INTO portfolio (id, symbol, shares, price) VALUES(:id, :symbol, :shares, :price)", id= session['user_id'], symbol=symbol, shares=amount, price=stock["price"])
            else:
                already_held = db.child("stock").child("portfolio").child(
                    session['user_id']).child(symbol).child("shares").get().val()
                last_price = db.child("stock").child("portfolio").child(
                    session['user_id']).child(symbol).child("price").get().val()
                db.child("stock").child("portfolio").child(session['user_id']).child(symbol).update({"price": (
                    ((float(last_price)*float(already_held)) + (float(price)*float(amount))) / (float(amount)+float(already_held)))})
                db.child("stock").child("portfolio").child(session['user_id']).child(
                    symbol).update({"shares": float(amount)+float(already_held)})
                db.child("stock").child("portfolio").child(session['user_id']).child(symbol).update(
                    {"last transacted": datetime.timestamp(datetime.now())})
                # temp = db.execute("SELECT shares FROM portfolio WHERE id=:id AND symbol=:symbol", id= session['user_id'], symbol=request.form.get("symbol"))
                # db.execute("UPDATE 'portfolio' SET shares=:shares WHERE id=:id AND symbol=:symbol", shares=temp[0]["shares"]+int(request.form.get("shares")), id=session['user_id'], symbol=request.form.get("symbol"))

            transacted = datetime.timestamp(datetime.now())

            new_history_entry = {"symbol": symbol, "shares": amount,
                                 "price": price, "Date Transacted": transacted}
            db.child("stock").child("history").child(session['user_id']).child(
                int(transacted)).set(new_history_entry)
            # db.execute("INSERT INTO history (id, symbol, shares, price, transacted) VALUES(:id, :symbol, :shares, :price, :transacted)", id= session['user_id'], symbol=request.form.get("symbol"), shares=request.form.get("shares"), price=stock["price"], transacted = transacted)

            db.child("users").child(session['user_id']).update(
                {"cash_stocks": float(cash)-(float(price)*float(amount))})
            # db.execute("UPDATE 'users' SET cash=:cash WHERE id=:id", cash=(cash[0]["cash"])-(float(amount)*stock["price"]), id= session['user_id'])

        else:
            flash("Not Enough Balance", "error")
            return redirect(url_for("portfolio_stock"))
        flash("Shares Bought", "success")
        return redirect(url_for("portfolio_stock"))

    else:
        return render_template("stock-buy.html", user=user, cash=cash)


@app.route("/sell_stock", methods=["GET", "POST"])
@login_required
def sell_stock():

    cash = db.child("users").child(
        session['user_id']).child("cash_stocks").get().val()
    user = db.child("users").child(
        session['user_id']).child("username").get().val()
    user_folio = db.child("stock").child("portfolio").child(
        session['user_id']).shallow().get().val()
    # user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    # cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    if request.method == "POST":
        symbol = request.form.get("symbol")
        amount = request.form.get("shares")
        already_held = db.child("stock").child("portfolio").child(
            session['user_id']).child(symbol).child("shares").get().val()
        last_price = db.child("stock").child("portfolio").child(
            session['user_id']).child(symbol).child("price").get().val()
        stock = lookup_stock(request.form.get("symbol"))
        if amount is None:
            return render_template("stock-sell.html", user=user, cash=cash, symbol=symbol, name=stock["name"], price=stock["price"])
        price = stock["price"]
        #sy = db.execute("SELECT shares FROM portfolio WHERE id = :id AND symbol=:symbol", id= session['user_id'], symbol=request.form.get("symbol"))
        if symbol not in user_folio:
            flash("You dont own this Stock", "error")
            return redirect(url_for("trade_stock"))
        if ((float(amount)) <= 0 or float(amount) > float(already_held)):
            flash("Invalid Shares", "error")
            return redirect(url_for("trade_stock"))
        if (float(already_held) == float(amount)):
            db.child("stock").child("portfolio").child(
                session['user_id']).child(symbol).remove()
            #db.execute("DELETE from 'portfolio' WHERE id = :id AND symbol=:symbol",id= session['user_id'], symbol=request.form.get("symbol") )
        else:

            db.child("stock").child("portfolio").child(session['user_id']).child(symbol).update({"price": (
                ((float(last_price)*float(already_held)) - (float(price)*float(amount))) / (float(already_held)-float(amount)))})
            db.child("stock").child("portfolio").child(session['user_id']).child(
                symbol).update({"shares": float(already_held)-float(amount)})
            db.child("stock").child("portfolio").child(session['user_id']).child(symbol).update(
                {"last transacted": datetime.timestamp(datetime.now())})
            # db.execute("UPDATE 'portfolio' SET shares=:shares WHERE id=:id AND symbol=:symbol", shares=sy[0]["shares"]-int(request.form.get("shares")), id=session['user_id'], symbol=request.form.get("symbol"))

        transacted = datetime.timestamp(datetime.now())
        new_history_entry = {"symbol": symbol, "shares": -1 *
                             float(amount), "price": price, "Date Transacted": transacted}
        db.child("stock").child("history").child(session['user_id']).child(
            int(transacted)).set(new_history_entry)

        # transacted = datetime.timestamp(datetime.now())
        # db.execute("INSERT INTO history (id, symbol, shares, price, transacted) VALUES(:id, :symbol, :shares, :price, :transacted)", id= session['user_id'], symbol=request.form.get("symbol"), shares=-int(request.form.get("shares")), price=stock["price"], transacted = transacted)
        profit = stock["price"]*float(amount)
        db.child("users").child(session['user_id']).update(
            {"cash_stocks": float(cash)+float(profit)})
        # temp = db.execute("SELECT cash FROM users WHERE id=:id",id= session['user_id'])
        # db.execute("UPDATE 'users' SET cash=:cash WHERE id=:id", cash=temp[0]["cash"]+profit, id= session['user_id'])
        flash("Shares Sold", "success")
        return redirect(url_for("portfolio_stock"))

    else:
        return render_template("stock-sell.html", user=user, cash=cash)


@app.route("/update_quote_stock", methods=["GET", "POST"])
@login_required
def update_quote_stock():
    symbol = request.args.get('symbol')
    temp = lookup_stock(symbol)
    price = temp["price"]
    return jsonify(price)


@app.route("/history_stock")
@login_required
def history_stock():
    cash = db.child("users").child(
        session['user_id']).child("cash_stocks").get().val()
    user = db.child("users").child(
        session['user_id']).child("username").get().val()
    # user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    # cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    symbol = list()
    share = list()
    price = list()
    transacted = list()
    total = []

    sy = db.child("stock").child("history").child(session['user_id']).shallow().get().val()
    if(sy != None):
        sy = (list(sy))

        if len(sy) != 0:
            for i in range(len(sy)):

                transacted.append(str(datetime.fromtimestamp(int(sy[i]))))
                share.append(db.child("stock").child("history").child(
                    session['user_id']).child(sy[i]).child("shares").get().val())
                price.append(db.child("stock").child("history").child(
                    session['user_id']).child(sy[i]).child("price").get().val())
                symbol.append(db.child("stock").child("history").child(
                    session['user_id']).child(sy[i]).child("symbol").get().val())
    # sy = db.execute("SELECT symbol FROM history WHERE id = :id", id= session['user_id'])
    # sh = db.execute("SELECT shares FROM history WHERE id = :id", id= session['user_id'])
    # pr = db.execute("SELECT price FROM history WHERE id = :id", id= session['user_id'])
    # tr = db.execute("SELECT transacted FROM history WHERE id = :id", id= session['user_id'])
    # for i in range (len(sy)):
    #     symbol.append(sy[i]["symbol"].upper())
    # for i in range (len(sh)):
    #     share.append(sh[i]["shares"])
    # for i in range (len(pr)):
    #     price.append(pr[i]["price"])
    # for i in range (len(tr)):
    #     transacted.append(tr[i]["transacted"])
        data = zip(symbol, share, price, transacted)
        return render_template("stock-history.html", data=data, user=user, cash=cash)
    else:
        return render_template("stock-history.html", user=user, cash=cash)


@app.route("/portfolio_stock")
@login_required
def portfolio_stock():
    cash = db.child("users").child(
        session['user_id']).child("cash_stocks").get().val()
    user = db.child("users").child(
        session['user_id']).child("username").get().val()
    # user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    symbol = list()
    share = list()
    price = list()
    latest = list()
    invested = list()
    day_gl = list()
    # cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    sy = db.child("stock").child("portfolio").child(session['user_id']).shallow().get().val()
    if(sy != None):
        sy = (list(sy))
    # sy = db.execute("SELECT symbol FROM portfolio WHERE id = :id", id= session['user_id'])
    # sh = db.execute("SELECT shares FROM portfolio WHERE id = :id", id= session['user_id'])
    # pr = db.execute("SELECT price FROM portfolio WHERE id = :id", id= session['user_id'])
        if len(sy) != 0:
            for i in range(len(sy)):
                # symbol.append(sy[i]["symbol"].upper())
                # prc=lookup(sy[i]["symbol"])
                # latest.append(prc["price"])
                # share.append(sh[i]["shares"])
                # price.append(pr[i]["price"])

                prc = lookup_stock(sy[i])
                latest.append(prc["price"])
                share.append(db.child("stock").child("portfolio").child(
                    session['user_id']).child(sy[i]).child("shares").get().val())
                price.append(db.child("stock").child("portfolio").child(
                    session['user_id']).child(sy[i]).child("price").get().val())
                symbol.append(sy[i])
                invested.append(float(db.child("stock").child("portfolio").child(session['user_id']).child(sy[i]).child("shares").get(
                ).val()) * float(db.child("stock").child("portfolio").child(session['user_id']).child(sy[i]).child("price").get().val()))
                day_gl.append((float(prc["price"])-float(db.child("stock").child("portfolio").child(session['user_id']).child(sy[i]).child(
                    "price").get().val()))*float(db.child("stock").child("portfolio").child(session['user_id']).child(sy[i]).child("shares").get().val()))
            data = zip(symbol, share, price, latest, invested, day_gl)
            inv_amt = list()
            gl = list()
            for i in range(len(sy)):
                gl.append((float(latest[i])-float(price[i]))*float(share[i]))
                inv_amt.append(float(price[i])*float(share[i]))
            lat_value = sum(inv_amt)+sum(gl)
            top_gain_index = gl.index(max(gl))
            top_loss_index = gl.index(min(gl))
            top_gain_symbol = symbol[top_gain_index]
            top_loss_symbol = symbol[top_loss_index]
            overall_gl = sum(gl)
            return render_template("stock-portfolio.html", data=data, lat_value=lat_value, top_gain=top_gain_symbol, top_loss=top_loss_symbol, overall_gl=overall_gl, cash=cash, user=user)
        else:
            return render_template("stock-portfolio.html", lat_value=0, top_gain='-', top_loss='-', overall_gl=0, cash=cash, user=user)

    else:
        return render_template("stock-portfolio.html", lat_value=0, top_gain='-', top_loss='-', overall_gl=0, cash=cash, user=user)


@app.route("/update_portfolio_stock", methods=['GET', 'POST'])
@login_required
def update_portfolio_stock():
    latest = list()
    share = list()
    price = list()

    sy = db.child("stock").child("portfolio").child(session['user_id']).shallow().get().val()
    if(sy != None):
        sy = (list(sy))
    # sy = db.execute("SELECT symbol FROM portfolio WHERE id = :id", id= session['user_id'])
    # sh = db.execute("SELECT shares FROM portfolio WHERE id = :id", id= session['user_id'])
    # pr = db.execute("SELECT price FROM portfolio WHERE id = :id", id= session['user_id'])
        if len(sy) != 0:
            for i in range(len(sy)):
                prc = lookup_stock(sy[i])
                latest.append(prc["price"])
                share.append(db.child("stock").child("portfolio").child(
                    session['user_id']).child(sy[i]).child("shares").get().val())
                price.append(db.child("stock").child("portfolio").child(
                    session['user_id']).child(sy[i]).child("price").get().val())
            inv_amt = list()
            gl = list()
            for i in range(len(sy)):
                glst = (float(latest[i])-float(price[i]))*float(share[i])
                gl.append(float("%.2f" % glst))
                inv_amt.append(float(price[i])*float(share[i]))
            tot_inv = float("%.2f" % sum(inv_amt))
            overall_gl = float("%.2f" % sum(gl))
            lat_value = tot_inv + overall_gl
            lat_value_final = float("%.2f" % lat_value)

            return jsonify(latest, gl, lat_value_final, overall_gl)
        else:
            return "-1"
    else:
        return "-1"


@app.route("/leaderboard_stock")
@login_required
def leaderboard_stock():
    # user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    # cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    cash = db.child("users").child(
        session['user_id']).child("cash_stocks").get().val()
    user = db.child("users").child(
        session['user_id']).child("username").get().val()

    # need to find a way to get list of users
    user_list = db.child("users").shallow().get().val()
    userlist = (list(user_list))

    # users = db.execute("SELECT id, username FROM users")
    user_scores = []
    for i in range(len(userlist)):
        folio_list = db.child("stock").child("portfolio").child(
            userlist[i]).shallow().get().val()

        # portfolio = db.execute("SELECT symbol,shares,price FROM portfolio WHERE id = :id", id= users[i]["id"])
        if (folio_list != None):
            print(1)
            folio_list = (list(folio_list))
            gl = 0
            inv = 0
            for j in range(len(folio_list)):
                latest = lookup_stock(folio_list[j])
                already_held = db.child("stock").child("portfolio").child(userlist[i]).child(
                    folio_list[j]).child("shares").get().val()
                last_price = db.child("stock").child("portfolio").child(userlist[i]).child(
                    folio_list[j]).child("price").get().val()
                inv += float(last_price)*float(already_held)
                gl += (float(latest["price"]) -
                       float(last_price))*float(already_held)
            profit_percent = (gl/inv)*100
            user_scores.append({"username": db.child("users").child(userlist[i]).child("username").get(
            ).val(), "profit": float("%.2f" % gl), "profit_percent": float("%.2f" % profit_percent)})
        else:
            continue

    if(len(user_scores) != 0):
        result = sorted(
            user_scores, key=lambda i: i["profit_percent"], reverse=True)

    else:
        result = []
    return render_template("stock-leaderboard.html", user_scores=result, user=user, cash=cash)


@app.route("/logout")
def logout():
    # forget any user_id
    # session.clear()
    session.pop('user_id', default=None)
    return redirect(url_for("login"))



if __name__ == "__main__":
    app.run()
