from fileinput import filename
import cv2
import numpy as np
import pygame.mixer
import math
import csv
import datetime
aruco = cv2.aruco
dictionary = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)


def loadSoundMap(soundMap_list): #loads csv of SoundMap, which is being used in volume Control
    soundMap_load_list = []
    for v in soundMap_list :
        with open(f"../sound map csv/soundMap_{v}.csv", "r") as f:
            reader = csv.reader(f)
            soundMap = [ e for e in reader ]
            soundMap_float = list(np.float_(soundMap))
            soundMap_load_list.append(soundMap_float)

    soundMap_load_tuple = tuple(soundMap_load_list)
    return soundMap_load_tuple


def calibratePerspective(img): #making the coordinate system using 4 AR codes, here makes 200*200

    corners, ids = aruco.detectMarkers(img)
    #to store the 4 AR codes' coorinate
    p = np.empty((4, 2))
    corners_data = [np.empty((1, 4, 2))] * 4
    fourARcode = False

    while True:

        if ids is None:
            cv2.putText(img, 'None Found', (400, 360), cv2.FONT_HERSHEY_PLAIN, 5, (0, 0, 255), 4, cv2.LINE_AA)
            break
        
        #0から3番のARマーカー4つの座標を取得する
        idList = ids.ravel()
        if idList.size == 4 and np.any(idList == 4) == True:
            cv2.putText(img, 'A calibrate marker Missing', (100, 300), cv2.FONT_HERSHEY_PLAIN, 5, (0, 0, 255), 4, cv2.LINE_AA)
            fourARcode = False
        elif idList.size >= 4:
            fourARcode = True
        else :
            cv2.putText(img, 'Put 4 AR markers', (300, 300), cv2.FONT_HERSHEY_PLAIN, 5, (0, 0, 255), 4, cv2.LINE_AA)

        for i, c in zip(idList, corners): #iがidsのことで、cがcornersに対応
            cv2.putText(img, 'Calibrating...', (400, 360), cv2.FONT_HERSHEY_PLAIN, 5, (0, 255, 0), 4, cv2.LINE_AA)
            if i <= 3:
                corners_data[i] = c.copy()
                
        break

    


    #uses each corners of AR codes
    p[0] = corners_data[0][0][0] #AR code placed in left top, and uses the left bottom corner coordinate
    p[1] = corners_data[1][0][1] #AR code placed in right top, and uses the right bottom corner coordinate
    p[2] = corners_data[2][0][2] #AR code placed in left bottom, and uses the left top corner coordinate
    p[3] = corners_data[3][0][3] #AR code placed in right bottom, and uses the right top corner coordinate

    """
    print("p[0]")
    print(p[0])
    print("p[1]")
    print(p[1])
    print("p[2]")
    print(p[2])
    print("p[3]")
    print(p[3])
    """

    pt1 = np.float32([p[0], p[1], p[2], p[3]]) #coordinates for trimming
    pt2 = np.float32([[0, 0], [200, 0], [200, 200], [0, 200]]) #converts to 200*200 coordinate system

    return pt1, pt2, fourARcode



def volumeControl(center, SoundMap): #controls the volume depending on the coordinate it receives
    
    x = int(center[0])
    y = int(center[1])
    volume = SoundMap[x][y] #takes the parameter in the list of SoundMap

    if volume <= 0.1: #prevents the volume to be lower than -20db
        volume = 0.1

    pygame.mixer.music.set_volume(volume)
    return volume


def arReader(cap, soundMap_tuple, writer): #mainly works in while loop to keep tracking the AR marker

    center  = [0,0] #initial value to prevent error
    idnumber = 4 #markers ID is 4, which this program tracks
    pt1, pt2 = (0,0)  #initial value to prevent error
    volume = 1 #volume is full in the beginning
    PersonalSound = 0 #personal sound field starts from 0, which is not a personal sound. so it wont change the volume no matter the coordinate is
    SoundMap = soundMap_tuple[PersonalSound] #there are 5 sound maps(including non-PersonalSoundField), it starts with 0

    while True:

        ret, frame = cap.read()
        Height, Width = frame.shape[:2]
        img_mirrored = cv2.resize(frame,(int(Width),int(Height))) 
        img = cv2.flip(img_mirrored, -1) #mirror the camera bc of the placement

        while True:
            if count == 11:
                print('Done calibration')
            elif count > 10:
                break
            #print(count)
            pt1, pt2, fourARcode = calibratePerspective(img) #coordinate pt1 which is made with 4 AR codes
            if fourARcode == True:
                count = count + 1
            break
            

        #transform the perspective
        gPT = cv2.getPerspectiveTransform(pt1, pt2) #transform from pt1 to pt2
        dst = cv2.warpPerspective(img, gPT, (200, 200)) #warped perspective is dst, resolution is 200*200
        #detect markers from dst
        corners, ids, rejectedImgPoint = aruco.detectMarkers(dst, dictionary)
        aruco.drawDetectedMarkers(dst, corners, ids, (0, 255, 0))


        #get the coordinate of the center of AR code by using coordinates of corners
        if idnumber in np.ravel(ids) :
            index = (np.where(ids == idnumber)[0][0]) #index is not ID Number, its an index of the recognized AR codes, and ids have the index like (array([0]), array([0])), so by writing [0][0], you get the index
            cornerUL = corners[index][0][0]
            cornerBR = corners[index][0][2]

            #here its supposed to devide by 2, but the dst resolution is 200*200, so by doing /4, it can act like 100*100
            center = [ (cornerUL[0]+cornerBR[0])/4 , (cornerUL[1]+cornerBR[1])/4 ] #caluclate the average of corners to get the middle coordinate,center
        
        #センターの座標をリストに追加
        if center[0] != 50 and center[1] != 50:
            center_save = center[0], center[1], volume, datetime.datetime.now() #write the coordinate, volume, and time
            writer.writerow(center_save)


        volume = volumeControl(center, SoundMap) #volumeControl will change the colume depending on center
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) #cameras resolution for width
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) #cameras resolution for height
        displayWindows(img, dst, center, volume, w, h, pt1) #displays windows

        key = cv2.waitKey(1) & 0xFF #waits for the key command

        if key == ord('q'): #when q is pressed, it quits the while loop
            print("quit")
            break
        
        elif key == ord('m'): #when m is pressed, it changes the personal sound
            PersonalSound = personalSoundSwitch(PersonalSound, writer)
            SoundMap = soundMap_tuple[PersonalSound]


    cap.release() #release cap
    cv2.destroyAllWindows() #shut down all of the windows


def displayWindows(img, dst, center, volume, width, height, pt1):
        #when the resolution is [100,100], the middle of coordinate would be [50,50]. but to display, I made it look like [0,0] is the middle by doing -50 on each coordinate. this changes depending on the dst's resolution
        cv2.putText(img, f"Coordinate : ({str(center[0] - 50)} , {str(center[1] - 50)}) cm", (50, 100), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 2, cv2.LINE_AA) #center's coordinate on img
        cv2.putText(img, f"Volume : {str(round(20 * math.log10(volume), 3))} dB", (50, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 2, cv2.LINE_AA) #Volume is in dB, and let users see how many dB it went down from the reference point

        color = (255, 0, 0) #blue
        cv2.line(img, (0, height/2), (width, height/2), color,2) #line that goes thru middle horizontally
        cv2.line(img, (width/2, 0), (width/2, height), color,2) #line that goes thru middle vertically

        #just the line to show the calibrated area
        cv2.line(img, (0, int(pt1[0][1])), (width, int(pt1[1][1])), color)
        cv2.line(img, (0, int(pt1[2][1])), (width, int(pt1[3][1])), color)
        cv2.line(img, (int(pt1[0][0]), 0), (int(pt1[3][0]), height), color)
        cv2.line(img, (int(pt1[1][0]), 0), (int(pt1[2][0]), height), color)

        cv2.imshow('drawDetectedMarkers', img) #show img

        cv2.line(dst, (0, 100), (200, 100), color) 
        cv2.line(dst, (100, 0), (100, 200), color)
        #cv2.flip(dst, 0) #flip dst
        cv2.imshow('cropped', dst) #show dst



def personalSoundSwitch(PersonalSound, writer): #it switches the personal sound, it goes 0-4, then when it reaches 5, it goes back to 0.
    PersonalSound += 1
    PersonalSound %= 5

    print(f"PersonalSound {PersonalSound}")
    writer.writerow(f"PS{PersonalSound}")
    return PersonalSound




def main():

    #soundMapNum = input("soundMap_")
    soundMap_list = [ "NoPS" , "4" , "5" , "4_ver2" , "5_ver2" ]
    soundMap_tuple = loadSoundMap(soundMap_list)
    cap = cv2.VideoCapture(0) #video from camera
    outName = input("out_PS_2_")
    musicName = input("Name of the music?:")
    pygame.mixer.init() #initial
    pygame.mixer.music.load(f"../music/{musicName}.mp3") 
    pygame.mixer.music.play(-1) #-1 means infinite loop

    with open(f"../tracking output/out_PS_2_{outName}.csv", 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow("New File")
        arReader(cap,soundMap_tuple, writer) #this starts the tracking


if __name__ == "__main__":
    main()