import cv2
import time
import pygame
import smtplib
import os
import socket
from email.mime.text import MIMEText
from ultralytics import YOLO

# ------------------------------
# Create Folders
# ------------------------------
os.makedirs("authorized_images", exist_ok=True)
os.makedirs("unauthorized_images", exist_ok=True)

# ------------------------------
# Alarm Sound
# ------------------------------
def play_alarm():
    pygame.mixer.init()
    pygame.mixer.music.load("alarm.wav")
    pygame.mixer.music.play()

# ------------------------------
# Force SMTP IPv4 Fix
# ------------------------------
def force_ipv4():
    smtplib.socket.getaddrinfo = lambda *args, **kwargs: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, '', ("74.125.130.108", 465))
    ]
force_ipv4()

# ------------------------------
# Gmail Notification
# ------------------------------
def send_gmail_alert(object_name):

    sender = "sharlife45@gmail.com"
    app_password = "crsawmmhdpprmwdn"
    receiver = "sharlife97@gmail.com"

    subject = "🚨 Unauthorized Object Detected"
    body = f"""
ALERT WARNING!

Unauthorized Object Detected: {object_name}
Time: {time.ctime()}
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender, app_password)
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()
        print("📧 Gmail Notification Sent")
    except Exception as e:
        print("❌ Gmail Notification Failed:", e)

# ------------------------------
# Load YOLOv8 (FAST MODEL!)
# ------------------------------
model = YOLO("yolov8n.pt", verbose=False)   # faster model

# ------------------------------
# Authorized Objects
# ------------------------------
AUTHORIZED_OBJECTS = [
    "person", "laptop", "chair", "book", "paper",
    "pen", "pencil", "table", "cash", "documents"
]

# ------------------------------
# Camera Setup
# ------------------------------
cap = cv2.VideoCapture(0)
unauthorized_event_active = False

print("System Running... Press Q to exit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # ↓↓↓ FASTER FRAME SIZE ↓↓↓
    frame_resized = cv2.resize(frame, (480, 360))

    # YOLO Prediction
    results = model.predict(frame_resized, conf=0.45, verbose=False)
    detected_labels = []

    for r in results:
        for box in r.boxes:

            # lower confidence threshold = faster
            if box.conf[0] < 0.45:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0])
            label = model.names[cls]
            detected_labels.append(label)

            cv2.rectangle(frame_resized, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame_resized, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    timestamp = int(time.time())

    # Unauthorized Object Logic
    unauthorized_objects = [o for o in detected_labels if o not in AUTHORIZED_OBJECTS]

    if unauthorized_objects:
        filename = f"unauthorized_images/un_{timestamp}.jpg"
        cv2.imwrite(filename, frame_resized)

        if not unauthorized_event_active:
            detected = unauthorized_objects[0]
            print(f"⚠ Unauthorized Object Detected → {detected}")

            play_alarm()
            send_gmail_alert(detected)

            unauthorized_event_active = True
    else:
        unauthorized_event_active = False

    cv2.imshow("Authorized Area Object Monitoring", frame_resized)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
pygame.mixer.quit()
print("System Closed Successfully.")
