import sqlite3
import os

DB_PATH = "trading_data.db"


# =========================
# INIT DATABASE
# =========================

def init_db():

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS trades (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            time TEXT,

            signal TEXT,

            ai_signal TEXT,

            news_signal TEXT,

            structure_signal TEXT,

            liquidity_signal TEXT,

            fvg_signal TEXT,

            ob_signal TEXT,

            entry_price REAL,

            stop_loss REAL,

            take_profit REAL,

            lot REAL,

            result REAL

        )
    """)

    conn.commit()
    conn.close()


# =========================
# SAVE TRADE
# =========================

def save_trade(

    signal,
    ai_signal,
    news_signal,
    structure_signal,
    liquidity_signal,
    fvg_signal,
    ob_signal,
    entry_price,
    stop_loss,
    take_profit,
    lot,
    result

):

    init_db()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""

        INSERT INTO trades (

            time,
            signal,
            ai_signal,
            news_signal,
            structure_signal,
            liquidity_signal,
            fvg_signal,
            ob_signal,
            entry_price,
            stop_loss,
            take_profit,
            lot,
            result

        ) VALUES (datetime('now'),?,?,?,?,?,?,?,?,?,?,?,?)

    """, (

        signal,
        ai_signal,
        news_signal,
        structure_signal,
        liquidity_signal,
        fvg_signal,
        ob_signal,
        entry_price,
        stop_loss,
        take_profit,
        lot,
        result

    ))

    conn.commit()
    conn.close()