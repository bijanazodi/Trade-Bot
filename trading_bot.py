import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import scrolledtext
import yfinance as yf
import pandas as pd
import logging
from threading import Thread
import ssl
import urllib.request

logging.basicConfig(level=logging.INFO)

def calculate_indicators(data):
    data['SMA50'] = data['Close'].rolling(window=50).mean()
    data['SMA200'] = data['Close'].rolling(window=200).mean()
    data['MACD'] = data['Close'].ewm(span=12, adjust=False).mean() - data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['RSI'] = 100 - (100 / (1 + data['Close'].pct_change().add(1).cumprod().rolling(window=14).mean() / data['Close'].pct_change().add(1).cumprod().rolling(window=14).std()))
    return data

def fetch_sp500_symbols():
    logging.info("Fetching S&P 500 stock symbols...")
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        context = ssl._create_unverified_context()
        response = urllib.request.urlopen(url, context=context)
        tables = pd.read_html(response, header=0)
        table = tables[0]
        symbols = table['Symbol'].tolist()
        return symbols
    except Exception as e:
        logging.error(f"Error fetching S&P 500 symbols: {e}")
        return []

def stock_screener(text_area):
    logging.info("Starting stock screener...")
    symbols = fetch_sp500_symbols()
    if not symbols:
        symbols = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'TSLA', 'NVDA', 'JPM', 'JNJ', 'UNH', 'V', 'PG', 'HD', 'DIS', 'PYPL', 'MA', 'NFLX', 'VZ']
    
    viable_stocks = []

    for symbol in symbols:
        text_area.insert(tk.END, f"Fetching data for {symbol}... ")
        text_area.yview(tk.END)
        data = yf.download(symbol, period='1y', interval='1d')  # Fetch 1 year of data
        
        if data.empty:
            text_area.insert(tk.END, "❌\n")
            continue

        data = calculate_indicators(data)
        last_row = data.iloc[-1]

        if not pd.isna(last_row['SMA200']):
            # Appropriate strictness criteria
            if last_row['MACD'] > last_row['MACD_Signal'] and 30 < last_row['RSI'] < 70 and last_row['Close'] > last_row['SMA50'] and last_row['Close'] > last_row['SMA200']:
                viable_stocks.append((symbol, last_row['MACD'], last_row['SMA50'], last_row['SMA200'], last_row['RSI']))
                text_area.insert(tk.END, "✅\n")
            else:
                text_area.insert(tk.END, "❌\n")
        else:
            text_area.insert(tk.END, "❌\n")

    viable_stocks.sort(key=lambda x: x[1], reverse=True)  # Sort by MACD value, strongest first
    show_summary_screen(viable_stocks)
    logging.info(f"Screened symbols: {viable_stocks}")
    return viable_stocks

def show_summary_screen(stocks):
    summary_window = tk.Toplevel()
    summary_window.title("Stock Screener Summary")
    summary_window.geometry("600x400")

    summary_frame = ttk.Frame(summary_window, padding=10)
    summary_frame.pack(fill=tk.BOTH, expand=True)

    summary_label = ttk.Label(summary_frame, text="Strong Buy Signals", font=("Helvetica", 16, "bold"))
    summary_label.pack(pady=10)

    summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD, font=("Helvetica", 10), width=70, height=20)
    summary_text.pack(fill=tk.BOTH, expand=True)

    for stock in stocks:
        symbol, macd, sma50, sma200, rsi = stock
        summary_text.insert(tk.END, f"Symbol: {symbol}\n")
        summary_text.insert(tk.END, f"MACD: {macd:.2f}\n")
        summary_text.insert(tk.END, f"SMA50: {sma50:.2f}\n")
        summary_text.insert(tk.END, f"SMA200: {sma200:.2f}\n")
        summary_text.insert(tk.END, f"RSI: {rsi:.2f}\n")
        summary_text.insert(tk.END, "-"*40 + "\n")

    summary_text.config(state=tk.DISABLED)

def start_screener(text_area):
    Thread(target=stock_screener, args=(text_area,)).start()

def create_gui():
    root = tk.Tk()
    root.title("Stock Screener and Trading Bot")
    root.geometry("800x600")

    style = ttk.Style()
    style.configure("TLabel", font=("Helvetica", 12))
    style.configure("TButton", font=("Helvetica", 12))
    style.configure("TFrame", background="#F5F5F5")
    style.configure("TScrolledText", font=("Helvetica", 10), wrap=tk.WORD)

    header_frame = ttk.Frame(root, padding=10)
    header_frame.grid(row=0, column=0, sticky="ew")
    header_label = ttk.Label(header_frame, text="Stock Screener and Trading Bot", font=("Helvetica", 16, "bold"))
    header_label.pack()

    main_frame = ttk.Frame(root, padding=10)
    main_frame.grid(row=1, column=0, sticky="nsew")

    text_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=100, height=20, font=("Helvetica", 10))
    text_area.pack(padx=10, pady=10)

    start_button = ttk.Button(main_frame, text="Start Screener", command=lambda: start_screener(text_area))
    start_button.pack(pady=10)

    footer_frame = ttk.Frame(root, padding=10)
    footer_frame.grid(row=2, column=0, sticky="ew")
    footer_label = ttk.Label(footer_frame, text="Developed by YourName", font=("Helvetica", 10))
    footer_label.pack()

    root.columnconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
