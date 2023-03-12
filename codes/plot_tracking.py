import csv
import numpy as np
import matplotlib.pyplot as plt
import math

"""
exporting the tracking output from PS_exp_2
"""

name_file_1 = "out_PS_"
name_file_2 = input("out_PS_")
with open(f"../tracking output/{name_file_1}{name_file_2}.csv", "r") as f:
    reader = csv.reader(f)
    trace = [ e for e in reader ]

# Remove "New File" line
trace = trace[1:]
# Get indices of experiments (plus the end index of the last experiment)
idx = [trace.index(list("PS1")), trace.index(list("PS2")), trace.index(list("PS3")), trace.index(list("PS4")), len(trace)]
# if experiments looped, get the index of where the loop starts (we do not care for values of the second loop)
if list("PS0") in trace:
    # negative indices index an array starting from the end
    # This means that this [-1] indexes the last value of the array
    idx[-1] = trace.index(list("PS0"))
# split trace-list by experiment-index
trace_PS = [trace[:idx[0]], trace[idx[0]+1:idx[1]], trace[idx[1]+1:idx[2]], trace[idx[2]+1:idx[3]], trace[idx[3]+1:idx[4]]]
    
trace_list_with_time = [[],[],[],[],[]]
trace_list = [[],[],[],[],[]]

for i, v in enumerate(trace_PS) :
    trace_list_with_time[i] = np.array(v)
    trace_list[i] = np.delete(trace_list_with_time[i], 3, 1)


x_PS = [[],[],[],[],[]]
y_PS = [[],[],[],[],[]]
color_PS = [[],[],[],[],[]]

for i, p in enumerate(trace_list) :
    plt.figure()
    x_PS[i] = np.float_(p[:, 0])
    y_PS[i] = np.float_(p[:, 1])
    color_PS[i] = np.float_(p[:, 2])
    plt.scatter(x_PS[i], y_PS[i], s = 10, c=color_PS[i], cmap='Blues',vmin=0.1, vmax=1.0)
    plt.text(60,102,f"Average: {str(round(20 * math.log10(np.mean(color_PS[i])), 3))} dB", size = 'large')
    plt.xlim(100.0, 0.0)
    plt.ylim(0.0, 100.0)
    plt.colorbar()
    plt.title(label = (f"{name_file_2}_PS{i}") ,loc = 'left')
    plt.savefig(f"../tracking plot/{name_file_2}_PS{i}.png")

