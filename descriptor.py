NORMAL = 1
PARAMETERS = 2
ARRAY = 3

class MalformedDescriptorException(Exception):
    pass

def _parse_descriptor(string, mode=NORMAL):
    result = []
    index = 0
    while index < len(string):
        if string[index] == '(' and mode == NORMAL:
            result.append(_parse_descriptor(string[index+1:string.find(')', index)], PARAMETERS)[0])
            index = string.find(')', index)+1
        elif string[index] in 'BCDFIJSZV':
            result.append(string[index])
            index +=1
        elif string[index] == 'L':
            result.append(string[index+1:string.find(';', index+1)])
            index = string.find(';', index+1)+1
        elif string[index] == '[':
            array_type, offset = _parse_descriptor(string[index+1:], ARRAY)
            assert len(array_type) == 1
            result.append('['+array_type[0])
            index += offset+1
        else:
            raise MalformedDescriptorException('Unknown character %s' % string[index])
        if mode == ARRAY:
            break

    if mode == NORMAL and len(result) not in (1, 2):
        raise MalformedDescriptorException()

    return result, index

def parse_descriptor(string, mode=NORMAL):
    return _parse_descriptor(string, mode)[0]

def descriptor_is_array(descriptor):
    return descriptor[0] == '['

if __name__ == '__main__':
    #print parse_descriptor('(I[D[[[BLjava/lang/Thread;)Ljava/lang/Object;')
    print parse_descriptor('(Ljava/lang/String$1;)V')
    print parse_descriptor('[Ljava/lang/String;')[0]
