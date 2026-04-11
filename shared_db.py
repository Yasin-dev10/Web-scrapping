# -*- coding: utf-8 -*-
"""
shared_db.py — Wadaagga Database-ka (SQLite) ee dhammaan barnaamijyada
=======================================================================
Barnaamijkan wuxuu keydiyaa dhammaan xogta scraped-ka ah meel keliya (SQLite).
Kaddib waxaad si fudud ugu soo daagi kartaa CSV ahaan.
"""
import os
import sqlite3
from datetime import datetime

# Path-ka database-ka — waa bartilmaameedka
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "unified_scraper.db")


def _get_conn():
    """Soo celi xiriir database (thread-safe)."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Samee jadwalka posts hadduu jirin."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            url         TEXT,
            text        TEXT,
            category    TEXT,
            source      TEXT,
            scraped_at  TEXT
        )
    """)
    conn.commit()
    conn.close()


def insert_post(url: str, text_content: str, category: str, source: str):
    """Gali xog cusub database-ka."""
    url          = "" if str(url).lower()          == "nan" else str(url)
    text_content = "" if str(text_content).lower() == "nan" else str(text_content)
    category     = "None" if str(category).lower() == "nan" else str(category)
    source       = str(source)
    scraped_at   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = _get_conn()
    conn.execute("""
        INSERT INTO posts (url, text, category, source, scraped_at)
        VALUES (?, ?, ?, ?, ?)
    """, (url, text_content, category, source, scraped_at))
    conn.commit()
    conn.close()


def insert_many(rows: list, source: str):
    """
    Gali xog badan hal mar (faster).
    rows: list of dict with keys: url, text, category
    """
    scraped_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = [
        (
            "" if str(r.get("url","")).lower() == "nan" else str(r.get("url","")),
            "" if str(r.get("text","")).lower() == "nan" else str(r.get("text","")),
            "None" if str(r.get("category","")).lower() == "nan" else str(r.get("category","")),
            source,
            scraped_at
        )
        for r in rows
    ]
    conn = _get_conn()
    conn.executemany("""
        INSERT INTO posts (url, text, category, source, scraped_at)
        VALUES (?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()


def get_all_posts(limit=None):
    """Soo celi dhammaan posts-ka (ama tirada la rabo)."""
    conn = _get_conn()
    if limit:
        rows = conn.execute("SELECT * FROM posts ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_posts_by_source(source: str):
    """Soo celi posts-ka source gaar ah."""
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM posts WHERE source=? ORDER BY id DESC", (source,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_posts_by_category(category: str):
    """Soo celi posts-ka category gaar ah."""
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM posts WHERE category=? ORDER BY id DESC", (category,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats():
    """Soo celi tirakoobka database-ka."""
    conn = _get_conn()
    total   = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    crime   = conn.execute("SELECT COUNT(*) FROM posts WHERE category='crime-related'").fetchone()[0]
    not_cr  = conn.execute("SELECT COUNT(*) FROM posts WHERE category='not crime-related'").fetchone()[0]
    sources = conn.execute("SELECT source, COUNT(*) as cnt FROM posts GROUP BY source").fetchall()
    conn.close()
    return {
        "total":     total,
        "crime":     crime,
        "not_crime": not_cr,
        "sources":   {r[0]: r[1] for r in sources}
    }


def clear_all():
    """Tirtir dhammaan xogta database-ka."""
    conn = _get_conn()
    conn.execute("DELETE FROM posts")
    conn.commit()
    conn.close()


def export_to_csv(output_path: str, category_filter: str = None, source_filter: str = None) -> int:
    """
    Soo daji xogta CSV ahaan.
    Returns: tirada rows-ka la keydiyey
    """
    import pandas as pd
    conn = _get_conn()
    
    query = "SELECT url, text, category, source, scraped_at FROM posts WHERE 1=1"
    params = []
    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)
    if source_filter:
        query += " AND source = ?"
        params.append(source_filter)
    
    import pandas as pd
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return len(df)


# Auto-init marka la import-gareysto
init_db()
