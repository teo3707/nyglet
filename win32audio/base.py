import math
import weakref

from abc import ABCMeta, abstractmethod


class AbstractListener(metaclass=ABCMeta):
    """The listener properties for positional audio"""

    _volume = 1.0
    _position = (0, 0, 0)
    _forward_orientation = (0, 0, -1)
    _up_orientation = (0, 1, 1)

    @abstractmethod
    def _set_volume(self, volume):
        pass

    volume = property(lambda self: self._volume,
                      lambda self, volume: self._set_volume(volume),
                      doc="""The master volume for sound playback.
                      
            All sound volumes are multiplied by this master volume before being
            played. A value of 0 will silence playback (but still consume
            resources). The nominal volume is 1.0
            
            :type: float
            """)

    @abstractmethod
    def _set_position(self, position):
        pass

    position = property(lambda self: self._position,
                        lambda self, position: self._set_position(position),
                        doc="""The position of the listener in 3D space.

            The position is given as a tuple of floats (x, y, z).  The unit
            defaults to meters, but can be modified with the listener
            properties.

            :type: 3-tuple of float
            """)

    @abstractmethod
    def _set_forward_orientation(self, orientation):
        pass

    forward_orientation = property(lambda self: self._forward_orientation,
                                   lambda self, o: self._set_forward_orientation(o),
                                   doc="""A vector giving the direction the
            listener is facing.

            The orientation is given as a tuple of floats (x, y, z), and has
            no unit.  The forward orientation should be orthagonal to the
            up orientation.

            :type: 3-tuple of float
            """)

    @abstractmethod
    def _set_up_orientation(self, orientation):
        pass

    up_orientation = property(lambda self: self._up_orientation,
                              lambda self, o: self._set_up_orientation(o),
                              doc="""A vector giving the "up" orientation
            of the listener.

            The orientation is given as a tuple of floats (x, y, z), and has
            no unit.  The up orientation should be orthagonal to the
            forward orientation.

            :type: 3-tuple of float
            """)


class AbstractAudioDriver(metaclass=ABCMeta):
    @abstractmethod
    def create_audio_player(self, source, player):
        pass

    @abstractmethod
    def get_listener(self):
        pass

    @abstractmethod
    def delete(self):
        pass


class AbstractAudioPlayer(metaclass=ABCMeta):
    """Base class for driver audio players."""

    # Audio synchronization constants
    AUDIO_DIFF_AVG_NB = 20
    # no audio correction is done if too big error
    AV_NOSYNC_THRESHOLD = 10.0

    def __init__(self, source, player):
        """Create a new audio player"""
        # We only keep weakref to the player and its source to avoid
        # circular references. It's the player who owns the source and
        # the audio_player
        self.source = source
        self.player = weakref.proxy(player)

        # Audio synchronization
        self.audio_diff_avg_count = 0
        self.audio_diff_cum = 0.0
        self.audio_diff_avg_coef = math.log10(0.01)    # 10**-2
        self.audio_diff_threshold = 0.1    # Experimental. ffplay computes it differently

    @abstractmethod
    def play(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def delete(self):
        pass

    def _play_group(self, audio_players):
        """Begin simultaneous playback on a list of audio players."""
        for player in audio_players:
            player.play()

    def _stop_group(self, audio_players):
        for player in audio_players:
            player.stop()

    @abstractmethod
    def clear(self):
        """Clear all buffered data and prepare for replacement data.

        The player should be stopped before calling this method.
        """
        self.audio_diff_avg_count = 0
        self.audio_diff_cum = 0.0

    @abstractmethod
    def get_time(self):
        """Return approximation of current playback time within current source.

        Returns ``None`` if the audio player does not know what the playback
        time is (for example, before any valid audio data has been read).

        :rtype: float
        :return: current play cursor time, in seconds.
        """

    @abstractmethod
    def prefill_audio(self):
        """Prefill the audio buffer with audio data.

        This method is called before the audio player starts in order to
        reduce the time it takes to fill the whole audio buffer.
        """

    def get_audio_time_diff(self):
        """Queries the time difference between the audio time and the `Player`
        master clock.

        The time difference returned is calculated using a weighted average on
        previous audio time differences. The algorithms will need at least 20
        measurements before returning a weighted average.
        """
        audio_time = self.get_time() or 0
        p_time = self.player.time
        diff = audio_time - p_time
        if abs(diff) < self.AV_NOSYNC_THRESHOLD:
            self.audio_diff_cum = diff + self.audio_diff_cum * self.audio_diff_avg_coef
            if self.audio_diff_avg_count < self.AUDIO_DIFF_AVG_NB:
                self.audio_diff_avg_count += 1
            else:
                avg_diff = self.audio_diff_cum * (1 - self.audio_diff_avg_coef)
                if abs(avg_diff) > self.audio_diff_threshold:
                    return avg_diff
        else:
            self.audio_diff_avg_count = 0
            self.audio_diff_cum = 0.0
        return 0.0

    def set_volume(self):
        pass

    def set_position(self, position):
        pass

    def set_min_distance(self, min_distance):
        pass

    def set_max_distance(self, max_distance):
        pass

    def set_pitch(self, pitch):
        pass

    def set_cone_orientation(self, cone_orientation):
        pass

    def set_cone_inner_angle(self, cone_inner_angle):
        pass

    def set_cone_outer_angle(self, cone_outer_angle):
        pass

    def set_cone_outer_gain(self, cone_outer_gaine):
        pass

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, value):
        self._source = weakref.proxy(value)
