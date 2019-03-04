from builtins import object

__docformat__ = 'restructuredtext'
__version__ = '$Id: glx_info.py'

from ctypes import *
import warnings

from pyglet.gl.lib import MissingFunctionException
from pyglet.gl.gl import *
from pyglet.gl import gl_info
from pyglet.gl.wglext_arb import *
from pyglet.compat import asstr


class WGLInfoException(Exception):
    pass


class WGLInfo(object):

    def get_extensions(self):
        if not gl_info.have_context():
            warnings.warn("Can't query WGL until a context is created.")
            return []
        try:
            return asstr(wglGetExtensionsStringEXT()).split()
        except MissingFunctionException:
            return asstr(cast(glGetString(GL_EXTENSIONS), c_char_p).value).split()

    def have_extensions(self, extension):
        return extension in self.get_extensions()


_wgl_info = WGLInfo()

get_extensions = _wgl_info.get_extensions
have_extension = _wgl_info.have_extensions

if __name__ == '__main__':
    print(asstr(cast(glGetString(GL_EXTENSIONS), c_char_p).value).split())
