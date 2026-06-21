import os
import cv2
import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier

MODEL_PATH = "model.pkl"

# Try importing mediapipe with fallback
try:
    import mediapipe as mp
    mp_face_detection = mp.solutions.face_detection
    USE_MEDIAPIPE = True
except (ImportError, AttributeError):
    USE_MEDIAPIPE = False
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def extract_face_features(img):
    """Extract face features using MediaPipe or OpenCV"""
    if img is None:
        return None
    
    try:
        if USE_MEDIAPIPE:
            with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                results = face_detection.process(rgb)
                if not results.detections:
                    return None
                detection = results.detections[0]
                h, w = img.shape[:2]
                bbox = detection.location_data.relative_bounding_box
                x1 = int(max(0, bbox.xmin * w))
                y1 = int(max(0, bbox.ymin * h))
                x2 = int(min(w, (bbox.xmin + bbox.width) * w))
                y2 = int(min(h, (bbox.ymin + bbox.height) * h))
                if x2 <= x1 or y2 <= y1:
                    return None
                face = img[y1:y2, x1:x2]
                gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
                face = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA)
                emb = face.flatten().astype(np.float32) / 255.0
                return emb
        else:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            if len(faces) == 0:
                return None
            (x, y, w, h) = faces[0]
            face = gray[y:y+h, x:x+w]
            face = cv2.resize(face, (32, 32), interpolation=cv2.INTER_AREA)
            emb = face.flatten().astype(np.float32) / 255.0
            return emb
    except Exception as e:
        print(f"Feature extraction error: {e}")
        return None

def extract_embedding_for_image(stream_or_bytes):
    try:
        data = stream_or_bytes.read()
        arr = np.frombuffer(data, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return None
        return extract_face_features(img)
    except Exception as e:
        print(f"Embedding extraction error: {e}")
        return None

def load_model_if_exists():
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Model load error: {e}")
        return None

def predict_with_model(clf, emb):
    try:
        proba = clf.predict_proba([emb])[0]
        idx = np.argmax(proba)
        label = clf.classes_[idx]
        conf = float(proba[idx])
        return label, conf
    except Exception as e:
        print(f"Prediction error: {e}")
        return None, 0.0

def train_model_background(dataset_dir, progress_callback=None):
    X = []
    y = []
    
    student_dirs = [d for d in os.listdir(dataset_dir) 
                   if os.path.isdir(os.path.join(dataset_dir, d)) and d.isdigit()]
    
    if not student_dirs:
        if progress_callback:
            progress_callback(0, "No students found. Please add students first.")
        return
    
    total_students = len(student_dirs)
    processed = 0
    total_images = 0
    
    for sid in student_dirs:
        folder = os.path.join(dataset_dir, sid)
        files = [f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        for fn in files:
            path = os.path.join(folder, fn)
            img = cv2.imread(path)
            if img is None:
                continue
            emb = extract_face_features(img)
            if emb is None:
                continue
            X.append(emb)
            y.append(int(sid))
            total_images += 1
        
        processed += 1
        if progress_callback:
            pct = min(int((processed / total_students) * 80), 80)
            progress_callback(pct, f"Processing student {processed}/{total_students} ({total_images} faces)")

    if len(X) == 0:
        if progress_callback:
            progress_callback(0, "No valid face data found. Please capture faces properly.")
        return

    X = np.stack(X)
    y = np.array(y)
    
    if progress_callback:
        progress_callback(90, f"Training RandomForest with {len(X)} samples...")
    
    clf = RandomForestClassifier(n_estimators=150, n_jobs=-1, random_state=42)
    clf.fit(X, y)
    
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(clf, f)
    
    if progress_callback:
        progress_callback(100, f"✅ Training complete! Model saved with {len(X)} samples.")