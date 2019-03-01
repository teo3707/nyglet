from builtins import object

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import sys
import inspect
from functools import partial
from .compat import WeakMethod

# PYTHON2 - remove this legacy backwards compatibility hack:
if sys.version_info < (3, 2):
    inspect.getfullargspec = inspect.getargspec

EVENT_HANDLED = True
EVENT_UNHANDLED = None


class EventException(Exception):
    """An exception raised when an event handler could not be attached."""


class EventDispatcher(object):
    """Generic event dispatcher interface.
    """
    _event_stack = ()

    @classmethod
    def register_event_type(cls, name):
        """Register an event type with dispatcher.
        """
        if not hasattr(cls, 'event_types'):
            cls.event_types = []
        cls.event_types.append(name)
        return name

    def push_handlers(self, *args, **kwargs):
        """Push a level onto the top of the handler stack, then attach zero or
        more event handlers
        """
        # Create event stack if necessary
        if type(self._event_stack) is tuple:
            self._event_stack = []

        # Place dict full of new handlers at beginning of stack
        self._event_stack.insert(0, {})
        self.set_handlers(*args, **kwargs)

    def _get_handlers(self, args, kwargs):
        pass
