import sqlite3
import pandas as pd

def load_trades():

    conn = sqlite3.connect("trading_data.db")

    df = pd.read_sql("SELECT * FROM trades", conn)

    conn.close()

    return df