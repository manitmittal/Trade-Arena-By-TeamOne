from functools import wraps
from flask import redirect, render_template, request, session, url_for
import csv
import urllib.request
from nsetools import Nse
import yfinance as yf
import cryptocompare
nse = Nse()


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.11/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def lookup_crypto(symbol):
    # data = yf.download(tickers=symbol+'.NS', period='10m', interval='5m')
    l=cryptocompare.get_coin_list(format = True)
    # valid = nse.is_valid_code(symbol)
    if (symbol.upper() in l):
        # stockdetails = nse.get_quote(symbol)
        price = cryptocompare.get_price(symbol.upper(), currency='USDT')[symbol.upper()]['USDT']
        # data2 = yf.Ticker(symbol+".NS")
        # name = data2.info['longName']
        return {
            "name": symbol.upper(),
            "price": price,
            "symbol": symbol.upper()
        }
    else:
        return None


def is_valid_crypto(symbol):

    # data = yf.download(tickers=symbol+'.NS', period='10m', interval='5m')
    # Print data
    l=cryptocompare.get_coin_list(format = True)
   
    # x = (len(data))
    if(symbol.upper() in l):
        return {
            "symbol": symbol.upper()
        }
    else:
        return None

def is_valid_stock(symbol):

    # data = yf.download(tickers=symbol+'.NS', period='10m', interval='5m')
    # Print data
    # l=cryptocompare.get_coin_list(format = True)
   
    # x = (len(data))
    if(nse.is_valid_code(symbol)):
        return {
            "symbol": symbol.upper()
        }
    else:
        return None


def lookup_stock(symbol):
    # data = yf.download(tickers=symbol+'.NS', period='10m', interval='5m')
    # l=cryptocompare.get_coin_list(format = True)
    # valid = nse.is_valid_code(symbol)
    if (nse.is_valid_code(symbol)):
        stockdetails = nse.get_quote(symbol)
        price = stockdetails['lastPrice']
        # data2 = yf.Ticker(symbol+".NS")
        name = stockdetails['companyName']
        return {
            "name": name,
            "price": price,
            "symbol": symbol.upper()
        }
    else:
        return None


# def lookup(symbol):
#     # data = yf.download(tickers=symbol+'.NS', period='10m', interval='5m')
#     l=cryptocompare.get_coin_list(format = True)
#     # valid = nse.is_valid_code(symbol)
#     if (symbol.upper() in l):
#         # stockdetails = nse.get_quote(symbol)
#         price = cryptocompare.get_price(symbol.upper(), currency='USDT')[symbol.upper()]['USDT']
#         # data2 = yf.Ticker(symbol+".NS")
#         # name = data2.info['longName']
#         return {
#             "name": symbol.upper(),
#             "price": price,
#             "symbol": symbol.upper()
#         }
#     else:
#         return None


# def is_valid(symbol):

#     # data = yf.download(tickers=symbol+'.NS', period='10m', interval='5m')
#     # Print data
#     l=cryptocompare.get_coin_list(format = True)
   
#     # x = (len(data))
#     if(symbol.upper() in l):
#         return {
#             "symbol": symbol.upper()
#         }
#     else:
#         return None
