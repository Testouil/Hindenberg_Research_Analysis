from flask import Flask, render_template, request
import yfinance
import pandas as pd
from datetime import timedelta
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredText
from matplotlib.figure import Figure
from io import BytesIO
import base64
import numpy as np

app = Flask(__name__)

#read from excel file
data = pd.read_excel(r'C:\Users\User\Desktop\20240504_h&r_ticker.xlsx', engine='openpyxl')
data['date_published'] = pd.to_datetime(data['date_published'])

#store the columns in excel file
ticker = data['ticker']
date_published = data['date_published']


#function to get stock data
def get_stock_data(ticker, date):
    start_date = date - timedelta(days=365)
    end_date = date + timedelta(days=365)
    price = yfinance.download(ticker, start=start_date, end=end_date)
    return price

stock_data = {}

#function to compute the statistics
def compute_statistics(data, event_date):
    pre_event_data = data.loc[:event_date]
    post_event_data = data.loc[event_date:]

    stats = {
        'pre_event_mean_return': pre_event_data['Close'].pct_change().mean(),
        'post_event_mean_return': post_event_data['Close'].pct_change().mean(),
        'pre_event_volatility': pre_event_data['Close'].pct_change().std(),
        'post_event_volatility': post_event_data['Close'].pct_change().std()
    }

    stats = {key: f"{value * 100: .2f}%" for key, value in stats.items()}
    return stats

#function to plot the data
def plot_stock_data(ticker, data, date):
    fig = Figure(figsize=(12, 6))
    axis = fig.add_subplot(1, 1, 1)
    axis.plot(data['Close'], label = 'Close Price')
    axis.axvline(x=date, color='r', linestyle='--', label='Event Date')
    axis.set_title(f"Stock Prices for {ticker}")
    axis.set_xlabel("Date")
    axis.set_ylabel("Stock Price")
    axis.legend()

    #convert plot into png image
    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    image_png = buf.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buf.close()
    return graph

def calculate_expected_return(data, event_date, ticker):
    if event_date in data.index:
        initial_price = data.loc[event_date, 'Close']
        final_price = data.iloc[-1]['Close']
        if pd.notna(initial_price) and pd.notna(final_price):
            return_percent = ((final_price / initial_price) - 1) * 100
            return f"Expected return of {ticker} : {return_percent:.2f}%"
    return "Data not available for {ticker}"

@app.route('/')
def index():
    # Pass tickers and dates to the template
    tickers_and_dates = data[['ticker', 'date_published']].to_dict(orient='records')
    return render_template('index.html', tickers_and_dates=tickers_and_dates)

@app.route('/analysis/<ticker>/<date>')
def analysis(ticker, date):
    date = pd.to_datetime(date)
    stock_data = get_stock_data(ticker, date)
    if not stock_data.empty:
        graph = plot_stock_data(ticker, stock_data, date)
        stats = compute_statistics(stock_data, date)
        expected_return = calculate_expected_return(stock_data, date, ticker)
        return render_template('analysis.html', graph=graph, stats=stats, expected_return=expected_return)
    else:
        return f"No data available for {ticker} on {date.strftime('%Y-%m-%d')}."

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')


