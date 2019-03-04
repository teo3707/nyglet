"""Application-wide functionality
"""
from builtins import object

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import sys
import weakref

from pyglet.app.base import EventLoop
from pyglet import compat_platform

_is_epydoc = hasattr(sys, 'is_epydoc') and sys.is_epydoc

if _is_epydoc:
    from pyglet.app.base import PlatformEventLoop
else:
    if compat_platform == 'darwin':
        from pyglet.app.cocoa import CocoaEventLoop as PlatformEventLoop
    elif compat_platform in ('win32', 'cygwin'):
        from pyglet.app.win32 import Win32EventLoop as PlatformEventLoop
    else:
        from pyglet.app.xlib import XlibEventLoop as PlatformEventLoop


    class AppException(Exception):
        pass


class WeakSet(object):
    """Set of objects, referenced weakly.
    """
    def __init__(self):
        self._dict = weakref.WeakKeyDictionary()

    def add(self, value):
        self._dict[value] = True

    def remove(self, value):
        # Value might be removed already fi this is during __del__ of the item.
        self._dict.pop(value, None)

    def pop(self):
        value, _ = self._dict.popitem()
        return value

    def __iter__(self):
        for key in self._dict.keys():
            yield key

    def __contains__(self, other):
        return other in self._dict

    def __len__(self):
        return len(self._dict)


# Set of all open windows (including invisible windows).
windows = WeakSet()


def run():
    """Begin processing events, scheduled functions and window updates.
    """
    event_loop.run()


def exit():
    """Exit the application event loop
    """
    event_loop.exit()


#: The global event loop. Applications can replace this
#: with their own subclass of :class:`EventLoop` before calling
#: :meth:`EventLoop.run`.
event_loop = EventLoop()

#: The platform-dependent event loop.
#: Applications must not subclass or replace this :class:`PlatformEventLoop`
#: object
platform_event_loop = PlatformEventLoop()
