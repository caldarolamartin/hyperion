# -*- coding: utf-8 -*-
"""
=======================
Hyperion Core Utilities
=======================

---------------------------------
Explanation of how to use logging
---------------------------------

Short version:
There is a single logging manager that you import in your files. This logging manager can create a logger objects (which
you use in your files and classes to do log-prints like logger.info('bla'). When creating the logger object, a stream
handler (writes to screen) and a file handler are passed with it. These take care of the layout, the level (e.g. whether
lower levels like debug or info are printed), and which file to write to. You can choose to disable the stream or file
handler, modify their layout and levels individually. The stream handler colors can be turned on or off and the color
format can be modified.

Full explanation:

In hyperion.core the class LoggingManager is defined. It is a "Singleton" class meaning that all instantiations of this
class are actually one and the same object.
In hyperion.core one object is already instantiated by the name of logman.
In hyperion __init__.py this is imported under the alias name logging.
Because it's a singleton class the following approaches of importing the logging manager object are all equivalent:
- from hyperion import logging
- from hyperion.core import logman as logging
- from hyperion.core import logman
- from hyperion.core import LoggingManager
  import hyperion
  log = LoggingManager( hyperion.log_path, 'my_log_name.log' )
- import hyperion.core
  log = hyperion.core.LoggingManager()
In all cases above logging, logman and log refer to the same single object of class LoggingManager.
For the rest of the following explanation logman is used, but if you're modifying an existing file that used logging,
you could remove the 'import logging' and replace it with 'from hyperion import logging'.
Note, the optional arguments are default_path and default_name for logging file.
LoggingManager has two optional arguments default_path and default_name, which are used as default values for creating
the log file. By default, the path is hyperion.log_path and the name is 'hyperion.log'
In your own project you could change those if you like.

Now, to use logging in your module (file) or in your class, you have to create a logger:
logger = logman.getLogger(__name__)
Note that instead of the usual module name __name__ you could hypothetically put in any string.
Note that as a shorthand you can also do directly: logger=logman(__name__)
When the logger is created, by default, both the stream handler and the file handler are passed with it. These take care
of printing to the screen and to a file. If you don't want to add both, you could omit adding them by setting the
optional keyword arguments add_stream or add_file to False. e.g.; logger = logman.getLogger(__name__, add_file=False)

Before creating a logger object, you can:
- Change the default path or name of the logfile in the stream_handler:
  logman.default_path  = 'd:\\'
  logman.default_name  = 'my_project.log'
- Set the level of the default stream or file handler in the logging manager (defaults are DEBUG)
  logman.stream_level = logman.WARNING      # note: you could also pass in the string 'WARNING'
  logman.file_level = 'INFO'                # note: you could also pass in logman.INFO
  (Note that changing the level in the manager after a logger object is created is likely to also affect that logger.
  This depends if the handler was modified in the meantime. If it wasn't, then it's the same object.)
- Change the default stream or file handler in the logging manager
  Change layout, file name, colors. See below.
- Enable/disable whether the stream of the file handler is passed when a logger object is created (default is True).
  logman.enable_stream = False
  logman.enable_file = True
After creating a logger object you can still:
- Add handlers
  logman.remove_stream_handler(my_handler)
  logman.remove_file_handler(my_handler)
- Or remove handlers
  logman.add_stream_handler(my_handler)
  logman.add_file_handler(my_handler)
- And you can modify the logging level of its handers. Just be aware that if the handlers in the manager weren't
  modified in the meantime, changing the level of one logger may change the level of others as well.
  logman.set_logger_stream_level(my_handler, 'WARNING')
  logman.set_logger_file_level(my_handler, logman.INFO)

Finally, explanation of setting up the handlers:
To create (or replace) the handlers use:
logman.set_stream( optional arguments )
logman.set_file( optional arguments )
All arguments are optional (they have a default value if omitted)
The arguements in both set_stream and set_file are:
- level                 If omitted, the default value is used
                        (default value can be set by logman.stream_level / logman.file_level)
- reduce_duplicates     Enables a Filer that detect repeated log comments (that were in a loop) and reduces the number
                        of lines printed. Defaults to True
- compact               A float between 0 and 1. A measure of how long or compact a line will be. 0 Means full length.
                        As the value of compact is increased the lines will become shorter. At 1 the line will be most
                        compact and it will be cut off at length maxwidth.
                        Default value for set_stream is 0.5, default value for set_file is 0
- maxwidth              See description of compact. Default value is 119
Arguments only in set_stream:
- color                 A bool that determines whether to use colors when printing levels names. Defaults to True
- color_scheme          A string indicating color_scheme. Possible values are: bright, dim, mixed, bg, universal
                        If the logger is used in Spyder it diverts to a modified scheme. To manually select different
                        schemes for both non-Spyder and Spyder do something like color_scheme=('mixed', 'spy_bright')
                        Scheme 'universal' will be readable and most similar on Spyder, Pycharm, PyCharm-darcula,
                        regular black terminal and blue PowerShell terminal. But it's not ver esthetically pleasing, so
                        the default is ('bright', 'spy_bright')
- All other keyword arguments are passed into logging.StreamHandler().
Arguments only in set_file:
- pathname              The path or only filename or full file-path. If path is not included it will use the default
                        path. If name is not included it will use the default name)
- All other keyword arguments are passed into logging.handlers.RotatingFileHandler().
  maxBytes will default to 5MB and backupCount will default to 9



example code 1:

from hyperion import logging

class A:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info('object of class A created')

if __name__=='__main__':
    logging.enable_file = False
    logging.stream_level = 'INFO'
    logging.set_stream(compact=0.4, color=False)
    a = A()


example code 2:

from hyperion.core import logman

class A:
    def __init__(self):
        logger = logman(__name__, add_stream=False)     # no stream logging at all for this class
        logger.info('object of class A created')

class B:
    def __init__(self):
        self.logger = logman(__name__)
        self.logger.info('object B: 1 - info')

        # Temporarily change logging level (note that this may affect other loggers as well)
        lvl = logman.get_logger_stream_level(self.logger)
        logman.set_logger_stream_level(self.logger, 'WARNING')
        self.logger.info('object B: 2 - info')
        self.logger.warning('object B: 2 - warning')
        logman.set_logger_stream_level(self.logger, lvl)

        self.logger.info('object B: 3 - info')

class C:
    def __init__(self):
        self.logger = logman(__name__)
        self.logger.info('object C: 1 - info')

        # Temporarily remove handler from logger
        h = logman.remove_stream_handler(self.logger)       # storing it in h is optional
        self.logger.info('object C: 2 - info')
        self.logger.warning('object C: 2 - warning')
        # To restore the exact handler:
        self.logger.addHandler(h)
        # It's also possible to add the handler from the manager:
        # logman.add_file_handler(self.logger)

        self.logger.info('object C: 3 - info')


if __name__=='__main__':
    logging.default_name = 'my_project.log'
    logging.set_stream(compact=0.4, color=False)
    a = A()
    b = B()
    c = C()

"""





import os
import logging
import logging.handlers
from time import time
from datetime import datetime
from sys import modules

# lantz imports colorama, but colorama actually breaks color printing in Spyder
# Therfore, IF Spyder is detected all colorama inputs will be replaced wih this empty class.
# Subsequently lantz catches the erroneous colorama and circumvents it by printing without color.
if any('SPYDER' in name for name in os.environ):
    class DisableColoramaInSpyder:
        def init(*args, **kwargs):
            pass
        def deinit():
            pass
    modules['colorama'] = DisableColoramaInSpyder

import colorama

from hyperion import log_path

class Singleton(type):
    """
    Metaclass to use for classes of which you only want one instance to exist.
    use like: class MyClass(ParentClass, metaclass=Singleton):
    If one tries to create a second object, the original object is returned.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class ANSIcolorFormat:
    """
    Class used as a wrapper function to apply colors to console prints.
    Arguments are the string followed by one or more color 'decorators':
    First letter of basic colors: r, g, y, b, m, c, w for white, k for black.
    Letter Preceded by an l means a lighter/brighter color (if supported).
    Letter(s) preceded by an underscore '_' means background color.
    Notes on PyCharm: 'emph' creates bold text. Darcula mode changes colors
    into bland "pastel-like" colors  and inverts pure white and black.
    Notes on general command/prompt window: 'emph' turns dark text to bright.
    Notes on Spyder: Does not support "light" colors with an "l", 'emph'/'norm'
    turns both text and background simultaneously to bright/dim.

    The 'decorators' can be passed as multiple arguments or a tuple or a list.
    A single string of ansi color code is also accepted (e.g. '1;46;31')
    If no additional arguments or the argument None is passed it returns the
    message without adding ansi color codes.
    The enabled property allows for toggling all color action of this object at once.
    The class method disable_all() allows to disable all color printing of all objects.

    Note: It's also possible to do from hyperion.core import ansicol
          Then you're using the same object (i.e. toggling that object will influence all)

    Example usage:
        from hyperion.core import ANSIcolorFormat
        ansicol = ANSIcolorFormat()
        print(ansicol('Hello World','emph','r','_y'))
        print(ansicol('Hello World')
        ansicol.enabled = False
        print(ansicol('Hello World','emph','r','_y'))
    """
    col_dict = {
        'emph': '1',  # bold or bright
        'norm': '2',  # normal / dim
        # Regular command window:
        # (Tested on Win7 and Win10: CMD, Anaconda prompt, Anaconda PowerShell propmt and PowerShell (Win10))
        # Does not make text bold, only makes foreground (text color) bright.
        # Spyder:
        # Making bright acts on both foreground and background simultaneous.
        # Black text on bright background is still possible by not specifying text color.
        # Does not make text bold
        # PyCharm:
        # Actually makes text bold, does not affect brightness

        'k': '30',  # black
        'r': '31',  # red
        'g': '32',  # green
        'y': '33',  # yellow
        'b': '34',  # blue
        'm': '35',  # magenta
        'c': '36',  # cyan
        'w': '37',  # white (grey)
        '_k': '40',  # black background
        '_r': '41',  # red background
        '_g': '42',  # green background
        '_y': '43',  # yellow background
        '_b': '44',  # blue background
        '_m': '45',  # magenta background
        '_c': '46',  # cyan background
        '_w': '47',  # white (grey) background
        # PyCharm in Darcula mode changes colors into bland "pastel-like" colors,
        # and inverts pure white and black

        'lk': '90',  # "light black"
        'lr': '91',  # light red
        'lg': '92',  # light green
        'ly': '93',  # light yellow
        'lb': '94',  # light blue
        'lm': '95',  # light magenta
        'lc': '96',  # light cyan
        'lw': '97',  # bright white
        '_lk': '100',  # "light black" background
        '_lr': '101',  # light red background
        '_lg': '102',  # light green background
        '_ly': '103',  # light yellow background
        '_lb': '104',  # light blue background
        '_lm': '105',  # light magenta background
        '_lc': '106',  # light cyan background
        '_lw': '107'  # bright white background
        # These are not always supported (e.g. not supported in Spyder IPython)
    }

    # class attributes:
    __disable_all = False
    __colorama_enabled = None       # unknown
    __in_spyder = any('SPYDER' in name for name in os.environ)

    @staticmethod
    def disable_all(boolean):
        """
        Class Method (with boolean input) to disable all color printing of all ANSIcolorFormat objects at once.
        Useful if your system can't deal with ANSI color codes.
        Note that this will overrule the enabled state of individual objects.
        Being a class method this can be run both on an object and directly on the class, like
        ANSIcolorFormat.disable_all(False)
        """
        ANSIcolorFormat.__disable_all = boolean

    def __init__(self, enable=True):
        self.enabled = enable

    @property
    def enabled(self):
        """
        Boolean property to get or set whether this ANSIcolorFormat object is enabled.
        If enabled is false it will not print colors.
        Note that the class disabled_all state overrules this object state.
        To enable you may also have to do .disable_all(False) on the object or on the class.

        """
        return self._enabled and not ANSIcolorFormat.__disable_all

    @enabled.setter
    def enabled(self, boolean):
        if boolean:
            if ANSIcolorFormat.__disable_all:
                print('WARNING: also enable all by .disable_all(False)' )
            if ANSIcolorFormat.__in_spyder and ANSIcolorFormat.__colorama_enabled is not False:
                colorama.deinit()
                ANSIcolorFormat.__colorama_enabled = False
            if not ANSIcolorFormat.__in_spyder and ANSIcolorFormat.__colorama_enabled is not True:
                colorama.init()
                ANSIcolorFormat.__colorama_enabled = True
        self._enabled = boolean

    def __call__(self, msg, *args):
        if not self.enabled or len(args) == 0 or args[0] is None:
            return msg
        try:
            if len(args) == 1:
                if type(args[0]) is str and args[0][0].isdigit():
                    return '\033[' + args[0] + 'm' + msg + '\033[0m'
                elif type(args[0]) is tuple or type(args[0]) is list:
                    args = args[0]
            if ANSIcolorFormat.__in_spyder and any('l' in c for c in args):
                print('WARNING: the "light" colors are not supported in Spyder')
            return '\033[' + ';'.join([self.col_dict[c] for c in args]) + 'm' + msg + '\033[0m'
        except KeyError:
            print('ERROR: incorrect color code')
            return msg

# Setting up logging =================================================

class DuplicateFilter(logging.Filter):
    """ Adding this filter to a logging handler will reduce repeated log-prints"""
    def filter(self, record):
        # Note to self. It appears the message from one handler is passed to the next one.
        # This means that if one handler modifies the message, the next one gets the modified version.
        self.repeat_message = ' > Logger message is being repeated...'
        # First strip the repeat_message from the message if it is there:
        replen = len(self.repeat_message)
        if len(record.msg) > replen and record.msg[-replen:] == self.repeat_message:
            record.msg = record.msg[:-replen]
        # Combine filename, linenumber and (corrected) message to create a record to compare
        current_record = (record.module, record.lineno, record.msg)
        # Compare it to the last record stored (if that variable exists)
        if current_record != getattr(self, "last_record", None):
            self.last_record = current_record  # store the current record in last_record, to be able to compare it on the next call
            self.last_unique_time = time()  # store the time of this message
            self.repeating = False  # set repeating flag to False
            return True  # Allow this record to be printed
        else:
            if not self.repeating:
                self.repeating = True  # set repeating flag True
            elif time() > self.last_unique_time + 20:  # if repeting==True AND 20 seconds have passed reset "timer"
                self.last_unique_time = time()  # reset the last_unique_time to in order repeat occasionally
            else:
                return False  # prevent message from being printed during those 20 seconds
            record.msg += self.repeat_message  # append repeat message
            return True  # allow the message to be printed

class CustomFormatter(logging.Formatter):
    """
    Custom format for log-prints.
    Adds a lot of information (time, module, line number, method, LEVEL, message)
    Setting the compact parameter to a value larger than 0 shrinks the date, module and method.
    Setting it to 1 (maximum) assures the length is maxwidth characters or less.
    The possible regular color schemes are: bright, dim, mixed, bg, universal. The optional additional secondary color
    schemes for Spyder are: spy_bright, spy_dim, spy_mixed, spy_bg, spy_universal.
    Specifying no color_scheme defaults to bright (and spy_bright if Spyder is detected).

    :param compact: float from 0 for full length, to 1 for very compact (defaults to 0)
    :param maxwidth: integer indicating max line width when compact is 1. None (default) uses 119.
    :param color: boolean indicating if ANSI colors should be used (defaults to False)
    :param color_scheme: string or tuple/list of two strings (defaults to bright / spy_bri)
    """

    # 'universal' and 'spy_uni' are chosen to be similar and readable in:
    # - regular black command window / terminal
    # - Spyder
    # - PyCharm default
    # - PyCharm darcula
    # - PowerShell (dark blue)
    # But they're ugly, so I'm using

    # Note: '105;97' is equivalent to ('_m','lw')
    color_schemes = {
        'universal': {logging.CRITICAL: ('_m', 'lw'),
                      logging.ERROR: ('_lr', 'ly'),
                      logging.WARNING: ('_ly', 'r'),
                      logging.INFO: ('_lc', 'k'),
                      logging.DEBUG: ('_lb', 'lw'),
                      None: None},  # do nothing (for unknown codes)
        'spy_universal': {logging.CRITICAL: '1;45;37',  # emph, magenta bg, white text
                         logging.ERROR: '1;41;33',  # emph, red bg, yellow text
                         logging.WARNING: '1;43;31',  # emph, yellow bg, red text
                         logging.INFO: '1;46',  # emph, cyan bg, keep text default black
                         logging.DEBUG: '1;44;37',  # emph, blue bg, white text
                         None: None},  # do nothing (for unknown codes)
        'bright': {logging.CRITICAL: 'lm',  # magenta text
                   logging.ERROR: 'lr',  # redtext
                   logging.WARNING: 'ly',  # yellowtext
                   logging.INFO: 'lg',
                   logging.DEBUG: 'lc',
                   None: None},  # do nothing (for unknown codes)
        'dim': {logging.CRITICAL: '35',  # magenta text
                logging.ERROR: '31',  # redtext
                logging.WARNING: '33',  # yellowtext
                logging.INFO: '32',
                logging.DEBUG: '36',
                None: None},  # do nothing (for unknown codes)
        'bg':  {logging.CRITICAL: ('_lm','lw'),
                logging.ERROR: ('_lr','lw'),
                logging.WARNING: ('_ly','k'),
                logging.INFO: ('_lg','k'),
                logging.DEBUG: ('_lc','k'),
                None: None},  # do nothing (for unknown codes)
        'mixed': {logging.CRITICAL: '95',  # magenta text
                  logging.ERROR: '91',  # redtext
                  logging.WARNING: '33',  # yellowtext
                  logging.INFO: '36',
                  logging.DEBUG: '32',
                  None: None},  # do nothing (for unknown codes)
        'spy_bright': {logging.CRITICAL: '1;35',  # magenta text
                       logging.ERROR: '1;31',  # redtext
                       logging.WARNING: '1;33',  # yellowtext
                       logging.INFO: '1;32',
                       logging.DEBUG: '1;36',
                       None: None},  # do nothing (for unknown codes)
        'spy_dim': {logging.CRITICAL: '35',  # magenta text
                    logging.ERROR: '31',  # redtext
                    logging.WARNING: '33',  # yellowtext
                    logging.INFO: '32',
                    logging.DEBUG: '36',
                    None: None},  # do nothing (for unknown codes)
        'spy_mixed': {logging.CRITICAL: '31;5',  # magenta text
                      logging.ERROR: '1;31',  # redtext
                      logging.WARNING: '33',  # yellowtext
                      logging.INFO: '32',
                      logging.DEBUG: '36',
                      None: None},  # do nothing (for unknown codes)
        'spy_bg': {logging.CRITICAL: '1;45',
                   logging.ERROR: '1;41',
                   logging.WARNING: '1;43',
                   logging.INFO: '1;42',
                   logging.DEBUG: '1;46',
                   None: None},  # do nothing (for unknown codes)
    }

    def __init__(self, compact=0.0, maxwidth=None, color=False, color_scheme=None):
        __default_scheme =        'bright'      # choose default mode here
        __default_scheme_spyder = 'spy_bright'  # choose default mode here
        __spyder = any('SPYDER' in name for name in os.environ)

        if color_scheme is None:
            self.color_scheme = __default_scheme_spyder if __spyder else __default_scheme
        else:
            try:
                # in case of tuple/list of length 1, extract that element:
                if type(color_scheme) is not str and len(color_scheme)==1:
                    color_scheme = color_scheme[0]
                if type(color_scheme) is str:
                    if __spyder:
                        if color_scheme[:4] != 'spy_': color_scheme = 'spy_'+color_scheme
                    else:
                        if color_scheme[:4] == 'spy_': color_scheme = color_scheme[4:]
                    self.color_scheme = color_scheme
                else:
                    if __spyder:
                        self.color_scheme = [sch for sch in color_scheme if sch[:3]=='spy_'][0]
                    else:
                        self.color_scheme = [sch for sch in color_scheme if sch[:3] != 'spy_'][0]
            except:
                print('WARNING: invalid color_scheme(s). (using defaults instead)')
                self.color_scheme = __default_scheme_spyder if __spyder else __default_scheme

        if compact > 1:
            self.compact = 1
        if compact < 0:
            self.compact = 0
        else:
            self.compact = compact
        self.color = color
        self.short_names = {10: 'DEBUG', 20: 'INFO', 30: 'WARN', 40: 'ERROR', 50: 'CRIT'}
        self.ansicol = ANSIcolorFormat()
        if maxwidth is None: maxwidth = 119                     # default value goes here
        self.maxwidth = int(maxwidth if maxwidth>56 else 56)    # shorter then 53 might cause errors
        super(CustomFormatter, self).__init__()

    def format(self, record):
        module = record.name
        func = record.funcName
        if self.compact<=0.5:
            lvl_str = '{:>8} '.format(record.levelname)
        else:
            lvl_str = '{:>5}'.format(self.short_names[record.levelno])
        if self.color:
            if record.levelno not in self.color_schemes[self.color_scheme]:
                lvl_str = self.ansicol(lvl_str, self.color_schemes[self.color_scheme][None])
            else:
                lvl_str = self.ansicol(lvl_str, self.color_schemes[self.color_scheme][record.levelno])
        if self.compact == 0:            # The full length version
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # show 3 out of 6 digits (i.e. milliseconds)
            message = '{} |{:>50} |{:>5} | {:32}|{}| {}'.format(timestamp, module, record.lineno, func + '()', lvl_str, record.msg)
        else:
            timestamp = datetime.now().strftime('%H:%M:%S')
            # module = '.'.join(module.split('.')[1:])  # strip off the first word before '.'(i.e. hyperion)
            lmod = int(50 - 33 * self.compact)  # >=14
            lfun = int(32 - 20 * self.compact)  # >=12
            if len(module) > lmod:
                module = '...' + module[-(lmod - 3):]  # truncate from the left
            if len(func) > lfun:
                func = func[:(lfun - 3)] + '...'

            if self.compact <= 0.5:
                message = '{} |{:>{mod_w}} |{:>5} | {:{fun_w}}|{}| {}'.format(timestamp, module, record.lineno,func + '()',
                                                                              lvl_str, record.msg, mod_w=lmod, fun_w=lfun+2)
            else:
                if record.lineno > 9999:
                    linenr = '>10k'
                else:
                    linenr = record.lineno
                tmpmsg = record.msg.replace('\n',' ')

                if self.compact==1 and len(tmpmsg) > (self.maxwidth-53):
                    msg = tmpmsg[:(self.maxwidth-56)]+'...'
                else:
                    msg = record.msg
                message = '{} {:>{mod_w}} {:>4} {:{fun_w}} {} {}'.format(timestamp, module, linenr, func + '()',
                                                                          lvl_str, msg, mod_w=lmod, fun_w=lfun+2)

        return message

class LoggingManager(metaclass=Singleton):
    """
    LogginManager class. This is a "Singleton" class which means that all of its instantiatons refer to one and the same
    object. If one tries to create a second object, the original object is returned.
    For a more elaborate explanation on how to use, see beginning of page.

    :ivar enable_stream: (bool) If true, the stream handler is passed to newly created logger objects (default is True)
    :ivar enable_file:   (bool) If true, the file handler is passed to newly created logger objects (default is True)
    :ivar default_path:  (str) Default path for logfile when file handler is created without specifying path (default hyperion.log_path)
    :ivar default_name:  (str) Default filename for logfile when file handler is created without specifying filename (default 'hyperion.log;)
    """
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    WARN = logging.WARN
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    _level_2_number = {'CRITICAL': CRITICAL, 'ERROR': ERROR, 'WARNING': WARNING, 'WARN': WARN, 'INFO': INFO,
                       'DEBUG': DEBUG}
    _number_2_level = {CRITICAL: 'CRITICAL', ERROR: 'ERROR', WARNING: 'WARNING', INFO: 'INFO', DEBUG: 'DEBUG'}

    def __init__(self, default_path=log_path, default_name='hyperion.log'):
        self.default_path = default_path
        self.default_name = default_name
        self._default_stream_level = logging.DEBUG
        self._default_file_level = logging.DEBUG
        self.set_stream()
        self.file_handler = None    # don't create it until it's necessary
        self.enable_stream = True   # add streamhandler to new logger objects, default value
        self.enable_file = True     # add filehandler to new logger objects, default value

    def set_stream(self, color=True, level = None, compact=0.5, reduce_duplicates=True, maxwidth=None, color_scheme=None, **kwargs):
        """
        Sets (replaces) the stream handler in the logging manager object.

        :param color: (bool) whether to print levelnames with color
        :param level: logging level. If omitted, default is used. To change default see file_level
        :param compact: see CustomFormatter (defaults to 0)
        :param maxwidth: see CustomFormatter
        :param reduce_duplicates: (bool) (defaults to True)
        :param color_scheme: (str or (str,str) ) color scheme to use, see above for possible values
        :param **kwargs: additional keyword arguments are passed into logging.StreamHandler()
        :return:
        """
        self.enable_stream = True
        self.stream_handler = logging.StreamHandler(**kwargs)
        self.stream_handler.setFormatter(CustomFormatter(compact=compact, color=color, color_scheme=color_scheme, maxwidth=maxwidth))
        if level is None: level = self._default_stream_level
        self.stream_handler.setLevel(level)  # default level for stream handler
        if reduce_duplicates:
            self.stream_handler.addFilter(DuplicateFilter())

    def set_file(self, pathname=None, level = None, compact=0, reduce_duplicates=True, maxwidth=None, maxBytes=(5 * 1024 * 1024), backupCount=9, **kwargs):
        """
        Sets (replaces) the file handler in the logging manager object.

        :param pathname: path or filename or full file-path (if only name of path is given, the other will use the default value)
        :param level: logging level. If omitted, default is used. To change default see file_level
        :param compact: see CustomFormatter (defaults to 0)
        :param maxwidth: see CustomFormatter
        :param reduce_duplicates: (bool) (defaults to True)
        :param maxBytes: see logging.handlers.RotatingFileHandler() (defaults to 5 * 1024 * 1024)
        :param backupCount: see logging.handlers.RotatingFileHandler() (defaults to 9)
        :param **kwargs: additional keyword arguments are passed into logging.handlers.RotatingFileHandler()
        """
        self.enable_file = True
        if pathname is None or os.path.dirname(pathname)=='':
            log_path = self.default_path
        else:
            log_path = os.path.dirname(pathname)
        if pathname is None or os.path.basename(pathname)=='':
            log_name = self.default_name
        else:
            log_name = os.path.basename(pathname)
        # make the directory if it doesn't exist yet:
        if not os.path.isdir(log_path):
            os.makedirs(log_path)
        self.file_handler = logging.handlers.RotatingFileHandler(filename=os.path.join(log_path,log_name), maxBytes=maxBytes,
                                                                 backupCount=backupCount, **kwargs)
        self.file_handler.setFormatter(CustomFormatter(compact=compact, maxwidth=maxwidth))
        if level is None: level = self._default_file_level
        self.file_handler.setLevel(level)
        if reduce_duplicates:
            self.file_handler.addFilter(DuplicateFilter())

    @property
    def stream_level(self):
        """
        Property to read and set the level of the current stream handler.
        When setting it also updates the default level.
        """
        return self._number_2_level[self._default_stream_level]

    @stream_level.setter
    def stream_level(self, number_or_string):
        self._default_stream_level = number_or_string
        self.stream_handler.setLevel(number_or_string)

    @property
    def file_level(self):
        """
        Property to read and set the level of the current file handler.
        When setting it also updates the default level.
        """
        return self._number_2_level[self._default_file_level]

    @file_level.setter
    def file_level(self, number_or_string):
        self._default_file_level = number_or_string
        if self.file_handler is not None:
            self.file_handler.setLevel(number_or_string)

    def getLogger(self, name, add_stream=None, add_file=None):
        """
        Returns logger object.

        :param name: (str) Name, usually the module name. i.e. __name__
        :param add_stream: (bool or None) add the streamhandler. None (default) uses object.enalbe_stream
        :param add_file: (bool or None) add the streamhandler. None (default) uses object.enalbe_stream
        :return: logger object
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)      # this is necessary for some reason
        logger.handlers = []                # to avoid duplicate handlers, remove all existing
        if add_stream or (add_stream is None and self.enable_stream):
            self.stream_level = self._default_stream_level      # assert the level in case it was changed externally
            logger.addHandler(self.stream_handler)
        if add_file or (add_file is None and self.enable_file):
            if self.file_handler is None:
                self.set_file()
            self.file_level = self._default_file_level          # assert the level in case it was changed externally
            logger.addHandler(self.file_handler)
        return logger

    def __call__(self,*args, **kwargs):
        """ A shorthand for getLogger():
        If logman is the LoggingManager object, logman(__name__) is equivalent to logman.getLogger(__name__)"""
        return self.getLogger(*args, **kwargs)

    def remove_stream_handler(self, logger):
        """
        Remove stream_handlers from an existing logger object.

        :param logger: a logger object
        :return: the removed stream handler object (or None)
        """
        r = None
        for i, h in enumerate(logger.handlers):
            if type(h) is logging.StreamHandler:
                r = h
                del logger.handlers[i]
        return h

    def remove_file_handlers(self, logger):
        """
        Remove stream_handlers from an existing logger object.

        :param logger: a logger object
        :return: the removed file handler object (or None)
        """
        r = None
        for i, h in enumerate(logger.handlers):
            if type(h) is logging.handlers.RotatingFileHandler:
                r = h
                del logger.handlers[i]
        return h

    def add_stream_handler(self, logger):
        """
        Add stream_handler to an existing logger object.

        :param logger: a logger object
        """
        logger.addHandler(self.stream_handler)

    def add_file_handler(self, logger):
        """
        Add file_handler to an existing logger object.

        :param logger: a logger object
        """
        logger.addHandler(self.file_handler)

    def set_logger_stream_level(self, logger, level):
        """
        Change level of the stream handler of an existing logger object.
        Note that this may affect other logger object, because they may share the same stream handler object.

        :param logger: existing logger object
        :param level: string like 'WARNING' or level like logman.WARNING
        """
        for h in logger.handlers:
            if type(h) is logging.StreamHandler:
                h.setLevel(level)

    def get_logger_stream_level(self, logger):
        """
        Get the level of the (first) stream handler of an existing logger object.

        :param logger: existing logger object
        """
        for h in logger.handlers:
            if type(h) is logging.StreamHandler:
                return h.level
        return None

    def set_logger_file_level(self, logger, level):
        """
        Change level of the file handler of an existing logger object.
        Note that this may affect other logger object, because they may share the same file handler object.

        :param logger: existing logger object
        :param level: string like 'WARNING' or level like logman.WARNING
        """
        for h in logger.handlers:
            if type(h) is logging.handlers.RotatingFileHandler:
                h.setLevel(level)

    def get_logger_file_level(self, logger):
        """
        Get the level of the (first) file handler of an existing logger object.

        :param logger: existing logger object
        """
        for h in logger.handlers:
            if type(h) is logging.handlers.RotatingFileHandler:
                return h.level
        return None

# Initialize LoggingManager object. Import this in other modules inside this package.
logman = LoggingManager(default_path=log_path, default_name='hyperion.log')