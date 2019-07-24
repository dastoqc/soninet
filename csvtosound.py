import csv
import math
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pygame, pygame.sndarray

class CreateSound(object):
    def __init__(self):
        self.sampleRate = 44100
        # 44.1kHz, 16-bit signed, mono
        pygame.mixer.init(self.sampleRate, size=16, channels=2, buffer=4096)
        pygame.init()
        self.channels = [[pygame.mixer.Channel(1),None,-1],[pygame.mixer.Channel(2),None,-1]]
        self.snds = [pygame.mixer.Sound('audio_files/bell001.flac'),pygame.mixer.Sound('audio_files/bell002.flac')]
        for index, channel_tuple in enumerate(self.channels):
            print('Test for ', index)
            channel_tuple[0].play(self.snds[index])
            time.sleep(1)

    def speedx(self, snd_array, factor):
        """ Speeds up / slows down a sound, by some factor. """
        indices = np.round(np.arange(0, len(snd_array), factor))
        indices = indices[indices < len(snd_array)].astype(int)
        return snd_array[indices]

    def stretch(self, snd_array, factor, window_size, h):
        """ Stretches/shortens a sound, by some factor. """
        phase = np.zeros(window_size)
        hanning_window = np.hanning(window_size)
        result = np.zeros(int(len(snd_array) / factor + window_size))

        for i in np.arange(0, len(snd_array) - (window_size + h), h*factor):
            i = int(i)
            # Two potentially overlapping subarrays
            a1 = snd_array[i: i + window_size]
            a2 = snd_array[i + h: i + window_size + h]

            # The spectra of these arrays
            s1 = np.fft.fft(hanning_window * a1)
            s2 = np.fft.fft(hanning_window * a2)

            # Rephase all frequencies
            phase = (phase + np.angle(s2/s1)) % 2*np.pi

            a2_rephased = np.fft.ifft(np.abs(s2)*np.exp(1j*phase))
            i2 = int(i/factor)
            result[i2: i2 + window_size] += hanning_window*a2_rephased.real

        # normalize (16bit)
        result = ((2**(16-4)) * result/result.max())

        return result.astype('int16')

    def pitchshift(self, snd_array, n, window_size=2**13, h=2**11):
        """ Changes the pitch of a sound by ``n`` semitones. """
        factor = 2**(1.0 * n / 12.0)
        stretched = self.stretch(snd_array, 1.0/factor, window_size, h)
        return self.speedx(stretched[window_size:], factor)

    def play(self, vol, semitone, chan):
        channel_tuple = self.channels[chan]
        if channel_tuple[0].get_busy() != 1:
            channel_tuple[1] = pygame.mixer.Sound(self.pitchshift(pygame.sndarray.array(self.snds[chan]), semitone))
            channel_tuple[1].set_volume(vol)

            channel_tuple[0].play(channel_tuple[1])


class AnimatedScatter(object):
    """An animated scatter plot using matplotlib.animations.FuncAnimation."""
    def __init__(self, posall, hop1all, hop2all, numpoints=10):
        self.numpoints = numpoints
        self.posall = posall
        self.hop1all = hop1all
        self.hop2all = hop2all
        self.selectID = 0
        self.CS = CreateSound()
        self.minmax = [-6, 6, -6, 6]
        # Setup the figure and axes...
        self.fig, self.ax = plt.subplots()
        # Then setup FuncAnimation.
        self.ani = FuncAnimation(self.fig, self.update, interval=100,
                                          init_func=self.setup_plot, blit=True)

    def setup_plot(self):
        """Initial drawing of the scatter plot."""
        self.scat = self.ax.scatter([0,0,0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0,0,0])
        self.ax.axis(self.minmax)
        # For FuncAnimation's sake, we need to return the artist we'll be using
        # Note that it expects a sequence of artists, thus the trailing comma.
        return self.scat,

    def updatesound(self, cnt):
        # Scale the values to fit sine wave generation
        semitone1 = round(self.hop1all[self.selectID][cnt][0]/self.numpoints*12)
        maxdist = math.sqrt((self.minmax[1]-self.minmax[0])*(self.minmax[1]-self.minmax[0])+(self.minmax[3]-self.minmax[2])*(self.minmax[3]-self.minmax[2]))
        vol1 = 1 - self.hop1all[self.selectID][cnt][1]/(maxdist/2)
        semitone2 = round(self.hop2all[self.selectID][cnt][0]/self.numpoints*12)
        vol2 = 1 - self.hop2all[self.selectID][cnt][1]/(maxdist/2)
        print(vol1, self.hop1all[self.selectID][cnt][1], semitone1, vol2, self.hop2all[self.selectID][cnt][1], semitone2)
        self.CS.play(vol1, semitone1, 0)
        self.CS.play(vol2, semitone2, 1)

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


if __name__ == "__main__":

    src_csv = 'log/Robot_'
    posall = {}
    hop1all = {}
    hop2all = {}

    # Parse the CSVs
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
                    x.append(float(row[3+nei*4+2])/100)
                    y.append(float(row[3+nei*4+3])/100)
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
                        x.append(float(row[3+nei*4+2])/100)
                        y.append(float(row[3+nei*4+3])/100)
                        #print(x,y)
                    ave = math.sqrt(Average(x)*Average(x)+Average(y)*Average(y))
                else:
                    ave = 0
                hop2all[rid].append([int(row[4+int(row[3])*4]),ave])
            else:
                hop2all[rid].append([0,0])
            i = i + 1

    # Start the scatter plot animation with sound
    a = AnimatedScatter(posall,hop1all,hop2all)
    plt.show()
