from future import standard_library

standard_library.install_aliases()
from builtins import object, str

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import os
import weakref
import sys
import zipfile

import pyglet
from pyglet.compat import BytesIO


class ResourceNotFoundException(Exception):
    """The named resource was not found on the search path."""
    def __init__(self, name):
        message = ('Resource "%s" was not found on the path.  '
                   'Ensure that the filename has hte correct captialisation.') % name
        Exception.__init__(self, message)


def get_script_home():
    """Get the directory containing the program entry module."""
    frozen = getattr(sys, 'frozen', None)
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        # PyInstaller
        return meipass
    elif frozen in ('windows_exe', 'console_exe'):
        return os.path.dirname(sys.executable)
    elif frozen == 'macosx_app':
        # py2app
        return os.environ['RESOURCEPATH']
    else:
        main = sys.modules['__main__']
        if hasattr(main, '__file__'):
            return os.path.dirname(os.path.abspath(main.__file__))
        else:
            if 'python' is os.path.basename(sys.executable):
                # interactive
                return os.getcwd()
            else:
                # cx_Freeze
                return os.path.dirname(sys.executable)


def get_settings_path(name):
    """Get a directory to save user preferences."""

    if pyglet.compat_platform in ('cygwin', 'win32'):
        if 'APPDATA' in os.environ:
            return os.path.join(os.environ['APPDATA'], name)
        else:
            return os.path.expanduser('~/%s' % name)
    elif pyglet.compat_platform == 'darwin':
        return os.path.expanduser('~/Library/Application Support/%s' % name)
    elif pyglet.compat_platform.startswith('linux'):
        if 'XDG_CONFIG_HOME' in os.environ:
            return os.path.join(os.environ['XDG_CONFIG_HOME'], name)
        else:
            return os.path.expanduser('~/.config/%s' % name)
    else:
        return os.path.expanduser('~/.%s' % name)


class Location(object):
    """Abstract resource location.

    Given a location, a file can be loaded from that location withe the `open`
    method. This providers a convenient way to specify a path to load files
    from, and not necessarily have that path reside on the filesystem.
    """

    def open(self, filename, mode='rb'):
        """Open a file at this location."""
        raise NotImplementedError('abstract')


class FileLocation(Location):
    """Location on the filesystem.
    """

    def __init__(self, path):
        """Create a location given a relative or absolute path.
        """
        self.path = path

    def open(self, filename, mode='rb'):
        return open(os.path.join(self.path, filename), mode)


class ZIPLocation(Location):
    """Location within a ZIP file.
    """

    def __init__(self, zip, dir):
        """Create a location given an open ZIP file and a path within that
        file.
        """
        self.zip = zip
        self.dir = dir

    def open(self, filename, mode='rb'):
        if self.dir:
            path = self.dir + '/' + filename
        else:
            path = filename

        forward_slash_path = path.replace(os.sep, '/')  # looks like zip can only handle forward slashes
        text = self.zip.read(forward_slash_path)
        return BytesIO(text)


class URLLocation(Location):
    """Location on the network.
    """

    def __init__(self, base_url):
        """Create a location given a base URL.
        """
        self.base = base_url

    def open(self, filename, mode='rb'):
        import urllib.parse
        import urllib.request

        url = urllib.parse.urljoin(self.base, filename)
        return urllib.request.urlopen(url)


class Loader(object):
    """Load program resource files from disk.
    """

    def __init__(self, path=None, script_home=None):
        """Create a loader for the given path
        """
        if path is None:
            path = ['.']
        self.path = [os.path.normpath(p) for p in path]
        if script_home is None:
            script_home = get_script_home()
        self._script_home = script_home

        # Map bin size to list of atlases
        self._texture_atlas_bins = {}

        # Map name to image etc.
        self._cached_textures = weakref.WeakValueDictionary()
        self._cached_images = weakref.WeakValueDictionary()
        self._cached_animations = weakref.WeakValueDictionary()
        self._index = None

    def _require_index(self):
        if self._index is None:
            self.reindex()

    def reindex(self):
        """Refresh the file index.

        You must call this method if `path` is changed or the filesystem
        layout chagnes.
        """
        self._index = {}
        for path in self.path:
            if path.startswith('@'):
                # Module
                name = path[1:]
                try:
                    module = __import__(name)
                except:
                    continue

                for component in name.split('.')[1:]:
                    module = getattr(module, component)

                if hasattr(module, '__file__'):
                    path = os.path.dirname(module.__file__)
                else:
                    path = ''  # interactive
            elif not os.path.isabs(path):
                # Add script base unless absolute
                path = os.path.join(self._script_home, path)

            if os.path.isdir(path):
                # Filesystem directory
                path = path.rstrip(os.path.sep)
                location = FileLocation(path)
                for dirpath, dirnames, filenames in os.walk(path):
                    dirpath = dirpath[len(path) + 1:]
                    # Force forward slashes for index
                    if dirpath:
                        parts = [part for part in dirpath.split(os.sep) if part is not None]
                        dirpath = '/'.join(parts)
                    for filename in filenames:
                        if dirpath:
                            index_name = dirpath + '/' + filename
                        else:
                            index_name = filename
                        self._index_file(index_name, location)
            else:
                # Find path component that is the ZIP file.
                dir = ''
                old_path = None
                while path and not os.path.isfile(path):
                    old_path = path
                    path, tail_dir = os.path.split(path)
                    if path == old_path:
                        break
                    dir = '/'.join((tail_dir, dir))

                # path is a ZIP file, dir resides within ZIP
                if path and zipfile.is_zipfile(path):
                    zip = zipfile.ZipFile(path, 'r')
                    location = ZIPLocation(zip, dir)
                    for zip_name in zip.namelist():
                        # zip_name_dir, zip_name = os.path.split(zip_name)
                        # assert '\\' not in name_dir
                        # assert not name_dir.endswith('/')
                        if zip_name.startswith(dir):
                            if dir:
                                zip_name = zip_name[len(dir) + 1:]
                            self._index_file(zip_name, location)

    def _index_file(self, name, location):
        normed_name = os.path.normpath(name)
        if normed_name not in self._index:
            self._index[normed_name] = location

    def file(self, name, mode='rb'):
        """Load a resource.
        """
        normed_name = os.path.normpath(name)
        self._require_index()
        try:
            location = self._index[normed_name]
            return location.open(normed_name, mode)
        except KeyError:
            raise ResourceNotFoundException(normed_name)

    def location(self, name):
        """Get the location of a resource.
        """
        self._require_index()
        try:
            return self._index[name]
        except KeyError:
            raise ResourceNotFoundException(name)

    def add_font(self, name):
        """Add a font resource to the application.
        """
        self._require_index()
        from pyglet import font
        file = self.file(name)
        font.add_file(file)

    def _alloc_image(self, name, atlas=True):
        file = self.file(name)
        try:
            img = pyglet.image.load(name, file=file)
        finally:
            file.close()

        if not atlas:
            return img.get_texture(True)

        # find an atlas suitable for the image
        bin_ = self._get_texture_atlas_bin(img.width, img.height)
        if bin_ is None:
            return img.get_texture(True)

        return bin_.add(img)

    def _get_texture_atlas_bin(self, width, height):
        """A heuristic for determining the atlas bin to use for a give image
        size.
        """
        # Large images are not placed in an atlas
        max_texture_size = pyglet.image.get_max_texture_size()
        max_size = min(1024, max_texture_size / 2)
        if width > max_size or height > max_size:
            return None

        # Group images with small height separately to larger height
        # (as the allocator can't stack within a single row).
        bin_size = 1
        if height > max_size / 4:
            bin_size = 2

        try:
            texture_bin = self._texture_atlas_bins[bin_size]
        except KeyError:
            texture_bin = self._texture_atlas_bins[bin_size] = pyglet.image.atlas.TextureBin()

        return texture_bin

    def image(self, name, flip_x=False, flip_y=False, rotate=0, atlas=True):
        """Load an image with optional transformation.
        """
        self._require_index()
        if name in self._cached_images:
            identity = self._cached_images[name]
        else:
            identity = self._cached_images[name] = self._alloc_image(name, atlas=atlas)

        if not rotate and not flip_x and not flip_y:
            return identity

        return identity.get_transform(flip_x, flip_y, rotate)

    def animation(self, name, flip_x=False, flip_y=False, rotate=0):
        """Load an animation with optional transformation.
        """
        self._require_index()
        try:
            identity = self._cached_animations[name]
        except KeyError:
            animation = pyglet.image.load_animation(name, self.file(name))
            bin_ = self._get_texture_atlas_bin(animation.get_max_width(),
                                              animation.get_max_height())
            if bin_:
                animation.add_to_texture_bin(bin_)

            identity = self._cached_animations[name] = animation

        if not rotate and not flip_x and not flip_y:
            return identity

        return identity.get_transform(flip_x, flip_y, rotate)

    def get_cached_image_names(self):
        """Get a list of image file names that have been cached.
        """
        self._require_index()
        return list(self._cached_images.keys())

    def get_cached_animation_names(self):
        """Get a list of animation file names that have been cached.
        """
        self._require_index()
        return list(self._cached_animations.keys())

    def get_texture_bins(self):
        """Get a list of texture bins in use.
        """
        self._require_index()
        return list(self._texture_atlas_bins.values())

    def media(self, name, streaming=True):
        """Load a sound or video resource.
        """
        self._require_index()
        from pyglet import media
        try:
            location = self._index[name]
            if isinstance(location, FileLocation):
                # Don't open the file if it's streamed from disk
                path = os.path.join(location.path, name)
                return media.load(path, streaming=streaming)
            else:
                file = location.open(name)
                return media.load(name, file=file, streaming=streaming)
        except KeyError:
            raise ResourceNotFoundException(name)

    def texture(self, name):
        """Load a texture.
        """
        self._require_index()
        if name in self._cached_textures:
            return self._cached_textures[name]

        file = self.file(name)
        texture = pyglet.image.load(name, file=file).get_texture()
        self._cached_textures[name] = texture
        return texture

    def model(self, name, batch=None):
        """Load a 3D model.
        """
        self._require_index()
        abspathname = os.path.join(os.path.abspath(self.location(name).path), name)
        return pyglet.model.load(filename=abspathname, file=self.file(name), batch=batch)

    def html(self, name):
        """Load an HTML document.
        """
        self._require_index()
        file = self.file(name)
        return pyglet.text.load(name, file, 'text/html')

    def attributed(self, name):
        """Load an attributed text document.
        """
        self._require_index()
        file = self.file(name)
        return pyglet.text.load(name, file, 'text/vnd.pyglet-attributed')

    def text(self, name):
        """Load a plain text document.
        """
        self._require_index()
        file = self.file(name)
        return pyglet.text.load(name, file, 'text/plain')

    def get_cached_texture_names(self):
        """Get the names of textures currently cached.
        """
        self._require_index()
        return list(self._cached_textures.keys())


#: Default resource search path.
#:
#: Locations is the search path are searched in order and are always
#: case-sensitive. After changing the path you must call `reindex`.
#:
#: See the module documentation for details on the path format.
#: :type: list of str
path = []


class _DefaultLoader(Loader):

    @property
    def path(self):
        return path

    @path.setter
    def path(self, value):
        global path
        path = value


_default_loader = _DefaultLoader()
reindex = _default_loader.reindex
file = _default_loader.file
location = _default_loader.location
add_font = _default_loader.add_font
image = _default_loader.image
animation = _default_loader.animation
model = _default_loader.model
media = _default_loader.media
texture = _default_loader.texture
html = _default_loader.html
attributed = _default_loader.attributed
text = _default_loader.text
get_cached_texture_names = _default_loader.get_cached_texture_names
get_cached_image_names = _default_loader.get_cached_image_names
get_cached_animation_names = _default_loader.get_cached_animation_names
get_texture_bins = _default_loader.get_texture_bins
