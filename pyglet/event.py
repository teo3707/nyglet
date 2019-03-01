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
        """Implement handler matching on arguments for set_handlers and
        remove_handlers.
        """
        for obj in args:
            if inspect.isroutine(obj):
                # Single magically named function
                name = obj.__name__
                if name not in self.event_types:
                    raise EventException('Unknown event "%s"' % name)
                if inspect.ismethod(obj):
                    yield name, WeakMethod(obj, partial(self._remove_handler, name))
                else:
                    yield name, obj
            else:
                # Single instance with magically named methods
                for name in dir(obj):
                    if name in self.event_types:
                        meth = getattr(obj, name)
                        yield name, WeakMethod(meth, partial(self._remove_handler, name))

        for name, handler in kwargs.items():
            # Function for handling given event (no magic)
            if name not in self.event_types:
                raise EventException('Unknown event "%s"' % name)
            if inspect.ismethod(handler):
                yield name, WeakMethod(handler, partial(self._remove_handler, name))
            else:
                yield name, handler

    def set_handlers(self, *args, **kwargs):
        """Attach one or more event handlers to the top level of the handler
        stack.
        """
        # Create event stack if necessary
        if type(self._event_stack) is tuple:
            self._event_stack = [{}]

        for name, handler in self._get_handlers(args, kwargs):
            self.set_handler(name, handler)

    def set_handler(self, name, handler):
        """Attach a single event handler
        """
        if type(self._event_stack) is tuple:
            self._event_stack = [{}]

        self._event_stack[0][name] = handler

    def pop_handlers(self):
        """Pop the top level of event handlers off the stack.
        """
        assert self._event_stack and 'No handlers pushed'

        del self._event_stack[0]

    def remove_handlers(self, *args, **kwargs):
        """Remove event handlers from the event stack.
        """
        handlers = list(self._get_handlers(args, kwargs))

        # Find the first stack frame containing any of the handlers
        def find_frame():
            for frame in self._event_stack:
                for name, handler in handlers:
                    try:
                        if frame[name] == handler:
                            return frame
                    except KeyError:
                        pass
        frame = find_frame()

        # No frame matched; no error.
        if not frame:
            return

        # Remove each handler from the frame
        for name, handler in handlers:
            try:
                if frame[name] == handler:
                    del frame[name]
            except KeyError:
                pass

        # Remove the frame if it's empty
        if not frame:
            self._event_stack.remove(frame)

    def remove_handler(self, name, handler):
        """Remove a single event handler.
        """
        for frame in self._event_stack:
            try:
                if frame[name] == handler:
                    del frame[name]
                    break
            except KeyError:
                pass
