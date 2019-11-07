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
log_path = os.path.join(parent_path, 'logs')        #   ###/###/logs/

# make log dir if it doesn't exist:
if not os.path.isdir(log_path):
    os.makedirs(log_path)

# keep root_dir for backward compatability
root_dir = os.path.dirname(__file__)

ls = os.pardir

# Setting up logging =================================================

# Create a filter to prevent continuous repeated duplicate messages
class DuplicateFilter(logging.Filter):
    """Adding this filter to a logging handler will reduce repeated """
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
_logger_settings = {'filename':'logger.log', 'maxBytes':(1048576 * 5), 'backupCount':7}


logging.Logger




# create handler for stream logging:
stream_logger = logging.StreamHandler()
# stream_logger.setFormatter(logging.Formatter(_logger_format_short, '%H:%M:%S')) # adding the ,'%H:%M:%S' changes the timestamp to the short version
stream_logger.setFormatter(CustomFormatter(compact=True))
stream_logger.setLevel(logging.DEBUG)    # default level for stream handler
stream_logger.addFilter(DuplicateFilter())

# create handler for file logging:
_default_log_filename = os.path.join( log_path , 'hyperion.log')
file_logger = logging.handlers.RotatingFileHandler(filename = _default_log_filename, maxBytes = (5 * 1024 * 1024), backupCount = 9)
# file_logger.setFormatter(logging.Formatter(_logger_format_long))
file_logger.setFormatter(CustomFormatter())
file_logger.setLevel(logging.DEBUG)        # default level for file handler
file_logger.addFilter(DuplicateFilter())

# set these handlers as default
# (note that the base level needs to be set to lowest level i.e. logging.DEBUG)
logging.basicConfig(level=logging.DEBUG, handlers=[file_logger, stream_logger])

# Function for changing the logger file:
# (apparently you have to remove, re-create and add the handler )
def set_logfile(base_filename, folder=log_path):
    """
    Change the log file.
    Note: The way base_filename is interpreted, means you could use hyperion.set_logfile(__file__) in your python file.

    :param base_filename: The base name of the log file. If it includes an extension, that will be replaced with '.log'. If it includes a path, that will be ignored unless folder=None)
    :param folder: Folder to store the log file. DEFAULT is log_path
    """
    global file_logger
    # first store the level and formatter of the existing file_logger
    level = file_logger.level
    formatter = file_logger.formatter
    logger = logging.getLogger()
    # remove the file_logger from root/base
    logger.removeHandler(file_logger)

    # if base_filename contains also path, split that out:
    user_folder = os.path.dirname(base_filename)
    if len(user_folder):
        base_filename = os.path.basename(base_filename)

    # if folder is None, use the folder inside base_filename, if specified
    if folder is None:
        folder = user_folder

    # if folder does not exist or invalid, use the default:
    if not os.path.isdir(folder):
        folder = log_path

    filepathname = os.path.join( folder, os.path.splitext(base_filename)[0]+'.log' )
    # overwrite the file_logger (this is needed)
    file_logger = logging.handlers.RotatingFileHandler(filename=filepathname, maxBytes=(5 * 1024 * 1024), backupCount=9)
    file_logger.setFormatter(formatter)
    file_logger.setLevel(level)  # default level for file handler
    file_logger.addFilter(DuplicateFilter())

    # add file_loggerto root/base
    logger.addHandler(file_logger)

# At the beginning of a file use: import hyperion
# Also import logging (or otherwise type hyperion.logging.X everywhere you would type logging.X)
# After that use this anywhere: self.logger = logging.getLogger(__name__)
# To change the logging file use this anywhere:
# hyperion.set_logfile('new_name')
# hyperion.set_logfile('new_name', 'my_folder')
# To modify the levels use this anywhere :
# hyperion.file_logger.setLevel( logging.INFO )
# hyperion.stream_logger.setLevel( logging.WARNING )


# define a list of colors to plot
_colors = ['#1f77b4','#aec7e8','#ff7f0e','#ffbb78', '#2ca02c','#98df8a', '#d62728','#ff9896','#9467bd','#c5b0d5',
            '#8c564b','#c49c94', '#e377c2', '#f7b6d2', '#7f7f7f', '#c7c7c7', '#bcbd22', '#dbdb8d', '#17becf', '#9edae5']
