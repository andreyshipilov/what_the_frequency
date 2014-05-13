#!/usr/bin/env python
from __future__ import print_function
from datetime import datetime
from os.path import abspath, join, dirname
import sys

import pyaudio
from colorama import Fore, init as colorama_init
colorama_init(autoreset=True)

# Reset some settings if Debugging.
DEBUG = True if 'debug' in sys.argv else False

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
SHORT_NORMALIZE = 1.0/32768.0

# Minimum treshold (RMS) to reach to start the record.
THRESHOLD = 200

# Timeout in minutes before record start.
RECORD_DELAY_FROM = 2 if DEBUG else 1
RECORD_DELAY_TO = 5 if DEBUG else 5

# Record cycle delay.
RECORD_DELAY_PERIOD = 0.1 if DEBUG else 60

# How many seconds to record.
RECORD_LENGTH = 30 if DEBUG else 30

# Colors for RMS terminal output.
RMS_COLORS = {
    "0": Fore.WHITE,
    "1": Fore.GREEN,
    "2": Fore.YELLOW,
    "3": Fore.RED
}

# Directory to save audio files in.
AUDIO_DIRECTORY = join(abspath(dirname(__file__)), "audio")

class AudioProcessingException(Exception):
    pass


class WTF(object):
    def __init__(self):
        """Create PyAudio instance. Open audio stream."""
        self.pyaudio_obj = pyaudio.PyAudio()
        self.stream = self.pyaudio_obj.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            input_device_index=1,
        )
        self.current_file_name = self.current_file_dir = ""
        self.latest_wav_file_path = self.latest_mp3_file_path = ""

    def run(self):
        if DEBUG:
            print(Fore.RED + "We're in debug mode btw!")

        print("Let's start. [{0}]\n".format(datetime.now()))

        try:
            while True:
                try:
                    input = self.stream.read(CHUNK)
                except IOError:
                    input = '\x00' * CHUNK
                rms_value = self.get_rms(input)
                self.draw_eq(rms_value, THRESHOLD)

                if rms_value > THRESHOLD:
                    import time
                    from random import randrange

                    print(Fore.GREEN + "\nOk, loud as hell! [{1}]".format(
                        THRESHOLD, datetime.now()))
                    timeout_minutes = randrange(RECORD_DELAY_FROM,
                                                RECORD_DELAY_TO)
                    print("You guys keep playing, " +
                          "I'll wait for {0} minutes.".format(timeout_minutes))

                    for minute in xrange(0, timeout_minutes):
                        print("{0}. ".format(minute + 1), end="")
                        time.sleep(RECORD_DELAY_PERIOD)

                    print("\nYep, let's record that.[{0}]".format(
                        datetime.now()))

                    audio_data = self.record_audio(RECORD_LENGTH)
                    self.terminate_stream()

                    print("I'll try to save it. [{0}]".format(datetime.now()))
                    self.save_audio(audio_data)

                    print("Let's convert the WAV to MP3. [{0}]".\
                          format(datetime.now()))
                    self.convert_wav_to_mp3()

                    print("Uploading the masterpiece to SoundColud. [{0}]".\
                          format(datetime.now()))
                    self.upload_to_soundcloud()

                    print("\n" + "_" * 79)
        except Exception as e:
            print(e)

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
        import struct

        count = len(frame) / 2
        shorts = struct.unpack("%dh" % (count), frame)
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
                try:
                    frames.append(self.stream.read(CHUNK))
                except IOError:
                    frames.append('\x00' * CHUNK)
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
            from os.path import exists
            import wave

            if not exists(file_dir):
                from os import makedirs
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

    def convert_wav_to_mp3(self):
        """Converts WAV file to MP3."""
        import subprocess
        from os.path import splitext, exists

        self.latest_mp3_file_path = splitext(self.latest_wav_file_path)[0] + ".mp3"
        if not exists(self.latest_wav_file_path):
            raise AudioProcessingException, "file %s does not exist" % self.latest_wav_file_path

        command = ["lame", "--silent", "--abr", str(75), self.latest_wav_file_path, self.latest_mp3_file_path]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout, stderr) = process.communicate()

        if process.returncode != 0 or not exists(self.latest_mp3_file_path):
            raise AudioProcessingException, stdout

    def upload_to_soundcloud(self):
        """Uploads MP3 to SoundCloud."""
        import soundcloud
        from secrets import CLIENT_ID, CLIENT_SECRET, USERNAME, PASSWORD

        client = soundcloud.Client(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            username=USERNAME,
            password=PASSWORD
        )
        client.post('/tracks', track={
            'title': datetime.now().strftime('%d %B, %Y'),
            'asset_data': open(self.latest_mp3_file_path, 'rb'),
            'genre': 'Live',
            'track_type': 'live',
            'tag_list': 'live demo jam',
            'downloadable': True
        })

    def post_to_twitter(self):
        """TODO: Creates a Twitter post with a SoundCloud link."""
        pass

    def terminate_stream(self):
        """Stop the stream, terminate PyAudio."""
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio_obj.terminate()


if __name__ == "__main__":
    WTF().run()
