CHAR_MASK = (2**16)-1
CHAR_TEST = 2**16
def charmask(n):
    return n & CHAR_MASK

BYTE_MASK = (2**8)-1
BYTE_TEST = 2**7
def bytemask(n):
    n &= BYTE_MASK
    if n > BYTE_TEST:
        n-= BYTE_TEST
    return n
