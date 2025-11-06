import re
import sqlite3
from pathlib import Path

# your database file name
db_file = "data.db"

# your .sql file
sql_file = "GenevaAuto.sql"


def mysql_to_sqlite(sql_text: str) -> str:
    """Very small MySQL -> SQLite preprocessor.

    - Removes/ignores MySQL-specific commands (SET, LOCK, UNLOCK, /*! ... */ hints).
    - Strips schema qualifiers like `csc206cars`.
    - Replaces backticks with nothing.
    - Converts simple MySQL types to SQLite types (int/varchar/decimal/enum -> INTEGER/TEXT/REAL/TEXT).
    - Removes ENGINE=... table options.
    - Removes KEY/UNIQUE KEY lines (they are optional for this import).

    This is intentionally conservative: it aims to make the dump runnable in SQLite for the
    tables and INSERTs present in your file. It is not a full SQL translator.
    """

    s = sql_text

    # Remove MySQL-specific SET statements and SQL mode comments
    s = re.sub(r"(?m)^SET .*?;\s*", "", s)
    s = re.sub(r"/\*!.*?\*/;?", "", s, flags=re.S)

    # Remove LOCK/UNLOCK/BEGIN/COMMIT lines which are not needed
    s = re.sub(r"(?m)^(LOCK TABLES .*?;)|^(UNLOCK TABLES;)|^(BEGIN;)|^(COMMIT;)", "", s)

    # Remove schema qualifiers like `csc206cars`.
    s = s.replace('`csc206cars`.', '')
    s = s.replace('csc206cars.', '')

    # Remove backticks
    s = s.replace('`', '')

    # Remove ENGINE and DEFAULT CHARSET table options at end of CREATE TABLE
    s = re.sub(r"\)\s*ENGINE=.*?;", ");", s, flags=re.S)
    s = re.sub(r"\)\s*AUTO_INCREMENT=\d+\s*DEFAULT CHARSET=.*?;", ");", s, flags=re.S)

    # Convert common types
    s = re.sub(r"\bint\(\d+\)\b", "INTEGER", s, flags=re.I)
    s = re.sub(r"\bdecimal\([^)]*\)", "REAL", s, flags=re.I)
    s = re.sub(r"\bvarchar\([^)]*\)", "TEXT", s, flags=re.I)
    s = re.sub(r"\bchar\([^)]*\)", "TEXT", s, flags=re.I)
    s = re.sub(r"\bdate\b", "TEXT", s, flags=re.I)
    s = re.sub(r"\benum\([^)]*\)", "TEXT", s, flags=re.I)

    # Remove AUTO_INCREMENT tokens in column definitions
    s = re.sub(r"\bAUTO_INCREMENT\b", "", s, flags=re.I)

    # Remove KEY / UNIQUE KEY / CONSTRAINT ... FOREIGN KEY lines to avoid sqlite differences
    # These often end with a comma inside CREATE TABLE; remove the whole line.
    s = re.sub(r"(?m)^[ \t]*(UNIQUE KEY|KEY|CONSTRAINT)[^\n]*[,;]?\s*$", "", s)

    # Remove table-specific index lines like PRIMARY KEY (...) on its own line is OK — keep them.

    # Some MySQL INSERTs use fully-qualified table names; we've already stripped schema.

    # Fix trailing commas before closing parens in CREATE TABLE blocks which cause
    # sqlite to error with "near ")": syntax error". This replaces patterns like
    # "...,\n);" or ", );" with ")".
    s = re.sub(r",\s*\)\s*;", ") ;", s)
    # Also handle cases where a trailing comma is followed immediately by a newline and closing paren
    s = re.sub(r",\s*\)\s*\n", ")\n", s)

    # Normalize any accidental ") ;" spacing introduced above
    s = s.replace(") ;", ");")

    return s


def run_import(db_path: str, sql_path: str):
    p = Path(sql_path)
    if not p.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")

    text = p.read_text(encoding='utf-8')
    fixed = mysql_to_sqlite(text)

    # write out a temporary cleaned SQL to inspect if needed
    (Path(".") / "_cleaned_sql_for_sqlite.sql").write_text(fixed, encoding='utf-8')

    conn = sqlite3.connect(db_path)
    try:
        # enable foreign keys
        conn.execute('PRAGMA foreign_keys = ON;')
        conn.executescript(fixed)
        conn.commit()
    finally:
        conn.close()


if __name__ == '__main__':
    print(f"Importing SQL from {sql_file} into {db_file} (preprocessing MySQL -> SQLite)...")
    run_import(db_file, sql_file)
    print(f"✅ Import finished. Cleaned SQL written to _cleaned_sql_for_sqlite.sql and DB: {db_file}")

