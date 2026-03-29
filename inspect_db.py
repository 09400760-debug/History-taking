import sqlite3

DB_PATH = "progress.db"   # change this if your database file has a different name

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("\nTABLES:\n")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

for table in tables:
    table_name = table[0]
    print(f"Table: {table_name}")
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    for col in columns:
        print(f"   {col}")
    print()

conn.close()
