#!/usr/bin/env python
from datetime import datetime
from math import pow
from random import randrange
import struct
import sys
import time
import wave

import pyaudio
from colorama import Fore, init as colorama_init
colorama_init(autoreset=True)


# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
SHORT_NORMALIZE = 1.0/32768.0

# Minimum treshold (RMS) to reach to start the record.
THRESHOLD = 130

# Timeout in minutes before record start.
RECORD_DELAY_FROM = 10
RECORD_DELAY_TO = 20

# How many minutes to record.
RECORD_LENGTH = 5

# Colors for RMS terminal output.
RMS_COLORS = {
    '0': Fore.WHITE,
    '1': Fore.GREEN,
    '2': Fore.YELLOW,
    '3': Fore.RED
}


class WTF(object):
    def __init__(self):
        self.pyaudio_obj = pyaudio.PyAudio()
        self.stream = self.pyaudio_obj.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            output=True,
            frames_per_buffer=CHUNK
        )

    def run(self):
        start_text = "Analyzing the sound. [{0}]".format(datetime.now())
        print start_text
        print '_' * len(start_text)

        while True:
            input = self.stream.read(CHUNK)
            rms_value = self.get_rms(input)
            rms_color = RMS_COLORS.get(str(int(rms_value * 3 / THRESHOLD)), 4)
            sys.stdout.write(rms_color + "\r{0}".format(rms_value))
            sys.stdout.flush()

            if (rms_value > THRESHOLD):
                print Fore.RESET + "\nThreshold reached {0}. [{1}]".format(
                    THRESHOLD,
                    datetime.now()
                )
                timeout_minutes = randrange(RECORD_DELAY_FROM, RECORD_DELAY_TO)
                print "Waiting {0} minutes timeout.".format(timeout_minutes)
                for minute in xrange(0, timeout_minutes):
                    minutes_left = timeout_minutes - minute
                    print "{0} minute{1} left.".format(
                        minutes_left,
                        '' if minutes_left == 1 else 's'
                    )
                    time.sleep(1)

    @staticmethod
    def get_rms(frame):
        """Returns RMS for a given frame of sound"""
        count = len(frame) / 2
        format = "%dh" % (count)
        shorts = struct.unpack(format, frame)
        sum_squares = 0.0

        for sample in shorts:
            n = sample * SHORT_NORMALIZE
            sum_squares += n * n

        rms = pow(sum_squares/count, 0.5)

        return int(rms * 1000)

    def save_audio(self, audio_data=None, file_path=''):
        """Stop the stream, terminate PyAudio. Save the data."""
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio_obj.terminate()

        if audio_data and file_path:
            wf = wave.open(file_path, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.pyaudio_obj.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(audio_data)
            wf.close()
        else:
            print "No audio data or wrong file path."


"""Start the app"""
if __name__ == "__main__":
    import wtf
    wtf = wtf.WTF()
    wtf.run()
