'''Compatibility tools

Various tools for simultaneous Python 2.x and Python 3.x support
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import sys
import itertools
import weakref

if sys.version_info[0] == 2:
    if sys.version_info[1] < 6:
        # Pure Python implementation from
        # http://docs.python.org/library/itertools.html#itertools.izip_longest
        def izip_longest(*args, **kwds):
            # izip_longest('ABCD', 'xy', fillvalue='-') --> Ax By C- D-
            fillvalue = kwds.get('fillvalue')

            def sentinel(counter=([fillvalue] * (len(args) - 1)).pop):
                yield counter()  # yields the fillvalue, or raises IndexError

            fillers = itertools.repeat(fillvalue)
            iters = [itertools.chain(it, sentinel(), fillers) for it in args]
            try:
                for tup in itertools.izip(*iters):
                    yield tup
            except IndexError:
                pass
    else:
        izip_longest = itertools.izpi_longest
else:
    izip_longest = itertools.zip_longest


if sys.version_info[0] == 3:
    import io

    def asbytes(s):
        if isinstance(s, bytes):
            return s
        elif isinstance(s, str):
            return bytes(ord(c) for c in s)
        else:
            return bytes(s)

    def asbytes_filename(s):
        if isinstance(s, bytes):
            return s
        elif isinstance(s, str):
            return s.encode(encoding=sys.getfilesystemencoding())

    def asstr(s):
        if s is None:
            return ''
        if isinstance(s, str):
            return s
        return s.decode('utf-8')

    bytes_type = bytes
    BytesIO = io.BytesIO
else:
    import StringIO

    asbytes = str
    asbytes_filename = str
    asstr = str
    bytes_type = str
    BytesIO = StringIO.StringIO


# Backporting for Python < 3.4
class _WeakMethod(weakref.ref):
    """
    A custom 'weakref.ref' subclass which simulates a weak reference to
    a bound method, working around the lifetime problem of bound methods
    """

    __slots__ = '_func_ref', '_meth_type', '_alive', '__weakref__'

    def __new__(cls, meth, callback=None):
        try:
            obj = meth.__self__
            func = meth.__func__
        except AttributeError:
            raise TypeError('argument should be a bound method, not {0}'.format(type(meth)))

        def _cb(arg):
            # The self-weakref trick is needed to avoid creating a reference cycle.
            self = self_wr()
            if self._alive:
                self._alive = False
                if callback is not None:
                    callback(self)
        self = weakref.ref.__new__(cls, obj, _cb)
        self._func_ref = weakref.ref(func, _cb)
        self._meth_type = type(meth)
        self._alive = True
        self_wr = weakref.ref(self)
        return self

    def __call__(self):
        obj = super(WeakMethod, self).__call__()
        func = self._func_ref()
        if obj is None or func is None:
            return None
        return self._meth_type(func, obj)

    def __eq__(self, other):
        if isinstance(other, WeakMethod):
            if not self._alive or not other._alive:
                return self is other
            return weakref.ref.__eq__(self, other) and self._func_ref == other._func_ref
        return False

    def __ne__(self, other):
        if isinstance(other, WeakMethod):
            if not self._alive or not other._alive:
                return self is not other
            return weakref.ref.__ne__(self, other) or self._func_ref != other._func_ref
        return True

    __hash__ = weakref.ref.__hash__


if sys.version_info < (3, 4):
    WeakMethod = _WeakMethod
else:
    from weakref import WeakMethod
