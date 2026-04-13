import cv2
from ultralytics import YOLO
import supervision as sv
import os

# Absolute video path
video_path = "C:/Users/LENOVO/Desktop/Predusk/multi-object-tracking/input/video1.mp4"

print("Checking video path:", os.path.exists(video_path))

# Load YOLO model
model = YOLO("yolov8n.pt")

# Load video
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("Error: Could not open input video")
    exit()

# Video properties
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))

print(f"Video Loaded: {width}x{height} at {fps} FPS")

# Output video
out = cv2.VideoWriter("../output/output.avi",
                      cv2.VideoWriter_fourcc(*'XVID'),
                      fps, (width, height))

if not out.isOpened():
    print("Error: VideoWriter not opened")
    exit()

# Tracker (compatible version)
tracker = sv.ByteTrack()

# Store trajectory
track_history = {}

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Finished processing video")
        break

    # Run detection
    results = model(frame)[0]

    # Convert detections
    detections = sv.Detections.from_ultralytics(results)

    # ---- FILTERING (IMPORTANT FOR STABILITY) ----

    # Keep only persons
    detections = detections[detections.class_id == 0]

    # Confidence filter
    detections = detections[detections.confidence > 0.4]

    # Remove very small boxes (reduces ID switching)
    detections = detections[
        (detections.xyxy[:, 2] - detections.xyxy[:, 0] > 30) &
        (detections.xyxy[:, 3] - detections.xyxy[:, 1] > 30)
    ]

    # --------------------------------------------

    # Tracking
    tracked = tracker.update_with_detections(detections)

    # Count players
    player_count = len(tracked.tracker_id)

    # Draw tracking info
    for box, track_id in zip(tracked.xyxy, tracked.tracker_id):
        x1, y1, x2, y2 = map(int, box)

        # Center point
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)

        # Store trajectory
        if track_id not in track_history:
            track_history[track_id] = []

        track_history[track_id].append((cx, cy))

        # Limit trajectory length
        if len(track_history[track_id]) > 30:
            track_history[track_id].pop(0)

        # Draw trajectory
        for i in range(1, len(track_history[track_id])):
            cv2.line(frame,
                     track_history[track_id][i-1],
                     track_history[track_id][i],
                     (255, 0, 0), 2)

        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Draw ID
        cv2.putText(frame, f"ID {track_id}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 255, 0), 2)

    # Show player count
    cv2.putText(frame, f"Players: {player_count}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1, (0, 0, 255), 3)

    # Write output
    out.write(frame)

    # Display
    cv2.imshow("Tracking", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

# Cleanup
cap.release()
out.release()
cv2.destroyAllWindows()

print("Output video saved successfully!")