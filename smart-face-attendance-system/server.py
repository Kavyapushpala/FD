from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import torch
import psycopg2
from facenet_pytorch import MTCNN, InceptionResnetV1
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
from PIL import Image
import io

# Your PostgreSQL database connection details
DB_NAME = "attendance_db"
DB_USER = "your_username"
DB_PASS = "your_password"
DB_HOST = "localhost"

# --- MODEL AND DEVICE INITIALIZATION ---
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
mtcnn = MTCNN(image_size=160, margin=0, min_face_size=20, device=device, keep_all=False)
model = InceptionResnetV1(pretrained='vggface2').eval().to(device)

# --- FLASK APP SETUP ---
app = Flask(__name__)
CORS(app)

# --- DATABASE HELPER FUNCTION ---
def load_known_embeddings_pg():
    conn = None
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cursor = conn.cursor()
        cursor.execute("SELECT name, reg_no, embedding FROM faces")
        data = cursor.fetchall()
        
        known_embeddings, known_names, known_regs = [], [], []
        for name, reg_no, embedding_bytes in data:
            embedding = np.frombuffer(embedding_bytes, dtype=np.float32).reshape(1, -1)
            known_embeddings.append(embedding)
            known_names.append(name)
            known_regs.append(reg_no)
        
        if not known_embeddings:
            return np.array([]), [], []
        return np.vstack(known_embeddings), known_names, known_regs

    except Exception as e:
        print(f"[ERROR] Database connection failed or table does not exist: {e}")
        return np.array([]), [], []
    finally:
        if conn:
            conn.close()

known_embeddings, known_names, known_regs = load_known_embeddings_pg()

# --- CORE LOGIC FUNCTIONS ---
def process_face_and_return_data(image_file):
    try:
        img_bytes = image_file.read()
        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        boxes, _ = mtcnn.detect(img)
        if boxes is None:
            return {"name": "No face detected", "reg_no": "N/A", "box_color": "red"}
        
        face_tensor = mtcnn(img)
        if face_tensor is None:
            return {"name": "Face tensor not created", "reg_no": "N/A", "box_color": "red"}
        
        face_embedding = model(face_tensor.unsqueeze(0).to(device)).detach().cpu().numpy()
        
        if known_embeddings.shape[0] > 0:
            similarities = cosine_similarity(face_embedding, known_embeddings)[0]
            best_match_idx = np.argmax(similarities)
            if similarities[best_match_idx] > 0.7:
                return {
                    "name": known_names[best_match_idx],
                    "reg_no": known_regs[best_match_idx],
                    "box_color": "green",
                    "box_coords": boxes[0] 
                }
        return {"name": "Unknown", "reg_no": "N/A", "box_color": "red"}
    except Exception as e:
        print(f"[ERROR] Error processing image: {e}")
        return None

def handle_attendance(endpoint, image_file, reg_no_from_student=None):
    conn = None
    try:
        data = process_face_and_return_data(image_file)
        if data is None or data['box_color'] == 'red':
            return {"message": "Face not recognized.", "recognized_id": "N/A", "box_color": 'red', "success": False}

        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cursor = conn.cursor()
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        message = ""
        
        # Online mode requires a match with the provided reg_no
        if endpoint == '/mark_online':
            if data['reg_no'] != reg_no_from_student:
                return {"message": "Face does not match the provided registration number.", "success": False, "box_color": 'red'}
            
            # Check for existing online attendance for the day
            cursor.execute("SELECT id FROM attendance WHERE reg_no = %s AND date = %s AND mode = 'online'", (reg_no_from_student, date_str))
            if cursor.fetchone():
                message = f"Attendance re-verified for {data['name']}."
            else:
                cursor.execute("INSERT INTO attendance (reg_no, name, type, time, date, mode) VALUES (%s, %s, %s, %s, %s, %s)",
                               (reg_no_from_student, data['name'], 'present', time_str, date_str, 'online'))
                conn.commit()
                message = f"Attendance marked for {data['name']}."
        else: # /mark_in or /mark_out (Offline mode)
            cursor.execute("SELECT type FROM attendance WHERE reg_no = %s AND date = %s AND mode = 'offline' ORDER BY id DESC LIMIT 1", (data['reg_no'], date_str))
            last_record = cursor.fetchone()
            last_state = last_record[0] if last_record else None
            
            if endpoint == '/mark_in':
                if not last_state or last_state == 'out':
                    cursor.execute("INSERT INTO attendance (reg_no, name, type, time, date, mode) VALUES (%s, %s, %s, %s, %s, %s)",
                                 (data['reg_no'], data['name'], 'in', time_str, date_str, 'offline'))
                    message = f"IN attendance marked for {data['name']}."
                else:
                    message = f"{data['name']} is already checked IN."
                    data['box_color'] = 'orange'
            elif endpoint == '/mark_out':
                if last_state == 'in':
                    cursor.execute("INSERT INTO attendance (reg_no, name, type, time, date, mode) VALUES (%s, %s, %s, %s, %s, %s)",
                                 (data['reg_no'], data['name'], 'out', time_str, date_str, 'offline'))
                    message = f"OUT attendance marked for {data['name']}."
                else:
                    message = f"{data['name']} needs to check IN first."
                    data['box_color'] = 'orange'
            
        conn.commit()
        return {"message": message, "recognized_id": f"{data['name']} ({data['reg_no']})", "box_color": data['box_color'], "success": True}
    except Exception as e:
        print(f"[ERROR] An error occurred in handle_attendance: {e}")
        if conn:
            conn.rollback()
        return {"message": f"Server error: {e}", "success": False, "box_color": "red"}
    finally:
        if conn:
            conn.close()

# --- API ENDPOINTS ---
@app.route('/mark_in', methods=['POST'])
def mark_in():
    if 'image' not in request.files: return jsonify({"message": "No image file provided.", "success": False}), 400
    result = handle_attendance('/mark_in', request.files['image'])
    return jsonify(result)

@app.route('/mark_out', methods=['POST'])
def mark_out():
    if 'image' not in request.files: return jsonify({"message": "No image file provided.", "success": False}), 400
    result = handle_attendance('/mark_out', request.files['image'])
    return jsonify(result)

@app.route('/mark_online', methods=['POST'])
def mark_online():
    if 'image' not in request.files or 'reg_no' not in request.form:
        return jsonify({"message": "Missing image or registration number.", "success": False}), 400
    result = handle_attendance('/mark_online', request.files['image'], request.form['reg_no'])
    return jsonify(result)

@app.route('/get_history/<reg_no>', methods=['GET'])
def get_history(reg_no):
    conn = None
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cursor = conn.cursor()
        cursor.execute("SELECT reg_no, name, type, time, date, mode FROM attendance WHERE reg_no = %s ORDER BY date DESC, time DESC", (reg_no,))
        records = cursor.fetchall()
        
        # Convert fetched records to a list of dictionaries for JSON
        history = []
        for record in records:
            history.append({
                "reg_no": record[0],
                "name": record[1],
                "type": record[2],
                "time": record[3],
                "date": record[4],
                "mode": record[5]
            })
        
        return jsonify(history)
    except Exception as e:
        print(f"[ERROR] Error fetching history: {e}")
        return jsonify({"message": "Error fetching history.", "success": False}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)