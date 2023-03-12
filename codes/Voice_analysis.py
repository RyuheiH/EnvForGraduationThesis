import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import sys
import warnings
import csv
import os

"""
Under the value of "threshold_Volume dBFS", this program makes them NaN, this is to prevent pyin method from masuring another persons voice
high pitch voice will be removed(outlier from boxplot)
"""

threshold_Volume = -48 #dBFS #-48dBFS is the standard
threshold = (f"_{threshold_Volume}dBFS")

#--------- f0 estimation ---------------
directory = ("../recorded voice/")
filename = ["Test_Jan_11"] #you can put several file names here
experiment_type = ["_RoadNoise","_NoPS","_PS1","_PS2","_PS3","_PS4"]
filetype = (".wav")





for f in range(len(filename)):
    print(filename[f])

    for i in range(len(experiment_type)):

        print(filename[f] + experiment_type[i])
        with warnings.catch_warnings(): #ignore warnings coming out of this loading
            warnings.simplefilter("ignore")
            y, sr = librosa.load(directory + filename[f] + experiment_type[i] +filetype) #gets the voice file


        #caluclate the fundamental voice frequency
        f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), no_trough_prob = 0) #this no_through_prob makes the estimation more strict with 0
        #get the time axis
        times_f0 = librosa.times_like(f0)
        times = librosa.times_like(f0)


        #--------- rsm dB analysis ---------------
        S, phase = librosa.magphase(librosa.stft(y))
        rms = librosa.feature.rms(S=S)
        #get time axis
        times_rms = librosa.times_like(rms)

        rms_float = np.array(list(np.float_(rms)))
        rms_dB = [20 * np.log10(n) for n in rms_float]


        #--------- check if time axis are matching, because this time values are used to put f0 and rms lists together ---------------
        if np.allclose(times_f0, times_rms) == True: 
            print("matching")
        else :
            print("Not matching")
            sys.exit()


        f0_rms = np.vstack((f0, rms_dB)) #f0とrms are put into 2 dementional array
        #the voice lower than the threshold_Volume will be NaN
        f0_rms_ExSV = np.where((f0_rms[1, :] < threshold_Volume), np.nan, f0_rms) 

        #this gets rid of Nan to caluclate Q25 and Q75, this process is needed to determine the outlier---------
        f0_rms_ExNanSV = (f0_rms_ExSV[:, ~np.isnan(f0_rms_ExSV).any(axis=0)]) #getting rid of Nan
        f0_ExNanSV = f0_rms_ExNanSV[0,:] #only f0 is needed for caluclation
        f0_q75, f0_q25 = np.percentile(f0_ExNanSV, [75 ,25]) #Q25 and Q75
        iqr = f0_q75 - f0_q25 #iqr
        #------------------------------------------------------

        f0_rms_ExSVHP = np.where((((f0_q25 - iqr * 1.5) > f0_rms_ExSV[0, :])
            | (f0_rms_ExSV[0, :] > (f0_q75 + iqr * 1.5))), 
            np.nan, f0_rms_ExSV) #when f0 is in the range of outlier, it gets replaced to NaN

        f0_rms_ExNanSVHP = (f0_rms_ExSVHP[:, ~np.isnan(f0_rms_ExSVHP).any(axis=0)]) #getting rid of Nan from the column

        new_average_rms = round(np.mean(f0_rms_ExNanSVHP[1,:]),2)
        new_f0_q75, new_f0_q25 = np.percentile(f0_rms_ExNanSVHP[0,:], [75 ,25])

        print("Average rms:"+ str(new_average_rms) + "dBFS(rms)")
        print("Q25% pitch:"+ str(round(new_f0_q25,2)) + "Hz")
            


        #plotting here-------------------------------------
        D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
        fig, ax = plt.subplots(nrows=2, sharex=True) #make 2 figure, x axis is shared

        #plotting rms
        ax[0].semilogy(times, f0_rms_ExSVHP[1, :], label='RMS Energy')
        ax[0].set_yscale('linear')
        ax[0].legend(loc='upper right')
        ax[0].set_title(label = filename[f] + experiment_type[i],loc = 'right')

        #plotting f0
        img = librosa.display.specshow(D, x_axis='time', y_axis='log', ax=ax[1])
        ax[1].plot(times, f0_rms_ExSVHP[0, :], label='f0', color='cyan', linewidth=3)
        ax[1].legend(loc='upper right')
        ax[1].text(0, 1.05, f"Q25% pitch: {str(round(new_f0_q25,2))}  Hz", transform=ax[1].transAxes,size = 'large')
        ax[1].text(0, 2.25, f"Average rms: {str(new_average_rms)}  dBFS(rms)", transform=ax[1].transAxes,size = 'large')
        ax[1].set_title(label = filename[f] + experiment_type[i] ,loc = 'right')

        plt.savefig("../analysed voice/"+ filename[f] + experiment_type[i] + threshold + ".png")
        #plt.show()
        plt.close()

        #-----------------------

        #output to a csv file-------------------------------------
        with open(f"../Voice numbers/Voice stats.csv", 'a', newline='') as f_w:
            writer = csv.writer(f_w)
            Voice_stats = [filename[f] + experiment_type[i]+ threshold,"dBFS(rms)",new_average_rms,"Q25 Hz",str(round(new_f0_q25,2))]
            writer.writerow(Voice_stats)
        #-------------------------------------






