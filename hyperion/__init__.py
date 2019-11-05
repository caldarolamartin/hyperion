import os
import logging
from time import time
import datetime
from lantz.core import UnitRegistry, Q_
__version__ = 0.2

# units
ur = UnitRegistry()
# logger format

# new
package_path = os.path.dirname(__file__)            #   ###/###/hyperion/hyperion/
repository_path = os.path.dirname(package_path)     #   ###/###/hyperion/
parent_path = os.path.dirname(repository_path)      #   ###/###/

# keep root_dir for backward compatability
root_dir = os.path.dirname(__file__)

ls = os.pardir

# Setting up logging =================================================

# Create a filter to prevent continuous repeated duplicate messages
class DuplicateFilter(logging.Filter):
    """Adding this filter to a logging handler wll reduce repeated """
    def filter(self, record):
        # Note to self. It appears the message from one handler is passed to the next one.
        # This means that if one handler modifies the message, the next one gets the modified version.
        self.repeat_message = ' > REPEATING...'
        # First strip the repeat_message from the message if it is there:
        replen = len(self.repeat_message)
        if len(record.msg) > replen and record.msg[-replen:] == self.repeat_message:
            record.msg = record.msg[:-replen]
        # Combine filename, linenumber and (corrected) message to create a record to compare
        current_record = (record.module, record.lineno, record.msg)
        # Compare it to the last record stored (if that variable exists)
        if current_record != getattr(self, "last_record", None):
            self.last_record = current_record       # store the current record in last_record, to be able to compare it on the next call
            self.last_unique_time = time()          # store the time of this message
            self.repeating = False                  # set repeating flag to False
            return True                             # Allow this record to be printed
        else:
            if not self.repeating:
                self.repeating = True               # set repeating flag True
            elif time() > self.last_unique_time + 20:   # if repeting==True AND 20 seconds have passed reset "timer"
                self.last_unique_time = time()      # reset the last_unique_time to in order repeat occasionally
            else:
                return False                        # prevent message from being printed during those 20 seconds
            record.msg += self.repeat_message       # append repeat message
            return True                             # allow the message to be printed

class CustomFormatter(logging.Formatter):
    # length = ['compact', 'medium', 'full']
    def __init__(self, compact=False):
        self.compact = compact
        super(CustomFormatter, self).__init__()

    def format(self, record):
        module = record.name
        func = record.funcName
        if self.compact:
            timestamp = datetime.datetime.now().strftime('%H:%M:%S')
            # module = '.'.join(module.split('.')[1:])  # strip off the first word before '.'(i.e. hyperion)
            if len(module)>38:
                module = '...'+module[-35:]        # truncate from the left to 38 characters
                msg = '{:.30}'.format(record.msg)           # truncate to 30 characters
            if len(func)>20:
                func = func[:17]+'...'
            message = '{} |{:>38} | {:22}|{:>8} | {}'.format(timestamp, module, func+'()', record.levelname, record.msg)
        else:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]   # show 3 out of 6 digits (i.e. milliseconds)
            # module = module[-min(len(module), 50):]       # truncate from the left to 50 characters
            # msg = '{:.200}'.format(record.msg)            # truncate to 200 characters
            # if len(func)>30:
            #     func = func[:27]+'...'
            message = '{} |{:>50} | {:32}|{:>8} | {}'.format(timestamp, module, func+'()', record.levelname, record.msg)
        return message

# format for logging
# _logger_format_long  = '%(asctime)s |%(levelname)+7s |%(funcName)+25s() | %(name)-45s | %(message)s'
# _logger_format_short = '%(asctime)s |%(levelname)+7s |%(funcName)+20s() | %(module)-20s | %(message)s'

_logger_format_long  = '%(asctime)s |%(name)+50s | %(funcName)+30s() |%(levelname)+7s | %(message)s'
_logger_format_short = '%(asctime)s |%(module)+22s | %(funcName)+22s()|%(levelname)+7s | %(message).40s'
# _logger_format_short = '%(asctime)s.%(msecs).3d |%(module)+22s | %(funcName)+22s()|%(levelname)+7s | %(message).40s'
# note: by adding ,'%H:%M:%S' to the Formatter (asctime) will turn into HH:MM:SS

# keep these two lines for backward compatability
_logger_format = _logger_format_long
_logger_settings = {'filename':'logger.log', 'maxBytes':(1048576 * 5), 'backupCount':9}

# create handler for stream logging:
stream_logger = logging.StreamHandler()
# stream_logger.setFormatter(logging.Formatter(_logger_format_short, '%H:%M:%S')) # adding the ,'%H:%M:%S' changes the timestamp to the short version
stream_logger.setFormatter(CustomFormatter(compact=True))
stream_logger.setLevel(logging.DEBUG)    # default level for stream handler
stream_logger.addFilter(DuplicateFilter())

# Function for changing the logger file:
# (apparently you have to remove, re-create and add the handler )
def set_logfile(file_basename='hyperion', folder = parent_path):
    """

    :param file_basename: The name of the logfile. (Note that the extension will be replaced with .log)
    :param folder: The folder to store the logfile (defaults to the parent_path of hyperion repository)
    """
    global file_logger
    # first store the level and formatter
    level = file_logger.level
    formatter = file_logger.formatter

    userfolder = os.path.dirname(file_basename)
    if os.path.isdir(userfolder):
        folder = userfolder
    filepathname = os.path.join(folder, os.path.splitext(file_basename)[0]+'.log' )
    # overwrite the file_logger (this is needed)
    file_logger = logging.handlers.RotatingFileHandler(filename=filepathname, maxBytes=(1048576 * 5), backupCount=9)
    file_logger.setFormatter(formatter)
    file_logger.setLevel(level)  # default level for file handler
    file_logger.addFilter(DuplicateFilter())

    # remove the file handler from the root/base and then add it again:
    logger = logging.getLogger()
    logger.removeHandler(file_logger)
    logger.addHandler(file_logger)

# create handler for file logging:
file_logger = logging.handlers.RotatingFileHandler(filename = 'hyperion.log', maxBytes =(1048576 * 5), backupCount = 9)

# file_logger.setFormatter(logging.Formatter(_logger_format_long))
file_logger.setFormatter(CustomFormatter())
file_logger.setLevel(logging.DEBUG)        # default level for file handler
file_logger.addFilter(DuplicateFilter())
set_logfile('hyperion')     # set to the default path

# set these handlers as default
# (note that the base level needs to be set to lowest level i.e. logging.DEBUG)
logging.basicConfig(level=logging.DEBUG, handlers=[file_logger, stream_logger])


# At the beginning of a file use: import hyperion
# Also import logging (or otherwise type hyperion.logging.X everywhere you would type logging.X)
# After that use this anywhere: self.logger = logging.getLogger(__name__)
# To change the logging file use this anywhere:
# hyperion.set_logfile('my_new_file_path_and_name.log')
# hyperion.set_logfile('__file__')
# To modify the levels use this anywhere :
# hyperion.file_logger.setLevel( logging.INFO )
# hyperion.stream_logger.setLevel( logging.WARNING )


