'''
CODER ZERO
connect with me at: https://www.youtube.com/channel/UCKipQAvBc7CWZaPib4y8Ajg
How to train custom yolov5: https://youtu.be/12UoOlsRwh8
DATASET: 1) https://www.kaggle.com/datasets/deepakat002/indian-vehicle-number-plate-yolo-annotation
         2) https://www.kaggle.com/datasets/elysian01/car-number-plate-detection
'''
### importing required libraries
import torch
import cv2
import time
# import pytesseract
import re
import numpy as np
import easyocr
import requests
import threading


##### DEFINING GLOBAL VARIABLE
EASY_OCR = easyocr.Reader(['en']) ### initiating easyocr
OCR_TH = 0.2

# Define a threading lock
lock = threading.Lock()
# Function to perform YOLOv5 detection
def perform_detection(model, frame,classes):

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = detectx(frame, model=model)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    frame_with_boxes = plot_boxes(results, frame, classes=classes)
    return results,frame_with_boxes
def display_frames(vid_path, model, classes,image_name="captured_image.jpg",vid_out= None):
    cap = cv2.VideoCapture(vid_path)
    cv2.namedWindow("vid_out", cv2.WINDOW_NORMAL)
    frame_no = 1
    skip_frame = 5  # Skip every 5 frames
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("[INFO] Failed to capture frame from camera")
            break

        # Perform YOLOv5 detection only for every 5th frame
        if frame_no % skip_frame == 0:

            results, frame_with_boxes = perform_detection(model, frame, classes)
            save_image(frame, image_name)
        else:
            # If it's not a frame for detection, use the original frame
            frame_with_boxes = frame

        # Display the original frame (or frame with bounding boxes)
        cv2.imshow("vid_out", frame_with_boxes)

        # Exit if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        frame_no += 1

    # Release the video capture object and close the OpenCV window
    cap.release()
    cv2.destroyAllWindows()

### -------------------------------------- function to run detection ---------------------------------------------------------
def detectx (frame, model):
    frame = [frame]
    #print(f"[INFO] Detecting. . . ")
    results = model(frame)
    # results.show()
    # print( results.xyxyn[0])
    # print(results.xyxyn[0][:, -1])
    # print(results.xyxyn[0][:, :-1])

    labels, cordinates = results.xyxyn[0][:, -1], results.xyxyn[0][:, :-1]

    return labels, cordinates

### ------------------------------------ to plot the BBox and results --------------------------------------------------------
def plot_boxes(results, frame,classes):

    """
    --> This function takes results, frame and classes
    --> results: contains labels and coordinates predicted by model on the given frame
    --> classes: contains the strting labels

    """
    labels, cord = results
    n = len(labels)
    x_shape, y_shape = frame.shape[1], frame.shape[0]

    #print(f"[INFO] Total {n} detections. . . ")
    #print(f"[INFO] Looping through all detections. . . ")


    ### looping through the detections
    for i in range(n):
        row = cord[i]
        if row[4] >= 0.55: ### threshold value for detection. We are discarding everything below this value
            print(f"[INFO] Extracting BBox coordinates. . . ")
            x1, y1, x2, y2 = int(row[0]*x_shape), int(row[1]*y_shape), int(row[2]*x_shape), int(row[3]*y_shape) ## BBOx coordniates
            text_d = classes[int(labels[i])]
            # cv2.imwrite("./output/dp.jpg",frame[int(y1):int(y2), int(x1):int(x2)])

            coords = [x1,y1,x2,y2]

            plate_num = recognize_plate_easyocr(img = frame, coords= coords, reader= EASY_OCR, region_threshold= OCR_TH)


            # if text_d == 'mask':
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2) ## BBox
            cv2.rectangle(frame, (x1, y1-20), (x2, y1), (0, 255,0), -1) ## for text label background
            cv2.putText(frame, f"{plate_num}", (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.5,(255,255,255), 2)

            # cv2.imwrite("./output/np.jpg",frame[int(y1)-25:int(y2)+25, int(x1)-25:int(x2)+25])




    return frame



#### ---------------------------- function to recognize license plate --------------------------------------
def check_extracted_text_in_database(extracted_text):
    extracted_text_str = ' '.join(extracted_text) if isinstance(extracted_text, list) else extracted_text
    response = requests.get('http://127.0.0.1:5000/check_plate', params={'extracted_text_str': extracted_text_str})
    print(response.text)
    print(">>>>>>>>>>>>>>>>>>>>>>>", extracted_text_str)

# function to recognize license plate numbers using Tesseract OCR
def recognize_plate_easyocr(img, coords,reader,region_threshold):
    # separate coordinates from box
    xmin, ymin, xmax, ymax = coords
    # get the subimage that makes up the bounded region and take an additional 5 pixels on each side
    # nplate = img[int(ymin)-5:int(ymax)+5, int(xmin)-5:int(xmax)+5]
    nplate = img[int(ymin):int(ymax), int(xmin):int(xmax)] ### cropping the number plate from the whole image


    ocr_result = reader.readtext(nplate)



    text = filter_text(region=nplate, ocr_result=ocr_result, region_threshold= region_threshold)

    if len(text) ==1:
        text = text[0].upper()
        check_extracted_text_in_database(text)
    return text





### to filter out wrong detections

def filter_text(region, ocr_result, region_threshold):
    rectangle_size = region.shape[0]*region.shape[1]

    plate = []
    print(ocr_result)
    for result in ocr_result:
        length = np.sum(np.subtract(result[0][1], result[0][0]))
        height = np.sum(np.subtract(result[0][2], result[0][1]))

        if length*height / rectangle_size > region_threshold:
            plate.append(result[1])
    return plate


def save_image(frame, image_name):
    if frame is None:
        print("Error: No frame to save")
        return
    # Save the captured frame as an image
    cv2.imwrite(image_name, frame)


### ---------------------------------------------- Main function -----------------------------------------------------

def main(img_path=None, vid_path=None,vid_out = None,image_name="captured_image.jpg"):

    print(f"[INFO] Loading model... ")
    ## loading the custom trained model
    # model =  torch.hub.load('ultralytics/yolov5', 'custom', path='last.pt',force_reload=True) ## if you want to download the git repo and then run the detection
    model =  torch.hub.load('./yolov5-master', 'custom', source ='local', path='best1.pt',force_reload=True) ### The repo is stored locally

    classes = model.names ### class names in string format




    ### --------------- for detection on image --------------------
    if img_path != None:
        print(f"[INFO] Working with image: {img_path}")
        img_out_name = f"./output/result_{img_path.split('/')[-1]}"

        frame = cv2.imread(img_path) ### reading the image
        frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)

        results = detectx(frame, model = model) ### DETECTION HAPPENING HERE

        frame = cv2.cvtColor(frame,cv2.COLOR_RGB2BGR)

        frame = plot_boxes(results, frame,classes = classes)


        cv2.namedWindow("img_only", cv2.WINDOW_NORMAL) ## creating a free windown to show the result

        while True:
            # frame = cv2.cvtColor(frame,cv2.COLOR_RGB2BGR)

            cv2.imshow("img_only", frame)

            if cv2.waitKey(5) & 0xFF == ord('q'):
                print(f"[INFO] Exiting. . . ")

                cv2.imwrite(f"{img_out_name}",frame) ## if you want to save he output result.

                break

    ### --------------- for detection on video --------------------
    elif vid_path !=None:
        print(f"[INFO] Working with video: {vid_path}")

        ## reading the video
        cap = cv2.VideoCapture(vid_path)


        if vid_out: ### creating the video writer if video output path is given
            # by default VideoCapture returns float instead of int
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps =int(cap.get(cv2.CAP_PROP_FPS))
            codec = cv2.VideoWriter_fourcc(*'avc1') ##(*'XVID')
            out = cv2.VideoWriter(vid_out, codec, fps, (width, height))

            print("Codec: {}".format(codec))
            print("Resolution: {}x{}".format(width, height))
            print("FPS: {}".format(fps))
        # assert cap.isOpened()
        frame_no = 1
        skip_frame = 1
        # Start a separate thread to display frames from the video source
        display_thread = threading.Thread(target=display_frames, args=(vid_path, model, classes))  # For webcam
        display_thread.start()



        print(f"[INFO] Clening up. . . ")
        print("Codec: {}".format(codec))
        print("Resolution: {}x{}".format(width, height))
        print("FPS: {}".format(fps))
        ### releaseing the writer




### -------------------  calling the main function-------------------------------


# main(vid_path="./test_images/vid_1.mp4",vid_out="vid_1.mp4") ### for custom video
main(vid_path=0,vid_out="outtt.mp4") #### for webcam
#main(vid_path='rtsp://admin:kurtdecena1@192.168.1.64:554/mpeg4/ch1/main/av_stream', vid_out="output.avi") #### for webcam
#main(img_path="./test_images/Cars74.jpg") ## for image



