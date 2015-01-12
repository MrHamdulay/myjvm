import struct

def doubleToRawLongBits(klass, vm, method, frame):
    pack = struct.pack('>d', frame.get_local(0))
    return struct.unpack('>q', pack)[0]
