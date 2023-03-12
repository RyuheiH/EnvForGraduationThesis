from fileinput import filename
import cv2
import numpy as np
import pygame.mixer
import math
import csv
import datetime


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


def volumeControl(center, SoundMap): #controls the volume depending on the coordinate it receives
    
    x = int(center[0])
    y = int(center[1])
    volume = SoundMap[x][y] #takes the parameter in the list of SoundMap

    if volume <= 0.1: #prevents the volume to be lower than -20db
        volume = 0.1

    pygame.mixer.music.set_volume(volume)
    return volume


def arReader(cap, soundMap_tuple, writer): #mainly works in while loop to keep tracking the AR marker
    aruco = cv2.aruco
    dictionary = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)

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

        pt1 = np.float32([[1450,1000], [500,1000], [500,50],[1450,50]]) #this is the trimming coordinates, this is already calibrated but usually uses calibration
        pt2 = np.float32([[0, 0], [200, 0], [200, 200], [0, 200]]) #this is warped coordinates

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
        displayWindows(img, dst, center, volume, w, h) #displays windows

        key = cv2.waitKey(1) & 0xFF #waits for the key command

        if key == ord('q'): #when q is pressed, it quits the while loop
            print("quit")
            break
        
        elif key == ord('m'): #when m is pressed, it changes the personal sound
            PersonalSound = personalSoundSwitch(PersonalSound, writer)
            SoundMap = soundMap_tuple[PersonalSound]


    cap.release() #release cap
    cv2.destroyAllWindows() #shut down all of the windows


def displayWindows(img, dst, center, volume, width, height):
        #when the resolution is [100,100], the middle of coordinate would be [50,50]. but to display, I made it look like [0,0] is the middle by doing -50 on each coordinate. this changes depending on the dst's resolution
        cv2.putText(img, f"Coordinate : ({str(center[0] - 50)} , {str(center[1] - 50)}) cm", (50, 100), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 2, cv2.LINE_AA) #center's coordinate on img
        cv2.putText(img, f"Volume : {str(round(20 * math.log10(volume), 3))} dB", (50, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 2, cv2.LINE_AA) #Volume is in dB, and let users see how many dB it went down from the reference point


        color = (255, 0, 0) #blue
        halfHeight = int(height/2)
        halfWidth = int(width/2)
        cv2.line(img, (0, halfHeight), (width, halfHeight), color,2) #line that goes thru middle horizontally
        cv2.line(img, (halfWidth, 0), (halfWidth, height), color,2) #line that goes thru middle vertically
        
        #just the line to show the calibrated area
        cv2.line(img, (0, 1000), (width, 1000), color)
        cv2.line(img, (0, 50), (width, 50), color)
        cv2.line(img, (1450, 0), (1450, height), color)
        cv2.line(img, (500, 0), (500, height), color)

        cv2.imshow('drawDetectedMarkers', img) #show img

        cv2.line(dst, (0, 100), (200, 100), color) 
        cv2.line(dst, (100, 0), (100, 200), color)

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
    outName = input("date? : out_PS_2_")
    userName = input("Name of the participant?:")
    with open(f"../music/Music_list.csv", "r") as f:
        reader = csv.reader(f)
        musicName = [ e for e in reader ]
        musicName = np.array(musicName)
    index = np.argwhere(musicName == userName) #look for the index of music that corresponds to the user name
    pygame.mixer.init() #initial
    #the reason why it is index[0][0] is that argwhere returns variable in the same shape of NDarray, 
    # thus in this case 2 dementional, so even I get only 1 row, I have to say the row as well. and the colunm
    pygame.mixer.music.load(f"../music/{musicName[index[0][0]][1]}.mp3") #corresponding music for the user name in music_list
    pygame.mixer.music.play(-1) #-1 means infinite loop
    with open(f"../tracking output/out_PS_2_{outName}_{userName}.csv", 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow("New File")
        arReader(cap,soundMap_tuple, writer) #this starts the tracking


if __name__ == "__main__":
    main()