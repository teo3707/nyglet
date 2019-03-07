import ctypes
from win32audio import com


lib = ctypes.oledll.dsound

DWORD = ctypes.c_uint32
LPDWORD = ctypes.POINTER(DWORD)
LONG = ctypes.c_long
LPLONG = ctypes.POINTER(LONG)
WORD = ctypes.c_uint16
HWND = DWORD
LPUNKNOWN = ctypes.c_void_p

D3DVALUE = ctypes.c_float
PD3DVALUE = ctypes.POINTER(D3DVALUE)


class D3DVECTOR(ctypes.Structure):
    _fields_ = [
        ('x', D3DVALUE),
        ('y', D3DVALUE),
        ('z', D3DVALUE)
    ]


PD3DVECTOR = ctypes.POINTER(D3DVECTOR)


class WAVEFORMATEX(ctypes.Structure):
    _fields_ = [
        ('wFormatTag', WORD),
        ('nChannels', WORD),
        ('nSamplesPerSec', DWORD),
        ('nAvgBytesPerSec', DWORD),
        ('nBlockAlign', WORD),
        ('wBitsPerSample', WORD),
        ('cbSize', WORD)
    ]

    def __repr__(self):
        return 'WAVEFORMATEX(wFormatTag={}, nChannels={}, nSamplesPerSec={}, nAvgBytesPerSec={}' \
               ', nBlockAlign={}, wBitsPerSample={}, cbSize={})'.format(
                    self.wFormatTag, self.nChannels, self.nSamplesPerSec,
                    self.nAvgBytesPerSec, self.nBlockAlign, self.wBitsPerSample,
                    self.cbSize)


LPWAVEFORMATEX = ctypes.POINTER(WAVEFORMATEX)
WAVE_FORMAT_PCM = 1


class DSCAPS(ctypes.Structure):
    _fields_ = [
        ('dwSize', DWORD),
        ('dwFlags', DWORD),
        ('dwMinSecondarySampleRate', DWORD),
        ('dwMaxSecondarySampleRate', DWORD),
        ('dwPrimaryBuffers', DWORD),
        ('dwMaxHwMixingAllBuffers', DWORD),
        ('dwMaxHwMixingStaticBuffers', DWORD),
        ('dwMaxHwMixingStreamingBuffers', DWORD),
        ('dwFreeHwMixingAllBuffers', DWORD),
        ('dwFreeHwMixingStaticBuffers', DWORD),
        ('dwFreeHwMixingStreamingBuffers', DWORD),
        ('dwMaxHw3DAllBuffers', DWORD),
        ('dwMaxHw3DStaticBuffers', DWORD),
        ('dwMaxHw3DStreamingBuffers', DWORD),
        ('dwFreeHw3DAllBuffers', DWORD),
        ('dwFreeHw3DStaticBuffers', DWORD),
        ('dwFreeHw3DStreamingBuffers', DWORD),
        ('dwTotalHwMemBytes', DWORD),
        ('dwFreeHwMemBytes', DWORD),
        ('dwMaxContigFreeHwMemBytes', DWORD),
        ('dwUnlockTransferRateHwBuffers', DWORD),
        ('dwPlayCpuOverheadSwBuffers', DWORD),
        ('dwReserved1', DWORD),
        ('dwReserved2', DWORD)
    ]


LPDSCAPS = ctypes.POINTER(DSCAPS)


class DSBCAPS(ctypes.Structure):
    _fields_ = [
        ('dwSize', DWORD),
        ('dwFlags', DWORD),
        ('dwBufferBytes', DWORD),
        ('dwUnlockTransferRate', DWORD),
        ('dwPlayCpuOverhead', DWORD),
    ]


LPDSBCAPS = ctypes.POINTER(DSBCAPS)


class DSBUFFERDESC(ctypes.Structure):
    _fields_ = [
        ('dwSize', DWORD),
        ('dwFlags', DWORD),
        ('dwBufferBytes', DWORD),
        ('dwReserved', DWORD),
        ('lpwfxFormat', LPWAVEFORMATEX),
    ]

    def __repr__(self):
        return 'DSBUFFERDESC(dwSize={}, dwFlags={}, dwBufferBytes={}, lpwfxFormat={})'.format(
                self.dwSize, self.dwFlags, self.dwBufferBytes,
                self.lpwfxFormat.contents if self.lpwfxFormat else None)


LPDSBUFFERDESC = ctypes.POINTER(DSBUFFERDESC)


class DS3DBUFFER(ctypes.Structure):
    _fields_ = [
        ('dwSize', DWORD),
        ('vPosition', D3DVECTOR),
        ('vVelocity', D3DVECTOR),
        ('dwInsideConeAngle', DWORD),
        ('dwOutsideConeAngle', DWORD),
        ('vConeOrientation', D3DVECTOR),
        ('lConeOutsideVolume', LONG),
        ('flMinDistance', D3DVALUE),
        ('flMaxDistance', D3DVALUE),
        ('dwMode', DWORD),
    ]


LPDS3DBUFFER = ctypes.POINTER(DS3DBUFFER)


class DS3DLISTENER(ctypes.Structure):
    _fields_ = [
        ('dwSize', DWORD),
        ('vPosition', D3DVECTOR),
        ('vVelocity', D3DVECTOR),
        ('vOrientFront', D3DVECTOR),
        ('vOrientTop', D3DVECTOR),
        ('flDistanceFactor', D3DVALUE),
        ('flRolloffFactor', D3DVALUE),
        ('flDopplerFactor', D3DVALUE),
    ]


LPDS3DLISTENER = ctypes.POINTER(DS3DLISTENER)


class IDirectSoundBuffer(com.IUnknown):
    _methods_ = [
        ('GetCaps', com.STDMethod(LPDSBCAPS)),
        ('GetCurrentPosition', com.STDMethod(LPDWORD, LPDWORD)),
        ('GetFormat', com.STDMethod(LPWAVEFORMATEX, DWORD, LPDWORD)),
        ('GetVolume', com.STDMethod(LPLONG)),
        ('GetPan', com.STDMethod(LPLONG)),
        ('GetFrequency', com.STDMethod(LPDWORD)),
        ('GetStatus', com.STDMethod(LPDWORD)),
        ('Initialize', com.STDMethod(ctypes.c_void_p, LPDSBUFFERDESC)),
        ('Lock', com.STDMethod(DWORD, DWORD,
                               ctypes.POINTER(ctypes.c_void_p), LPDWORD,
                               ctypes.POINTER(ctypes.c_void_p), LPDWORD,
                               DWORD)),
        ('Play', com.STDMethod(DWORD, DWORD, DWORD)),
        ('SetCurrentPosition', com.STDMethod(DWORD)),
        ('SetFormat', com.STDMethod(LPWAVEFORMATEX)),
        ('SetVolume', com.STDMethod(LONG)),
        ('SetPan', com.STDMethod(LONG)),
        ('SetFrequency', com.STDMethod(DWORD)),
        ('Stop', com.STDMethod()),
        ('Unlock', com.STDMethod(ctypes.c_void_p, DWORD, ctypes.c_void_p, DWORD)),
        ('Restore', com.STDMethod())
    ]


IID_IDirectSound3DListener = com.GUID(
    0x279AFA84, 0x4981, 0x11CE, 0xA5, 0x21, 0x00, 0x20, 0xAF, 0x0B, 0xE5, 0x60)


class IDirectSound3DListener(com.IUnknown):
    _methods_ = [
        ('GetAllParameters', com.STDMethod(LPDS3DLISTENER)),
        ('GetDistanceFactor', com.STDMethod(PD3DVALUE)),
        ('GetDopplerFactor', com.STDMethod(PD3DVALUE)),
        ('GetOrientation', com.STDMethod(PD3DVECTOR, PD3DVECTOR)),
        ('GetPosition', com.STDMethod(PD3DVECTOR)),
        ('GetRolloffFactor', com.STDMethod(PD3DVALUE)),
        ('GetVelocity', com.STDMethod(PD3DVECTOR)),
        ('SetAllParameters', com.STDMethod(LPDS3DLISTENER)),
        ('SetDistanceFactor', com.STDMethod(D3DVALUE, DWORD)),
        ('SetDopplerFactor', com.STDMethod(D3DVALUE, DWORD)),
        ('SetOrientation', com.STDMethod(D3DVALUE, D3DVALUE, D3DVALUE, D3DVALUE, D3DVALUE, D3DVALUE, DWORD)),
        ('SetPosition', com.STDMethod(D3DVALUE, D3DVALUE, D3DVALUE, DWORD)),
        ('SetRolloffFactor', com.STDMethod(D3DVALUE, DWORD)),
        ('SetVelocity', com.STDMethod(D3DVALUE, D3DVALUE, D3DVALUE, DWORD)),
        ('CommitDeferredSettings', com.STDMethod()),
    ]


IID_IDirectSound3DBuffer = com.GUID(
    0x279AFA86, 0x4981, 0x11CE, 0xA5, 0x21, 0x00, 0x20, 0xAF, 0x0B, 0xE5, 0x60)


class IDirectSound3DBuffer(com.IUnknown):
    _methods_ = [
        ('GetAllParameters', com.STDMethod(LPDS3DBUFFER)),
        ('GetConeAngles', com.STDMethod(LPDWORD, LPDWORD)),
        ('GetConeOrientation', com.STDMethod(PD3DVECTOR)),
        ('GetConeOutsideVolume', com.STDMethod(LPLONG)),
        ('GetMaxDistance', com.STDMethod(PD3DVALUE)),
        ('GetMinDistance', com.STDMethod(PD3DVALUE)),
        ('GetMode', com.STDMethod(LPDWORD)),
        ('GetPosition', com.STDMethod(PD3DVECTOR)),
        ('GetVelocity', com.STDMethod(PD3DVECTOR)),
        ('SetAllParameters', com.STDMethod(LPDS3DBUFFER, DWORD)),
        ('SetConeAngles', com.STDMethod(DWORD, DWORD, DWORD)),
        ('SetConeOrientation', com.STDMethod(D3DVALUE, D3DVALUE, D3DVALUE, DWORD)),
        ('SetConeOutsideVolume',  com.STDMethod(LONG, DWORD)),
        ('SetMaxDistance', com.STDMethod(D3DVALUE, DWORD)),
        ('SetMinDistance', com.STDMethod(D3DVALUE, DWORD)),
        ('SetMode', com.STDMethod(DWORD, DWORD)),
        ('SetPosition', com.STDMethod(D3DVALUE, D3DVALUE, D3DVALUE, DWORD)),
        ('SetVelocity', com.STDMethod(D3DVALUE, D3DVALUE, D3DVALUE, DWORD)),
    ]


class IDirectSound(com.IUnknown):
    _methods_ = [
        ('CreateSoundBuffer', com.STDMethod(LPDSBUFFERDESC, ctypes.POINTER(IDirectSoundBuffer), LPUNKNOWN)),
        ('GetCaps', com.STDMethod(LPDSCAPS)),
        ('DuplicateSoundBuffer', com.STDMethod(IDirectSoundBuffer, ctypes.POINTER(IDirectSoundBuffer))),
        ('SetCooperativeLevel', com.STDMethod(HWND, DWORD)),
        ('Compact', com.STDMethod()),
        ('GetSpeakerConfig', com.STDMethod(LPDWORD)),
        ('SetSpeakerConfig', com.STDMethod(DWORD)),
        ('Initialize', com.STDMethod(com.LPGUID)),
    ]


DirectSoundCreate = lib.DirectSoundCreate
DirectSoundCreate.argtypes = [com.LPGUID, ctypes.POINTER(IDirectSound), ctypes.c_void_p]


DSCAPS_PRIMARYMONO = 0x00000001
DSCAPS_PRIMARYSTEREO = 0x00000002
DSCAPS_PRIMARY8BIT = 0x00000004
DSCAPS_PRIMARY16BIT = 0x00000008
DSCAPS_CONTINUOUSRATE = 0x00000010
DSCAPS_EMULDRIVER = 0x00000020
DSCAPS_CERTIFIED = 0x00000040
DSCAPS_SECONDARYMONO = 0x00000100
DSCAPS_SECONDARYSTEREO = 0x00000200
DSCAPS_SECONDARY8BIT = 0x00000400
DSCAPS_SECONDARY16BIT = 0x00000800

DSSCL_NORMAL = 0x00000001
DSSCL_PRIORITY = 0x00000002
DSSCL_EXCLUSIVE = 0x00000003
DSSCL_WRITEPRIMARY = 0x00000004

DSSPEAKER_DIRECTOUT = 0x00000000
DSSPEAKER_HEADPHONE = 0x00000001
DSSPEAKER_MONO = 0x00000002
DSSPEAKER_QUAD = 0x00000003
DSSPEAKER_STEREO = 0x00000004
DSSPEAKER_SURROUND = 0x00000005
DSSPEAKER_5POINT1 = 0x00000006
DSSPEAKER_7POINT1 = 0x00000007

DSSPEAKER_GEOMETRY_MIN = 0x00000005  #   5 degrees
DSSPEAKER_GEOMETRY_NARROW = 0x0000000A  #  10 degrees
DSSPEAKER_GEOMETRY_WIDE = 0x00000014  #  20 degrees
DSSPEAKER_GEOMETRY_MAX = 0x000000B4  # 180 degrees

DSBCAPS_PRIMARYBUFFER = 0x00000001
DSBCAPS_STATIC = 0x00000002
DSBCAPS_LOCHARDWARE = 0x00000004
DSBCAPS_LOCSOFTWARE = 0x00000008
DSBCAPS_CTRL3D = 0x00000010
DSBCAPS_CTRLFREQUENCY = 0x00000020
DSBCAPS_CTRLPAN = 0x00000040
DSBCAPS_CTRLVOLUME = 0x00000080
DSBCAPS_CTRLPOSITIONNOTIFY = 0x00000100
DSBCAPS_CTRLFX = 0x00000200
DSBCAPS_STICKYFOCUS = 0x00004000
DSBCAPS_GLOBALFOCUS = 0x00008000
DSBCAPS_GETCURRENTPOSITION2 = 0x00010000
DSBCAPS_MUTE3DATMAXDISTANCE = 0x00020000
DSBCAPS_LOCDEFER = 0x00040000

DSBPLAY_LOOPING = 0x00000001
DSBPLAY_LOCHARDWARE = 0x00000002
DSBPLAY_LOCSOFTWARE = 0x00000004
DSBPLAY_TERMINATEBY_TIME = 0x00000008
DSBPLAY_TERMINATEBY_DISTANCE = 0x000000010
DSBPLAY_TERMINATEBY_PRIORITY = 0x000000020

DSBSTATUS_PLAYING = 0x00000001
DSBSTATUS_BUFFERLOST = 0x00000002
DSBSTATUS_LOOPING = 0x00000004
DSBSTATUS_LOCHARDWARE = 0x00000008
DSBSTATUS_LOCSOFTWARE = 0x00000010
DSBSTATUS_TERMINATED = 0x00000020

DSBLOCK_FROMWRITECURSOR = 0x00000001
DSBLOCK_ENTIREBUFFER = 0x00000002

DSBFREQUENCY_MIN = 100
DSBFREQUENCY_MAX = 100000
DSBFREQUENCY_ORIGINAL = 0

DSBPAN_LEFT = -10000
DSBPAN_CENTER = 0
DSBPAN_RIGHT = 10000

DSBVOLUME_MIN = -10000
DSBVOLUME_MAX = 0

DSBSIZE_MIN = 4
DSBSIZE_MAX = 0x0FFFFFFF
DSBSIZE_FX_MIN = 150  # NOTE: Milliseconds, not bytes

DS3DMODE_NORMAL = 0x00000000
DS3DMODE_HEADRELATIVE = 0x00000001
DS3DMODE_DISABLE = 0x00000002

DS3D_IMMEDIATE = 0x00000000
DS3D_DEFERRED = 0x00000001

DS3D_MINDISTANCEFACTOR = -1000000.0 # XXX FLT_MIN
DS3D_MAXDISTANCEFACTOR = 1000000.0  # XXX FLT_MAX
DS3D_DEFAULTDISTANCEFACTOR = 1.0

DS3D_MINROLLOFFFACTOR = 0.0
DS3D_MAXROLLOFFFACTOR = 10.0
DS3D_DEFAULTROLLOFFFACTOR = 1.0

DS3D_MINDOPPLERFACTOR = 0.0
DS3D_MAXDOPPLERFACTOR = 10.0
DS3D_DEFAULTDOPPLERFACTOR = 1.0

DS3D_DEFAULTMINDISTANCE = 1.0
DS3D_DEFAULTMAXDISTANCE = 1000000000.0

DS3D_MINCONEANGLE = 0
DS3D_MAXCONEANGLE = 360
DS3D_DEFAULTCONEANGLE = 360

DS3D_DEFAULTCONEOUTSIDEVOLUME = DSBVOLUME_MAX

# Return codes
DS_OK = 0x00000000
DSERR_OUTOFMEMORY = 0x00000007
DSERR_NOINTERFACE = 0x000001AE
DS_NO_VIRTUALIZATION = 0x0878000A
DS_INCOMPLETE = 0x08780014
DSERR_UNSUPPORTED = 0x80004001
DSERR_GENERIC = 0x80004005
DSERR_ACCESSDENIED = 0x80070005
DSERR_INVALIDPARAM = 0x80070057
DSERR_ALLOCATED = 0x8878000A
DSERR_CONTROLUNAVAIL = 0x8878001E
DSERR_INVALIDCALL = 0x88780032
DSERR_PRIOLEVELNEEDED = 0x88780046
DSERR_BADFORMAT = 0x88780064
DSERR_NODRIVER = 0x88780078
DSERR_ALREADYINITIALIZED = 0x88780082
DSERR_BUFFERLOST = 0x88780096
DSERR_OTHERAPPHASPRIO = 0x887800A0
DSERR_UNINITALIZED = 0x887800AA
DSERR_BUFFERTOOSMALL = 0x887810B4
DSERR_DS8_REQUIRED = 0x887810BE
DSERR_SENDLOOP = 0x887810C8
DSERR_BADSENDBUFFERGUID = 0x887810D2
DSERR_FXUNAVAILABLE = 0x887810DC
DSERR_OBJECTNOTFOUND = 0x88781161


def test():
    import os
    for root, dirs, files in os.walk(os.path.join(os.path.dirname(__file__), 'res')):
        for filename in files:
            if filename.endswith('.wav'):
                with open(os.path.join(os.path.dirname(__file__), 'res', filename), 'rb') as f:
                    print(f)


if __name__ == '__main__':
    test()
