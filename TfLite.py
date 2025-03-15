import cv2
import numpy as np
import tensorflow as tf
import warnings
import time
import threading

warnings.filterwarnings("ignore", category=FutureWarning)

# Load the TensorFlow Lite model (CPU only)
interpreter = tf.lite.Interpreter(model_path="best-fp16.tflite")  # Replace with your TFLite model path
interpreter.allocate_tensors()

# Get model input and output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Define the class names corresponding to the class IDs
class_names = ["Plate Number", "Rock", "Scissor"]  # Replace with your actual class names

# Global variables
latest_frame = None
frame_lock = threading.Lock()
detected_objects = []
bounding_boxes = []
confidence_threshold = 0.5
iou_threshold = 0.4  # Intersection over Union threshold for NMS
stop_threads = False  # Flag to signal threads to stop

# Define helper functions for preprocessing and postprocessing
def preprocess_image(image, input_size):
    image_resized = cv2.resize(image, input_size)
    image_normalized = image_resized / 255.0  # Normalize pixel values to [0, 1]
    input_data = np.expand_dims(image_normalized, axis=0).astype(np.float32)
    return input_data

def non_max_suppression(bboxes, scores, iou_threshold):
    indices = cv2.dnn.NMSBoxes(bboxes, scores, confidence_threshold, iou_threshold)
    return indices.flatten() if len(indices) > 0 else []

def postprocess_output(detections, image):
    global bounding_boxes, detected_objects
    height, width, _ = image.shape
    boxes, scores, labels = [], [], []

    for detection in detections:
        score = detection[4]
        if score >= confidence_threshold:
            x_center, y_center, w, h = detection[0:4]
            x1 = int((x_center - w / 2) * width)
            y1 = int((y_center - h / 2) * height)
            x2 = int((x_center + w / 2) * width)
            y2 = int((y_center + h / 2) * height)
            class_id = int(detection[5])

            boxes.append([x1, y1, x2 - x1, y2 - y1])
            scores.append(float(score))
            labels.append(class_id)

    indices = non_max_suppression(boxes, scores, iou_threshold)

    # Update global bounding boxes and detected objects
    bounding_boxes.clear()
    detected_objects.clear()
    for i in indices:
        x1, y1, w, h = boxes[i]
        x2, y2 = x1 + w, y1 + h
        label = f"{class_names[labels[i]]} | Confidence: {scores[i]:.2f}"
        bounding_boxes.append((x1, y1, x2, y2, label))
        detected_objects.append((class_names[labels[i]], scores[i]))

        print(f"Detected Object - Name: {class_names[labels[i]]}, Confidence: {scores[i]:.2f}")

# Thread for video capture
def video_capture_thread(vid_path=0):
    global latest_frame, stop_threads
    cap = cv2.VideoCapture(vid_path)
    if not cap.isOpened():
        print("Error: Could not open video stream.")
        return

    while not stop_threads:
        ret, frame = cap.read()
        if not ret:
            break
        with frame_lock:
            latest_frame = frame.copy()

    cap.release()

# Thread for running inference
def inference_thread():
    global latest_frame, stop_threads
    input_size = (input_details[0]['shape'][2], input_details[0]['shape'][1])

    while not stop_threads:
        with frame_lock:
            if latest_frame is None:
                continue
            frame = latest_frame.copy()

        input_data = preprocess_image(frame, input_size)
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        output_data = interpreter.get_tensor(output_details[0]['index'])[0]
        postprocess_output(output_data, frame)

# Start threads
video_thread = threading.Thread(target=video_capture_thread, args=(0,))
inference_thread = threading.Thread(target=inference_thread)

video_thread.start()
inference_thread.start()

# Main loop to display the results
while True:
    with frame_lock:
        if latest_frame is None:
            continue
        frame_display = latest_frame.copy()

    # Draw bounding boxes
    for (x1, y1, x2, y2, label) in bounding_boxes:
        cv2.rectangle(frame_display, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame_display, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Display the output frame
    cv2.imshow('TFLite Real-Time Detection (CPU)', frame_display)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        stop_threads = True
        break

# Wait for threads to finish
video_thread.join()
inference_thread.join()

# Release resources and close windows
cv2.destroyAllWindows()
