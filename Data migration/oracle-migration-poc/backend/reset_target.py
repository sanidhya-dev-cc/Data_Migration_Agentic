r"""
Empty the TARGET database (drops every table owned by the target user).
The source database is never touched.

Usage (from the backend folder):
    .\.venv\Scripts\python.exe reset_target.py
"""

import oracledb
from dotenv import load_dotenv

from db import target_config

load_dotenv()

cfg = target_config()
conn = cfg.connect()
cur = conn.cursor()

tables = [t for (t,) in cur.execute("SELECT table_name FROM user_tables").fetchall()]
for t in tables:
    cur.execute(f'DROP TABLE "{t}" CASCADE CONSTRAINTS PURGE')
    print(f"Dropped {t}")

remaining = cur.execute("SELECT COUNT(*) FROM user_tables").fetchone()[0]
conn.close()
print(f"Target {cfg.dsn} emptied: {len(tables)} table(s) dropped, {remaining} remaining.")
