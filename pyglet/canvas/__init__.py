import sys


from pyglet.app import WeakSet

_is_epydoc = hasattr(sys, 'is_epydoc') and sys.is_epydoc


_displays = WeakSet()


def get_display():
    """Get the default display device.
    """
    # If there are existing displays, return one of them arbitrarily.
    for display in _displays:
        return display

    # Otherwise, create a new display and return it
    return Display()


if _is_epydoc:
    from pyglet.canvas.base import Display, Screen, Canvas, ScreenMode
else:
    from pyglet import compat_platform
    if compat_platform == 'darwin':
        from pyglet.canvas.cocoa import CocoaDisplay as Display
        from pyglet.canvas.cocoa import CocoaScreen as Screen
        from pyglet.canvas.cocoa import CocoaCanvas as Canvas
    elif compat_platform in ('win32', 'cygwin'):
        from pyglet.canvas.win32 import Win32Display as Display
        from pyglet.canvas.win32 import Win32Screen as Screen
        from pyglet.canvas.win32 import Win32Canvas as Canvas
    else:
        from pyglet.canvas.xlib import XlibDisplay as Display
        from pyglet.canvas.xlib import XlibScreen as Screen
        from pyglet.canvas.xlib import XlibCanvas as Canvas