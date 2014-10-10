NORMAL = 1
PARAMETERS = 2

class MalformedDescriptorException(Exception):
    pass

def parse_descriptor(string, mode=NORMAL):
    result = []
    index = 0
    while index < len(string):
        if string[index] == '(' and mode == NORMAL:
            result.append(parse_descriptor(string[index+1:string.find(')', index)], PARAMETERS))
            index = string.find(')', index)+1
        elif string[index] in 'BCDFIJSZV':
            result.append(string[index])
            index +=1
        elif string[index] == 'L':
            result.append(string[index+1:string.find(';', index+1)])
            index = string.find(';', index+1)+1

    if mode == NORMAL and len(result) not in (1, 2):
        raise MalformedDescriptorException()

    return result

if __name__ == '__main__':
    print parse_descriptor('(IDLjava/lang/Thread;)Ljava/lang/Object;')
