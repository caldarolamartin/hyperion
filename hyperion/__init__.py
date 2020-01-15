
__version__ = 0.3
import os
# useful paths:
package_path =    os.path.dirname(__file__)          #   ###/###/hyperion/hyperion/
repository_path = os.path.dirname(package_path)      #   ###/###/hyperion/
parent_path =     os.path.dirname(repository_path)   #   ###/###/
log_path =        os.path.join(parent_path, 'logs')  #   ###/###/logs/
# keep root_dir for backward compatability
root_dir = package_path
ls = os.pardir
# It's important that log_path is defined before importing from hyperion.core
from hyperion.core import logman as logging
# It's important that lantz is after hyperion.core import
from lantz.core import UnitRegistry, Q_
# units
ur = UnitRegistry()
# Define alternative to Q_ that doesn't throw error when input is None, but returns None
Quan = lambda inp: None if inp is None else Q_(inp)



# These colors should not be specified here
# Maybe in plotting_tools, or ui_tools
# Or maybe in core.py

# define a list of colors to plot
_colors = ['#1f77b4','#aec7e8','#ff7f0e','#ffbb78', '#2ca02c','#98df8a', '#d62728','#ff9896','#9467bd','#c5b0d5',
            '#8c564b','#c49c94', '#e377c2', '#f7b6d2', '#7f7f7f', '#c7c7c7', '#bcbd22', '#dbdb8d', '#17becf', '#9edae5']
