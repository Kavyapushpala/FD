import psycopg2

# Your PostgreSQL database connection details
DB_NAME = "attendance_db"
DB_USER = "your_username"
DB_PASS = "your_password"
DB_HOST = "localhost"

def delete_face():
    conn = None
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cursor = conn.cursor()

        reg_no = input("Enter the registration number of the student to delete: ")

        cursor.execute("SELECT * FROM faces WHERE reg_no = %s", (reg_no,))
        student = cursor.fetchone()

        if student:
            print(f"[INFO] Found student: Reg No = {student[0]}, Name = {student[1]}")
            confirm = input("Are you sure you want to delete this student? (y/n): ").strip().lower()
            if confirm == 'y':
                cursor.execute("DELETE FROM faces WHERE reg_no = %s", (reg_no,))
                conn.commit()
                print(f"[✅ SUCCESS] Student with Reg No {reg_no} deleted successfully.")
            else:
                print("[INFO] Deletion cancelled.")
        else:
            print("[❌ ERROR] No student found with that registration number.")

    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    delete_face()