import java_lang_System
import java_lang_Object
import java_lang_Class
import java_lang_Float
import java_lang_Throwable
import java_lang_Double
import java_lang_Thread
import java_security_AccessController
import sun_misc_VM
import sun_misc_Unsafe
import sun_reflect_Reflection

classes_with_natives = {
        'java/lang/Object': java_lang_Object,
        'java/lang/Class': java_lang_Class,
        'java/lang/System': java_lang_System,
        'java/lang/Float': java_lang_Float,
        'java/lang/Throwable': java_lang_Throwable,
        'java/lang/Double': java_lang_Double,
        'java/lang/Thread': java_lang_Thread,
        'java/security/AccessController': java_security_AccessController,
        'sun/misc/VM': sun_misc_VM,
        'sun/misc/Unsafe': sun_misc_Unsafe,
        'sun/reflect/Reflection': sun_reflect_Reflection,
}

primitive_classes = {}
