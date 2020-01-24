from hyperion.core import logman
import importlib

def get_class(string):
    """
    Returns class by interpreting input string as module path and class name.
    Module path should be separated by dots as usual. Separate class name from module by '/'.
    Example: my_class = get_class('hyperion.controller.example_controller/ExampleController')

    :param string: string containing module path and class name separated by '/'
    :return: class
    """
    logger = logman.getLogger(__name__)
    if '/' not in string:
        logger.error("The string is not properly formatted. Use '/' to separate module path from classname. String is: {}".format(string))
        return
    module_name, class_name = string.split('/')
    try:
        logger.debug('Retrieving class {} from module {}'.format(class_name, module_name))
        temp_class = getattr(importlib.import_module(module_name), class_name)
    except ModuleNotFoundError:
        logger.error("Module not found: {}".format(module_name))
        raise
    except AttributeError:
        logger.error("Class not found: {}".format(class_name))
        raise
    except:
        logger.error("Unexpected error while loading {}".format(string))
        raise

    return temp_class
