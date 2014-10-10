import ply.yacc as yacc
import ply.lex as lex

class DescriptorTokenizer(object):
    literals = '[VBCDFIJSZ();{}'
    tokens = ['klassname']
    t_klassname = r'(<(cl)?init>|[a-zA-Z]+(/[a-zA-Z]+)*)'

class DescriptorParser(object):
    tokens = ['klassname']

    def p_fielddescriptor(self, p):
        'fielddescriptor: fieldtype'
        p[0] = p[1]

    def p_fieldtype(self, p):
        'fieldtype : basetype | objecttype | arraytype'
        p[0] = p[1]

    def p_basetype(self, p):
        '''basetype : 'B' | 'C' | 'D' | 'F' | 'I' | 'J' | 'S' | 'Z' '''
        p[0] = p[1]

    def p_objecttype(self, p):
        ''' objecttype : 'L' klassname ';' '''
        p[0] = p[2]

    def p_arraytype(self, p):
        ''' arraytype: '[' componenttype '''
        p[0] = p[2]

    def p_componenttype(self, p):
        ''' componenttype: fieldtype '''
        p[0] = p[1]

    def p_methoddescriptor(self, p):
        ''' methoddescriptor : '(' parameterlist ')' returndescriptor '''
        p[0] = p[2], p[4]

    def p_parameterlist(self, p):
        ' parameterlist : fieldtype parameterlist | fieldtype '
        p[0] = [p[1]] + ([] if len(p) == 2 else p[2])

    def p_returndescriptor(self, p):
        ''' returndescriptor : 'V' | fieldtype '''
        p[0] = p[1]

lexer = lex.lex(module=DescriptorTokenizer())
parser = yacc.yacc(module=DescriptorParser())

def parse_descriptor(string):
    return parser.parse(string, lexer=lexer, debug=0)
