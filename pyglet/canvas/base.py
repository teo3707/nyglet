from builtins import object
from pyglet import app
from pyglet import gl
from pyglet import window
from pyglet import canvas


class Display(object):
    """A display device supporting one or more screens.
    """

    # Name of this display, if applicable.
    name = None

    # The X11 screen number of this display, if applicable.
    x_screen = None

    def __init__(self, name=None, x_screen=None):
        """Create a display connection for the given name and screen.
        """
        canvas._displays.add(self)

    def get_screens(self):
        """Get the available screens.
        """
        raise NotImplementedError('abstract')

    def get_default_screen(self):
        return self.get_screens()[0]

    def get_window(self):
        """Get the windows currently attached to this display.
        """
        return [window for window in app.windows if window.display is self]


class Screen(object):
    """A virtual monitor that supports fullscreen windows.
    """
    def __init__(self, display, x, y, width, height):
        self.display = display
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __repr__(self):
        return '%s(x=%d, y=%d, width=%d, height=%d)' % \
               (self.__class__.__name__, self.x, self.y, self.width, self.height)

    def get_best_config(self, template=None):
        """Get the best available GL config.
        """
        configs = None
        if template is None:
            for template_config in [
                gl.Config(double_buffer=True, depth_size=24),
                gl.Config(double_buffer=True, depth_size=16),
                None]:
                try:
                    configs = self.get_matching_configs(template_config)
                    break
                except window.NoSuchConfigException:
                    pass
        else:
            configs = self.get_matching_configs(template)
        if not configs:
            raise window.NoSuchConfigException()
        return configs[0]

    def get_matching_configs(self, template):
        """Get a list of configs that match a specification."""
        raise NotImplementedError('abstract')

    def get_modes(self):
        """Get a list of screen modes supported by this screen.
        """
        raise NotImplementedError('abstract')

    def get_mode(self):
        """Get the current display mode for this screen.
        """
        raise NotImplementedError('abstract')

    def get_closet_mode(self, width, height):
        """Get the screen mode that best matches a given size.
        """
        current = self.get_mode()

        best = None
        for mode in self.get_modes():
            # Reject resolutions that are too small
            if mode.width < width or mode.height < height:
                continue

            if best is None:
                best = mode

            # Must strictly dominate dimensions
            if (mode.width <= best.width and mode.height <= best.height and
                    (mode.width < best.width or mode.height < best.height)):
                best = mode

            # Preferable match rate, then depth.
            if mode.width == best.width and mode.height == best.height:
                points = 0
                if mode.rate == current.rate:
                    points += 2
                if best.rate == current.rate:
                    points -= 2
                if mode.depth == current.depth:
                    points += 1
                if best.depth == current.depth:
                    points -= 1

                if points > 0:
                    best = mode
        return best

    def set_mode(self, mode):
        """Set the display mode for this screen.
        """
        raise NotImplementedError('abstract')

    def restore_mode(self):
        """Restore the screen mode to the user's default."""
        raise NotImplementedError('abstract')


class ScreenMode(object):
    """Screen resolution and display settings.
    """
    # Width of screen, in pixels.
    width = None

    # Height of screen, in pixels.
    height = None

    # Pixel color depth, in bits per pixel.
    depth = None

    # Screen refresh rate in Hz.
    rate = None

    def __init__(self, screen):
        self.screen = screen

    def __repr__(self):
        return '%s(width=%r, height=%r, depth=%r, rate=%r)' % (
            self.__class__.__name__,
            self.width, self.height, self.depth, self.rate)


class Canvas(object):
    """Abstract drawing area.
    """
    def __init__(self, display):
        self.display = display
