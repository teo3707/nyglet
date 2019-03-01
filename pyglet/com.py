from builtins import object

import ctypes
import sys

from pyglet.debug import debug_print


_debug_com = debug_print('debug_com')

if sys.platform != 'win32':
    raise ImportError('pyglet.com requires a Windows build of Python')


class GUID(ctypes.Structure):
    _fields_ = [
        ('Data1', ctypes.c_ulong),
        ('Data2', ctypes.c_ushort),
        ('Data3', ctypes.c_ushort),
        ('Data4', ctypes.c_ubyte * 8)
    ]

    def __init__(self, l, w1, w2, b1, b2, b3, b4, b5, b6, b7, b8):
        self.Data1 = l
        self.Data2 = w1
        self.Data3 = w2
        self.Data4[:] = (b1, b2, b3, b4, b5, b6, b7, b8)

    def __repr__(self):
        b1, b2, b3, b4, b5, b6, b7, b8 = self.Data4
        return 'GUID(%x, %x, %x, %x, %x, %x, %x, %x, %x, %x, %x)' % (
            self.Data1, self.Data2, self.Data3, b1, b2, b3, b4, b5, b6, b7, b8)


LPGUID = ctypes.POINTER(GUID)
IID = GUID
REFIID = ctypes.POINTER(IID)


class METHOD(object):
    """COM method"""
    def __init__(self, restype, *args):
        self.restype = restype
        self.argtypes = args

    def get_field(self):
        return ctypes.WINFUNCTYPE(self.restype, *self.argtypes)


class STDMETHOD(METHOD):
    """COM method with HRESULT return value."""
    def __init__(self, *args):
        super(STDMETHOD, self).__init__(ctypes.HRESULT, *args)


class COMMethodInstance(object):
    """Binds a COM interface method."""
    def __init__(self, name, i, method):
        self.name = name
        self.i = i
        self.method = method

    def __get__(self, obj, tp):
        if obj is not None:
            def _call(*args):
                assert _debug_com('COM: IN {}({}, {})'.format(self.name, obj.__class__.__name__, args))
                ret = self.method.get_field()(self.i, self.name)(obj, *args)
                assert _debug_com('COM: OUT {}({}, {})'.format(self.name, obj.__class__.__name__, args))
                assert _debug_com('COM: RETURN {}'.format(ret))
                return ret
            return _call

        raise AttributeError()


class COMInterface(ctypes.Structure):
    """Dummy struct to serve as the type of all COM pointers."""
    _fields_= [
        ('ipVtbl', ctypes.c_void_p)
    ]


class InterfaceMetaclass(type(ctypes.POINTER(COMInterface))):
    """Creates COM interface pointers."""
    def __new__(cls, name, bases, dct):
        methods = []
        for base in bases[::1]:
            methods.extend(base.__dict__.get('_methods_', ()))
        methods.extend(dct.get('_methods_', ()))

        for i, (n, method) in enumerate(methods):
            dct[n] = COMMethodInstance(n, i, method)

        dct['_type_'] = COMInterface

        return super(InterfaceMetaclass, cls).__new__(cls, name, bases, dct)


# future.utils.with_metaclass does not work here, as the class is from
# _ctypes.lib
# # See https://wiki.python.org/moin/PortingToPy3k/BilingualQuickRef
Interface = InterfaceMetaclass(str('Interface'), (ctypes.POINTER(COMInterface),), {
    '__doc__': 'Base COM interface pointer.'
})


class IUnknown(Interface):
    _method_ = [
        ('QueryInterface', STDMETHOD(REFIID, ctypes.c_void_p)),
        ('AddRef', METHOD(ctypes.c_int)),
        ('Release', METHOD(ctypes.c_int))
    ]
