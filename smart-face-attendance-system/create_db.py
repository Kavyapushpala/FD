import psycopg2
import os

# Your PostgreSQL database connection details
DB_NAME = "attendance_db"
DB_USER = "your_username"
DB_PASS = "your_password"
DB_HOST = "localhost"

def create_db_tables():
    conn = None
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cursor = conn.cursor()

        # Create 'faces' table to store student embeddings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS faces (
                reg_no TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                embedding BYTEA NOT NULL
            )
        ''')

        # Create 'attendance' table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                reg_no TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL, -- 'in', 'out', or 'present'
                time TEXT NOT NULL,
                date TEXT NOT NULL,
                mode TEXT NOT NULL -- 'offline' or 'online'
            )
        ''')
        
        conn.commit()
        print("[SUCCESS] PostgreSQL tables created successfully.")

    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    create_db_tables()