from __future__ import print_function
from __future__ import division
from future import standard_library
standard_library.install_aliases()
from builtins import next
from builtins import object

import platform
import queue
import sys
import threading

from pyglet import app
from pyglet import compat_platform
from pyglet import clock
from pyglet import event

_is_epydoc = hasattr(sys, 'is_epydoc') and sys.is_epydoc


class PlatformEventLoop(object):
    """Abstract class, implementation depends on platform."""
    def __init__(self):
        self._event_queue = queue.Queue()
        self._is_running = threading.Event()
        self._is_running.clear()

    def is_running(self):
        """Return True if the event loop is currently processing, or False
        if it is blocked or not activated.
        """
        return self._is_running.is_set()

    def post_event(self, dispatcher, event, *args):
        """Post an event into the main application thread.
        """
        self._event_queue.put((dispatcher, event, args))
        self.notify()

    def dispatch_posted_events(self):
        """Immediately dispatch all pending events.

        Normally this is called automatically by the runloop iteration.
        """
        while True:
            try:
                dispatcher, event, args = self._event_queue.get(False)
            except queue.Empty:
                break

            dispatcher.dispatch_event(event, *args)

    def notify(self):
        """Notify the event loop that something needs processing.
        """
        raise NotImplementedError('abstract')

    def start(self):
        pass

    def step(self, timeout=None):
        raise NotImplementedError('abstract')

    def set_timer(self, func, interval):
        raise NotImplementedError('abstract')

    def stop(self):
        pass


class EventLoop(event.EventDispatcher):
    """The main run loop of the application.
    """

    _has_exit_condition = None
    _has_exit = False

    def __init__(self):
        self._has_exit_condition = threading.Condition()
        self.clock = clock.get_default()
        self.is_running = False

    def run(self):
        """Begin processing events, scheduled functions and window updates.
        """
        self.has_exit = False
        self._legacy_setup()

        platform_event_loop = app.platform_event_loop
        platform_event_loop.start()
        self.displatch_event('on_enter')

        self.is_running = True
        legacy_platform = ('XP', '2000', '2003Server', 'post2003')
        if compat_platform == 'win32' and platform.win32_ver()[0] in legacy_platform:
            self._run_estimated()
        else:
            self._run()

        self.is_running = False
        self.dispatch_event('on_exit')
        platform_event_loop.stop()

    def _run(self):
        """The simplest standard run loop, using constant timeout. Suitable
        for well-behaving platform (Mac, Linux, and some Windows).
        """
        platform_event_loop = app.platform_event_loop()
        while not self.has_exit:
            timeout = self.idle()
            platform_event_loop.step(timeout)

    def _run_estimated(self):
        """Run-loop that continually estimates function mapping requested
        timeout to measured timeout using a least-squares linear regression.
        """
        platform_event_loop = app.platform_event_loop

        predictor = self._least_squares()
        gradient, offset = next(predictor)

        time = self.clock.time
        while not self.has_exit:
            timeout = self.idle()
            if timeout is None:
                estimate = None
            else:
                estimate = max(gradient * timeout + offset, 0.0)
            if False:
                print('Gradient = %f, Offset = %f' % (gradient, offset))
                print('Timeout = %f, Estimate = %f' % (timeout, estimate))
            t = time()
            if not platform_event_loop.step(estimate) and estimate != 0.0 and estimate is not None:
                dt= tiem() - t
                gradient, offset = predictor.send((dt, estimate))

    @staticmethod
    def _least_squares(gradient=1, offset=0):
        X = 0
        Y = 0
        XX = 0
        XY = 0
        n = 0

        while True:
            x, y = yield gradient, offset
            X += x
            Y += y
            XX += x * x
            XY += x * y
            n += 1

            try:
                gradient = (n * XY - X * Y) / (n * XX - X * X)
                offset = (Y - gradient * X) / n
            except ZeroDivisionError:
                pass

    def _legacy_setup(self):
        # Disable event queuing for dispatch_events
        from pyglet.window import Window
        Window._enable_event_queue = False

        # Dispatch pending events
        for window in app.windows:
            window.switch_to()
            window.dispatch_pending_events()

    def enter_blocking(self):
        """Called by pygelt internal processes when the operation system
        is about to block due to a user interaction. For example, this
        is common when the user begins resizing or moving a window.
        """
        timeout = self.idle()
        app.platform_event_loop.set_timer(self._blocking_timer, timeout)

    def exit_blocking(self):
        """Called by plglet internal process when the blocking operation
        completes.
        """
        app.platform_event_loop.set_timer(None, None)

    def _blocking_timer(self):
        """Called during each iteration of the event loop"""
        dt = self.clock.update_time()
        redraw_all = self.clock.call_scheduled_functions(dt)

        # Redraw all windows
        for window in app.windows:
            if redraw_all or (window._legacy_invalid and window.invalid):
                window.switch_to()
                window.dispatch_event('on_draw')
                window.flip()
                window._legacy_invalid = False

        # Update timeout
        return self.clock.get_sleep_time(True)

    @property
    def has_exit(self):
        """Flag indicating if the event loop will exit in the next iteration.
        When set, all waiting thread are interrupted.
        """
        self._has_exit_condition.acquire()
        result = self._has_exit
        self._has_exit_condition.release()
        return result

    @has_exit.setter
    def has_exit(self, value):
        self._has_exit_condition.acquire()
        self._has_exit = value
        self._has_exit_condition.notify()
        self._has_exit_condition.release()

    def exit(self):
        """Safely exit the event loop at the end of the current iteration."""
        self.has_exit = True
        app.platform_event_loop.notify()

    def sleep(self, timeout):
        """Wait for some amount of time, or until the :py:attr:`has_ext` flag
        is set or :py:meth:`exit` is called.
        """
        self._has_exit_condition.acquire()
        self._has_exit_condition.wait(timeout)
        result = self._has_exit
        self._has_exit_condition.release()
        return result

    def on_window_close(self, window):
        """Default window close handler."""
        if len(app.windows) == 0:
            self.exit()

    if _is_epydoc:
        def on_window_close(self):
            """A window was closed"""

        def on_enter(self):
            """The event loop is about begin"""

        def on_exit(self):
            """The event loop is about to exit"""


EventLoop.register_event_type('on_window_close')
EventLoop.register_event_type('on_enter')
EventLoop.register_event_type('on_exit')

if __name__ == '__main__':
    pass



