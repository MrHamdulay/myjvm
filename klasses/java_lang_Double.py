from __future__ import absolute_import
import struct

def doubleToRawLongBits(klass, vm, method, frame):
    pack = struct.pack('>d', frame.get_local(0))
    return struct.unpack('>q', pack)[0]

def longBitsToDouble(klass, vm, method, frame):
    pack = struct.pack('>q', frame.get_local(0))
    return struct.unpack('>d', pack)[0]
