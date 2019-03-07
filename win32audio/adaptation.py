import ctypes
import math
import weakref
import threading

from win32audio import interface
from win32audio.base import AbstractAudioPlayer, AbstractAudioDriver


def _convert_coordinates(coordinates):
    x, y, z = coordinates
    return x, y, -z


def _gain2db(gain):
    """Convert linear gain in range [0.0, 1.0] to 100ths of dB.

    Power gain = P1/P2
    dB = 10 log(P1/P2)
    dB * 100 = 1000 * log(power gain)
    """
    if gain <= 0:
        return -10000

    return max(-10000, min(int(1000 * math.log10(min(gain, 1))), 0))


def _db2gain(db):
    """Convert 100ths of dB to linear gain."""
    return math.pow(10.0, float(db)/1000.0)


class DirectSoundAudioPlayer(AbstractAudioPlayer):
    # Need to cache these because pyglet API allows update separately, but
    # DSound requires both to be set at once.
    _cone_inner_angle = 360
    _cone_outer_angle = 360

    min_buffer_size = 9600

    def __init__(self, driver, ds_driver, source, player):
        super(DirectSoundAudioPlayer, self).__init__(source, player)

        # We keep here a strong reference because the AudioDriver is anyway
        # a singleton object which will only be deleted when the application
        # shuts down. The AudioDriver does not keep a ref to the AudioPlayer.
        self.driver = driver
        self._ds_driver = ds_driver

        # Desired play state (may be actually paused due to underrun -- not
        # implemented yet).
        self._playing = False

        # Up to one audio data may be buffered if too much data was received
        # from the source that could not be written immediately into the
        # buffer. See refill()
        self._audiodata_buffer = None

        # Theoretical write and play cursors for an infinite buffer. play
        # cursor is always <= write cursor (when equal, underrun is
        # happening).
        self._write_cursor = 0
        self._play_cursor = 0

        # Cursor position of end of data.  Silence is written after
        # eos for one buffer size.
        self._eos_cursor = None

        # Indexes into DSound circular buffer. Complications ensure wrt each
        # other to avoid writing over the play cursor. See get_write_size and
        # write().
        self._play_cursor_ring = 0
        self._write_cursor_ring = 0

        # List of (play_cursor, MediaEvent), in sort order
        self._events = []

        # List of (cursor, timestamp), in sort order (cursor gives expiry
        # place of the timestamp)
        self._timestamps = []

        audio_format = source.audio_format

        # DSound buffer
        self._ds_buffer = self._ds_driver.create_buffer(audio_format)
        self._buffer_size = self._ds_buffer.buffer_size

        self._ds_buffer.current_position = 0

        self.refill(self._buffer_size)

    def __del__(self):
        self.driver._ds_driver._native_dsound.Release()

    def delete(self):
        pass

    _thread = None

    def play(self):
        if self._thread:
            try:
                self._thread.join(0)
            except:
                pass
        self._thread = threading.Thread(target=self._check_refill)
        self._thread.start()

        if not self._playing:
            self._get_audiodata()    # prebuffer if needed
            self._playing = True
            self._ds_driver.play()

    def stop(self):
        if self._playing:
            try:
                self._thread.join(0)
            except:
                pass
            self._playing = False
            self._ds_buffer.stop()

    def clear(self):
        super(DirectSoundAudioPlayer, self).clear()
        self._ds_buffer.current_position = 0
        self._play_cursor_ring = self._write_cursor_ring = 0
        self._play_cursor = self._write_cursor
        self._eos_cursor = None
        self._audiodata_buffer = None
        del self._events[:]
        del self._timestamps[:]

    def _check_refill(self, dt):    # Need a better name!
        write_size = self.get_write_size()
        if write_size > self.min_buffer_size:
            self.refill(write_size)

    def refill(self, write_size):
        while write_size > 0:
            audio_data = self._get_audiodata()

            if audio_data is not None:
                length = min(write_size, audio_data.length)
                self.write(audio_data, length)
                write_size -= length
            else:
                self.write(None, write_size)
                write_size = 0

    def _has_underrun(self):
        return (self._eos_cursor is not None
                and self._play_cursor > self._eos_cursor)

    def _dispatch_new_event(self, event_name):
        pass

    def _get_audiodata(self):
        if self._audiodata_buffer is None or self._audiodata_buffer.lenght == 0:
            self._get_new_audiodata()

        return self._audiodata_buffer

    def _get_new_audiodata(self):
        compensation_time = self.get_audio_time_diff()



