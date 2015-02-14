CHAR_MASK = (2**16)-1
CHAR_TEST = 2**16
def charmask(n):
    n &= CHAR_MASK
    return n

BYTE_MASK = (2**8)-1
BYTE_TEST = 2**7
def bytemask(n):
    n &= BYTE_MASK
    if n >= BYTE_TEST:
        n-= 2*BYTE_TEST
    return n

INT_MASK = (2**32)-1
INT_TEST = 2**31

def intmask(n):
    n &= INT_MASK
    if n >= INT_TEST:
        n-= 2*INT_TEST
    return int(n)
