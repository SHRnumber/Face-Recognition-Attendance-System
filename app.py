import os
import io
import threading
import sqlite3
import datetime
import json
import shutil
from flask import Flask, render_template, request, jsonify, send_file, abort
from model import train_model_background, extract_embedding_for_image, MODEL_PATH

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "attendance.db")
DATASET_DIR = os.path.join(APP_DIR, "dataset")
os.makedirs(DATASET_DIR, exist_ok=True)

TRAIN_STATUS_FILE = os.path.join(APP_DIR, "train_status.json")

app = Flask(__name__, static_folder="static", template_folder="templates")

# ---------- DB helpers ----------
def init_db():
    """Initialize database with proper schema and handle migrations"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create students table
    c.execute("""CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    roll TEXT,
                    class TEXT,
                    section TEXT,
                    reg_no TEXT,
                    created_at TEXT
                )""")
    
    # Create attendance table with all columns
    c.execute("""CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    name TEXT,
                    timestamp TEXT,
                    type TEXT DEFAULT 'entry'
                )""")
    
    # Check if type column exists, add if missing (for existing databases)
    c.execute("PRAGMA table_info(attendance)")
    columns = [col[1] for col in c.fetchall()]
    if 'type' not in columns:
        app.logger.info("Adding 'type' column to attendance table")
        c.execute("ALTER TABLE attendance ADD COLUMN type TEXT DEFAULT 'entry'")
    
    # Check if session_id column exists, add if needed
    if 'session_id' not in columns:
        app.logger.info("Adding 'session_id' column to attendance table")
        c.execute("ALTER TABLE attendance ADD COLUMN session_id TEXT DEFAULT 'default'")
    
    conn.commit()
    conn.close()
    app.logger.info("Database initialized successfully")

# Initialize database
init_db()

# ---------- Train status helpers ----------
def write_train_status(status_dict):
    with open(TRAIN_STATUS_FILE, "w") as f:
        json.dump(status_dict, f)

def read_train_status():
    if not os.path.exists(TRAIN_STATUS_FILE):
        return {"running": False, "progress": 0, "message": "Not trained"}
    with open(TRAIN_STATUS_FILE, "r") as f:
        return json.load(f)

write_train_status({"running": False, "progress": 0, "message": "No training yet."})

# ---------- Routes ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/attendance_stats")
def attendance_stats():
    import pandas as pd
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT timestamp FROM attendance", conn)
        conn.close()
        
        if df.empty:
            from datetime import date, timedelta
            days = [(date.today() - timedelta(days=i)).strftime("%d-%b") for i in range(29, -1, -1)]
            return jsonify({"dates": days, "counts": [0]*30})
        
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        last_30 = [(datetime.date.today() - datetime.timedelta(days=i)) for i in range(29, -1, -1)]
        counts = [int(df[df['date'] == d].shape[0]) for d in last_30]
        dates = [d.strftime("%d-%b") for d in last_30]
        return jsonify({"dates": dates, "counts": counts})
    except Exception as e:
        app.logger.error(f"Stats error: {e}")
        return jsonify({"dates": [], "counts": []})

@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    if request.method == "GET":
        return render_template("add_student.html")
    
    data = request.form
    name = data.get("name", "").strip()
    roll = data.get("roll", "").strip()
    cls = data.get("class", "").strip()
    sec = data.get("sec", "").strip()
    reg_no = data.get("reg_no", "").strip()
    
    if not name:
        return jsonify({"error": "Name is required"}), 400
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.datetime.utcnow().isoformat()
    c.execute("""INSERT INTO students (name, roll, class, section, reg_no, created_at) 
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (name, roll, cls, sec, reg_no, now))
    sid = c.lastrowid
    conn.commit()
    conn.close()
    
    os.makedirs(os.path.join(DATASET_DIR, str(sid)), exist_ok=True)
    return jsonify({"student_id": sid})

@app.route("/upload_face", methods=["POST"])
def upload_face():
    student_id = request.form.get("student_id")
    if not student_id:
        return jsonify({"error": "student_id required"}), 400
    
    files = request.files.getlist("images[]")
    if not files:
        return jsonify({"error": "No images uploaded"}), 400
    
    saved = 0
    folder = os.path.join(DATASET_DIR, student_id)
    os.makedirs(folder, exist_ok=True)
    
    for f in files:
        if f.filename == '':
            continue
        # Validate file type
        if not f.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        try:
            fname = f"{datetime.datetime.utcnow().timestamp():.6f}_{saved}.jpg"
            path = os.path.join(folder, fname)
            f.save(path)
            saved += 1
        except Exception as e:
            app.logger.error(f"Save error: {e}")
    
    return jsonify({"saved": saved})

@app.route("/train_model", methods=["GET"])
def train_model_route():
    status = read_train_status()
    if status.get("running"):
        return jsonify({"status": "already_running"}), 202
    
    write_train_status({"running": True, "progress": 0, "message": "Starting training..."})
    
    def progress_callback(p, m):
        write_train_status({"running": True, "progress": p, "message": m})
    
    t = threading.Thread(target=train_model_background, args=(DATASET_DIR, progress_callback))
    t.daemon = True
    t.start()
    return jsonify({"status": "started"}), 202

@app.route("/train_status", methods=["GET"])
def train_status():
    return jsonify(read_train_status())

@app.route("/mark_attendance", methods=["GET"])
def mark_attendance_page():
    return render_template("mark_attendance.html")

@app.route("/recognize_face", methods=["POST"])
def recognize_face():
    """
    Recognize face and mark attendance.
    Allows unlimited markings per day.
    Includes anti-spam protection (3 second cooldown between markings).
    """
    if "image" not in request.files:
        return jsonify({"recognized": False, "error": "No image"}), 400
    
    img_file = request.files["image"]
    try:
        # Extract face embedding
        emb = extract_embedding_for_image(img_file.stream)
        if emb is None:
            return jsonify({"recognized": False, "error": "No face detected"}), 200
        
        # Load model and predict
        from model import load_model_if_exists, predict_with_model
        clf = load_model_if_exists()
        if clf is None:
            return jsonify({"recognized": False, "error": "Model not trained"}), 200
        
        pred_label, conf = predict_with_model(clf, emb)
        
        # Check confidence threshold
        if conf < 0.5:
            return jsonify({"recognized": False, "confidence": float(conf)}), 200
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get student name
        c.execute("SELECT name FROM students WHERE id=?", (int(pred_label),))
        row = c.fetchone()
        name = row[0] if row else "Unknown"
        
        # Anti-spam: Check if this student was marked in the last 3 seconds
        c.execute("""SELECT timestamp FROM attendance 
                     WHERE student_id=? 
                     ORDER BY timestamp DESC LIMIT 1""", (int(pred_label),))
        last_record = c.fetchone()
        
        if last_record:
            try:
                last_time = datetime.datetime.fromisoformat(last_record[0])
                current_time = datetime.datetime.utcnow()
                diff = (current_time - last_time).total_seconds()
            except:
                # If timestamp format is different, skip anti-spam
                diff = 10  # Force skip if parsing fails
            
            # If last marking was within 3 seconds, skip to prevent duplicate spam
            if diff < 3:
                # Get count of today's markings
                today = datetime.date.today().isoformat()
                c.execute("""SELECT COUNT(*) FROM attendance 
                             WHERE student_id=? AND date(timestamp)=?""", 
                          (int(pred_label), today))
                count_today = c.fetchone()[0]
                conn.close()
                
                return jsonify({
                    "recognized": True, 
                    "student_id": int(pred_label), 
                    "name": name, 
                    "confidence": float(conf),
                    "message": "Already marked recently (3s cooldown)",
                    "count_today": count_today,
                    "anti_spam": True
                }), 200
        
        # Get current timestamp
        ts = datetime.datetime.utcnow().isoformat()
        today = datetime.date.today().isoformat()
        
        # Insert attendance record (unlimited per day)
        c.execute("""INSERT INTO attendance (student_id, name, timestamp, type) 
                     VALUES (?, ?, ?, ?)""", 
                 (int(pred_label), name, ts, 'entry'))
        conn.commit()
        
        # Get count of today's markings
        c.execute("""SELECT COUNT(*) FROM attendance 
                     WHERE student_id=? AND date(timestamp)=?""", 
                  (int(pred_label), today))
        count_today = c.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "recognized": True, 
            "student_id": int(pred_label), 
            "name": name, 
            "confidence": float(conf),
            "timestamp": ts,
            "count_today": count_today,
            "message": f"Marked {count_today} times today"
        }), 200
        
    except Exception as e:
        app.logger.exception("Recognition error")
        return jsonify({"recognized": False, "error": str(e)}), 500

@app.route("/attendance_record", methods=["GET"])
def attendance_record():
    period = request.args.get("period", "all")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    q = "SELECT id, student_id, name, timestamp FROM attendance"
    params = ()
    
    if period == "daily":
        today = datetime.date.today().isoformat()
        q += " WHERE date(timestamp) = ?"
        params = (today,)
    elif period == "weekly":
        start = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
        q += " WHERE date(timestamp) >= ?"
        params = (start,)
    elif period == "monthly":
        start = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        q += " WHERE date(timestamp) >= ?"
        params = (start,)
    
    q += " ORDER BY timestamp DESC LIMIT 5000"
    c.execute(q, params)
    rows = c.fetchall()
    conn.close()
    return render_template("attendance_record.html", records=rows, period=period)

@app.route("/attendance_summary", methods=["GET"])
def attendance_summary():
    """Get summary statistics for attendance"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get today's total marks
    today = datetime.date.today().isoformat()
    c.execute("SELECT COUNT(*) FROM attendance WHERE date(timestamp)=?", (today,))
    today_total = c.fetchone()[0]
    
    # Get total unique students marked today
    c.execute("SELECT COUNT(DISTINCT student_id) FROM attendance WHERE date(timestamp)=?", (today,))
    today_unique = c.fetchone()[0]
    
    # Get total students
    c.execute("SELECT COUNT(*) FROM students")
    total_students = c.fetchone()[0]
    
    # Get top 5 most active students today
    c.execute("""SELECT name, COUNT(*) as count 
                 FROM attendance 
                 WHERE date(timestamp)=? 
                 GROUP BY student_id, name 
                 ORDER BY count DESC 
                 LIMIT 5""", (today,))
    top_students = c.fetchall()
    
    conn.close()
    
    return jsonify({
        "today_total": today_total,
        "today_unique": today_unique,
        "total_students": total_students,
        "top_students": [{"name": s[0], "count": s[1]} for s in top_students]
    })

@app.route("/attendance_by_student/<int:student_id>", methods=["GET"])
def attendance_by_student(student_id):
    """Get attendance history for a specific student"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT id, student_id, name, timestamp, type 
                 FROM attendance 
                 WHERE student_id=? 
                 ORDER BY timestamp DESC 
                 LIMIT 100""", (student_id,))
    rows = c.fetchall()
    conn.close()
    
    records = [{"id": r[0], "student_id": r[1], "name": r[2], 
                "timestamp": r[3], "type": r[4] if len(r) > 4 else 'entry'} for r in rows]
    return jsonify({"records": records})

@app.route("/download_csv", methods=["GET"])
def download_csv():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, student_id, name, timestamp FROM attendance ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    
    output = io.StringIO()
    output.write("id,student_id,name,timestamp\n")
    for r in rows:
        output.write(f'{r[0]},{r[1]},"{r[2]}",{r[3]}\n')
    
    mem = io.BytesIO()
    mem.write(output.getvalue().encode("utf-8"))
    mem.seek(0)
    return send_file(mem, as_attachment=True, download_name="attendance.csv", mimetype="text/csv")

@app.route("/students", methods=["GET"])
def students_list():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, roll, class, section, reg_no, created_at FROM students ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    data = [{"id": r[0], "name": r[1], "roll": r[2], "class": r[3], 
             "section": r[4], "reg_no": r[5], "created_at": r[6]} for r in rows]
    return jsonify({"students": data})

@app.route("/students/<int:sid>", methods=["DELETE"])
def delete_student(sid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM students WHERE id=?", (sid,))
    c.execute("DELETE FROM attendance WHERE student_id=?", (sid,))
    conn.commit()
    conn.close()
    
    folder = os.path.join(DATASET_DIR, str(sid))
    if os.path.isdir(folder):
        shutil.rmtree(folder, ignore_errors=True)
    
    return jsonify({"deleted": True})

@app.route("/today_attendance", methods=["GET"])
def today_attendance():
    """Get today's attendance records with counts"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = datetime.date.today().isoformat()
    
    c.execute("""SELECT student_id, name, COUNT(*) as count, 
                 GROUP_CONCAT(timestamp) as timestamps
                 FROM attendance 
                 WHERE date(timestamp)=? 
                 GROUP BY student_id, name 
                 ORDER BY count DESC""", (today,))
    rows = c.fetchall()
    conn.close()
    
    data = []
    for r in rows:
        timestamps = r[3].split(',') if r[3] else []
        data.append({
            "student_id": r[0],
            "name": r[1],
            "count": r[2],
            "timestamps": timestamps
        })
    
    return jsonify({"today": today, "records": data})

@app.route("/fix_database", methods=["GET"])
def fix_database():
    """Utility endpoint to fix database schema"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if type column exists
        c.execute("PRAGMA table_info(attendance)")
        columns = [col[1] for col in c.fetchall()]
        
        fixes = []
        if 'type' not in columns:
            c.execute("ALTER TABLE attendance ADD COLUMN type TEXT DEFAULT 'entry'")
            fixes.append("Added 'type' column")
        
        if 'session_id' not in columns:
            c.execute("ALTER TABLE attendance ADD COLUMN session_id TEXT DEFAULT 'default'")
            fixes.append("Added 'session_id' column")
        
        conn.commit()
        conn.close()
        
        if fixes:
            return jsonify({"status": "success", "fixes": fixes})
        else:
            return jsonify({"status": "success", "message": "Database schema is up to date"})
            
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)