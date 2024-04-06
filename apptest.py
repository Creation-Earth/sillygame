# app.py
#
# Minor Programmeren
# Ali Najib
#
# Implement a website via which users can “buy” and “sell” stocks.

import os

import requests
from decimal import *

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from cs50 import SQL
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import apology, login_required, lookup, usd
from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import scoped_session, sessionmaker

from flask_socketio import SocketIO

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")




@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Show portfolio of stocks"""

    # Form the ranking using database
    db.execute("DROP TABLE score")
    db.execute("CREATE TABLE score (user_id TEXT NOT NULL, username TEXT NOT NULL, total NUMERIC NOT NULL)")

    # Form the scores vector
    ids_active = db.execute("SELECT id FROM users")
    for id_active in ids_active:
        portfolio_stocks = db.execute("SELECT symbol FROM portfolio WHERE user_id = ?", id_active["id"])
        cash = db.execute("SELECT cash FROM users WHERE id = ?", id_active["id"])
        cash = cash[0]["cash"]
        portfolio = db.execute("SELECT * FROM portfolio WHERE user_id = ?", id_active["id"])
        total = cash
        for i in range(0, len(portfolio_stocks)):
            stock_symbol = portfolio[i]["symbol"] 
            stock_quote = lookup(stock_symbol)

            portfolio[i]["name"] = stock_quote["name"]
            portfolio[i]["price"] = stock_quote["price"]
            portfolio[i]["total"] = portfolio[i]["shares"] * stock_quote["price"]
            total = total + portfolio[i]["total"]
        username = db.execute("SELECT username FROM users WHERE id = ?", id_active["id"])
        username = username[0]["username"]

        db.execute("INSERT INTO score (user_id, username, total) VALUES(?, ?, ?)", id_active["id"], username, total)

    scores = db.execute("SELECT * FROM score ORDER BY total DESC")
    

    # Form the personal portfolio table
    portfolio_stocks = db.execute("SELECT symbol FROM portfolio WHERE user_id = ?", session["user_id"])
    stock_iterator = []
    for i in range(0, len(portfolio_stocks)):
        stock_iterator.append(portfolio_stocks[i]["symbol"])

    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
    if len(cash) > 0:
        cash = cash[0]["cash"]
    else:
        cash = 0
    portfolio = db.execute("SELECT * FROM portfolio WHERE user_id = ?", session["user_id"])
    total = cash
    for i in range(0, len(portfolio_stocks)):
        stock_symbol = portfolio[i]["symbol"]
        stock_quote = lookup(stock_symbol)
        portfolio[i]["name"] = stock_quote["name"]
        portfolio[i]["price"] = stock_quote["price"]
        portfolio[i]["total"] = portfolio[i]["shares"] * stock_quote["price"]
        total = total + portfolio[i]["total"]

    # Form the chat
    chat_users = db.execute("SELECT username FROM chat")
    chat_messages = db.execute("SELECT message FROM chat")
    chat = chat_users
    for i in range(0, len(chat_messages)):
        chat[i]["message"] = chat_messages[i]["message"]

    # Render home page
    return render_template("index.html", scores= scores, portfolio=portfolio, cash=cash, total=total, chat = chat)


# Implement chat functionality!

### CHAT SEEMS NOT TO WORK?!
def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')





@app.route("/guild", methods=["GET", "POST"])
@login_required
def guild():
    """Show guild portfolio or be redirected to join page"""

    #Retrieve guild symbol
    guild = db.execute("SELECT guild FROM users WHERE id = ?", session["user_id"])
    guild = guild[0]["guild"]

    # Check if user in guild and redirect user accordingly
    if guild == "N":
        guildstats = db.execute("SELECT * FROM guildcash")
        for i in range(0, len(guildstats)):
            guild = guildstats[i]["guild"]
            members = db.execute("SELECT username FROM users WHERE guild = ?", guild)
            membercount = len(members)
            guildstats[i]["membercount"] = membercount
            total = db.execute("SELECT total FROM guildscore WHERE symbol = ?", guild)
            guildstats[i]["total"] = total[0]["total"]
            
        return render_template("join.html", guild = guild, guildstats = guildstats)
    else:

        # Form the ranking using database
        db.execute("DROP TABLE guildscore")
        db.execute("CREATE TABLE guildscore (symbol TEXT NOT NULL, total NUMERIC NOT NULL)")

        # Form the ranking table
        guilds_active = db.execute("SELECT guild FROM guildcash")

        for guild_active in guilds_active:
            guild_active = guild_active["guild"]
            portfolio_stocks = db.execute("SELECT symbol FROM guildportfolio WHERE guild = ?", guild_active)
            cash = db.execute("SELECT cash FROM guildcash WHERE guild = ?", guild_active)
            cash = cash[0]["cash"]
            portfolio = db.execute("SELECT * FROM guildportfolio WHERE guild = ?", guild_active)
            total = cash
            for i in range(0, len(portfolio_stocks)):
                stock_symbol = portfolio[i]["symbol"] 
                stock_quote = lookup(stock_symbol)
                portfolio[i]["name"] = stock_quote["name"]
                portfolio[i]["price"] = stock_quote["price"]
                portfolio[i]["total"] = portfolio[i]["shares"] * stock_quote["price"]
                total = total + portfolio[i]["total"]
            #guildname = db.execute("SELECT username FROM users WHERE id = ?", guild_active)
            #guildname = username[0]["username"]

            db.execute("INSERT INTO guildscore (symbol, total) VALUES(?, ?)", guild_active, total)
        guildscores = db.execute("SELECT * FROM guildscore ORDER BY total DESC")

        # Form the guild portfolio table
        portfolio_stocks = db.execute("SELECT symbol FROM guildportfolio WHERE guild = ?", guild)
        stock_iterator = []
        for i in range(0, len(portfolio_stocks)):
            stock_iterator.append(portfolio_stocks[i]["symbol"])

        cash = db.execute("SELECT cash FROM guildcash WHERE guild = ?", guild)
        cash = cash[0]["cash"]
        portfolio = db.execute("SELECT * FROM guildportfolio WHERE guild = ?", guild)
        total = cash
        for i in range(0, len(portfolio_stocks)):
            stock_symbol = portfolio[i]["symbol"]
            stock_quote = lookup(stock_symbol)
            portfolio[i]["name"] = stock_quote["name"]
            portfolio[i]["price"] = stock_quote["price"]
            portfolio[i]["total"] = portfolio[i]["shares"] * stock_quote["price"]
            total = total + portfolio[i]["total"]

            # Form the chat
            guild = db.execute("SELECT guild FROM users WHERE id = ?", session["user_id"])
            guild = guild[0]["guild"]
            chat_users = db.execute("SELECT username FROM guildchat WHERE guild = ?", guild)
            chat_messages = db.execute("SELECT message FROM guildchat WHERE guild = ?", guild)
            chat = chat_users
            for i in range(0, len(chat_messages)):
                chat[i]["message"] = chat_messages[i]["message"]

        # Obtain guild-members
        members = db.execute("SELECT username FROM users WHERE guild = ?", guild)

        return render_template("guild.html", portfolio = portfolio, total = total, stock_iterator = stock_iterator, 
                               guildscores = guildscores, chat = chat, members = members, cash = cash)




@app.route("/join", methods=["GET", "POST"])
@login_required
def join():
    """Join a guild"""
    if request.method == "POST":
        
        # Check if user is already in guild
        guild = db.execute("SELECT guild FROM users WHERE id = ?", session["user_id"])
        guild = guild[0]["guild"]
        if guild == "N":
            guildsymbol = request.form.get("guild")
            # Check if guild exists
            guildlist = db.execute("SELECT guild FROM guildportfolio WHERE guild = ?", guildsymbol)
            members = db.execute("SELECT username FROM users WHERE guild = ?", guild)
            membercount = len(members)
            if len(guildlist) != 0 and membercount < 5:
                db.execute("UPDATE users SET guild = ? WHERE id = ?", guildsymbol, session["user_id"])
            guild = db.execute("SELECT guild FROM users WHERE id = ?", session["user_id"])
            guild = guild[0]["guild"]
        return redirect("/guild")
        
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        guildstats = db.execute("SELECT * FROM guildcash")
        for i in range(0, len(guildstats)):
            guild = guildstats[i]["guild"]
            members = db.execute("SELECT username FROM users WHERE guild = ?", guild)
            membercount = len(members)
            guildstats[i]["membercount"] = membercount
            total = db.execute("SELECT total FROM guildscore WHERE symbol = ?", guild)
            guildstats[i]["total"] = total[0]["total"]
        return render_template("join.html", guildstats=guildstats)
    


        
@app.route("/leave", methods=["GET", "POST"])
@login_required
def leave():
    """Leave guild"""
    if request.method == "POST":
        db.execute("UPDATE users SET guild = ? WHERE id = ?", "N", session["user_id"])
        return redirect("/join")

    # User reached route via GET (as by clicking a link or via redirect) 
    else:
        return render_template("/guild")



@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """Show portfolio of stocks"""
    
    # add guild to guildportfolio with starting 10 TSL stocks
    if request.method == "POST":
        guild = request.form.get("guild")
        symbol = "TSL"

        # Check if guild already exists
        guildlist = db.execute("SELECT guild FROM guildportfolio WHERE guild = ?", guild)
        if len(guildlist) != 0:
            return render_template("join.html")

        # Create guild
        db.execute("INSERT INTO guildportfolio VALUES(?, ?, ?)", 10, symbol, guild)
        db.execute("INSERT INTO guildcash VALUES(?,?)", 200000.00, guild)
        db.execute("UPDATE users SET guild = ? WHERE id = ?", guild, session["user_id"])
        portfolio = db.execute("SELECT * FROM guildportfolio WHERE guild = ?", guild)
        return redirect("/guild")

    # User reached route via GET (as by clicking a link or via redirect) 
    else:
        return render_template("join.html")






@app.route("/guildbuy", methods=["GET", "POST"])
@login_required
def guildbuy():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Render an apology if the input is blank or the symbol does not exist
        symbol = request.form.get("symbol")
        symbol = symbol.upper()
        if lookup(symbol) == None or symbol == "":
            return apology("Invalid ticker symbol", 400)

        # Render an apology if the input is not a positive integer
        shares = request.form.get("shares")
        try:
           int(shares)
        except ValueError:
            return apology("Amount of shares must be integer.", 400)

        shares = int(shares)
        if not shares > 0: 
            return apology("Amount of shares must be positive.", 400)
        
        guild = db.execute("SELECT guild FROM users WHERE id = ?", session["user_id"])
        guild = guild[0]["guild"]

        # Render an apology, without completing a purchase, if the guild cannot afford the number of shares at the current price.
        cash = db.execute("SELECT cash FROM guildcash WHERE guild = ?", guild)
        cash = cash[0]["cash"]
        quote = lookup(symbol)
        if  (shares * quote["price"]) > cash:
            return apology("Guild cannot afford the number of shares at the current price")
         
        # Update cash reserves
        db.execute("UPDATE guildcash SET cash = ? WHERE guild = ?", cash - (shares * quote["price"]), guild)

       # Update guildhistory
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
        username = username[0]["username"]
        db.execute("INSERT INTO guildhistory (symbol, shares, price, transacted, username, guild) VALUES(?, ?, ?, ?, ?, ?)", symbol, (-1 * shares), quote["price"], dt_string, username, guild)

        # Update guildportfolio
        portfolio_entry = db.execute("SELECT symbol FROM guildportfolio WHERE symbol = ? AND guild = ?", symbol, guild)
        if len(portfolio_entry) != 1:
            db.execute("INSERT INTO guildportfolio (shares, symbol, guild) VALUES(?, ?, ?)", 0, symbol, guild)
        current_holdings = db.execute("SELECT shares FROM guildportfolio WHERE symbol = ? AND guild = ?", symbol, guild)
        current_holdings = current_holdings[0]["shares"]
        db.execute("UPDATE guildportfolio SET shares = ? WHERE symbol = ? AND guild = ?", current_holdings + shares, symbol, guild)

        # Redirect user to home page
        return redirect("/guild")


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return redirect("/guild")
    


@app.route("/guildsell", methods=["GET", "POST"])
@login_required
def guildsell():
    """Sell shares of stock"""
    # User reached route via POST (as by submitting a form via POST)
   
    guild = db.execute("SELECT guild FROM users WHERE id = ?", session["user_id"])
    guild = guild[0]["guild"]
    portfolio_stocks = db.execute("SELECT symbol FROM guildportfolio WHERE guild = ?", guild)
    stock_iterator = []
    for i in range(0, len(portfolio_stocks)):
        stock_iterator.append(portfolio_stocks[i]["symbol"])
 
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        symbol = request.form.get("symbol")
        if symbol == None:
            return apology("Choose a stock!")
        symbol = symbol.upper()
        quote =  lookup(symbol)

        # Render an apology if the input is not a positive integer
        shares = int(request.form.get("shares"))
        if not shares > 0:
            return apology("Amount of shares must be positive.")

        # Compare current stock holdings against stock to be sold
        current_holdings = db.execute("SELECT shares FROM guildportfolio WHERE symbol = ? AND guild = ?", symbol, guild)
        if len(current_holdings) > 0:
            current_holdings_int = current_holdings[0]["shares"]
        else:
            current_holdings_int = 0
        if len(current_holdings) != 1 or shares > current_holdings_int:
            return apology("Guild does not own any or enough shares of that stock.")

        # Update cash reserves
        cash = db.execute("SELECT cash FROM guildcash WHERE guild = ?", guild)
        cash = cash[0]["cash"]
        db.execute("UPDATE guildcash SET cash = ? WHERE guild = ?", cash + (shares * quote["price"]), guild)

        # Update guildhistory
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
        username = username[0]["username"]
        db.execute("INSERT INTO guildhistory (symbol, shares, price, transacted, username, guild) VALUES(?, ?, ?, ?, ?, ?)", symbol, (-1 * shares), quote["price"], dt_string, username, guild)

        # Update portfolio
        db.execute("UPDATE guildportfolio SET shares = ? WHERE symbol = ? AND guild = ?", current_holdings_int - shares, symbol, guild)
        current_holdings = db.execute("SELECT shares FROM guildportfolio WHERE symbol = ? AND guild = ?", symbol, guild)
        current_holdings = current_holdings[0]["shares"]
        if current_holdings == 0:
            db.execute("DELETE FROM guildportfolio WHERE symbol = ? AND guild = ?", symbol, guild)

        # Redirect user to home page
        return redirect("/guild")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return redirect("/guild")











@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Render an apology if the input is blank or the symbol does not exist
        symbol = request.form.get("symbol")
        symbol = symbol.upper()
        if lookup(symbol) == None or symbol == "":
            return apology("Invalid ticker symbol", 400)

        # Render an apology if the input is not a positive integer
        shares = request.form.get("shares")
        try:
           int(shares)
        except ValueError:
            return apology("Amount of shares must be integer.", 400)

        shares = int(shares)
        if not shares > 0: 
            return apology("Amount of shares must be positive.", 400)

        # Render an apology, without completing a purchase, if the user cannot afford the number of shares at the current price.
        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        cash = cash[0]["cash"]
        quote = lookup(symbol)
        if  (shares * quote["price"]) > cash:
            return apology("Cannot afford the number of shares at the current price")
         
        # Update cash reserves
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash - (shares * quote["price"]), session["user_id"])

        # Update history
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        db.execute("INSERT INTO history (symbol, shares, price, transacted, user_id) VALUES(?, ?, ?, ?, ?)", symbol, shares, quote["price"], dt_string, session["user_id"])

        # Update portfolio
        portfolio_entry = db.execute("SELECT symbol FROM portfolio WHERE symbol = ? AND user_id = ?", symbol, session["user_id"])
        if len(portfolio_entry) != 1:
            db.execute("INSERT INTO portfolio (symbol, shares, user_id) VALUES(?, ?, ?)", symbol, 0, session["user_id"])
        current_holdings = db.execute("SELECT shares FROM portfolio WHERE symbol = ? AND user_id = ?", symbol, session["user_id"])
        current_holdings = current_holdings[0]["shares"]
        db.execute("UPDATE portfolio SET shares = ? WHERE symbol = ? AND user_id = ?", current_holdings + shares, symbol, session["user_id"])

        # Redirect user to home page
        return redirect("/")


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        guild = db.execute("SELECT guild FROM users WHERE id = ?", session["user_id"])
        guild = guild[0]["guild"]
        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        cash = cash[0]["cash"]
        if guild != 'N':
            gcash = db.execute("SELECT cash FROM guildcash WHERE guild = ?", guild)
            gcash = gcash[0]["cash"]
            return render_template("buy.html", guild = guild, cash = cash, gcash = gcash)
        else:
            return render_template("buy.html", guild = guild, cash = cash)
















@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    history = db.execute("SELECT * FROM history WHERE user_id = ?", session["user_id"])
    guild = db.execute("SELECT guild FROM users WHERE id = ?", session["user_id"])
    guild = guild[0]["guild"]
    guildhistory = db.execute("SELECT * FROM guildhistory WHERE guild = ?", guild)
    len_guildhistory = len(guildhistory)
    
    return render_template("history.html", history=history, guildhistory = guildhistory, len_guildhistory = len_guildhistory)



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")



@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Obtain stock quote
        symbol = request.form.get("symbol").upper()
        quote =  lookup(symbol)
        if lookup(symbol) == None or symbol == "":
            return apology("Invalid ticker symbol", 400)
        
        # Form the "Time Series Arena" graph
        symbol = 'K'
        url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=' + symbol + '&interval=5min&outputsize=full&apikey=UK5AYAG1U5ITGG96'
        r = requests.get(url)
        data = r.json()

        time_series = data["Time Series (5min)"]
        data_dates = []
        data_close = []
        for key in time_series:
            data_dates.append(key)
            data_close.append(time_series[key]['4. close'])
        data_length = len(data_close)
        
        # Redirect user to quoted page
        return render_template("quoted.html", quote=quote, data_dates = data_dates, 
                           data_close = data_close, data_length = data_length)
        
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Form the "Time Series Arena" graph
        symbol = 'K'
        url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=' + symbol + '&interval=5min&outputsize=full&apikey=UK5AYAG1U5ITGG96'
        r = requests.get(url)
        data = r.json()

        time_series = data["Time Series (5min)"]
        data_dates = []
        data_close = []
        for key in time_series:
            data_dates.append(key)
            data_close.append(time_series[key]['4. close'])
        data_length = len(data_close)
        return render_template("quote.html", data_dates = data_dates, 
                           data_close = data_close, data_length = data_length)



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
                
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure username has not been taken
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) == 1:
            return apology("name already taken", 400)

        # Ensure password and password confirmation was submitted
        if not request.form.get("password") or not request.form.get("confirmation"):
            return apology("must provide password and confirm password", 400)

        # Ensure passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match")

        # Register new user
        name=request.form.get("username")
        hash=generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", name, hash)

        # Redirect user to login form
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    portfolio_stocks = db.execute("SELECT symbol FROM portfolio WHERE user_id = ?", session["user_id"])
    stock_iterator = []
    for i in range(0, len(portfolio_stocks)):
        stock_iterator.append(portfolio_stocks[i]["symbol"])
 
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        symbol = request.form.get("symbol")
        if symbol == None:
            return apology("Choose a stock!")
        symbol = symbol.upper()
        quote =  lookup(symbol)

        # Render an apology if the input is not a positive integer
        shares = int(request.form.get("shares"))
        if not shares > 0:
            return apology("Amount of shares must be positive.")

        # Compare current stock holdings against stock to be sold
        current_holdings = db.execute("SELECT shares FROM portfolio WHERE symbol = ? AND user_id = ?", symbol, session["user_id"])
        current_holdings_int = current_holdings[0]["shares"]
        if len(current_holdings) != 1 or shares > current_holdings_int:
            return apology("user does not own any or enough shares of that stock.")

        # Update cash reserves
        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        cash = cash[0]["cash"]
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash + (shares * quote["price"]), session["user_id"])

        # Update history
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        db.execute("INSERT INTO history (symbol, shares, price, transacted, user_id) VALUES(?, ?, ?, ?, ?)", symbol, (-1 * shares), quote["price"], dt_string, session["user_id"])

        # Update portfolio
        db.execute("UPDATE portfolio SET shares = ? WHERE symbol = ? AND user_id = ?", current_holdings_int - shares, symbol, session["user_id"])
        current_holdings = db.execute("SELECT shares FROM portfolio WHERE symbol = ? AND user_id = ?", symbol, session["user_id"])
        current_holdings = current_holdings[0]["shares"]
        if current_holdings == 0:
            db.execute("DELETE FROM portfolio WHERE symbol = ? AND user_id = ?", symbol, session["user_id"])

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Form the personal portfolio table
        portfolio_stocks = db.execute("SELECT symbol FROM portfolio WHERE user_id = ?", session["user_id"])
        stock_iterator = []
        for i in range(0, len(portfolio_stocks)):
            stock_iterator.append(portfolio_stocks[i]["symbol"])
        portfolio = db.execute("SELECT * FROM portfolio WHERE user_id = ?", session["user_id"])
        for i in range(0, len(portfolio_stocks)):
            stock_symbol = portfolio[i]["symbol"]
            stock_quote = lookup(stock_symbol)
            portfolio[i]["name"] = stock_quote["name"]
            portfolio[i]["price"] = stock_quote["price"]
            portfolio[i]["total"] = portfolio[i]["shares"] * stock_quote["price"]


        guild = db.execute("SELECT guild FROM users WHERE id = ?", session["user_id"])
        guild = guild[0]["guild"]
        if guild != 'N':
            # Form the guild portfolio table
            portfolio_stocks = db.execute("SELECT symbol FROM guildportfolio WHERE guild = ?", guild)
            gstock_iterator = []
            for i in range(0, len(portfolio_stocks)):
                gstock_iterator.append(portfolio_stocks[i]["symbol"])

            cash = db.execute("SELECT cash FROM guildcash WHERE guild = ?", guild)
            cash = cash[0]["cash"]
            gportfolio = db.execute("SELECT * FROM guildportfolio WHERE guild = ?", guild)
            total = cash
            for i in range(0, len(portfolio_stocks)):
                stock_symbol = gportfolio[i]["symbol"]
                stock_quote = lookup(stock_symbol)
                gportfolio[i]["name"] = stock_quote["name"]
                gportfolio[i]["price"] = stock_quote["price"]
                gportfolio[i]["total"] = gportfolio[i]["shares"] * stock_quote["price"]
                total = total + gportfolio[i]["total"]




            return render_template("sell.html", stock_iterator = stock_iterator, gstock_iterator = gstock_iterator, guild = guild, gportfolio = gportfolio, portfolio = portfolio)
        
        else:
            return render_template("sell.html", stock_iterator = stock_iterator, guild = guild, portfolio = portfolio)

        
        
        return render_template("sell.html", stock_iterator = stock_iterator, guild = guild)





@app.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    """Show portfolio of stocks"""
    
    # add chat message
    if request.method == "POST":
        message = request.form.get("message")
        username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
        username = username[0]["username"]
        db.execute("INSERT INTO chat (username, message) VALUES(?, ?)", username, message)
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect) 
    else:
        return render_template("index.html")
    

@app.route("/guildchat", methods=["GET", "POST"])
@login_required
def guildchat():
    """Show portfolio of stocks"""
    
    # add chat message
    if request.method == "POST":
        message = request.form.get("message")
        username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
        guild = db.execute("SELECT guild FROM users WHERE id = ?", session["user_id"])
        username = username[0]["username"]
        guild = guild[0]["guild"]

        db.execute("INSERT INTO guildchat (username, message, guild) VALUES(?, ?, ?)", username, message, guild)
        return redirect("/guild")

    # User reached route via GET (as by clicking a link or via redirect) 
    else:
        return render_template("guild.html")




if __name__ == "__main__":
    app.run(port=8000, debug=True)