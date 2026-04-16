import cv2
import numpy as np
import face_recognition
import os
import pandas as pd
from datetime import datetime

# ========== LOAD IMAGES ==========
path = 'images'   # ✅ FIXED (important)
images = []
classNames = []

myList = os.listdir(path)

for cl in myList:
    curImg = cv2.imread(os.path.join(path, cl))
    if curImg is not None:
        images.append(curImg)
        classNames.append(os.path.splitext(cl)[0].upper())

# ========== ENCODING ==========
def findEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodes = face_recognition.face_encodings(img)

        if len(encodes) > 0:
            encodeList.append(encodes[0])

    return encodeList

# ========== GET STUDENT DETAILS ==========
def getStudentDetails(name):
    try:
        df = pd.read_csv('students.csv')
        df.columns = df.columns.str.strip()

        student = df[df['Name'].astype(str).str.strip().str.upper() == name]

        if not student.empty:
            uid = student.iloc[0]['UID']
            student_class = student.iloc[0]['Class']
            course = student.iloc[0]['Course']
            return uid, student_class, course
    except:
        pass

    return "NA", "NA", "NA"

# ========== MARK ATTENDANCE ==========
def markAttendance(name, uid, student_class, course, status):
    if name == "INVALID":
        return

    file_exists = os.path.isfile('attendance.csv')

    with open('attendance.csv', 'a+') as f:

        if not file_exists:
            f.write('Name,UID,Class,Course,Status,Time,Date\n')

        f.seek(0)
        data = f.readlines()

        now = datetime.now()
        dateString = now.strftime('%d-%m-%Y')

        for line in data:
            entry = line.strip().split(',')
            if len(entry) > 0:
                if entry[0] == name and entry[-1] == dateString:
                    return

        dtString = now.strftime('%H:%M:%S')
        f.writelines(f'{name},{uid},{student_class},{course},{status},{dtString},{dateString}\n')

# ========== MAIN ==========
encodeListKnown = findEncodings(images)
print("Encoding Complete")

cap = cv2.VideoCapture(0)

while True:
    success, img = cap.read()

    if not success:
        print("Camera not working")
        break

    imgS = cv2.resize(img, (0,0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    facesCurFrame = face_recognition.face_locations(imgS)
    encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

        matchIndex = np.argmin(faceDis)

        if matches[matchIndex] and faceDis[matchIndex] < 0.5:
            name = classNames[matchIndex]
            uid, student_class, course = getStudentDetails(name)
            color = (0,255,0)
            status = "PRESENT"
        else:
            name = "INVALID"
            uid, student_class, course = "NA", "NA", "NA"
            color = (0,0,255)
            status = "INVALID"

        # SCALE BACK
        y1, x2, y2, x1 = faceLoc
        y1, x2, y2, x1 = y1*4, x2*4, y2*4, x1*4

        # DRAW BOX
        cv2.rectangle(img,(x1,y1),(x2,y2),color,2)
        cv2.rectangle(img,(x1,y2-70),(x2,y2),color,cv2.FILLED)

        # DISPLAY TEXT
        cv2.putText(img, name, (x1+6,y2-45),
                    cv2.FONT_HERSHEY_COMPLEX, 0.7, (255,255,255),2)

        info = f"{uid} | {student_class} | {course} | {status}"
        cv2.putText(img, info, (x1+6,y2-10),
                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (255,255,255),1)

        markAttendance(name, uid, student_class, course, status)

    cv2.imshow('Face Attendance System', img)

    if cv2.waitKey(1) == 13:
        break

cap.release()
cv2.destroyAllWindows()