import os
from lantz.core import UnitRegistry, Q_
__version__ = 0.1

# units
ur = UnitRegistry()
# logger format
_logger_format = '%(asctime)s | %(levelname)+8s | %(funcName)+25s() | %(name)-45s | %(message)s'
_logger_settings = {'filename':'logger.log', 'maxBytes':(1048576 * 5), 'backupCount':7}
# for finding the configuration files
root_dir = os.path.dirname(__file__)
ls = os.pardir
