from flask import Flask, render_template, Response, jsonify
import cv2
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
     "status": "on_leave", "check_in": "—", "kpi": 68, "alerts": 0}
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
    emotions = ["Happy", "Neutral", "Surprised", "Sad", "Angry", "Disgusted", "Fearful"]
    total = 100
    
    # Generate random percentages that sum to 100%
    percentages = []
    remaining = total
    for _ in range(len(emotions) - 1):
        if remaining <= 0:
            percentages.append(0)
        else:
            p = random.randint(0, remaining)
            percentages.append(p)
            remaining -= p
    percentages.append(remaining)
    
    # Shuffle to randomize
    random.shuffle(percentages)
    
    # Create emotion stats and sort by percentage
    stats = [{"emotion": e, "percentage": p} for e, p in zip(emotions, percentages)]
    stats.sort(key=lambda x: x["percentage"], reverse=True)
    
    # Take top 5
    emotion_stats = stats[:5]
    return emotion_stats

# Camera handling
def generate_frames():
    global current_frame, detected_emotion
    
    # Create a direct camera connection for the video feed
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    if not camera.isOpened():
        print("Error: Could not open camera directly in generate_frames")
        return
        
    # Set lower resolution for better streaming performance
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 700)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 300)
    

    # Add a frame counter
    frame_counter = 0
    
    try:
        while True:
            success, frame = camera.read()
            
            if not success:
                print("Failed to capture frame in generate_frames")
                time.sleep(0.1)
                try:
                    cv2.VideoCapture.release(camera)
                    cv2.VideoCapture(0, cv2.CAP_DSHOW)
                except Exception as e:
                    print(f"Error in generate_frames: {e}")
                continue

            # Convert frame to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
            # Detect faces in the frame
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            # Draw rectangles around detected faces
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Perform emotion analysis (only on every 5th frame to improve performance)
            frame_counter += 1
            if frame_counter % 5 == 0:  # Process every 5th frame

                # Perform emotion analysis
                try:
                    result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                    print(result)
                    # Extract dominant emotion if analysis is successful
                    if isinstance(result, dict) and 'dominant_emotion' in result:
                        dominant_emotion = result['dominant_emotion']
                        detected_emotion = dominant_emotion.capitalize()
                                    
                except Exception as e:
                    print(f"Error during face analysis: {str(e)}")
                    result = None

                
            # Process the frame more simply - avoid excessive processing
            #frame = cv2.resize(frame, (320, 240))
            
            # Convert frame to JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame_bytes = buffer.tobytes()
            
            # Yield frame in multipart response
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                   
            # Add a small delay to control frame rate
            time.sleep(0.03)
    except Exception as e:
        print(f"Error in generate_frames: {e}")
    finally:
        camera.release()


# Start camera thread
'''
def camera_thread():
    # Try DirectShow backend instead of Microsoft Media Foundation
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)  
    
    # Check if camera opened successfully
    if not camera.isOpened():
        print("Error: Could not open camera. Check if it's being used by another application.")
        return
        
    # Set camera properties for better compatibility
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    global current_frame, detected_emotion
    
    try:
        while True:
            success, frame = camera.read()
            if success:
                # Resize frame
                frame = cv2.resize(frame, (400, 300))
                
                # Convert to grayscale for face detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Detect faces
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                # Draw rectangle around faces
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                
                # Analyze emotion using DeepFace
                try:
                    if random.randint(0, 20) == 0:  # Only analyze occasionally to reduce CPU usage
                        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                        if isinstance(result, dict) and 'dominant_emotion' in result:
                            detected_emotion = result['dominant_emotion'].capitalize()
                        else:
                            detected_emotion = "No emotion detected"
                except Exception as e:
                    print(f"Error during face analysis: {str(e)}")
                
                # Store current frame for other functions
                with frame_lock:
                    current_frame = frame.copy()
            else:
                # If frame read failed, wait a bit and try again
                print("Failed to capture frame, retrying...")
                time.sleep(0.5)
                
            time.sleep(0.03)  # ~30 FPS
    finally:
        # Always release camera when done
        camera.release()
'''

# Routes
@app.route('/')
def index():
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
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

@app.route('/camera_test')
def camera_test():
    # This returns plain text for debugging
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
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
    return jsonify({"time": current_time, "date": current_date})

@app.route('/refresh_emotions')
def refresh_emotions():
    new_stats = refresh_emotion_data()
    return jsonify({"emotion_stats": new_stats})

    
"""update_live_emotion_thread = threading.Thread(target=refresh_live_emotion_data, daemon=True)
update_live_emotion_thread.start()  """  
# Start the camera thread
#camera_thread = threading.Thread(target=camera_thread, daemon=True)
#camera_thread.start()

if __name__ == "__main__":
    app.run(debug=True)