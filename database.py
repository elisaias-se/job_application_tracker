"""Request-scoped MySQL connections; every value uses bound parameters."""
import mysql.connector
from flask import current_app, g

def get_db():
    if "db" not in g:
        c = current_app.config
        g.db = mysql.connector.connect(host=c['DB_HOST'], port=c['DB_PORT'],
            user=c['DB_USER'], password=c['DB_PASSWORD'], database=c['DB_NAME'])
    return g.db

def query(sql, params=(), *, write=False):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        if write:
            db.commit()
            return cursor.lastrowid
        return cursor.fetchall()
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()

def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
