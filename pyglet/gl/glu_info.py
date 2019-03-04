from builtins import object

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypes import *
import warnings

from pyglet.gl.glu import *
from pyglet.compat import asstr


class GLUInfo(object):
    """Information interface for the GLU library.
    """
    have_context = False
    version = '0.0.0'
    extensions = []

    _have_info = False

    def set_active_context(self):
        self.have_context = True
        if not self._have_info:
            self.extensions = asstr(cast(gluGetString(GLU_EXTENSIONS), c_char_p).value).split()
            self.version = asstr(cast(gluGetString(GLU_VERSION), c_char_p).value)
            self._have_info = True

    def have_version(self, major, minor=0, release=0):
        """Determine if a version of GLU is supported.
        """
        if not self.have_context:
            warnings.warn('No GL context created yet.')
        ver = '%s.0.0' % self.version.split(' ', 1)[0]
        imajor, iminor, irelease = [int(v) for v in ver.split('.', 3)[:3]]
        return imajor > major or \
               (imajor == major and iminor > minor) or \
               (imajor == major and iminor == minor and irelease >= release)

    def get_version(self):
        '''Get the current GLU version.

        :return: the GLU version
        :rtype: str
        '''
        if not self.have_context:
            warnings.warn('No GL context created yet.')
        return self.version

    def have_extension(self, extension):
        '''Determine if a GLU extension is available.

        :Parameters:
            `extension` : str
                The name of the extension to test for, including its
                ``GLU_`` prefix.

        :return: True if the extension is provided by the implementation.
        :rtype: bool
        '''
        if not self.have_context:
            warnings.warn('No GL context created yet.')
        return extension in self.extensions

    def get_extensions(self):
        '''Get a list of available GLU extensions.

        :return: a list of the available extensions.
        :rtype: list of str
        '''
        if not self.have_context:
            warnings.warn('No GL context created yet.')
        return self.extensions


# Single instance useful for apps with only a single context (or all contexts
# have same GLU driver, common case).
_glu_info = GLUInfo()

set_active_context = _glu_info.set_active_context
have_version = _glu_info.have_version
get_version = _glu_info.get_version
have_extension = _glu_info.have_extension
get_extensions = _glu_info.get_extensions

if __name__ == '__main__':
    print(asstr(cast(gluGetString(GLU_EXTENSIONS), c_char_p).value).split())
