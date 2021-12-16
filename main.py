from sqlite3.dbapi2 import Row
import requests
import configparser
import sqlite3
import hmac
import hashlib

db = sqlite3.connect('database.db')
config = configparser.ConfigParser()		
config.read("secrets.ini")

API_URL = 'https://api.binance.com/'
AUTH = (config['API']['API_KEY'], config['API']['SECRET_KEY'])

def initDB():
    curs = db.cursor()
    curs.execute('CREATE TABLE candles (Id INTEGER PRIMARY KEY, date INT, high REAL, low REAL, open REAL, close REAL, volume REAL)')
    # curs.execute('CREATE TABLE data (Id INTEGER PRIMARY KEY, uuid TEXT, traded_crypto REAL, price REAL, created_at_int INT, side TEXT)')
    # curs.execute('CREATE TABLE updates (Id INTEGER PRIMARY KEY, exchange TEXT, trading_pair TEXT, duration TEXT, table_name TEXT, last_check INT, startdate INT, last_id INT)')
    curs.close()

def prettyPrintArray(array):
    for item in array:
        print('- ' + str(item))

def formatDollar(amount):
    split = str(amount).split('.')
    return '.'.join([split[0], split[1][:2]]) + '$'

def getAllPairs():
    r = requests.get(API_URL + 'api/v1/exchangeInfo', auth=AUTH)
    data = r.json()
    all_symbols = []
    for symbol in data['symbols']:
        all_symbols.append(symbol['symbol'])

    return all_symbols

def getDepth(direction = 'asks', pair = 'BTCUSDT'):
    r = requests.get(API_URL + 'api/v1/depth', auth=AUTH, params={'symbol': pair, 'limit': 5})
    data = r.json()
    return data[direction][0][0]

def getOrderBook(pair = 'BTCUSDT'):
    r = requests.get(API_URL + 'api/v1/depth', auth=AUTH, params={'symbol': pair})
    data = r.json()
    return (data['bids'], data['asks'])

def refreshDataCandle(pair = 'BTCUSDT', duration = '5m'):
    r = requests.get(API_URL + 'api/v3/klines', auth=AUTH, params={'symbol': pair, 'interval':duration})
    data = r.json()

    # check last candle
    update = True
    lastupdate = 0
    curs = db.cursor()
    for row in curs.execute('SELECT date FROM candles ORDER BY date DESC LIMIT 1'):
        lastupdate = row[0]

    if update:
        for candle in data:
            if candle[0] > lastupdate:
                curs.execute("insert into candles values (?, ?, ?, ?, ?, ?, ?)", (candle[0], candle[0], candle[2], candle[3], candle[1], candle[4], candle[5]))

    db.commit()
    curs.close()

    return data

def createOrder(direction, price, amount, pair = 'BTCUSD_d', orderType = 'LimitOrder'):
    data={
        'symbol': pair, 
        'side':direction, 
        'price': price,
        'quoteOrderQty': amount,
        'type': orderType
    }

    request = requests.Request(
        'POST', 
        API_URL + 'api/v1/order',
        data=data,
        auth=AUTH
    )
    prepped = request.prepare()
    signature = hmac.new(config['API']['SECRET_KEY'], prepped.body, digestmod=hashlib.sha512)
    prepped.headers['Sign'] = signature.hexdigest()

    with requests.Session() as session:
        response = session.send(prepped)

    return response

def cancelOrder(uuid, pair = 'BTCUSD_d'):
    data={
        'symbol': pair, 
        'orderId':uuid
    }

    request = requests.Request(
        'DELETE', 
        API_URL + 'api/v1/order',
        data=data,
        auth=AUTH
    )
    prepped = request.prepare()
    signature = hmac.new(config['API']['SECRET_KEY'], prepped.body, digestmod=hashlib.sha512)
    prepped.headers['Sign'] = signature.hexdigest()

    with requests.Session() as session:
        response = session.send(prepped)

    return response


if __name__ == '__main__':
    # initDB()
    # prettyPrintArray(getAllPairs())
    # print(formatDollar(getDepth(direction='bids')))
    # print(getOrderBook())
    # refreshDataCandle()


    exit(0)
    