import psycopg2
import os

# Your PostgreSQL database connection details
DB_NAME = "attendance_db"
DB_USER = "your_username"
DB_PASS = "your_password"
DB_HOST = "localhost"

def reset_db():
    conn = None
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cursor = conn.cursor()
        print("[INFO] PostgreSQL database connection successful.")

        cursor.execute("DROP TABLE IF EXISTS attendance CASCADE")
        cursor.execute("DROP TABLE IF EXISTS faces CASCADE")
        print("[INFO] Dropped existing tables.")

        cursor.execute('''
            CREATE TABLE faces (
                reg_no TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                embedding BYTEA NOT NULL
            )
        ''')
        print("[SUCCESS] 'faces' table created successfully.")

        cursor.execute('''
            CREATE TABLE attendance (
                id SERIAL PRIMARY KEY,
                reg_no TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL, 
                time TEXT NOT NULL,
                date TEXT NOT NULL,
                mode TEXT NOT NULL 
            )
        ''')
        print("[SUCCESS] 'attendance' table created successfully with 'mode' column.")

        conn.commit()
        print("[INFO] Changes committed to the database.")

    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("[INFO] Database connection closed.")

if __name__ == '__main__':
    reset_db()