import ctypes


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


class Method(object):
    """COM method."""
    def __init__(self, restype, *args):
        self.restype = restype
        self.argtypes = args

    def get_field(self):
        return ctypes.WINFUNCTYPE(self.restype, *self.argtypes)


class STDMethod(Method):
    """COM method with HRESULT return value"""
    def __init__(self, *args):
        super(STDMethod, self).__init__(ctypes.HRESULT, *args)


class COMMethodInstance(object):
    """Binds a COM interface method."""
    def __init__(self, name, i, method):
        self.name = name
        self.i = i
        self.method = method

    def __get__(self, obj, tp):
        if obj is not None:
            def _call(*args):
                com_method = self.method.get_field()(self.i, self.name)
                # obj is COMInterface structure.
                return com_method(obj, *args)
            return _call
        raise AttributeError()


class COMInterface(ctypes.Structure):
    """Dummy structure to serve as the type of all COM pointers."""
    _fields_ = [
        ('lpVtbl', ctypes.c_void_p)
    ]


class InterfaceMetaclass(type(ctypes.POINTER(COMInterface))):
    """Creates COM interface pointers."""
    def __new__(cls, name, bases, dct):
        methods = []
        for base in bases[::-1]:
            methods.extend(base.__dict__.get('_methods_', ()))
        methods.extend(dct.get('_methods_', ()))
        for i, (n, method) in enumerate(methods):
            dct[n] = COMMethodInstance(n, i, method)

        dct['_type_'] = COMInterface
        return super(InterfaceMetaclass, cls).__new__(cls, name, bases, dct)


class Interface(ctypes.POINTER(COMInterface),  metaclass=InterfaceMetaclass):
    """Base COM interface pointer."""


class IUnknown(Interface):
    _methods_ = [
        ('QueryInterface', STDMethod(REFIID, ctypes.c_void_p)),
        ('AddRef', Method(ctypes.c_int)),
        ('Release', Method(ctypes.c_int))
    ]


def test():
    interface = IUnknown()
    try:
        interface.AddRef()
    except ValueError as e:
        assert str(e) == 'NULL COM pointer access', 'error must be NULL COM pointer access'


if __name__ == '__main__':
    test()
