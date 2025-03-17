
# filepath: c:\Users\princ\Documents\Jan 2025\TTP\DataAnalysisPy39\app.py
from flask import Flask, render_template, Response, request, redirect, url_for, flash
import cv2
import datetime
import base64
import threading
import time
import io
from PIL import Image, ImageDraw
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

# Global variables
camera = None
camera_lock = threading.Lock()
camera_enabled = True
latest_frame = None
screenshot_saved = False

# Sample data - would come from database in a real app
manager_name = "John Doe"
employees = [
    {"id": 1, "name": "Sarah Johnson", "position": "Cashier", "performance": "High", "hours": "4/8"},
    {"id": 2, "name": "Michael Smith", "position": "Stocker", "performance": "Medium", "hours": "3/8"},
    {"id": 3, "name": "Emily Davis", "position": "Customer Service", "performance": "High", "hours": "6/8"},
    {"id": 4, "name": "Robert Wilson", "position": "Cashier", "performance": "Low", "hours": "2/8"},
    {"id": 5, "name": "Amanda Lee", "position": "Team Lead", "performance": "High", "hours": "7/8"}
]

def get_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
    return camera

def camera_thread():
    global latest_frame, camera_enabled
    
    while True:
        if camera_enabled:
            with camera_lock:
                camera = get_camera()
                success, frame = camera.read()
                if success:
                    latest_frame = cv2.resize(frame, (400, 300))
        time.sleep(0.03)  # ~30 FPS

def generate_frames():
    global latest_frame
    while True:
        if latest_frame is not None:
            # Convert frame to JPEG
            success, encoded_image = cv2.imencode('.jpg', latest_frame)
            if not success:
                continue
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + 
                   encoded_image.tobytes() + b'\r\n')
        else:
            # If no frame is available, yield a placeholder
            placeholder = Image.new('RGB', (400, 300), color='black')
            draw = ImageDraw.Draw(placeholder)
            draw.text((150, 150), "No camera feed", fill=(255, 255, 255))
            
            img_byte_arr = io.BytesIO()
            placeholder.save(img_byte_arr, format='JPEG')
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + 
                   img_byte_arr.getvalue() + b'\r\n')
        
        time.sleep(0.1)

def generate_performance_chart():
    # Count performances
    performance_counts = {"High": 0, "Medium": 0, "Low": 0}
    for employee in employees:
        performance_counts[employee["performance"]] += 1
    
    # Create pie chart
    labels = performance_counts.keys()
    sizes = performance_counts.values()
    colors = ['#4caf50', '#ff9800', '#f44336']
    
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    plt.title('Employee Performance')
    
    # Save to bytes
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png')
    img_bytes.seek(0)
    plt.close(fig)
    
    return base64.b64encode(img_bytes.getvalue()).decode('utf-8')

@app.route('/')
def index():
    # Calculate summary statistics
    high_performers = sum(1 for e in employees if e["performance"] == "High")
    low_performers = sum(1 for e in employees if e["performance"] == "Low")
    
    # Generate performance chart
    performance_chart = generate_performance_chart()
    
    # Get current time
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    
    # Check for screenshot notification
    global screenshot_saved
    screenshot_notification = None
    if screenshot_saved:
        screenshot_notification = "Screenshot saved successfully!"
        screenshot_saved = False
    
    return render_template('index.html', 
                          manager_name=manager_name,
                          employees=employees,
                          total_employees=len(employees),
                          high_performers=high_performers,
                          low_performers=low_performers,
                          current_date=datetime.datetime.now().strftime("%A, %B %d, %Y"),
                          current_time=current_time,
                          performance_chart=performance_chart,
                          screenshot_notification=screenshot_notification)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/screenshot', methods=['POST'])
def take_screenshot():
    global latest_frame, screenshot_saved
    
    # Save the current frame as a screenshot
    if latest_frame is not None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.jpg"
        cv2.imwrite(f"static/screenshots/{filename}", latest_frame)
        screenshot_saved = True
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Start camera thread
    threading.Thread(target=camera_thread, daemon=True).start()
    
    # Ensure screenshots directory exists
    import os
    os.makedirs('static/screenshots', exist_ok=True)
    
    app.run(debug=True)
