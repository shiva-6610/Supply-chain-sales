import sqlite3
import pandas as pd

def init_db(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS supply_data (
            date TEXT,
            product_id TEXT,
            product_name TEXT,
            category TEXT,
            region TEXT,
            units_sold INTEGER,
            unit_price REAL,
            revenue REAL,
            competitor_price REAL,
            google_trend_score INTEGER,
            market_sentiment TEXT,
            stock_level INTEGER,
            lead_time_days INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def insert_data_from_csv(db_name, csv_path):
    df = pd.read_csv(csv_path)
    conn = sqlite3.connect(db_name)
    df.to_sql('supply_data', conn, if_exists='append', index=False)
    conn.close()
