from __future__ import absolute_import
import struct

def floatToRawIntBits(klass, vm, method, frame):
    float_value = frame.get_local(0)
    print 'float', float_value
    assert isinstance(float_value, float)

    int_bits = struct.unpack('>l', struct.pack('>f', float_value))[0]
    return int_bits
