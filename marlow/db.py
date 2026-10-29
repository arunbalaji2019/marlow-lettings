"""SQLite access."""
import decimal
import sqlite3
from pathlib import Path

from flask import current_app, g

MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"

SEED = [
    ("Bright 2-bed near Clapham Common", "London", "1850.00", 2),
    ("Studio flat, Leith", "Edinburgh", "925.50", 0),
    ("3-bed family house with garden", "Bristol", "1600.00", 3),
    ("1-bed canal-side flat", "Manchester", "1095.00", 1),
    ("Clapham 1-bed, 100% newly refurbished", "London", "1475.25", 1),
]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db(conn):
    for script in sorted(MIGRATIONS.glob("*.sql")):
        conn.executescript(script.read_text())
    if conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO listings (title, city, rent, bedrooms) VALUES (?, ?, ?, ?)",
            SEED,
        )
    conn.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db(get_db())


def to_listing(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "city": row["city"],
        "rent": decimal.Decimal(row["rent"]),
        "bedrooms": row["bedrooms"],
    }
