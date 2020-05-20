
import cv2
from flask import Flask, render_template, Response
import threading
import time
import json
from camera import VideoCamera



first_frame=None
video_camera = None
global_frame = None

#Data contains is an array of dictionaries that contains all the pictures of movement
data = []
try:                      #فارغ detectionsاذا كان ملف 
    with open('detections.txt') as json_data:
        data  = json.load(json_data)
except:
    print("The data file is empty")
print(data)

'''
videothread 
 لفيديو و مبيوفرش غير صوره 
 وبيقدم الصوره لباقي البرنامج
'''

class videothread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.shutdown = False

        self.video = cv2.VideoCapture(0)
        success, image = self.video.read()
        ret , jpeg = cv2.imencode('.jpg', image)
        self.img = jpeg.tobytes()

    def run(self):
        self.update_frame()
    def __del__(self):
        self.video.release()

    def update_frame(self):
        while not self.shutdown:
            success, image = self.video.read()
            if (success):
                ret, jpeg = cv2.imencode('.jpg', image)
                self.img = jpeg.tobytes()

        


'''

surveillancethread

takes the image from   videothread   and processes it in order to determine might be movement or not in the frame.
If movement is detected a picture the thread will save a picture                      
'''
class surveillancethread(threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.shutdown = False
        self.photoevery = 1
        self.timer = time.time()
        self.timer_flag = True
        self.movement_flag = False

    def timercontrol(self):   #get the time in seconds using time.time function
        if not self.timer_flag:
            if ( time.time()-self.timer )>self.photoevery:
                self.timer = time.time()
                self.timer_flag = True

    def run(self):                                               #Get the first frame to compare later frame
        ret, frame = cvthread.video.read()
        gray1 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray1 = cv2.GaussianBlur(gray1, (21, 21), 0)
        glob_contours = []                                       #vector  to stores the nº of contours detected each time

        while not self.shutdown:              #Thread shutdown                                                                                                                                                                          
            ret, frame = cvthread.video.read()                   #Getting the second frame to compare
            gray2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)

            #Calculating the delta and the contours                 #absdiff()   calculate difference between two arrays 
            frameDelta = cv2.absdiff(gray1, gray2)                                          
            thresh = cv2.threshold(frameDelta,15, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=0)
            contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)    #use binary images. So before finding contours, apply threshold edge detection.

            #glob contour contains the nº of contours of the last 4 measurements
            while len(glob_contours) > 4:
                glob_contours.pop(0)
            glob_contours.append(contours)

            #A mean of the values to  avoid noise
            mean = 0
            for contiterator in glob_contours:
                mean = len(contiterator) + mean
            #If the mean is above a certain threshold                
            if (mean >5):
                self.movement_flag = True          #the movement_flag is actiavted
            else:
                self.movement_flag = False

            gray1 = gray2                  #This frame is now the last frame for the next loop

            #If the timer is not set(no photos saved in the last 3 seconds) and movement_flag is activated
            if (self.movement_flag and self.timer_flag):
                print("Taking picture")
                self.timer_flag = False
                self.timer = time.time()
                                                  #Saving image detection
                cv2.imwrite("detection-.jpg", frame)
                
                                                  #Writing the entry in the json file
                new_entry = {'Folder' : "frame/detection-.jpg" }
                data.append(new_entry)
                from  mail import  send_an_email 
            self.timercontrol()
           
            

      

    
    

'''Flask server:
'''
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html'  , pages=data)

def video_stream():
    global video_camera 
    global global_frame

    if video_camera == None:
        video_camera = VideoCamera()
        
    while True:
        frame = video_camera.get_frame()

        if frame != None:
            global_frame = frame
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        else:
            yield (b'--frame\r\n'
                            b'Content-Type: image/jpeg\r\n\r\n' + global_frame + b'\r\n\r\n')

@app.route('/video_viewer')
def video_viewer():
    return Response(video_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    #Launch opencv stream thread
    cvthread = videothread(3, str(time.time))
    cvthread.start()
    #Launch the surveillancethread, 
    surthread = surveillancethread(1, str(time.time))
    surthread.start()
    #Launch Flask server
    app.run(threaded=True ,  host='127.0.0.1' )
    #Once exited Flask with control + C save the new data entries to detections.txt
    with open("detections.txt", "w") as outfile:
        json.dump(data, outfile)
    print("Exiting server")
    #Finish the threads
    cvthread.shutdown = True
    surthread.shutdown = True
    cvthread.join()
    surthread.join()
