from __future__ import print_function

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

_first_heading = True


def _heading(heading):
    global _first_heading
    if not _first_heading:
        print()
    else:
        _first_heading = False
    print(heading)
    print('-' * 78)


def dump_python():
    """Dump Python version and environment to stdout."""
    import os
    import sys
    print('sys.version:', sys.version)
    print('sys.platform:', sys.platform)
    print('sys.maxint:', sys.maxsize)
    if sys.platform == 'darwin':
        try:
            from objc import __version__ as pyobjc_version
            print('objc.__version__:', pyobjc_version)
        except:
            print('PyObjC not available')
        print('os.getcwd():', os.getcwd())
        for key, value in os.environ.items():
            if key.startswith('PYGLET_'):
                print("os.environ['%s']: %s" % (key, value))


def dump_pyglet():
    """Dump pygelt version and options."""
    import pyglet
    print('pyglet.version:', pyglet.version)
    print('pygget.compat_platform:', pyglet.compat_platform)
    print('pyglet.__file__:', pyglet.__file__)
    for key, value in pyglet.options.items():
        print("pyglet.options['%s'] = %r" % (key, value))


def dump_window():
    """Dump display, window, screen and default config info."""
    import pyglet
    import pyglet.window
    display = pyglet.canvas.get_display()
    print('display:', repr(display))
    screens = display.get_screens()
    for i, screen in enumerate(screens):
        print("screens['%d']: %r" % (i, screen))
    window = pyglet.window.Window(visible=False)
    for key, value in window.config.get_gl_attributes():
        print("config['%s'] = %r" % (key, value))
    print('context:', repr(window.context))

    _heading('window.config._info')
    dump_gl(window.context)
    window.close()


def dump_gl(context=None):
    """Dump GL info."""
    if context is not None:
        info = context.get_info()
    else:
        from pyglet.gl import gl_info as info
    print('gl_info.get_version():', info.get_version())
    print('gl_info.get_vendor():', info.get_vendor())
    print('gl_info.get_renderer():', info.get_renderer())
    print('gl_info.get_extensions():')
    extensions = list(info.get_extensions())
    extensions.sort()
    for name in extensions:
        print('  ', name)





def _try_dump(heading, func):
    _heading(heading)
    try:
        func()
    except:
        import traceback
        traceback.print_exc()


def dump():
    """Dump all information to stdout."""
    _try_dump('Python', dump_python)
    _try_dump('pyglet', dump_pyglet)
    _try_dump('window', dump_window)


if __name__ == '__main__':
    dump()

