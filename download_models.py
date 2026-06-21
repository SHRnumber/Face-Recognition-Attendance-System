import urllib.request
import os

# Download face detection model
url = "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
file_path = "face_detection_short_range.tflite"

if not os.path.exists(file_path):
    print("Downloading face detection model...")
    urllib.request.urlretrieve(url, file_path)
    print("Download complete!")
else:
    print("Model already exists.")