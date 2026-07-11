"""Credential database operations backed by DuckDB.

Shoonya-fy26.py is the session key capture script — do NOT edit.
It uses its own DB_PATH = os.path.join(__file__ dir, "auth.duckdb").
A symlink auth/auth.duckdb -> auth/ganah.duckdb resolves the difference.
"""

import os
import duckdb
import pandas as pd

_GANAH_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(_GANAH_DIR, "auth", "ganah.duckdb")


def _resolve(db_path=None):
    return db_path or DEFAULT_DB_PATH


def get_connection(db_path=None):
    conn = duckdb.connect(_resolve(db_path))
    conn.execute("SET timezone = 'Asia/Kolkata'")
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS authsession_id_seq START 1;
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS authsession (
            id INTEGER PRIMARY KEY DEFAULT nextval('authsession_id_seq'),
            brokername VARCHAR(50) NOT NULL,
            username VARCHAR(50) NOT NULL,
            pwd VARCHAR(255),
            factor2 VARCHAR(255),
            vc VARCHAR(100),
            apikey VARCHAR(255),
            secretkey VARCHAR(255),
            imei VARCHAR(100),
            sessionkey VARCHAR(255),
            updateddatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(brokername, username)
        )
    """)
    try:
        conn.execute("ALTER TABLE authsession ADD COLUMN id INTEGER")
        conn.execute("ALTER TABLE authsession ALTER id SET DEFAULT nextval('authsession_id_seq')")
    except Exception:
        pass
    count = conn.execute("SELECT COUNT(*) FROM authsession").fetchone()[0]
    if count == 0:
        defaults = [
            ('SHOONYA', 'FA138862', 'to be set post deployment', 'M5K425EV3LKEA53H3RI7FE663364G76T',
             'FA138862_U', 'fc07277061a787a8c28c9b11c6f46336', '', 'to be set post deployment'),
            ('FLATTRADE', 'FZ08430', 'to be set post deployment', 'LTJA7EP327OW7XXK4B466367CM6453NJ',
             '', '77dc8a91bc2b4fc29c215efdccb5ae5d', '2025.4ae323cdd99a4f10b2af60905df264626da4ab1fd65d7b1d', ''),
            ('FLATTRADE', 'FZ09213', 'to be set post deployment', '5R5J4PK6NB3SOAC335DUW2OTADK4Y5IS',
             '', '102f58f241a84c9a8d35686c61afd341', '2025.4505ab11ecd5496e9af00046241f2926aec2a09117cf70fe', ''),
            ('FLATTRADE', 'FZ08343', 'to be set post deployment', 'U4XBU3A6U33KJNLI7N3B2TUMV6OC2T62',
             '', '4579f39b71374bd7bf9cb48d924e9875', '2025.183f21f072084b26abd2c158b69800a0929a9f891ebc8dbd', ''),
        ]
        for row in defaults:
            conn.execute("""
                INSERT INTO authsession (brokername, username, pwd, factor2, vc, apikey, secretkey, imei)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, row)
        print(f"[ganah] Seeded {len(defaults)} default credential(s) into DuckDB")
    conn.close()


def read_credentials(brokername, username, db_path=None):
    conn = get_connection(db_path)
    df = conn.execute("""
        SELECT brokername, username, pwd, factor2, vc, apikey, secretkey, imei, sessionkey
        FROM authsession
        WHERE brokername = ? AND username = ?
    """, [brokername, username]).fetchdf()
    conn.close()
    return df


def update_session_key(brokername, username, sessionkey, db_path=None):
    conn = get_connection(db_path)
    conn.execute("""
        UPDATE authsession
        SET sessionkey = ?, updateddatetime = CURRENT_TIMESTAMP
        WHERE brokername = ? AND username = ?
    """, [sessionkey, brokername, username])
    conn.commit()
    conn.close()


def update_credentials(brokername, username, pwd=None, factor2=None, db_path=None):
    conn = get_connection(db_path)
    sets = []
    params = []
    if pwd is not None:
        sets.append("pwd = ?")
        params.append(pwd)
    if factor2 is not None:
        sets.append("factor2 = ?")
        params.append(factor2)
    if not sets:
        conn.close()
        return
    sets.append("updateddatetime = CURRENT_TIMESTAMP")
    params.extend([brokername, username])
    conn.execute(f"""
        UPDATE authsession
        SET {', '.join(sets)}
        WHERE brokername = ? AND username = ?
    """, params)
    conn.commit()
    conn.close()


def get_all_credentials(db_path=None):
    conn = get_connection(db_path)
    has_id = False
    try:
        conn.execute("SELECT id FROM authsession LIMIT 0")
        has_id = True
    except Exception:
        pass
    id_expr = "id" if has_id else "row_number() OVER () as id"
    rows = conn.execute(f"""
        SELECT {id_expr}, brokername, username, pwd, factor2, vc, apikey, secretkey, imei,
               CASE WHEN sessionkey IS NOT NULL AND sessionkey != '' THEN '***' ELSE '' END as has_session,
               updateddatetime::VARCHAR as updateddatetime
        FROM authsession
        ORDER BY brokername, username
    """).fetchall()
    conn.close()
    cols = ['id', 'brokername', 'username', 'pwd', 'factor2', 'vc', 'apikey', 'secretkey', 'imei',
            'has_session', 'updateddatetime']
    return pd.DataFrame(rows, columns=cols)


if __name__ == "__main__":
    init_db()
    print(f"[ganah] DuckDB auth database initialized at: {DEFAULT_DB_PATH}")
