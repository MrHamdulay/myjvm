import java_lang_System
import java_lang_Object
import java_lang_Class
import java_lang_Float

class Box:
    def __init__(self, value):
        self.value = value

classes_with_natives = {
        'java/lang/Object': java_lang_Object,
        'java/lang/Class': java_lang_Class,
        'java/lang/System': java_lang_System,
        'java/lang/Float': java_lang_Float,
}

builtin_classes = {
    'float': Box,
    'Integer': Box,
    'Double': Box,
}
