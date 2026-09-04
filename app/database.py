import sqlite3

DB_PATH = "data/app.db"


def get_connection():
    return sqlite3.connect(DB_PATH)