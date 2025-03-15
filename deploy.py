import torch
import cv2
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Your YOLOv5 detection code here

# Check if CUDA is available
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")
# Load the custom YOLOv5 model
model_path = 'bestP.pt'  # Replace with the path to your model
#model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, force_reload=True).to(device)
model =  torch.hub.load('./yolov5', 'custom', source ='local', path='bestP.pt', force_reload=True) ### The repo is stored locally

# Initialize webcam (0 is the default camera index, change if you have multiple cameras)
cap = cv2.VideoCapture(0)

# Check if the webcam is opened correctly
if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

# Loop for real-time detection
while True:
    # Capture each frame from the webcam
    ret, frame = cap.read()

    if not ret:
        print("Error: Failed to capture image.")
        break

    # Perform object detection
    results = model(frame)

    # Get detection results: labels, confidences, and coordinates
    labels = results.names  # List of class labels
    detections = results.xyxy[0].cpu().numpy()  # Get the detection results in [x1, y1, x2, y2, conf, cls] format

    # Loop through detections and print them
    for detection in detections:
        x1, y1, x2, y2, conf, cls = detection
        object_name = labels[int(cls)]
        print(f"Detected: {object_name}, Confidence: {conf:.2f}")

    # Render the results on the frame (bounding boxes and labels)
    result_img = results.render()[0]

    # Display the output frame
    cv2.imshow('YOLOv5 Real-Time Detection', result_img)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close OpenCV windows
cap.release()
cv2.destroyAllWindows()
