import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def init_db():
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()
    sql_file = os.path.join(os.path.dirname(__file__), 'setup_tables.sql')
    with open(sql_file, 'r') as f:
        cur.execute(f.read())
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database berhasil diinisialisasi.")

if __name__ == "__main__":
    init_db()
