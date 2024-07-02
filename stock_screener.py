import yfinance as yf
import pandas as pd
import logging

def print_alert(message):
    print(f"ALERT: {message}")

def calculate_indicators(data):
    data['SMA50'] = data['Close'].rolling(window=50).mean()
    data['SMA200'] = data['Close'].rolling(window=200).mean()
    data['MACD'] = data['Close'].ewm(span=12, adjust=False).mean() - data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['RSI'] = 100 - (100 / (1 + data['Close'].pct_change().add(1).cumprod().rolling(window=14).mean() / data['Close'].pct_change().add(1).cumprod().rolling(window=14).std()))
    return data

def fetch_all_symbols():
    logging.info("Fetching all stock symbols from NASDAQ...")
    try:
        nasdaq_url = "https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=1000&exchange=NASDAQ"
        data = pd.read_json(nasdaq_url)
        symbols = data['data']['table']['rows']['symbol'].tolist()
        return symbols
    except Exception as e:
        logging.error(f"Error fetching stock symbols: {e}")
        return []

def stock_screener():
    logging.info("Starting stock screener...")
    symbols = fetch_all_symbols()
    if not symbols:
        symbols = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'TSLA', 'NVDA', 'JPM', 'JNJ', 'UNH', 'V', 'PG', 'HD', 'DIS', 'PYPL', 'MA', 'NFLX', 'VZ']
        
    viable_stocks = []

    for symbol in symbols:
        logging.info(f"Fetching data for {symbol}...")
        data = yf.download(symbol, period='1y', interval='1d')  # Fetch 1 year of data
        
        if data.empty:
            logging.warning(f"No data found for {symbol}")
            continue

        data = calculate_indicators(data)
        last_row = data.iloc[-1]

        logging.info(f"{symbol} - MACD: {last_row['MACD']}, MACD Signal: {last_row['MACD_Signal']}, RSI: {last_row['RSI']}, SMA50: {last_row['SMA50']}, SMA200: {last_row['SMA200']}")

        if last_row['SMA200'] is not None and not pd.isna(last_row['SMA200']):
            if last_row['MACD'] > last_row['MACD_Signal'] and last_row['SMA50'] > last_row['SMA200']:
                viable_stocks.append(symbol)
                message = f"{symbol} is showing a strong buy signal.\nMACD: {last_row['MACD']}\nSMA50: {last_row['SMA50']}\nSMA200: {last_row['SMA200']}\nRSI: {last_row['RSI']}"
                print_alert(message)

    logging.info(f"Screened symbols: {viable_stocks}")
    return viable_stocks

if __name__ == "__main__":
    stock_screener()
