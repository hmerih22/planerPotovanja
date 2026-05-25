import sqlite3
import os


def povezava():

    os.makedirs("database", exist_ok=True)

    conn = sqlite3.connect(
        "database/potovanja.db"
    )

    conn.row_factory = sqlite3.Row

    return conn


def ustvari_tabelo():

    conn = povezava()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS destinacije (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            ime TEXT,
            prevoz REAL,
            prehrana REAL,
            lokalni_prevoz REAL,
            aktivnosti REAL,
            prenocisce REAL

        )
    """)

    conn.commit()

    conn.close()


def pridobi_destinacije():

    conn = povezava()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM destinacije"
    )

    podatki = cursor.fetchall()

    conn.close()

    return podatki