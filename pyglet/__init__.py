from __future__ import print_function
from __future__ import absolute_import

# Check if future is installed, if not use included batteries
try:
    import future
except ImportError:
    import os.path as op
    import sys

    future_base = op.abspath(op.join(op.dirname(__file__), 'extlibs', 'future'))
    sys.path.insert(0, op.join(future_base, 'py2_3'))
    if sys.version_info[:2] < (3, 0):
        sys.path.insert(0, op.join(future_base, 'py2'))
    del future_base
    del sys
    del op
    try:
        import future
    except ImportError:
        print('Failed to get python-future')
        raise

from builtins import range
from builtins import object

import os
import sys

if 'sphinx' in sys.modules:
    setattr(sys, 'is_epydoc', True)
_is_epydoc = getattr(sys, 'is_epydoc', False)

version = '1.4.0b1'

# Pyglet platform treats *BSD systems as Linux
compat_platform = sys.platform
if 'bsd' in compat_platform:
    compat_platform = 'linux-compat'

_enable_optimisations = not __debug__
if getattr(sys, 'frozen', None):
    _enable_optimisations = True

#: Global dict of pyglet options. To change an option from its default, you
#: must import ``pyglet`` before any sub-packages.
options = {
    'audio': ('directsound', 'openal', 'pulse', 'silent'),
    'debug_font': False,
    'debug_gl': not _enable_optimisations,
    'debug_gl_trace': False,
    'debug_gl_trace_args': False,
    'debug_graphics_batch': False,
    'debug_lib': False,
    'debug_media': False,
    'debug_texture': False,
    'debug_trace': False,
    'debug_trace_args': False,
    'debug_trace_depth': 1,
    'debug_trace_flush': True,
    'debug_win32': False,
    'debug_x11': False,
    'graphics_vbo': True,
    'shadow_window': False,
    'vsync': None,
    'xsync': True,
    'xlib_fullscreen_override_redirect': False,
    'darwin_cocoa': True,
    'search_local_libs': True,
}

_option_types = {
    'audio': tuple,
    'debug_font': bool,
    'debug_gl': bool,
    'debug_gl_trace': bool,
    'debug_gl_trace_args': bool,
    'debug_graphics_batch': bool,
    'debug_lib': bool,
    'debug_media': bool,
    'debug_texture': bool,
    'debug_trace': bool,
    'debug_trace_args': bool,
    'debug_trace_depth': int,
    'debug_trace_flush': bool,
    'debug_win32': bool,
    'debug_x11': bool,
    'ffmpeg_libs_win': tuple,
    'graphics_vbo': bool,
    'shadow_window': bool,
    'vsync': bool,
    'xsync': bool,
    'xlib_fullscreen_override_redirect': bool,
}


def _read_environment():
    """Read defaults for options from environment"""
    for key in options:
        env = 'PYGLET_%s' % key.upper()
        try:
            value = os.environ[env]
            if _option_types[key] is tuple:
                options[key] = value.split(',')
            elif _option_types[key] is bool:
                options[key] = value in ('true', 'TRUE', 'True', '1')
            elif _option_types[key] is int:
                options[key] = int(value)
        except KeyError:
            pass


_read_environment()

if compat_platform == 'cygwin':
    # This hack pretends that the posix-like ctypes provides windows
    # functionality. COM does not work with this hack, so there is no
    # DirectSound support.
    import ctypes

    ctypes.windll = ctypes.cdll
    ctypes.oledll = ctypes.cdll
    ctypes.WINFUNCTYPE = ctypes.CFUNCTYPE
    ctypes.HRESULT = ctypes.c_long

# Call tracing
# ------------

_trace_filename_abbreviations = {}


def _trace_repr(value, size=40):
    value = repr(value)
    if len(value) > size:
        value = value[:size // 2 - 2] + '...' + value[-size // 2 - 1:]
    return value


def _trace_frame(thread, frame, indent):
    from pyglet import lib
    if frame.f_code is lib._TraceFunction.__call__.__code__:
        is_ctypes = True
        func = frame.f_locals['self']._func
        name = func.__name__
        location = '[ctypes]'
    else:
        is_ctypes = False
        code = frame.f_code
        name = code.co_fname
        path = code.co_filename
        line = code.co_firstlineno

        try:
            filename = _trace_filename_abbreviations[path]
        except KeyError:
            # Trim path down
            dir = ''
            path, filename = os.path.split(path)
            while len(dir + filename) < 30:
                filename = os.path.join(dir, filename)
                path, dir = os.path.split(path)
                if not dir:
                    filename = os.path.join('', filename)
                    break
            else:
                filename = os.path.join('...', filename)
            _trace_filename_abbreviations[path] = filename

        location = '(%s:%d)' % (filename, line)

    if indent:
        name = 'Called from %s' % name
    print('[%d] %s%s %s' % (thread, indent, name, location))

    if _trace_args:
        if is_ctypes:
            args = [_trace_repr(arg) for arg in frame.f_locals['args']]
            print('    %sargs=(%s)' % (indent, ', '.join(args)))
        else:
            for argname in code.co_varnames[:code.co_argcount]:
                try:
                    argvalue = _trace_repr(frame.f_locals[argname])
                    print('  %s%s=%s' % (indent, argname, argvalue))
                except:
                    pass
    if _trace_flush:
        sys.stdout.flush()


def _thread_trace_func(thread):
    def _trace_func(frame, event, arg):
        if event == 'call':
            indent = ''
            for i in range(_trace_depth):
                _trace_frame(thread, frame, indent)
                indent += '  '
                frame = frame.f_back
                if not frame:
                    break
        elif event == 'exception':
            (exception, value, traceback) = arg
            print('First chance exception raised:', repr(exception))

    return _trace_func


def _install_trace():
    global _trace_thread_count
    sys.setprofile(_thread_trace_func(_trace_thread_count))
    _trace_thread_count += 1


_trace_thread_count = 0
_trace_args = options['debug_trace_args']
_trace_depth = options['debug_trace_depth']
_trace_flush = options['debug_trace_flush']
if options['debug_trace']:
    _install_trace()


# Lazy loading
# ------------

class _ModuleProxy(object):
    _module = None

    def __init__(self, name):
        self.__dict__['_module_name'] = name

    def __getattr__(self, name):
        try:
            return getattr(self._module, name)
        except AttributeError:
            if self._module is not None:
                raise

            import_name = 'pyglet.%s' % self._module_name
            __import__(import_name)
            module = sys.modules[import_name]
            object.__setattr__(self, '_module', module)
            globals()[self._module_name] = module
            return getattr(module, name)

    def __setattr__(self, name, value):
        try:
            setattr(self._module, name, value)
        except AttributeError:
            if self._module is not None:
                raise

            import_name = 'pyglet.%s' % self._module_name
            __import__(import_name)
            module = sys.modules[import_name]
            object.__setattr__(self, '_module', module)
            globals()[self._module_name] = module
            setattr(module, name, value)


if True:
    app = _ModuleProxy('app')
    canvas = _ModuleProxy('canvas')
    clock = _ModuleProxy('clock')
    com = _ModuleProxy('com')
    event = _ModuleProxy('event')
    font = _ModuleProxy('font')
    gl = _ModuleProxy('gl')
    graphics = _ModuleProxy('graphics')
    image = _ModuleProxy('image')
    input = _ModuleProxy('input')
    lib = _ModuleProxy('lib')
    media = _ModuleProxy('media')
    model = _ModuleProxy('model')
    resource = _ModuleProxy('resource')
    sprite = _ModuleProxy('sprite')
    text = _ModuleProxy('text')
    window = _ModuleProxy('window')

# Fool py2exe, py2app into including all top-level modules (doesn't understand
# lazy loading)
if False:
    from . import app
    from . import canvas
    from . import clock
    from . import com
    from . import event
    from . import font
    from . import gl
    from . import graphics
    from . import input
    from . import image
    from . import lib
    from . import media
    from . import model
    from . import resource
    from . import sprite
    from . import text
    from . import window

# Hack around some epydoc bug that causes it to think pyglet.window is None.
if False:
    from . import window
