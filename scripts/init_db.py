"""Initialize the ganah auth database with schema and default credentials.

Usage:
    python scripts/init_db.py [path/to/auth.duckdb]
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ganah.db import init_db, DEFAULT_DB_PATH

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB_PATH
    init_db(db_path=db_path)
    print(f"Initialized auth DB at: {db_path}")
