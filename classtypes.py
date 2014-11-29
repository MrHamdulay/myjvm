from collections import namedtuple

AnnotationDefaultAttribute = namedtuple('AnnotationDefaultAttribute', 'attribute_name attribute_name_length default_value')
BootstapMethodsAttribute = namedtuple('BootstapMethodsAttribute', 'bootstrap_methods')
CodeAttribute = namedtuple('CodeAttribute', 'max_stack max_locals code exceptions attributes')
ConstantValueAttribute = namedtuple('ConstantValueAttribute', 'value type')
EnclosingMethodAttribute = namedtuple('EnclosingMethodAttribute', 'classs method_index')
ExceptionsAttribute = namedtuple('ExceptionsAttribute', 'exception_indexes')
Field = namedtuple('Field', 'access_flags name descriptor attributes')
InnerClass = namedtuple('InnerClass', 'inner_class outer_class inner_name inner_class_access_flags')
InnerClassesAttribute = namedtuple('InnerClassesAttribute', 'inner_classes')
LineNumberTableAttribute = namedtuple('LineNumberTableAttribute', 'source_file')
Method = namedtuple('Method', 'access_flags name descriptor attributes parameters return_type')
MethodParametersAttribute = namedtuple('MethodParametersAttribute', 'paremeters')
RuntimeInvisibleAnnotations = namedtuple('RuntimeVisibleAnnotations', 'annotations')
RuntimeInvisibleParameterAnnotations = namedtuple('RuntimeInvisibleParameterAnnotations', 'parameters')
RuntimeInvisibleTypeAnnotations = namedtuple('RuntimeInvisibleTypeAnnotations', 'type_annotations')
RuntimeVisibleAnnotations = namedtuple('RuntimeVisibleAnnotations', 'annotations')
RuntimeVisibleParameterAnnotations = namedtuple('RuntimeVisibleParameterAnnotations', 'parameters')
RuntimeVisibleTypeAnnotations = namedtuple('RuntimeVisibleTypeAnnotations', 'type_annotations')
SignatureAttribute = namedtuple('SignatureAttribute', 'signature_index')
SourceFileAttribute = namedtuple('SourcefileAttribute', 'source_file')
StackMapTableAttribute = namedtuple('StackMapTableAttribute', 'stack_map_frames')
SyntheticAttribute = namedtuple('SyntheticAttribute', '')
TypeAnnotation = namedtuple('TypeAnnotation', 'target_type type_path type_index element_values')
