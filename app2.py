from flask import Flask, render_template, Response, jsonify, request, redirect, url_for, session, flash
import cv2
import gc
import datetime
import os
import random
import json
import numpy as np
import base64
from deepface import DeepFace
import threading
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for sessions

# Simple user database (in a real app, you'd use a proper database)
users = {
    "admin": {
        "password": "admin123",
        "name": "Admin User"
    },
    "manager": {
        "password": "manager123",
        "name": "Arthur Morgan"
    }
}

# Global variables
frame_lock = threading.Lock()
current_frame = None
detected_emotion = "Detecting..."
#add random emotions later
emotion_stats = [
    {"emotion": "Happy", "percentage": 65},
    {"emotion": "Neutral", "percentage": 20},
    {"emotion": "Surprised", "percentage": 10},
    {"emotion": "Sad", "percentage": 2.5},
    {"emotion": "Angry", "percentage": 2.5}
]

# Sample data
manager_name = "Arthur Morgan"
employees = [
    {"id": 1, "name": "Sarah Johnson", "position": "Cashier", "performance": "High", "hours": "4/8", 
     "status": "present", "check_in": "08:05", "kpi": 97, "alerts": 0},
    {"id": 2, "name": "Michael Smith", "position": "Stocker", "performance": "Medium", "hours": "3/8",
     "status": "late", "check_in": "09:15", "kpi": 72, "alerts": 1},
    {"id": 3, "name": "Emily Davis", "position": "Customer Service", "performance": "High", "hours": "6/8",
     "status": "present", "check_in": "08:00", "kpi": 94, "alerts": 0},
    {"id": 4, "name": "Robert Wilson", "position": "Cashier", "performance": "Low", "hours": "2/8",
     "status": "absent", "check_in": "—", "kpi": 45, "alerts": 2},
    {"id": 5, "name": "Amanda Lee", "position": "Team Lead", "performance": "High", "hours": "7/8",
     "status": "present", "check_in": "07:50", "kpi": 98, "alerts": 0},
    {"id": 6, "name": "Daniel Miller", "position": "Stocker", "performance": "Medium", "hours": "5/8",
     "status": "on_leave", "check_in": "—", "kpi": 68, "alerts": 0},
    {"id": 7, "name": "Olivia Brown", "position": "Cashier", "performance": "High", "hours": "4/8",
    "status": "present", "check_in": "08:10", "kpi": 91, "alerts": 1},
    {"id": 8, "name": "James Wilson", "position": "Customer Service", "performance": "Low", "hours": "3/8",
    "status": "absent", "check_in": "—", "kpi": 42, "alerts": 3},
    {"id": 9, "name": "Sophia Martinez", "position": "Cashier", "performance": "High", "hours": "6/8",
    "status": "present", "check_in": "07:55", "kpi": 95, "alerts": 0},
    {"id": 10, "name": "William Taylor", "position": "Stocker", "performance": "Medium", "hours": "5/8",
    "status": "late", "check_in": "09:00", "kpi": 70, "alerts": 1}
]

# Add a function to calculate employee summary metrics
def get_employee_summary():
    total = len(employees)
    present = sum(1 for e in employees if e["status"] == "present")
    absent = sum(1 for e in employees if e["status"] == "absent")
    late = sum(1 for e in employees if e["status"] == "late")
    on_leave = sum(1 for e in employees if e["status"] == "on_leave")
    alerts = sum(e["alerts"] for e in employees)
    avg_kpi = sum(e["kpi"] for e in employees) / total if total > 0 else 0
    
    return {
        "total": total,
        "present": present,
        "absent": absent,
        "late": late,
        "on_leave": on_leave,
        "alerts": alerts,
        "avg_kpi": round(avg_kpi, 1)
    }

# Configure face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Function to get metrics
def get_metrics():
    return [
        {"title": "Total Employees", "value": str(len(employees)), "icon": "👥"},
        {"title": "High Performers", "value": str(sum(1 for e in employees if e["performance"] == "High")), "icon": "🌟"},
        {"title": "Low Performers", "value": str(sum(1 for e in employees if e["performance"] == "Low")), "icon": "⚠️"}
    ]

# Function to refresh emotion data
def refresh_emotion_data():
    global emotion_stats
    
    # If no existing stats, generate random ones
    if not emotion_stats:
        emotions = ["Happy", "Neutral", "Surprised", "Sad", "Angry", "Disgusted", "Fearful"]
        percentages = [random.randint(5, 30) for _ in range(len(emotions))]
        total = sum(percentages)
        percentages = [int((p / total) * 100) for p in percentages]
        # Adjust the last one to ensure sum is 100
        percentages[-1] += (100 - sum(percentages))
        stats = [{"emotion": e, "percentage": p} for e, p in zip(emotions, percentages)]
        emotion_stats = sorted(stats, key=lambda x: x["percentage"], reverse=True)[:5]
        return emotion_stats
    
    # For subsequent refreshes, modify existing values slightly
    new_stats = []
    remaining = 100
    
    # Process all but the last emotion, with slight variations
    for i in range(len(emotion_stats) - 1):
        current = emotion_stats[i]
        # Vary by -5% to +5% of current value, but stay at least 2%
        variation = random.randint(-5, 5)
        new_percentage = max(2, current["percentage"] + variation)
        
        # Ensure we don't exceed remaining percentage
        if new_percentage > remaining - 2 * (len(emotion_stats) - i - 1):
            new_percentage = max(2, remaining - 2 * (len(emotion_stats) - i - 1))
            
        remaining -= new_percentage
        new_stats.append({"emotion": current["emotion"], "percentage": new_percentage})
    
    # Set the last emotion to take the remaining percentage
    new_stats.append({
        "emotion": emotion_stats[-1]["emotion"], 
        "percentage": remaining
    })
    
    # Sort by percentage
    new_stats.sort(key=lambda x: x["percentage"], reverse=True)
    emotion_stats = new_stats
    
    return emotion_stats

def generate_frames():
    frame_count = 0
    global current_frame, detected_emotion
    camera = None
    
    try:
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        
        if not camera.isOpened():
            print("Error: Could not open camera directly in generate_frames")
            return
            
        # Set lower resolution for better streaming performance
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 700)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 300)
        
        while True:
            try:
                success, frame = camera.read()
                if not success:
                    print("Failed to capture frame")
                    break
                    
                # Process frame and detect faces
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                # Draw rectangles around detected faces
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Emotion analysis (less frequent)
                if random.randint(0, 20) == 0:
                    try:
                        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                        if isinstance(result, dict) and 'dominant_emotion' in result:
                            detected_emotion = result['dominant_emotion'].capitalize()
                    except Exception as e:
                        print(f"Emotion analysis error: {e}")
                
                # Convert to JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                time.sleep(0.03)  # Frame rate control
                
                frame_count += 1
                if frame_count % 100 == 0:  # Every 100 frames
                    gc.collect()
                
            except Exception as e:
                print(f"Frame processing error: {e}")
                break
                
    except Exception as e:
        print(f"Camera error: {e}")
    finally:
        if camera is not None:
            camera.release()
             
def reset_camera():
    global current_frame, detected_emotion
    current_frame = None
    detected_emotion = "Detecting..."
    time.sleep(1)  # Wait before retrying
            
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    
    # If user is already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and users[username]['password'] == password:
            # Set user in session
            session['user_id'] = username
            session['user_name'] = users[username]['name']
            # Redirect to dashboard
            return redirect(url_for('index'))
        else:
            error = "Invalid username or password. Please try again."
    
    return render_template('login.html', error=error)

# Make root URL redirect to login
@app.route('/')
def root():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('index'))

# Add logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    return redirect(url_for('login'))

# Modify the index route to check for login
@app.route('/dashboard')
def index():
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get the user's name from session
    manager_name = session.get('user_name', 'Manager')
    
    current_time = datetime.datetime.now().strftime("%I:%M:%S %p")
    current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
    
    return render_template('index.html', 
                          manager_name=manager_name,
                          employees=employees,
                          employee_summary=get_employee_summary(),
                          metrics=get_metrics(),
                          emotion_stats=emotion_stats,
                          current_time=current_time,
                          current_date=current_date,
                          detected_emotion=detected_emotion)
    
@app.route('/analytics')
def analytics():

    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Performance trend data (simulated)
    performance_trend = {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "datasets": [
            {
                "label": "Employee Productivity",
                "data": [65, 72, 78, 75, 82, 87]
            },
            {
                "label": "Team Target",
                "data": [70, 70, 75, 75, 80, 80]
            }
        ]
    }
    
    # Emotion analysis over time
    emotion_trend = {
        "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
        "datasets": [
            {"label": "Happy", "data": [45, 52, 38, 41]},
            {"label": "Neutral", "data": [32, 28, 39, 36]},
            {"label": "Sad", "data": [12, 7, 11, 8]},
            {"label": "Angry", "data": [8, 10, 7, 12]},
            {"label": "Surprised", "data": [3, 3, 5, 3]}
        ]
    }
    
    # Attendance metrics
    attendance_data = {
        "present": [92, 88, 95, 91, 93, 89],
        "absent": [5, 7, 3, 6, 4, 8],
        "late": [3, 5, 2, 3, 3, 3],
        "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    }
    
    # Department performance comparison
    department_performance = {
        "departments": ["Cashiers", "Customer Service", "Stockers", "Management"],
        "values": [76, 82, 71, 88]
    }
    
    return render_template('analytics.html',
                          manager_name=manager_name,
                          performance_trend=json.dumps(performance_trend),
                          emotion_trend=json.dumps(emotion_trend),
                          attendance_data=json.dumps(attendance_data),
                          department_performance=json.dumps(department_performance),
                          employee_summary=get_employee_summary())

@app.route('/employees', methods=['GET', 'POST'])
def employees_page():
    
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 12-hour format with AM/PM
    current_time = datetime.datetime.now().strftime("%I:%M:%S %p")
    current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
    
    if request.method == 'POST':
        # Logic to update employee statuses
        employee_ids = request.form.getlist('employee_ids')
        new_status = request.form.get('status')
        
        if employee_ids and new_status:
            for emp_id in employee_ids:
                emp_id = int(emp_id)
                for emp in employees:
                    if emp['id'] == emp_id:
                        emp['status'] = new_status
                        # If marking as present, set a check-in time
                        if new_status == 'present':
                            emp['check_in'] = datetime.datetime.now().strftime("%H:%M")
                        # If marking as absent or on leave, clear check-in time
                        elif new_status in ['absent', 'on_leave']:
                            emp['check_in'] = "—"
            
            # Return success message
            return jsonify({'success': True, 'message': f'Updated {len(employee_ids)} employees to {new_status}'})
        
        return jsonify({'success': False, 'message': 'Missing required data'})
    
    # GET request - render the employees page
    return render_template('employees.html', 
                          manager_name=manager_name, 
                          employees=employees,
                          employee_summary=get_employee_summary(),
                          current_time=current_time,
                          current_date=current_date)


@app.route('/camera_test')
def camera_test():
    global current_frame
    if current_frame is None:
        return "No frames captured yet"
    frame_shape = current_frame.shape if current_frame is not None else "None"
    return f"Camera status: Frame shape={frame_shape}"


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/get_emotion')
def get_emotion():
    return jsonify({"emotion": detected_emotion})


@app.route('/get_current_time')
def get_current_time():
    current_time = datetime.datetime.now().strftime("%I:%M:%S %p")
    current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
    return jsonify({"time": current_time, "date": current_date})


@app.route('/refresh_emotions')
def refresh_emotions():
    new_stats = refresh_emotion_data()
    return jsonify({"emotion_stats": new_stats})

@app.route('/health')
def health_check():
    global current_frame
    status = {
        "camera_active": current_frame is not None,
        "last_emotion": detected_emotion,
        "memory_usage": f"{gc.get_count()}"
    }
    return jsonify(status)

if __name__ == "__main__":
    try:
        app.run(debug=True)
    except Exception as e:
        print(f"Application error: {e}")
        # Cleanup
        cv2.destroyAllWindows()