import csv
from PIL import Image
import numpy as np
from matplotlib import pyplot as plt

"""
This program turns jpg images of soundmaps into csv files which is conpatible with PS_exp.py.
This will also creates csv files in dB parameter, which is used to make a heatmap, which is a better visualization.
"""

#------------convert to csv from jpg------------------------------------------------
filename = "soundMap_"
filenum = input("Which jpg image do you wanna make it into csv, dB csv, and heatmap? : soundMap_")
imgtype = ".jpg"
exportType = ".csv"

#import the image
img = Image.open(f"../sound map image/{filename}{filenum}{imgtype}")

#convert into black and white picture, L for luminance
img = img.convert("L")
width, height = img.size

#get the brightness(since it is black and white, the data you get is luminance only, not RGB)
data = list(img.getdata())

#the numbers in the list will be 0-255, but the parameter used in the experiment is 0-1, so devide them with 255d
def data_calc(n):
    return n / 255


data_2 = list(map(data_calc, data))


with open("../sound map csv/" + filename + filenum + exportType, 'w', newline='') as csvfile: #save brightness on a csv file
    spamwriter  = csv.writer(csvfile)

    #get the data by each row, and it puts all the data of column
    x = 0
    for y in range(height):
        #data of the row
        line_data = data_2[x:x+width]
        #write the data from the row
        spamwriter.writerow(line_data)
        x += width
#------------------------------------------------------------


#------------convert to dB------------------------------------------------
importType = ".csv"

with open(f"../sound map csv/{filename}{filenum}{importType}", "r") as f:
    reader = csv.reader(f)
    data = [ e for e in reader ]
    data_float = np.array(list(np.float_(data)))
    
#mainly data is over -20dB, which is 0.1 in parameter. in case it goes under 0.1, it puts back to 0.1
data_float = (np.where(data_float <= 0.1, 0.1 , data_float))
data_dB = [20 * np.log10(n) for n in data_float]

with open(f"../sound map csv/{filename}{filenum}_dB.csv", 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(data_dB)
#------------------------------------------------------------



#------------plot a heatmap------------------------------------------------
data = np.loadtxt(f"../sound map csv/{filename}{filenum}_dB.csv", delimiter=",")
plt.imshow(data, aspect="auto", interpolation = "none",cmap='RdBu_r')
plt.colorbar()
plt.text(-10, 105, "cm")
plt.text(106, -3, "dB")
plt.savefig(f"../heatmap/{filename}{filenum}_heatmap_dB" + ".png")
plt.show()
#------------------------------------------------------------