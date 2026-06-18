import cv2
import threading
import time
import colorsys
import os
from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS
from detector import Detector
from tracker import Sort

app = Flask(__name__)
CORS(app)

# Global state
processing_thread = None
running = False
paused = False

# Parameters
conf_threshold = 0.25
iou_threshold = 0.30
tracking_enabled = True
selected_model = "yolov8n.pt"
selected_source = "sample.mp4"

# State locks
frame_lock = threading.Lock()
latest_frame = None

# Analytics
stats = {
    "status": "stopped",
    "fps": 0.0,
    "active_count": 0,
    "total_count": 0,
    "class_counts": {},
    "error_msg": ""
}

seen_track_ids = set()
detector = None
tracker = None

# Color generator helper for track IDs
def get_color(idx):
    h = (idx * 0.618033988749895) % 1.0
    r, g, b = [int(x * 255) for x in colorsys.hls_to_rgb(h, 0.5, 0.8)]
    return (b, g, r)  # BGR format for OpenCV

def video_processing_worker():
    global running, paused, latest_frame, stats, seen_track_ids, detector, tracker
    global conf_threshold, iou_threshold, tracking_enabled, selected_model, selected_source
    
    stats["status"] = "loading"
    stats["error_msg"] = ""
    
    # 1. Initialize detector (downloads weight file if needed)
    try:
        # Load detector if not already loaded or if the model name changed
        if detector is None or getattr(detector, 'model_name', '') != selected_model:
            detector = Detector(model_name=selected_model)
            detector.model_name = selected_model
    except Exception as e:
        stats["status"] = "error"
        stats["error_msg"] = f"Model load error: {str(e)}"
        running = False
        return

    # 2. Initialize tracker
    tracker = Sort(iou_threshold=iou_threshold)
    Sort.trackers = []
    seen_track_ids.clear()
    
    # 3. Check and open video source
    source_val = selected_source
    # Check if webcam index is selected (digit)
    if source_val.isdigit():
        source_val = int(source_val)
        
    cap = cv2.VideoCapture(source_val)
    if not cap.isOpened():
        stats["status"] = "error"
        stats["error_msg"] = f"Could not open video source: '{selected_source}'."
        running = False
        return
        
    stats["status"] = "running"
    fps_ema = 0.0
    alpha = 0.1
    
    while running:
        if paused:
            time.sleep(0.05)
            continue
            
        start_time = time.time()
        ret, frame = cap.read()
        if not ret:
            # Video ended or webcam disconnected
            break
            
        # Run detection
        try:
            detections = detector.detect(frame, conf_threshold)
        except Exception as e:
            print(f"Web backend inference error: {e}")
            continue
            
        active_count = 0
        total_count = 0
        class_counts = {}
        
        if tracking_enabled:
            # Run tracker
            tracks = tracker.update(detections)
            active_count = len(tracks)
            
            for track in tracks:
                x1, y1, x2, y2, track_id, class_id = track
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                track_id = int(track_id)
                class_id = int(class_id)
                
                seen_track_ids.add(track_id)
                class_name = detector.class_names.get(class_id, f"Class {class_id}")
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
                
                # Draw box
                color = get_color(track_id)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                # Draw text label
                label_text = f"ID {track_id}: {class_name.capitalize()}"
                (w, h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                y1_label = max(y1, h + 10)
                cv2.rectangle(frame, (x1, y1_label - h - 10), (x1 + w, y1_label), color, -1)
                cv2.putText(frame, label_text, (x1, y1_label - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                
            total_count = len(seen_track_ids)
        else:
            # Draw raw detections only
            active_count = len(detections)
            total_count = 0
            
            for det in detections:
                x1, y1, x2, y2, score, class_id = det
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                class_id = int(class_id)
                score = float(score)
                
                class_name = detector.class_names.get(class_id, f"Class {class_id}")
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
                
                color = (255, 165, 0)  # Orange
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                label_text = f"{class_name.capitalize()}: {score:.2f}"
                (w, h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                y1_label = max(y1, h + 10)
                cv2.rectangle(frame, (x1, y1_label - h - 10), (x1 + w, y1_label), color, -1)
                cv2.putText(frame, label_text, (x1, y1_label - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        # Smooth FPS estimation
        elapsed = time.time() - start_time
        current_fps = 1.0 / elapsed if elapsed > 0 else 0
        if fps_ema == 0:
            fps_ema = current_fps
        else:
            fps_ema = (1.0 - alpha) * fps_ema + alpha * current_fps
            
        # Save frame bytes and stats
        stats["fps"] = fps_ema
        stats["active_count"] = active_count
        stats["total_count"] = total_count
        stats["class_counts"] = class_counts
        
        # Compress frame as JPEG
        ret_enc, jpeg = cv2.imencode('.jpg', frame)
        if ret_enc:
            with frame_lock:
                latest_frame = jpeg.tobytes()
                
    cap.release()
    running = False
    stats["status"] = "stopped"
    with frame_lock:
        latest_frame = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    def gen():
        while running:
            with frame_lock:
                if latest_frame is None:
                    time.sleep(0.01)
                    continue
                frame = latest_frame
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            # Limit streaming frame rate to roughly 30 FPS to avoid clogging network/browser
            time.sleep(0.033)
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/stats')
def get_stats():
    return jsonify(stats)

@app.route('/api/start', methods=['POST'])
def api_start():
    global running, paused, processing_thread, selected_source, selected_model
    global conf_threshold, iou_threshold, tracking_enabled
    
    if running:
        return jsonify({"status": "already_running"})
        
    data = request.get_json() or {}
    selected_source = data.get("source", "sample.mp4")
    selected_model = data.get("model", "yolov8n.pt")
    conf_threshold = data.get("conf", 0.25)
    iou_threshold = data.get("iou", 0.30)
    tracking_enabled = data.get("tracking_enabled", True)
    
    running = True
    paused = False
    
    processing_thread = threading.Thread(target=video_processing_worker, daemon=True)
    processing_thread.start()
    
    return jsonify({"status": "started"})

@app.route('/api/pause', methods=['POST'])
def api_pause():
    global paused
    paused = not paused
    return jsonify({"paused": paused})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    global running, paused, processing_thread
    running = False
    paused = False
    if processing_thread is not None:
        processing_thread.join(timeout=1.0)
        processing_thread = None
    return jsonify({"status": "stopped"})

@app.route('/api/set_params', methods=['POST'])
def api_set_params():
    global conf_threshold, iou_threshold, tracking_enabled, tracker
    data = request.get_json() or {}
    conf_threshold = data.get("conf", conf_threshold)
    iou_threshold = data.get("iou", iou_threshold)
    tracking_enabled = data.get("tracking_enabled", tracking_enabled)
    
    if tracker is not None:
        tracker.iou_threshold = iou_threshold
        
    return jsonify({"status": "updated"})

if __name__ == '__main__':
    # Run server locally on port 5000
    app.run(host='127.0.0.1', port=5000, debug=False)
