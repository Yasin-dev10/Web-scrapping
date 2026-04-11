from sqlalchemy import create_engine, text
from datetime import datetime

# Direct Supabase URL (SQLAlchemy compatible)
DB_URL = "postgresql://postgres:Yaasiin2026@db.pqxesutzhsufqpmazuqg.supabase.co:5432/postgres"

# Create a connection engine
engine = create_engine(DB_URL)

def get_connection():
    # Return SQLAlchemy connection which Pandas supports natively
    return engine.connect()

def init_db():
    conn = get_connection()
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            url TEXT,
            text TEXT,
            category TEXT,
            source TEXT,
            scraped_at TIMESTAMP
        )
    """))
    conn.commit()
    conn.close()

def insert_post(url, text_content, category, source):
    # Difaac (Safety checks for NaN or invalid data types from Pandas)
    if str(url).lower() == 'nan': url = ''
    if str(text_content).lower() == 'nan': text_content = ''
    if str(category).lower() == 'nan': category = 'None'
    
    conn = get_connection()
    conn.execute(text("""
        INSERT INTO posts (url, text, category, source, scraped_at)
        VALUES (:u, :t, :c, :s, :time)
    """), {
        "u": str(url),
        "t": str(text_content),
        "c": str(category),
        "s": str(source),
        "time": datetime.now()
    })
    conn.commit()
    conn.close()
