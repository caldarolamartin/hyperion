import os
from lantz.core import UnitRegistry

# units
ur = UnitRegistry()
Q_ = ur.Quantity
# logger format
_logger_format = '%(asctime)s | %(levelname)+8s | %(funcName)+25s() | %(name)-35s | %(message)s'
# for finding the configuration files
root_dir = os.path.dirname(__file__)
ls = os.pardir
