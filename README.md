# 📸 Face Recognition Attendance System

A powerful, web-based attendance management system that uses **facial recognition technology** to automatically mark student attendance. Built with Flask, OpenCV, and Machine Learning.

<img width="510" height="428" alt="Screenshot 2026-06-21 102810" src="https://github.com/user-attachments/assets/a101230a-2817-4926-9522-eca60b723d26" />
  
<img width="502" height="610" alt="Screenshot 2026-06-21 102820" src="https://github.com/user-attachments/assets/9b170b28-a292-4889-b447-f8bfc401a019" />

<img width="759" height="573" alt="Screenshot 2026-06-21 102901" src="https://github.com/user-attachments/assets/73be76b0-c3ad-45ad-a06b-a9d335c75b9c" />

<img width="1110" height="558" alt="Screenshot 2026-06-21 102844" src="https://github.com/user-attachments/assets/9bc64cff-3efe-494f-99b1-9f0894c08f09" />


## ✨ Features

### Core Functionality
- **Face Registration**: Capture 50 face images per student via webcam
- **Smart Training**: Train RandomForest classifier on captured faces
- **Live Recognition**: Real-time face detection and attendance marking
- **Unlimited Marking**: Students can be marked multiple times per day

### Management Features
- **Student Management**: Add, list, and delete students with all data
- **Attendance Records**: View, filter (daily/weekly/monthly), and export CSV
- **Analytics Dashboard**: Visual charts and attendance statistics
- **Session Tracking**: Track check-in/check-out patterns

### Technical Features
- **RESTful API**: Full API for integration
- **Background Training**: Model training runs in background thread
- **Progress Tracking**: Real-time training progress updates
- **Responsive Design**: Works on desktop and mobile devices


## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Webcam
- Git (optional)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/SHRnumber/Face-Recognition-Attendance-System.git
cd Face-Recognition-Attendance-System
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python app.py
```

4. **Access the system**
Open your browser and navigate to: `http://localhost:5000`

### First-Time Setup

1. **Add Students**: Click "Add Student" and register students
2. **Capture Faces**: Take 50 face images per student
3. **Train Model**: Click "Train Now" on the dashboard
4. **Start Marking**: Click "Mark Attendance" and recognize faces


## 📋 Workflow

```
Add Student → Capture Faces → Train Model → Mark Attendance → View Records
```

### Step-by-Step Guide

#### 1. Add Student
- Fill in student details (Name required)
- Click "Save Info"
- Click "Start Capture" to begin face capture
- Stay in front of the camera for 50 images
- Click "Add Student" to complete

#### 2. Train Model
- Return to dashboard
- Click "Train Now"
- Wait for training to complete (progress bar shows status)
- Model is now ready for recognition

#### 3. Mark Attendance
- Click "Mark Attendance"
- Click "Start" to open camera
- Show faces to the camera
- Recognized students appear in the list
- Click "Stop" when done

#### 4. View Records
- Click "View Records"
- Filter by All, Daily, Weekly, or Monthly
- Download CSV for reports


## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (HTML/CSS/JS)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │   Dashboard  │  │ Add Student  │  │ Mark Attendance │ │
│  └──────────────┘  └──────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                    Flask Backend (app.py)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │   Routes     │  │   Database   │  │ Training Thread  │ │
│  │  (Endpoints) │  │   (SQLite)   │  │   (Background)   │ │
│  └──────────────┘  └──────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    Face Recognition (model.py)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ Face Detection│  │ Face Feature │  │  RandomForest   │ │
│  │   (OpenCV)    │  │  Extraction  │  │   Classifier    │ │
│  └──────────────┘  └──────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```


## 📁 Project Structure

```
Face-Recognition-Attendance-System/
├── app.py                    # Main Flask application
├── model.py                  # Face recognition logic
├── requirements.txt          # Python dependencies
├── runtime.txt              # Python version for deployment
│
├── static/                   # Static assets
│   ├── css/
│   │   └── style.css        # Custom styling
│   ├── js/
│   │   ├── dashboard.js     # Dashboard logic
│   │   ├── camera_add_student.js # Student registration
│   │   └── camera_mark.js   # Attendance marking
│   └── images/
│       └── bg.png           # Background image
│
├── templates/               # HTML templates
│   ├── index.html           # Dashboard
│   ├── add_student.html     # Add student form
│   ├── mark_attendance.html # Camera view
│   └── attendance_record.html # Records view
│
├── dataset/                 # Student face images (auto-created)
│   └── {student_id}/
│       └── {timestamp}.jpg
│
├── attendance.db            # SQLite database (auto-created)
├── model.pkl               # Trained RandomForest model (auto-created)
└── train_status.json       # Training progress (auto-created)
```


## 🛠️ Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Backend** | Flask | 2.3.3 |
| **Face Detection** | OpenCV (Haar Cascade) | 4.8.1 |
| **Machine Learning** | scikit-learn (RandomForest) | 1.3.0 |
| **Database** | SQLite | Built-in |
| **Frontend** | Bootstrap | 5.3.1 |
| **Charts** | Chart.js | Latest |
| **Language** | Python | 3.8+ |


## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dashboard |
| POST | `/add_student` | Add new student |
| POST | `/upload_face` | Upload face images |
| GET | `/train_model` | Start model training |
| GET | `/train_status` | Training progress |
| POST | `/recognize_face` | Recognize face & mark attendance |
| GET | `/attendance_record` | View records (filtered) |
| GET | `/attendance_stats` | Chart statistics |
| GET | `/attendance_summary` | Daily summary |
| GET | `/today_attendance` | Today's records |
| GET | `/students` | List all students |
| DELETE | `/students/<id>` | Delete student |
| GET | `/download_csv` | Export attendance |
| GET | `/fix_database` | Fix database schema |

### Example API Usage

**Recognize Face**
```bash
curl -X POST -F "image=@face.jpg" http://localhost:5000/recognize_face
```

**Response:**
```json
{
  "recognized": true,
  "student_id": 1,
  "name": "John Doe",
  "confidence": 0.92,
  "count_today": 3,
  "message": "Marked 3 times today"
}
```

**Get Today's Summary**
```bash
curl http://localhost:5000/attendance_summary
```

**Response:**
```json
{
  "today_total": 45,
  "today_unique": 12,
  "total_students": 15,
  "top_students": [
    {"name": "John Doe", "count": 5},
    {"name": "Jane Smith", "count": 4}
  ]
}
```


## 💾 Database Schema

### Students Table
```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    roll TEXT,
    class TEXT,
    section TEXT,
    reg_no TEXT,
    created_at TEXT
);
```

### Attendance Table
```sql
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    name TEXT,
    timestamp TEXT,
    type TEXT DEFAULT 'entry',
    session_id TEXT DEFAULT 'default'
);
```


## 📈 Performance

| Operation | Time |
|-----------|------|
| Face Detection | ~30ms per frame |
| Feature Extraction | ~50ms per face |
| Model Prediction | ~10ms per face |
| Training (2 students) | ~10-20 seconds |


## 🔒 Security Considerations

### For Development
- Debug mode enabled
- SQLite database (suitable for small deployments)
- No authentication (ideal for testing)
  

### For Production
- Use Gunicorn or Waitress server
- Add authentication (JWT, OAuth)
- Use PostgreSQL/MySQL database
- Enable HTTPS
- Implement rate limiting
- Use environment variables for secrets
  

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Guidelines
- Follow PEP 8 style guide
- Write clear commit messages
- Add comments for complex code
- Update documentation
- Test your changes
  

## 🧪 Testing

Run tests manually:
```bash
# Test API endpoints
curl http://localhost:5000/students
curl http://localhost:5000/attendance_stats

# Test database
sqlite3 attendance.db "SELECT * FROM students;"
```


## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## 🙏 Acknowledgments

- OpenCV community for face detection
- scikit-learn for machine learning
- Flask framework
- Bootstrap for UI components


## 📧 Contact

- **Author**: [HAMZA RASHID]
- **Email**: [your.shrnumber002@gamil.com]
- **Project Link**: (https://github.com/SHRnumber/Face-Recognition-Attendance-System)


## ⭐ Support

If you find this project useful, please give it a star! ⭐

---

### Made with ❤️ and Python
