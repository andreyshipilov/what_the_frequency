#!/usr/bin/env python
# pylint: disable=E1101

"""
    "What The Frequency"
    https://soundcloud.com/what_the_frequency
    Every time our music room is filled with sounds and tunes,
    30 seconds is being randomly recorded and posted to SoundCloud once a day.
"""

from __future__ import print_function
from datetime import datetime
from os.path import abspath, join, dirname
import sys

import pyaudio
from colorama import Fore, init as colorama_init
colorama_init(autoreset=True)
from secrets import SOUND_CLOUD, TWITTER

# Reset some settings if Debugging.
DEBUG = True if 'debug' in sys.argv else False

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
SHORT_NORMALIZE = 1.0/32768.0

# Minimum treshold (RMS) to reach to start the record.
THRESHOLD = 200

# Timeout in minutes before record start.
RECORD_DELAY_FROM = 2 if DEBUG else 1
RECORD_DELAY_TO = 5 if DEBUG else 5

# Minute length for easier debug.
MINUTE_LENGTH = 0.1 if DEBUG else 60

# How many seconds to record.
RECORD_LENGTH = 1 if DEBUG else 30

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
    """Fake exception class."""

    pass


class WTF(object):
    """Main class."""

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
        self.current_file_name = self.current_file_dir = None
        self.latest_wav_file_path = self.latest_mp3_file_path = None
        self.latest_uploaded_track = None

    def run(self):
        """Main method."""
        if DEBUG:
            print(Fore.RED + "We're in debug mode btw!")

        print("Let's start. [{0}]\n".format(datetime.now()))

        while True:
            try:
                input_data = self.stream.read(CHUNK)
            except IOError:
                input_data = '\x00' * CHUNK
            rms_value = self.get_rms(input_data)
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
                    time.sleep(MINUTE_LENGTH)

                print("\nYep, let's record that.[{0}]".format(
                    datetime.now()))

                audio_data = self.record_audio(RECORD_LENGTH)

                print("I'll try to save it. [{0}]".format(datetime.now()))
                self.save_audio(audio_data)

                print("Let's convert the WAV to MP3. [{0}]".
                      format(datetime.now()))
                self.convert_wav_to_mp3()

                if not DEBUG:
                    print("Uploading the masterpiece to SoundColud. [{0}]".
                          format(datetime.now()))
                    self.upload_to_soundcloud()

                    #TODO: Fix Twitter.
                    #print("Tweeting the masterpiece to everyone. [{0}]".
                    #      format(datetime.now()))
                    #self.post_to_twitter()

                    print("Now I'm going to sleep for 24 hours. [{0}]".format(
                        datetime.now()))
                    for hour in xrange(1, 25):
                        print("{0} [{1}]".format(str(25-hour), datetime.now()))
                        # Sleep for an hour.
                        time.sleep(MINUTE_LENGTH * 60)

                print(Fore.GREEN + "All done! [{0}]\n".format(datetime.now()))

    @staticmethod
    def draw_eq(rms, maximum):
        """Draws textual equalizer. A bit flaky but, meh."""
        level = (rms * 79 / maximum)
        color = RMS_COLORS.get(str(int(level * 3 / 79)), '4')
        # Yes, the next line draws a penis.
        sys.stdout.write(color + "\r8=" + "=" * (level - 3) + "o" + Fore.BLACK
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
            num = sample * SHORT_NORMALIZE
            sum_squares += num * num
        rms = pow(sum_squares/count, 0.5)
        return int(rms * 1000)

    def record_audio(self, seconds):
        """Record audio stream into file."""
        seconds = int(seconds)
        if seconds:
            frames = []
            for _ in xrange(0, int(RATE / CHUNK * seconds)):
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
            print(">>> {0}". format(file_path))
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
        from os import remove

        self.latest_mp3_file_path = "{0}.mp3".format(
            splitext(self.latest_wav_file_path)[0])
        if not exists(self.latest_wav_file_path):
            raise AudioProcessingException(
                "file {0} does not exist".format(self.latest_wav_file_path))

        command = ["lame",
                   "--silent",
                   "--abr", str(75),
                   self.latest_wav_file_path,
                   self.latest_mp3_file_path]
        process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        (stdout, _) = process.communicate()

        if process.returncode != 0 or not exists(self.latest_mp3_file_path):
            raise AudioProcessingException(stdout)
        else:
            remove(self.latest_wav_file_path)

    def upload_to_soundcloud(self):
        """Uploads MP3 to SoundCloud."""
        import soundcloud

        client = soundcloud.Client(
            client_id=SOUND_CLOUD['id'],
            client_secret=SOUND_CLOUD['secret'],
            username=SOUND_CLOUD['username'],
            password=SOUND_CLOUD['password']
        )
        self.latest_uploaded_track = client.post('/tracks', track={
            'title': datetime.now().strftime('%d %B, %Y'),
            'asset_data': open(self.latest_mp3_file_path, 'rb'),
            'genre': 'Live',
            'track_type': 'live',
            'tag_list': 'live demo jam',
            'downloadable': True
        })

    def post_to_twitter(self):
        """Posts a tweet to Twitter"""
        if self.latest_uploaded_track:
            import tweepy

            auth = tweepy.OAuthHandler(
                TWITTER['consumer_key'],
                TWITTER['consumer_secret'])
            auth.set_access_token(
                TWITTER['access_token'],
                TWITTER['access_token_secret'])
            api = tweepy.API(auth)
            api.update_status("{0} #what_the_frequency".format(
                self.latest_uploaded_track.permalink_url))

    def terminate_stream(self):
        """Stop the stream, terminate PyAudio."""
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio_obj.terminate()


if __name__ == "__main__":
    WTF().run()
