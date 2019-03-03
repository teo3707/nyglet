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

    def _remove_handler(self, name, handler):
        """Used internally to remove all handler instances for the given event name.
        """
        # Iterate over a copy as we might mutate teh list
        for frame in list(self._event_stack):
            if name in frame and frame[name] == handler:
                del frame[name]
                if not frame:
                    self._event_stack.remove(frame)

    def dispatch_event(self, event_type, *args):
        """Dispatch a single event to teh attached handlers.
        """
        assert hasattr(self, 'event_types'), (
            "No Events registered on this EventDispatcher. "
            "You need to register events with teh class method "
            "EventDispatcher.register_event_type('event_name')"
        )
        assert event_type in self.event_types,\
            "%r not found in %r.event_types == %r" % (event_type, self, self.event_types)

        invoked = False

        # Search handler stack for matching event handlers
        for frame in list(self._event_stack):
            handler = frame.get(event_type, None)
            if not handler:
                continue
            if isinstance(handler, WeakMethod):
                handler = handler()
                assert handler is not None
            try:
                invoked = True
                if handler(*args):
                    return EVENT_HANDLED
            except TypeError as exception:
                self._raise_dispatch_exception(event_type, args, handler, exception)

        # Check instance for an event handler
        try:
            if getattr(self, event_type)(*args):
                return EVENT_HANDLED
        except AttributeError:
            pass
        except TypeError as exception:
            self._raise_dispatch_exception(event_type, args, getattr(self, event_type), exception)
        else:
            invoked = True

        if invoked:
            return EVENT_HANDLED

        return False

    def _raise_dispatch_exception(self, event_type, args, handler, exception):
        # A common problem in application is having teh wrong number of
        # arguments in an event handler, This is caught as a TypeError in
        # dispatch_event but the error message is obfuscated.
        #
        # Here we check if there is indent a mismatch in argument count,
        # and construct a more useful exception message if so. If this method
        # doesn't find a problem with the number of arguments, the error
        # is re-raised as if we weren't here.
        n_args = len(args)

        # Inspect the handler
        argspecs = inspect.getfullargspec(handler)
        handler_args = argspecs.args
        handler_varargs = argspecs.varargs
        handler_defaults = argspecs.defaults

        n_handler_args = len(handler_args)

        # Remove "self" arg from handle if it's a bound method
        if inspect.ismethod(handler) and handler.__self__:
            n_handler_args -= 1

        # Allow *args varargs to over specify arguments
        n_handler_args = max(n_handler_args, n_args)

        # Allow default values to over specify arguments
        if (n_handler_args != n_args and handler_defaults and
                n_handler_args - len(handler_defaults) <= n_args):
            n_handler_args = n_args

        if n_handler_args != n_args:
            if inspect.isfunction(handler) or inspect.ismethod(handler):
                descr = "'%s' at %s:%d" % (handler.__name__,
                                           handler.__code__.co_filename,
                                           handler.__code__.co_firstlineno)
            else:
                descr = repr(handler)

            raise TypeError("The '{0} event was dispatch with {1} arguments, "
                            "but your handler {2} accepts only {3} arguments.".format(
                             event_type, len(args), descr, len(handler_args)))
        else:
            raise exception

    def event(self, *args):
        """Function decorator for an event handler.
        """
        if len(args) == 0:                           # @window.event()
            def decorator(func):
                name = func.__name__
                self.set_handler(name, func)
                return func
            return decorator
        elif inspect.isroutine(args[0]):             # @window.event
            func = args[0]
            name = func.__name__
            self.set_handler(name, func)
            return args[0]
        elif isinstance(args[0], str):               # @window.event('on_resize')
            name = args[0]

            def decorator(func):
                self.set_handler(name, func)
                return func
            return decorator
