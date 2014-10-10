MAGIC = [0xCA, 0xFE, 0xBA, 0xBE]

CONSTANT_Utf8 = 1
CONSTANT_Integer = 3
CONSTANT_Float = 4
CONSTANT_Long = 5
CONSTANT_Double =6
CONSTANT_Class = 7
CONSTANT_String = 8
CONSTANT_Fieldref = 9
CONSTANT_Methodref = 10
CONSTANT_InterfaceMethodref = 11
CONSTANT_NameAndType = 12
CONSTANT_MethodHandle = 15
CONSTANT_MethodType = 16
CONSTANT_InvokeDynamic = 18

CONSTANT_POOL_NAMES = [
#1
'Utf8',
#2
'',
#3
'Integer',
#4
'Float',
#5
'Long',
#6
'Double',
#7
'Class',
#8
'String',
#9
'Fieldref',
#10
'Methodref',
#11
'InterfaceMethodref',
#12
'NameAndType',
#13
'MethodHandle',
#14
'MethodType',
#15
'InvokeDynamic']


ACC_PUBLIC    = 0x0001
ACC_PRIVATE   = 0x0002
ACC_PROTECTED = 0x0004
ACC_STATIC    = 0x0008
ACC_FINAL     = 0x0010
ACC_VOLATILE  = 0x0040
ACC_TRANSIENT = 0x0080
ACC_SYNTHETIC = 0x1000
ACC_ENUM      = 0x4000

ITEM_Top = 0
ITEM_Integer = 1
ITEM_Float = 2
ITEM_Double = 3
ITEM_Long = 4
ITEM_Null = 5
ITEM_UnitialisedThis = 6
ITEM_Object = 7
ITEM_Unitialised = 8

ITEMS = ['Top', 'Integer', 'Float', 'Double', 'Long', 'Null', 'UnitialisedThis', 'Object', 'Unitialised']
