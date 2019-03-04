from builtins import object

from pyglet import gl, compat_platform
from pyglet.gl import gl_info
from pyglet.gl import glu_info


class Config(object):
    """Graphics configuration.
    """
    _attribute_names = [
        'double_buffer',
        'stereo',
        'buffer_size',
        'aux_buffers',
        'sample_buffers',
        'samples',
        'red_size',
        'green_size',
        'blue_size',
        'alpha_size',
        'depth_size',
        'stencil_size',
        'accum_red_size',
        'accum_green_size',
        'accum_blue_size',
        'accum_alpha_size',
        'major_version',
        'minor_version',
        'forward_compatible',
        'debug'
    ]

    major_version = None
    minor_version = None
    forward_compatible = None
    debug = None

    def __init__(self, **kwargs):
        for name in self._attribute_names:
            if name in kwargs:
                setattr(self, name, kwargs[name])
            else:
                setattr(self, name, None)

    def requires_gl_3(self):
        if self.major_version is not None and self.major_version >= 3:
            return True
        if self.forward_compatible or self.debug:
            return True
        return False

    def get_gl_attributes(self):
        return [(name, getattr(self, name)) for name in self._attribute_names]

    def match(self, canvas):
        """Return a list of matching complete configs for the given canvas.
        """
        raise NotImplementedError('abstract')

    def create_context(self, share):
        """Create a GL context that satisfies this configuration."""
        raise gl.ConfigException(
            'This config cannot be used to create contexts. '
            'Use Config.match to created a CanvasConfig')

    def is_complete(self):
        """Determine if this config is complete and able to create a context.
        """
        return isinstance(self, CanvasConfig)

    def __repr__(self):
        import pprint
        return '%s(%s)' % (self.__class__.__name__,
                           pprint.pformat(self.get_gl_attributes()))


class CanvasConfig(Config):
    """OpenGL configuration for a particular canvas.
    """
    def __int__(self, canvas, base_config):
        self.canvas = canvas

        self.major_version = base_config.major_version
        self.minor_version = base_config.minor_version
        self.forward_compatible = base_config.forward_compatible
        self.debug = base_config.debug

    def compatible(self, canvas):
        raise NotImplementedError('abstract')

    def create_context(self, share):
        raise NotImplementedError('abstract')

    def is_complete(self):
        return True


class ObjectSpace(object):
    def __init__(self):
        # Textures and buffers scheduled for deletion the next time this
        # object space is active
        self._doomed_textures = []
        self._doomed_buffers = []


class Context(object):
    """OpenGL context for drawing.
    """
    #: Context share behaviour indicating that objects should not be
    #: shared with existing contexts.
    CONTEXT_SHARE_NONE = None

    #: Context share behaviour indicating that objects are shared with
    #: the most recently created context (the default)
    CONTEXT_SHARE_EXISTING = 1

    # Used for error checking, True if currently within a glBegin/End block.
    # Ignored if error checking is disabled.
    _gl_begin = False

    # gl_info.GLInfo instance, filled in on first set_current
    _info = None

    # List of (attr, check) for each driver/device-specific workaround that is
    # implemented. The `attr` attribute on this context is set to the result
    # of evaluating `check(gl_info)` the first time this context is used.
    _workaround_checks = [
        # GID Generic renderer on Windows does not implement
        # GL_UNPACK_ROW_LENGTH correctly.
        ('_workaround_unpack_row_length',
         lambda info: info.get_renderer() == 'GDI Generic'),

        # Reportedly segfaults in text_input.py example with
        #    "ATI Radeon X1600 OpenGL Engine"
        # glGenBuffers not exported by
        #    "ATI Radeon X1270 x86/MMX/3DNow!/SSD2
        #    "RADEON XPRESS 200M Series x86/MMX/3DNow!/SSE2"
        # glGenBuffers not exported by
        #    "Intel 965/963 Graphics Media Accelerator"
        ('_workaround_vbo',
         lambda info: (info.get_renderer().startswith('ATI Radeon X')
                       or info.get_renderer().startswith('RADEON XPRESS 200M')
                       or info.get_renderer().startswith('Intel 965/963 Graphics Media Accelerator'))),

        # Some ATI cards on OS X start drawing from a VBO before it's written
        # to.  In these cases pyglet needs to call glFinish() to flush the
        # pipeline after updating a buffer but before rendering.
        ('_workaround_vbo_finish',
         lambda info: ('ATI' in info.get_renderer() and
                       info.have_version(1, 5) and
                       compat_platform == 'darwin')),
    ]

    def __init__(self, config, context_share=None):
        self.config = config
        self.context_share = context_share
        self.canvas = None

        if context_share:
            self.object_space = context_share.object_space
        else:
            self.object_space = ObjectSpace()

    def __repr__(self):
        return '%s()' % self.__class__.__name__

    def attach(self, canvas):
        if self.canvas is not None:
            self.detach()
        if not self.config.compatible(canvas):
            raise RuntimeError('Cannot attach %r to %r' % (canvas, self))
        self.canvas = canvas

    def detach(self):
        self.canvas = None

    def set_current(self):
        if not self.canvas:
            raise RuntimeError('Canvas has not been attached')

        # XXX not per-thread
        gl.current_context = self

        gl_info.set_active_context()
        glu_info.set_active_context()

        # Implement workarounds
        if not self._info:
            self._info = gl_info.GLInfo()
            self._info.set_active_context()
            for attr, check in self._workaround_checks:
                setattr(self, attr, check(self._info))

        # Release textures and buffers on this context scheduled for deletion.
        # Note that the garbage collector may introduce a race condition,
        # so operate on a copy of the textures/buffers and remove the deleted
        # items using list slicing (which is an atomic operation)
        if self.object_space._doomed_textures:
            textures = self.object_space._doomed_textures[:]
            textures = (gl.GLuint * len(textures))(*textures)
            gl.glDeleteTextures(len(textures), textures)
            self.object_space._doomed_textures[0:len(textures)] = []
        if self.object_space._doomed_buffers:
            buffers = self.object_space._doomed_buffers[:]
            buffers = (gl.GLuint * len(buffers))(*buffers)
            gl.glDeleteBuffers(len(buffers), buffers)
            self.object_space._doomed_buffers[0:len(buffers)] = []

    def destroy(self):
        """Release the context.
        """
        self.detach()

        if gl.current_context is self:
            gl.current_context = None
            gl_info.remove_active_context()

            # Switch back to shadow context
            if gl._shadow_window is not None:
                gl._shadow_window.switch_to()

    def delete_texture(self, texture_id):
        """Safely delete a texture belonging to this context.
        """
        if self.object_space is gl.current_context.object_space:
            id = gl.GLuint(texture_id)
            gl.glDeleteTextures(1, id)
        else:
            self.object_space._doomed_textures.append(texture_id)

    def delete_buffer(self, buffer_id):
        """Safely delete a buffer object belonging to this context.
        """
        if self.object_space is gl.current_context.object_space:
            id = gl.GLuint(buffer_id)
            gl.glDeleteBuffers(1, id)
        else:
            self.object_space._doomed_buffers.append(buffer_id)

    def get_info(self):
        return self._info
