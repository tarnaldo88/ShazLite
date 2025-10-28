import psycopg2

conn = psycopg2.connect(
    host='localhost', 
    port=5433, 
    database='audio_fingerprinting', 
    user='postgres', 
    password='audio_password_change_me'
)

cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
tables = cur.fetchall()
print('Existing tables:', [t[0] for t in tables])

# Check if we have any data
for table_name in [t[0] for t in tables]:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cur.fetchone()[0]
        print(f"Table '{table_name}': {count} rows")
    except Exception as e:
        print(f"Error querying {table_name}: {e}")

conn.close()