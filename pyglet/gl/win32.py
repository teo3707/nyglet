from __future__ import absolute_import
from builtins import zip

from pyglet.canvas.win32 import Win32Canvas
from .base import Config, CanvasConfig, Context

from pyglet import gl
from pyglet.gl import gl_info
from pyglet.gl import wgl
from pyglet.gl import wglext_arb
from pyglet.gl import wgl_info

from pyglet.libs.win32 import _user32, _kernel32, _gdi32
from pyglet.libs.win32.constants import *
from pyglet.libs.win32.types import *


class Win32Config(Config):
    pass
