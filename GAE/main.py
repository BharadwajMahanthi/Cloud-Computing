#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify
import math
import logging
import random
import json
import yfinance as yf
import os
import pandas as pd
from datetime import date, timedelta
from pandas_datareader import data as pdr

app = Flask(__name__)


@app.route('/')
@app.route('/index.htm')
def index():
    return render_template('index.htm')


def doRender(tname, values={}):
    if not os.path.isfile(os.path.join(os.getcwd(), 'templates/' + tname)):  # No such file
        return render_template('index.htm')
    return render_template(tname, **values)


# override yfinance with pandas – seems to be a common step
yf.pdr_override()

# Get stock data from Yahoo Finance – here, asking for about 10 years of Amazon
today = date.today()
decadeAgo = today - timedelta(days=3652)

data = pdr.get_data_yahoo('NFLX', start=decadeAgo, end=today)
# Other symbols: CSCO – Cisco, NFLX – Netflix, INTC – Intel, TSLA - Tesla


# Add two columns to this to allow for Buy and Sell signals
# fill with zero
data['Buy'] = 0
data['Sell'] = 0

# Find the 4 different types of signals – uncomment print statements
# if you want to look at the data these pick out in some another way
for i in range(len(data)):
    # Hammer
    realbody = math.fabs(data.Open[i] - data.Close[i])
    bodyprojection = 0.1 * math.fabs(data.Close[i] - data.Open[i])

    if data.High[i] >= data.Close[i] and data.High[i] - bodyprojection <= data.Close[i] and data.Close[i] > data.Open[
        i] and data.Open[i] > data.Low[i] and data.Open[i] - data.Low[i] > realbody:
        data.at[data.index[i], 'Buy'] = 1
        # print("H", data.Open[i], data.High[i], data.Low[i], data.Close[i])

    # Inverted Hammer
    if data.High[i] > data.Close[i] and data.High[i] - data.Close[i] > realbody and data.Close[i] > data.Open[i] and \
            data.Open[i] >= data.Low[i] and data.Open[i] <= data.Low[i] + bodyprojection:
        data.at[data.index[i], 'Buy'] = 1
        # print("I", data.Open[i], data.High[i], data.Low[i], data.Close[i])

    # Hanging Man
    if data.High[i] >= data.Open[i] and data.High[i] - bodyprojection <= data.Open[i] and data.Open[i] > data.Close[
        i] and data.Close[i] > data.Low[i] and data.Close[i] - data.Low[i] > realbody:
        data.at[data.index[i], 'Sell'] = 1
        # print("M", data.Open[i], data.High[i], data.Low[i], data.Close[i])

    # Shooting Star
    if data.High[i] > data.Open[i] and data.High[i] - data.Open[i] > realbody and data.Open[i] > data.Close[i] and \
            data.Close[i] >= data.Low[i] and data.Close[i] <= data.Low[i] + bodyprojection:
        data.at[data.index[i], 'Sell'] = 1
        # print("S", data.Open[i], data.High[i], data.Low[i], data.Close[i])

# Data now contains signals, so we can pick signals with a minimum amount
# of historic data, and use shots for the amount of simulated values
# to be generated based on the mean and standard deviation of the recent history
minhistory = 100
shots = 1000000
global m
global n
global mn
global sh
mn = 0
sh = 0
m = []
n = []
global c, d
c = []
d = []
c.clear()
d.clear()
m.clear()
n.clear()
date_time = today.strftime("%m/%d/%Y")
# e = [date_time]
e = []


@app.route('/addnumber')
def calculate():
    # service = request.form['service']
    y = request.args.get('y', 0, type=int)
    z = request.args.get('z', 0, type=int)
    t = request.args.get('t', 0, type=int)
    mn = y
    c.append(mn)
    sh = z
    d.append(sh)
    print(c, d)

    def call():
        for i in range(mn):
            lis = values_return(mn, sh, t)
            # print(lis)
        return lis

    e.clear()
    x = date_time
    for i in range(mn):
        e.append(x)
    print(e)

    ca = call()
    json_string = json.dumps(ca)
    print(ca)
    return jsonify(result=json_string)


def values_return(minh, sho, ti):
    for i in range(minh, len(data)):
        if ti == 1:
            if data.Buy[i] == 1:
                mean = data.Close[i - minh:i].pct_change(1).mean()
                std = data.Close[i - minh:i].pct_change(1).std()
                # generate much larger random number series with same broad characteristics
                simulated = [random.gauss(mean, std) for x in range(sho)]
                # sort and pick 95% and 99%  - not distinguishing long/short here
                simulated.sort(reverse=True)
                var95 = simulated[int(len(simulated) * 0.95)]
                m.append(var95)
                var99 = simulated[int(len(simulated) * 0.99)]
                n.append(var99)
                # print(m, n, mn, sh, d)
                print(var95, var99)  # so you can see what is being produced

                def fun():
                    a = var95
                    b = var99
                    return [a, b];

                list1 = fun()
                return list1
        else:
            if data.Sell[i] == 1:
                mean = data.Close[i - minh:i].pct_change(1).mean()
                std = data.Close[i - minh:i].pct_change(1).std()
                # generate much larger random number series with same broad characteristics
                simulated = [random.gauss(mean, std) for x in range(sho)]
                # sort and pick 95% and 99%  - not distinguishing long/short here
                simulated.sort(reverse=True)
                var95 = simulated[int(len(simulated) * 0.95)]
                m.append(var95)
                var99 = simulated[int(len(simulated) * 0.99)]
                n.append(var99)
                # print(m, n, mn, sh, d)
                print(var95, var99)  # so you can see what is being produced

                def fun():
                    a = var95
                    b = var99
                    return [a, b];

                list2 = fun()
                return list2


@app.route('/chart', methods=['POST'])
def chart():
    ad = 0.0
    ad1 = 0.0
    for i in range(len(m)):
        ad = ad + m[i]
        ad1 = ad1 + n[i]
    print(len(m), len(n), len(e), c, d)
    return render_template('chart.htm', dates=e, list95=m, list99=n, vr95=ad/len(m), vr99=ad1/len(n), mn=c, sh=d)


@app.errorhandler(500)
# A small bit of error handling
def server_error(e):
    logging.exception('ERROR!')
    return """
    An  error occurred: <pre>{}</pre>
    """.format(e), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1",port=8080, debug=True)
