import sqlite3
from datetime import datetime

DB_NAME = "scraper_data.sqlite3"

def get_connection():
    # Allow multithreading/multiple connections
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    # Create the posts table to store scraped data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            text TEXT,
            category TEXT,
            source TEXT,
            scraped_at TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def insert_post(url, text, category, source):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO posts (url, text, category, source, scraped_at)
        VALUES (?, ?, ?, ?, ?)
    """, (url, text, category, source, datetime.now()))
    conn.commit()
    conn.close()
