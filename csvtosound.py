import csv
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pygame, pygame.sndarray

sampleRate = 44100
# 44.1kHz, 16-bit signed, mono
pygame.mixer.pre_init(sampleRate, -16, 1)
pygame.init()

class AnimatedScatter(object):
    """An animated scatter plot using matplotlib.animations.FuncAnimation."""
    def __init__(self, posall, hop1all, hop2all, numpoints=10):
        self.numpoints = numpoints
        self.posall = posall
        self.hop1all = hop1all
        self.hop2all = hop2all
        self.selectID = 0
        self.channels = [[pygame.mixer.Channel(1),None,-1],[pygame.mixer.Channel(2),None,-1]]

        # Setup the figure and axes...
        self.fig, self.ax = plt.subplots()
        # Then setup FuncAnimation.
        self.ani = FuncAnimation(self.fig, self.update, interval=5,
                                          init_func=self.setup_plot, blit=True)

    def setup_plot(self):
        """Initial drawing of the scatter plot."""
        self.scat = self.ax.scatter([0,0,0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0,0,0])
        self.ax.axis([-8, 8, -8, 8])
        # For FuncAnimation's sake, we need to return the artist we'll be using
        # Note that it expects a sequence of artists, thus the trailing comma.
        return self.scat,

    def updatesound(self, cnt):
        # Scale the values to fit sine wave generation
        freq1 = self.hop1all[self.selectID][cnt][0]*35+120
        vol1 = 8000 - self.hop1all[self.selectID][cnt][1]*50
        freq2 = self.hop2all[self.selectID][cnt][0]*35+120
        vol2 = 8000 - self.hop2all[self.selectID][cnt][1]*50
        print(vol1, freq1, vol2, freq2)
        # generation the sine wave data
        arr1 = np.array([vol1 * np.sin(2.0 * np.pi * freq1 * x / sampleRate) for x in range(0, int(1.4*sampleRate))]).astype(np.int16)
        arr2 = np.array([vol2 * np.sin(2.0 * np.pi * freq2 * x / sampleRate) for x in range(0, int(1.4*sampleRate))]).astype(np.int16)
        # play (2 channels avalaible)
        for index, channel_tuple in enumerate(self.channels):
            if channel_tuple[0].get_busy() != 1:
                if(index==0):
                    channel_tuple[1] = pygame.sndarray.make_sound(arr1)
                else:
                    channel_tuple[1] = pygame.sndarray.make_sound(arr2)
                try:
                    channel_tuple[0].play(channel_tuple[1])
                except:
                    pass

    def update(self, cnt):
        """Update the scatter plot."""

        # Set x and y data...
        xy = np.array([self.posall[0][cnt],self.posall[1][cnt],self.posall[2][cnt],self.posall[3][cnt],self.posall[4][cnt],self.posall[5][cnt],self.posall[6][cnt],self.posall[7][cnt],self.posall[8][cnt],self.posall[9][cnt]])
        self.scat.set_offsets(xy)
        # Set sizes...
        #self.scat.set_sizes(300 * abs(data[:, 2])**1.5 + 100)
        # Set colors..
        col = np.array([20,20,20,20,20,20,20,20,20,20])
        col[self.selectID] = 1
        self.scat.set_array(col)

        self.updatesound(cnt)

        return self.scat,

def Average(lst):
    return sum(lst) / len(lst)

src_csv = 'log/Robot_'
posall = {}
hop1all = {}
hop2all = {}

for rid in range(0,10):
    csvfile = open(src_csv+str(rid), 'r')
    reader = csv.reader(csvfile, delimiter=',', lineterminator='\n')
    row_count = sum(1 for row in reader)
    print(str(rid), " has ", row_count, " lines")
    csvfile.seek(0)
    posall[rid]=[]
    hop1all[rid]=[]
    hop2all[rid]=[]
    i = 0

    for row in reader:
        posall[rid].append([float(row[0]),float(row[1])])
        x = []
        y = []
        if int(row[3])>0:
            for nei in range(0,int(row[3])):
                x.append(float(row[3+nei*4+2]))
                y.append(float(row[3+nei*4+3]))
                #print(x,y)
            ave = math.sqrt(Average(x)*Average(x)+Average(y)*Average(y))
        else:
            ave = 0
        hop1all[rid].append([int(row[3]),ave])
        #print(int(row[3]))
        if(len(row)>12):
            #print(i,len(row),int(row[3]),int(row[4+int(row[3])*4]))
            if int(row[4+int(row[3])*4])>0:
                x = []
                y = []
                for nei in range(0,int(row[4+int(row[3])*4])):
                    x.append(float(row[3+nei*4+2]))
                    y.append(float(row[3+nei*4+3]))
                    #print(x,y)
                ave = math.sqrt(Average(x)*Average(x)+Average(y)*Average(y))
            else:
                ave = 0
            hop2all[rid].append([int(row[4+int(row[3])*4]),ave])
        else:
            hop2all[rid].append([0,0])
        i = i + 1
#print(hop2all)
a = AnimatedScatter(posall,hop1all,hop2all)
plt.show()
