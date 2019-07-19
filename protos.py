import pygame, pygame.sndarray
import time
import numpy as np

def speedx(snd_array, factor):
    """ Speeds up / slows down a sound, by some factor. """
    indices = np.round(np.arange(0, len(snd_array), factor))
    indices = indices[indices < len(snd_array)].astype(int)
    return snd_array[indices]

def stretch(snd_array, factor, window_size, h):
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

def pitchshift(snd_array, n, window_size=2**13, h=2**11):
    """ Changes the pitch of a sound by ``n`` semitones. """
    factor = 2**(1.0 * n / 12.0)
    stretched = stretch(snd_array, 1.0/factor, window_size, h)
    return speedx(stretched[window_size:], factor)

sampleRate = 44100
# 44.1kHz, 16-bit signed, mono
pygame.mixer.pre_init(sampleRate, -16, 1)
pygame.mixer.init()

snd = pygame.mixer.Sound('medias/bell.wav')
# transposition in semitones, see table in README
sndUni = pygame.mixer.Sound(pitchshift(pygame.sndarray.array(snd), 0))
sndThird = pygame.mixer.Sound(pitchshift(pygame.sndarray.array(snd), 4))
sndFift = pygame.mixer.Sound(pitchshift(pygame.sndarray.array(snd), 7))

for i in range(12):
    if i % 2:
        sndUni.play()
    elif i % 3:
        sndFift.play()
    else:
        sndThird.play()
    time.sleep(0.5)
