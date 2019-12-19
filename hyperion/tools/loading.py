from hyperion.core import logman
import importlib

def get_class(string):
    logger = logman.getLogger(__name__)
    if '/' not in string:
        logger.error("The string is not properly formatted. Use '/' to separate module path from classname. String is: {}".format(string))
        return
    module_name, class_name = string.split('/')
    try:
        temp_class = getattr(importlib.import_module(module_name), class_name)
    except ModuleNotFoundError:
        logger.error("Module not found: {}".format(module_name))
    except AttributeError:
        logger.error("Class not found: {}".format(class_name))
    except:
        logger.error("Unexpected error")
    return temp_class
