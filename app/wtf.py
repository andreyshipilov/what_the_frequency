#!/usr/bin/env python
from __future__ import print_function
from datetime import datetime
from math import pow
from os import makedirs
from os.path import abspath, join, dirname, exists
from random import randrange
import struct
import sys
import time
import wave

import pyaudio
from processing import create_wave_images, convert_to_mp3
from colorama import Fore, init as colorama_init
colorama_init(autoreset=True)


# Reset some settings if Debugging.
DEBUG = True

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
SHORT_NORMALIZE = 1.0/32768.0

# Minimum treshold (RMS) to reach to start the record.
THRESHOLD = 130

# Timeout in minutes before record start.
RECORD_DELAY_FROM = 1 if DEBUG else 10
RECORD_DELAY_TO = 2 if DEBUG else 20

# How many minutes to record.
RECORD_LENGTH = 5 if DEBUG else 60 * 5

# Colors for RMS terminal output.
RMS_COLORS = {
    '0': Fore.WHITE,
    '1': Fore.GREEN,
    '2': Fore.YELLOW,
    '3': Fore.RED
}

# Directory to save audio files in.
AUDIO_DIRECTORY = join(abspath(dirname(__file__)), "audio")


class WTF(object):
    def __init__(self):
        """Create PyAudio instance. Open audio stream."""
        self.pyaudio_obj = pyaudio.PyAudio()
        self.stream = self.pyaudio_obj.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        self.current_file_name = ""
        self.current_file_dir = ""
        self.latest_wav_file_path = ""

    def run(self):
        print("Let's start. [{0}]\n".format(datetime.now()))

        try:
            while True:
                input = self.stream.read(CHUNK)
                rms_value = self.get_rms(input)
                self.draw_eq(rms_value, THRESHOLD)

                if (rms_value > THRESHOLD):
                    print(Fore.GREEN + "\nWow, loud as hell! [{1}]".format(
                        THRESHOLD, datetime.now()))
                    timeout_minutes = randrange(RECORD_DELAY_FROM,
                                                RECORD_DELAY_TO)
                    print("You guys keep playing, \
                          I'll wait for {0} minutes.".format(timeout_minutes))

                    for minute in xrange(0, timeout_minutes):
                        print("{0}. ".format(minute + 1), end="")
                        time.sleep(.1)

                    print("\nYep, let's record that.[{0}]".format(
                        datetime.now()))
                    audio_data = self.record_audio(RECORD_LENGTH)

                    print("I'll try to save it. [{0}]".format(datetime.now()))
                    self.save_audio(audio_data)

                    print("Gonna make some pictures now. [{0}]".format(
                        datetime.now()))
                    self.create_waveform_images()

                    print("\n" + "_" * 79)
        except:
            pass

    @staticmethod
    def draw_eq(rms, maximum):
        """Draws textual equalizer. A bit flaky but, meh."""
        level = (rms * 79 / maximum)
        color = RMS_COLORS.get(str(int(level * 3 / 79)), '4')
        # Yes, the next line draws a penis.
        sys.stdout.write(color + "\r8=" + "=" * (level - 3) + "0" + Fore.BLACK
                         + " " * (79 - level))
        sys.stdout.flush()

    @staticmethod
    def get_rms(frame):
        """Returns RMS for a given frame of sound."""
        count = len(frame) / 2
        format = "%dh" % (count)
        shorts = struct.unpack(format, frame)
        sum_squares = 0.0
        for sample in shorts:
            n = sample * SHORT_NORMALIZE
            sum_squares += n * n
        rms = pow(sum_squares/count, 0.5)
        return int(rms * 1000)

    def record_audio(self, seconds):
        """Record audio stream into file."""
        seconds = int(seconds)
        if seconds:
            frames = []
            for i in xrange(0, int(RATE / CHUNK * seconds)):
                frames.append(self.stream.read(CHUNK))
            print("Ok, seems like I've recorded something.")
            return b''.join(frames)
        else:
            print(Fore.RED + "What? Should I record 0 seconds?")

    def save_audio(self, audio_data=None):
        """Save the data."""
        now = datetime.now()
        file_name = now.strftime("%d_%b_%Y_(%H_%M)")
        file_dir = join(AUDIO_DIRECTORY, str(now.year), file_name)
        file_path = join(file_dir, file_name + ".wav")

        if audio_data:
            if not exists(file_dir):
                makedirs(file_dir)
            print("I'll put the file here:")
            print(file_path)
            wave_file = wave.open(file_path, 'wb')
            wave_file.setnchannels(CHANNELS)
            wave_file.setsampwidth(self.pyaudio_obj.get_sample_size(FORMAT))
            wave_file.setframerate(RATE)
            wave_file.writeframes(audio_data)
            wave_file.close()
            print("Saved the WAV, all good bro.")
            self.current_file_name = file_name
            self.current_file_dir = file_dir
            self.latest_wav_file_path = file_path
        else:
            print(Fore.RED + "Should I save nothing? That's stupid.")

    def create_waveform_images(self):
        """Creates waveform and spectrum analyzed images."""
        file_name = join(self.current_file_dir, self.current_file_name)
        waveform_path = "{0}_waveform.png".format(file_name)
        spectrum_path = "{0}_spectrum.jpg".format(file_name)
        create_wave_images(self.latest_wav_file_path,
                           waveform_path,
                           spectrum_path,
                           2000, 501, 1024)
        print("Done. I've saved waveform and spectrum here:")
        print(spectrum_path)

    def convert_wav_to_mp3(self):
        """TODO: Converts WAV file to MP3."""
        # convert_to_mp3()
        pass

    def upload_to_soundcloud(self):
        """TODO: Uploads MP3 to SoundCloud."""
        pass

    def post_to_twitter(self):
        """TODO: Creates a Twitter post with a SoundCloud link."""
        pass

    def terminate_stream(self):
        """Stop the stream, terminate PyAudio."""
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio_obj.terminate()


"""Start the app."""
if __name__ == "__main__":
    WTF().run()
