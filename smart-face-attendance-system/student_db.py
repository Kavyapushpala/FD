import cv2
import torch
import psycopg2
import numpy as np
from facenet_pytorch import MTCNN, InceptionResnetV1
import os
import time

# Your PostgreSQL database connection details
DB_NAME = "attendance_db"
DB_USER = "postgres"
DB_PASS = "Kavya@2832"
DB_HOST = "localhost5432"

# --- INITIALIZATION ---
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
mtcnn = MTCNN(image_size=160, margin=0, min_face_size=20, device=device, keep_all=False)
model = InceptionResnetV1(pretrained='vggface2').eval().to(device)
SAMPLE_COUNT = 50

# --- MAIN FUNCTION ---
def register_new_face():
    conn = None
    try:
        name = input("Enter the person's name: ")
        reg_no = input("Enter the person's registration number: ")

        if not name or not reg_no:
            print("[ERROR] Name and registration number cannot be empty.")
            return

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[ERROR] Failed to open webcam.")
            return

        print("[INFO] Webcam opened. Please look at the camera and hold still.")
        
        embeddings_list = []
        while len(embeddings_list) < SAMPLE_COUNT:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Failed to capture frame.")
                break
            
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_tensor = mtcnn(img_rgb)
            
            if face_tensor is not None:
                embedding = model(face_tensor.unsqueeze(0).to(device)).detach().cpu().numpy()
                embeddings_list.append(embedding)
                print(f"[INFO] Sample {len(embeddings_list)}/{SAMPLE_COUNT} captured.")
                
            progress_text = f"Samples: {len(embeddings_list)} / {SAMPLE_COUNT}"
            cv2.putText(frame, progress_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "Hold still...", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow('Register Face', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[INFO] Registration cancelled by user.")
                return

        final_embedding = np.mean(embeddings_list, axis=0)
        
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cursor = conn.cursor()
        
        cursor.execute("INSERT INTO faces (name, reg_no, embedding) VALUES (%s, %s, %s) ON CONFLICT (reg_no) DO UPDATE SET name=EXCLUDED.name, embedding=EXCLUDED.embedding",
                        (name, reg_no, final_embedding.tobytes()))
        conn.commit()
        print(f"\n[SUCCESS] Face for {name} ({reg_no}) saved successfully!")

    except Exception as e:
        print(f"[ERROR] Could not save to database: {e}")
        if conn:
            conn.rollback()
    finally:
        if cap:
            cap.release()
        cv2.destroyAllWindows()
        if conn:
            conn.close()

if __name__ == '__main__':
    register_new_face()