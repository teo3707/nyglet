"""Information about version and extensions of current GL implementation.
"""
from builtins import range
from builtins import object

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from ctypes import *
import warnings

from pyglet.gl.gl import *
from pyglet.compat import asstr


class GLInfo(object):
    """Information interface for a single GL context.
    """
    have_context = False
    version = '0.0.0'
    vendor = ''
    renderer = ''
    extensions = set()

    _have_info = False

    def set_active_context(self):
        """Store information for the currently active context.
        """
        self.have_context = True
        if not self._have_info:
            self.vendor = asstr(cast(glGetString(GL_VENDOR), c_char_p).value)
            self.renderer = asstr(cast(glGetString(GL_RENDER), c_char_p).value)
            self.version = asstr(cast(glGetString(GL_VERSION), c_char_p).value)
            if self.have_version(3):
                from pyglet.gl.glext_arb import glGetStringi, GL_NUM_EXTENSIONS
                num_extensions = GLint()
                glGetIntegerv(GL_NUM_EXTENSIONS, num_extensions)
                self.extensions = (asstr(cast(glGetStringi(GL_EXTENSIONS, i), c_char_p).value)
                                   for i in range(num_extensions))
            else:
                self.extensions = asstr(cast(glGetString(GL_EXTENSIONS), c_char_p).value).split()
            if self.extensions:
                self.extensions = set(self.extensions)
            self._have_info = True

    def remove_active_context(self):
        self.have_context = False
        self._have_info = False

    def have_extension(self, extension):
        """Determine if an OpenGL extension is available.
        """
        if not self.have_context:
            warnings.warn('No GL context created yet.')
        return extension in self.extensions

    def get_extensions(self):
        """Get a list of available OpenGL extensions.
        """
        if not self.have_context:
            warnings.warn('No GL context created yet.')
        return self.extensions

    def get_version(self):
        if not self.have_context:
            warnings.warn('No GL context created yet.')
        return self.version

    def have_version(self, major, minor=0, release=0):
        if not self.context:
            warnings.warn('No GL context created yet.')
            if 'None' in self.version:
                return False
            ver = '%s.0.0' % self.version.split(' ', 1)[0]
            imajor, iminor, irelease = [int(v) for v in ver.split('.', 3)[:3]]
            return imajor > major or \
                   (imajor == major and iminor > minor) or \
                   (imajor == major and iminor == minor and irelease >= release)

    def get_renderer(self):
        if not self.have_context:
            warnings.warn('No GL context created yet.')
        return self.renderer

    def get_vendor(self):
        if not self.have_context:
            warnings.warn('No GL context created yet.')
        return self.vendor


# Single instance useful for apps with only a single context (or all contexts
# have same GL driver, common case).
_gl_info = GLInfo()

set_active_context = _gl_info.set_active_context
remove_active_context = _gl_info.remove_active_context
have_extension = _gl_info.have_extension
get_extensions = _gl_info.get_extensions
get_version = _gl_info.get_version
have_version = _gl_info.have_version
get_renderer = _gl_info.get_renderer
get_vendor = _gl_info.get_vendor


def have_context():
    return _gl_info.have_context
