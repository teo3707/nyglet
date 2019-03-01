from __future__ import print_function

import pyglet


def debug_print(enabled_or_options='debug'):
    if isinstance(enabled_or_options, bool):
        enabled = enabled_or_options
    else:
        enabled = pyglet.options.get(enabled_or_options, False)

    if enabled:
        def _debug_print(*args, **kwargs):
            print(*args, **kwargs)
            return True
    else:
        def _debug_print(*args, **kwargs):
            return True

    return _debug_print
