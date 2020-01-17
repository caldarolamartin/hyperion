"""
    ===============
    Base Experiment
    ===============

    This is a base experiment class. The proposal is put all the common methods needed for the experiment
    classes so they are shared and easily modified.

"""
import os
from hyperion.core import logman as logging
import yaml
import importlib
import hyperion
import time
from hyperion.tools.saving_tools import name_incrementer
from hyperion.tools.loading import get_class
# from hyperion.tools.saver import Saver
import copy
# import h5py
import numpy as np
from netCDF4 import Dataset


class DefaultDict(dict):
    """
    Special dictionary (inherits from dict).
    When accessing key of this dict it will return obj.default_dict[key] if obj.main_dict[key] doesn't exist.
    Writing and deleting always act on main_dict.
    Methods like keys(), values(), items() act on the combined list (where main_dict supersedes default_dict in case of duplicate values).
    Original default_dict is never changed. Also attempted changes to default_dict after creation of obj are ignored.

    :param main_dict: primary dictionary
    :type main_dict: dict
    :param default_dict: dictionary with default values that will be returned if key is not present in main_dict (defaults to {})
    :type default_dict: dict
    :param ReturnNoneForMissingKey: flag indicating if None should be returned if an unknown key is requested (defaults to False)
    :type ReturnNoneForMissingKey: bool
    :returns: DefaultDict object which can mostly be used and accessed as a regular dict
    :rtype: DefaultDict object

    :Example:

    obj = DefaultDict(main_dict, [default_dict, , ReturnNoneForMissingKey] )
    """

    def __init__(self, main_dict, default_dict={}, ReturnNoneForMissingKey = False):
        # self.logger = logging.getLogger(__name__)
        self.__ReturnNoneForMissingKey = ReturnNoneForMissingKey
        self.__logger = logging.getLogger(__name__)
        combined = copy.deepcopy(default_dict)
        combined.update(main_dict)
        super().__init__(combined)

        self.main_dict = main_dict
        self.default_dict = copy.deepcopy(default_dict)


    def __getitem__(self, key):
        if key in self.main_dict:
            return self.main_dict[key]
        elif key in self.default_dict:
            return self.default_dict[key]
        elif self.__ReturnNoneForMissingKey:
            # self.__logger.debug('Key {} not in main and not in default: returning None because ReturnNoneForMissingKey=True'.format(key))
            return None
        else:
            # self.__logger.error('DefaultDict: key not found: {}'.format(key))
            raise KeyError(key)

    def __setitem__(self, key, value):
        self.main_dict[key] = value
        super().__setitem__(key, value)

    def __delitem__(self, key):
        if key in self.main_dict:
            del self.main_dict[key]
        super().__delitem__(key)

    def __repr__(self):
        # return self.__dict__.__repr__()
        return {'main_dict':self.main_dict, 'default_dict':self.default_dict}.__repr__()

    def __str__(self):
        return self.__repr__().__str__()


class ActionDict(DefaultDict):
    def __init__(self, actiondict, types={}, exp=None):
        """
        Creates a DefaultDict from actiondict and actiontype (which can be passed through types or exp).
        When accessing a key of the ActionDict onbject returned it returns the value from actiondict if key is present.
        Otherwise value from actiontype if actiontype can be found and key is present. Otherwise returns None.
        Actiontypes can be passed in types or extracted from exp.
        Note: the actiondict must contain a key 'Type' that points to the name of the actiontype.
        Note: if both types and exp are specified, types is used.

        :param actiondict: dict following the Action dictionary format (typically retrieved from a Measurement in a config file)
        :type actiondict: dict
        :param types: dict of action type dicts containing default values. (typically retrieved from an ActionType in a config file) (optional, defaults to {})
        :type types: dict of dicts
        :param exp: experiment object containing .properties['ActionTypes']) (optional, defaults to None)
        :type types: BaseExperiment
        :returns: DefaultDict object which can mostly be used and accessed as a regular dict
        :rtype: DefaultDict object

        seealso:: DefaultDict
        """
        # self.logger = logging.getLogger(__name__)
        if types == {} and exp is not None:
            types = exp.properties['ActionTypes']

        if 'Type' in actiondict and actiondict['Type'] in types:
            actiontype = types[actiondict['Type']]
        else:
            actiontype = {}
        super().__init__(actiondict, actiontype, ReturnNoneForMissingKey=True)


def valid_python(name):
    """
    Converts all illegal characters for python object names to underscore.
    Also adds underscore prefix if the name starts with a number.

    :param name: input string
    :type name: str
    :return: corrected string
    :rtype: str
    """
    __illegal = str.maketrans(' `~!@#$%^&*()-+=[]\{\}|\\;:\'",.<>/?', '_' * 34)
    if name[0].isdigit():
        name = '_'+name
    return name.translate(__illegal)


class DataManager:
    """
    DataManager takes care of writing to file. Uses netCDF4 Dataset.
    Typically used inside an experiment class.

    :param experiment: experiment
    :type experiment: BaseExperiment
    :param lowercase: if True, all names in Dataset will be lowercase (optional, defaults to False)
    :type lowercase: bool

    :Example:

    # When used inside an experiment:
    datman = DataManager(self)
    datman.open_file('filename.nc')
    datman.meta(hello='world')
    dataman.dim_coord('wav', np.array([500, 600, 700]), unit='nm')
    dataman.var('spectrum', np.array(), extra_dims=('wav'), meta={'unit':'counts', 'exposuretime':'0.1s'}):
    dataman.dim_coord('x_pos', np.array([1,2,3,4]), unit='mm')
    for indx in range(4):
        fake_datapoint = indx**2
        datman.var('pow', fake_datapoint, indices=indx, dims=('x_pos'), unit='mW'):

    datman.meta('spectrum', dic={'model': 'aaa'})
    datman.meta('spectrum', dic={'model': 'aaa'})
    """
    def __init__(self, experiment, lowercase=False):
        self.logger = logging.getLogger(__name__)
        self.experiment = experiment
        self.filename = None
        self._is_open = False
        self.lowercase = lowercase
        self._version = 0.1

    def open_file(self, filename, write_mode='w', **kwargs):
        """
        Opens a file and creates a netCDF4 Dataset.
        Already adds any meta arguments present in experiment._saving_meta dictionary.

        :param filename: The filename to write to.
        :type filename: str
        :param write_mode: file access mode ('w', 'a', 'r+') (defaults to 'w')
        :type write_mode: str
        :param **kwargs: any additional keyword arguments are passed along to netCDF4.Dataset()
        """
        self.filename = filename
        if not self._is_open:
            self.logger.info('Opening datafile: {}'.format(filename))
            self.root = Dataset(filename, write_mode, format='NETCDF4', **kwargs)
            self._is_open = True
            self.meta(dic=self.experiment._saving_meta)
            self.meta(DataManager=self._version)
            self.sync_hdd()
            print('completed adding meta after opening')

        else:
            self.logger.warning('A file is already open')

    def __check_not_open(self):
        # Private helper function
        if not self._is_open:
            self.logger.warning('File not open')
            return True

    def __name_or_dict(self, name_or_dict):
        """
        Private helper function.
        If name_or_dict is an actiondict, it returns _store_name if available, otherwise Name.
        If name_or_dict is a string it uses that.
        IN ALL CASES it applies valid_python() before returning (replace all illegal varname characters with _)
        """
        if name_or_dict is None:
            return None
        elif type(name_or_dict) is str:
            name = valid_python(name_or_dict)
        elif '_store_name' in name_or_dict:
            name = valid_python(name_or_dict['_store_name'])
        else:
            name = valid_python(name_or_dict['Name'])
        if self.lowercase:
            return name.lower()
        else:
            return name

    def dim(self, name_or_dict, length=None):
        """
        Create a dimension without coordinates.
        Note that the name is converted to a valid python object name by replacing illegal characters to '_'.

        :param name_or_dict: name (as string) or ActionDict (uses ['_store_name'] of otherwise ['Name'])
        :type name_or_dict: str or ActionDict
        :param length: length of the dimension, if None dimension is unlimited (Defaults to None)
        :type length: int or None
        """
        if self.__check_not_open(): return
        name = self.__name_or_dict(name_or_dict)
        if name not in self.root.dimensions:
            self.logger.info('DataManager: Creating Dimension: {}'.format(name))
            self.root.createDimension(name, length)

    def dim_coord(self, name_or_dict, array_or_value=None, meta=None, **kwargs):
        """
        Create or append coordinates.
        Also creates dimension to hold the coordinates.

        If Dimension does not exist it is created.
        If Coordinate does not exist it is created.
        If an array is passed, those values are put in the Coordinates. The Dimension is of fixed size.
        If a value (int or float) is passed, Dimension is of unlimited size and the value is appended to the Coordinates.
        Note that values are only appended during the first iteration of a parent loops
        Optionally meta parameters can passed as meta={} or as keyword arguments.
        Note that the name is converted to a valid python object name by replacing illegal characters to '_'.

        :param name_or_dict: name (as string) or ActionDict (uses ['_store_name'] of otherwise ['Name'])
        :type name_or_dict: str or ActionDict
        :param array_or_value: numpy array to completely initialize the Coordinates, or just a value for unlimited (extendable) coordinates.
        :type array_or_value: np.ndarray or int or float
        :param meta: dictionary holding meta arguments(Optional)
        :type meta: dict
        :param **kwargs: additional unknown keyword arguments are added as meta attributes
        """

        if self.__check_not_open(): return
        name = self.__name_or_dict(name_or_dict)
        if name not in self.root.dimensions:
            self.logger.info('DataManager: Creating Dimension and Coordinate: {}'.format(name))
            length = None if type(array_or_value) is not np.ndarray else len(array_or_value)
            self.root.createDimension(name, length)
            self.root.createVariable(name, 'f8', name)
            if length is not None:
                self.root.variables[name][:] = array_or_value
            if meta is not None:
                self.meta(name, meta)

        if type(array_or_value) is not np.ndarray:
            if name in self.experiment._nesting_parents:
                indx = 1+ self.experiment._nesting_indices[self.experiment._nesting_parents.index(name)]
            else:
                indx = 0
            if indx >= self.root.variables[name].size:
                self.root.variables[name][indx] = array_or_value
        ### old alternative to the 7 lines above
        # if type(array_or_value) is not np.ndarray:
        #     if (len(self.experiment._nesting_indices) == 0 or len(self.experiment._nesting_indices)<len(self.experiment._nesting_parents)):
        #         self.root.variables[name][self.root.variables[name].size] = array_or_value


    def __attach_meta(self, attach, dic):
        """
        Private method. Used by meta()
        Tries to attach all keys in dic to element of netcdf4 dataset. Invalid datatypes only result in a logger warning.
        If attach is None, attributes are added to root of Dataset.
        Only netCDF4 allowed variable types are allowed: 'S1', 'i1', 'u1', 'i2', 'u2', 'i4', 'u4', 'i8', 'u8', 'f4', 'f8'.
        Lists that are completely of a single allowed type are also allowed.
        One addition: bools and bools as elements of lists will be converted to int.
        Note that keys starting with '~' or '_' are ignored (except for '_method'). This allowes for passing a whole actiondict at once.
        """
        for key, value in dic.items():
            # attach.setncattr(key, value)
            if key[0] == '~': continue                      # Always skip if key starts with '~'  (i.e. ~nested)
            if key[0] == '_' and key !='_method': continue  # Always skip if key starts with '_' unless it's _method
            try:
                if type(value) is list and any(type(k) is bool for k in value):
                    attach.setncattr(key, [int(k) if type(k) is bool else k for k in value])
                elif type(value) is bool:
                    attach.setncattr(key, int(value))
                else:
                    attach.setncattr(key, value)
            except:
                self.logger.warning('unsupported {} in dict: {}: {}'.format(type(value), key, value))

    def meta(self, attach_to=None, dic=None, only_once=False, *args, **kwargs):
        """
        Attach meta data as attributes to netCDF4 Dataset.
        Attaches them to attach_to which can be a Variable or a Coordinate. Or if None is used, attributes are placed in the root.
        Note that attach_to can be a string or an ActionDict.
        Attributes can be passed as a dict through dic or as keyword arguments.
        Invalid datatypes are not attached and result in a logger warning.
        NetCDF4 allowed variable types: 'S1', 'i1', 'u1', 'i2', 'u2', 'i4', 'u4', 'i8', 'u8', 'f4', 'f8'.
        Lists that are completely of a single allowed type are also allowed.
        One addition: bools and bools as elements of lists will be converted to int.
        Note that keys starting with '~' or '_' are ignored (except for '_method'). This allowes for passing a whole actiondict at once.
        Note that attach_to is converted to a valid python object name by replacing illegal characters to '_'.

        :param attach_to: name (as string) or ActionDict (uses ['_store_name'] of otherwise ['Name']).
        :type attach_to: str or ActionDict

        :param dic: dictionary holding meta attributes (optional)
        :type dic: dict (or ActionDict)
        :param only_once: If True it will not overwrite existing meta attribute of the same name (defaults to False)
        :type only_once: bool
        :param *args: if a single argument of type dict is passed it will be interpreted as being dic
        :param **kwargs: additional unknown keyword arguments are added as meta attributes.

        :Examples:

        # These 3 examples are the same and add 'a' and 'b' to the root of the Dataset
        datman.meta(a=1, b=2)
        datman.meta({'a': 1, 'b':2})
        datman.meta(dic={'a': 1, 'b':2})
        # These 3 examples are the same and add 'c' and 'd' to the Coordinate 'sample_x'
        datman.meta('sample_x', c=3, d=4)
        datman.meta('sample_x', {'c': 3, 'd':4})
        datman.meta('sample_x', dic={'c': 3, 'd':4})
        # Example of using an actiondict for name:
        ad = ActionDict({'Name': 'spectrum', 'exposuretime': '0.2s'})
        datman.meta(ad, exposuretime = '0.1s')
        # Example of using an actiondict for meta
        datman.meta(ad, ad)
        """
        if self.__check_not_open(): return
        # Skip if only_once is True and parent loops are not in first iteration:
        if only_once and not sum(self.experiment._nesting_indices): return
        attach_to = self.__name_or_dict(attach_to)
        # add attributes to set of variable
        attach = self.root
        if attach_to in self.root.variables:
            attach = self.root.variables[attach_to]
        if type(dic) is dict or type(dic) is ActionDict or type(dic) is DefaultDict:
            self.__attach_meta(attach, dic)
        # If a single unknown argument is given assume it's dict of meta info to attach:
        if len(args) == 1 and type(args[0]) is dict:
            self.__attach_meta(attach, args[0])
        # Unknown keyword arguments will be stored as meta info
        self.__attach_meta(attach, kwargs)

    def var(self, name_or_dict, data, indices=None, dims=None, extra_dims=None, meta=None, **kwargs):
        """
        Add or update a Variable.
        Can automatically deduce dimensions and indices if used in automated scanning (i.e. perform_actionlist() of BaseExperiment.)
        If higher dimensional data is to be stored, those extra dimensions should be passed under extra_dims. Note that
        in automated scanning you have to create those extra dimensions yourself.
        Optionally meta parameters can passed as meta={} or as keyword arguments.
        Note that the name is converted to a valid python object name by replacing illegal characters to '_'.
        Note: will store data as float (f8).

        :param name_or_dict: name (as string) or ActionDict (uses ['_store_name'] of otherwise ['Name'])
        :type name_or_dict: str or ActionDict
        :param data: single number or array for higher dimensional data
        :type data: float (or int) or np.ndarray for higher dimensional data
        :param indices: indices in "parent" dimensions, OMIT when using in automated scanning.
        :type indices: list of integers
        :param dims: "parent" dimensions, OMIT when using in automated scanning.
        :type dims: tuple or list of strings
        :param extra_dims: extra dimensions for higher dimensional data.
        :type extra_dims: tuple or list of strings
        :param meta: dictionary holding meta arguments(Optional)
        :type meta: dict
        :param **kwargs: additional unknown keyword arguments are added as meta attributes
        """
        if self.__check_not_open(): return
        name = self.__name_or_dict(name_or_dict)
        if indices is None:
            indices = self.experiment._nesting_indices

        if name not in self.root.variables:
            self.logger.info('DataManager: Creating Variable: {}'.format(name))
            if dims is None:
                dims = tuple(self.experiment._nesting_parents)  # automatically get dims
            # For higher dimensional data:
            if extra_dims is not None:
                if type(extra_dims) is str:
                    dims = dims + (extra_dims,)
                else:
                    dims = dims + tuple(extra_dims)
            self.root.createVariable(name, 'f8', dims)
            if meta is not None or len(kwargs):
                self.meta(name, meta, **kwargs)
        # if extra_dims is None:
        if len(indices):
            npdata = np.array(data)
            npdata = npdata.reshape(tuple([1] * len(indices)) + npdata.shape)
            self.root.variables[name][tuple(indices)] = npdata
        else:
            self.root.variables[name][:] = data

    def sync_hdd(self):
        """ Update file on hdd with data in memory. """
        if self.__check_not_open(): return
        self.root.sync()

    def close(self):
        """
        Closes the file. ( First applies sync_hdd() )
        """
        if self._is_open and self.root.isopen():
            self.root.sync()        # Don't know if this is necessary
            self.root.close()
        self._is_open = False
        self.filename = None


class BaseExperiment:
    """
    Base experiment class for experiment classes to inherit from.
    Takes care of some built-in functionality like loading instruments and automated scanning.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info('Initializing the BaseExperiment class.')

        self.properties = {}    # this is to load the config yaml file and store all the
                                # settings for the experiment. see load config

        # this variable is to keep track of all the instruments that are connected and
        # properly close connections with them at the end
        self.instruments_instances = {}
        # these next variables are for the master gui.
        self.view_instances = {}
        self.graph_view_instance = {}

        self.filename = ''
        self.config_filename = None  # load_config(filename) stores the config filename here

        # Measurement status flags:
        # They can be set externally to control the flow of a measurement:
        self.apply_pause = False   # used for temporarily interrupting a measurement
        self.apply_break = False   # used for a soft stop (e.g. stop after current loop iteration)
        self.apply_stop =  False   # used for a hard stop

        # Measurement status
        self.running_status = 0    # 0 for not running, 1 for running, 1 for paused, 2 for breaking, 3 for stopping
        # For convenience, the numbers are also stored in these constants:
        self._not_running = 0
        self._running = 1
        self._pausing = 2
        self._breaking = 3
        self._stopping = 4

        # These are parameters that will be updated and used by automated scanning and saving
        self._nesting_indices = []
        self._nesting_parents = []
        self._measurement_name = ''
        self.datman = DataManager(self)
        self._finalize_measurement_method = lambda *args, **kwargs: None
        self.__store_properties = None
        # self._exit_status = 'running'
        self._saving_meta = {}

        # placeholder do-nothing function that can be overwritten by saver gui
        self._saver_gui_incremeter = lambda : None  # empty function

    def reset_measurement_flags(self):
        """ Reset measurement flags (at the end of a measurement or when it's stopped). """
        self.apply_pause = False   # used for temporarily interrupting a measurement
        self.apply_break = False   # used for a soft stop (e.g. stop after current loop iteration)
        self.apply_stop =  False   # used for a hard stop
        self.running_status = 0  # 0 for not running, 1 for paused, 2 for breaking, 3 for stopping

    def check_stop(function):
        """
        Decorator for stopping function:
        If optional keyword argument force is set to True it will set self.apply_stop to True.
        Calls the stop method it applied to and then reset_measurement_flags()
        """
        def wrapper_accepting_arguments(self, *args, force=False, **kwargs):
            if self.running_status == self._stopping:
                return True
            if self.apply_stop or force:
                self.running_status = self._stopping
                function(self, *args, **kwargs)
                return True
            else:
                return False
            #
            # if force: self.apply_stop = True
            # if (self.apply_stop or force):# and self.running_status < self._stopping:
            #     # Only run the function the first time
            #     if self.running_status != self._stopping:
            #         function(self, *args, **kwargs)
            #     self.running_status = self._stopping
            #     # self.reset_measurement_flags()  # make sure all flags are reset    ##  THIS LINE PREVENTS NESTED FUNCTION FROM ESCAPING ALL LAYERS, HAVE TO LOOK INTO THIS HOW TO SOLVE
            #     return True
            # return False

            # if force: self.apply_stop = True
            # if (self.apply_stop or force):# and self.running_status < self._stopping:
            #     # Only run the function the first time
            #     if self.running_status != self._stopping:
            #         function(self, *args, **kwargs)
            #     self.running_status = self._stopping
            #     # self.reset_measurement_flags()  # make sure all flags are reset    ##  THIS LINE PREVENTS NESTED FUNCTION FROM ESCAPING ALL LAYERS, HAVE TO LOOK INTO THIS HOW TO SOLVE
            #     return True
            # return False
        return wrapper_accepting_arguments

    def check_break(function):
        """
        Decorator for breaking function:
        First checks for "Stop", then calls the break function it is applied to, if self.apply_break is True
        In that case also sets self.running_status to self._breaking
        """
        def wrapper_accepting_arguments(self, *args, force=False, **kwargs):
            # First check for "Stop" and return True if True
            if self.stop_measurement():
                return True
            # if force: self.apply_break = True
            if self.apply_break and self.running_status < self._stopping:
                # if not self.__exitself._exit_status = self._breaking
                self.running_status = self._breaking
                function(self, *args, **kwargs)
                return True
            else:
                return False
        return wrapper_accepting_arguments

    def check_pause(function):
        """
        Decorator for pausing function:
        First checks for "Stop", then calls the pause function it is applied to, if self.apply_pause is True
        In that case also sets self.running_status to self._pausing. Afterward, restores self.running_status to state it
        was before (unless modified externally)
        """
        def wrapper_accepting_arguments(self, *args, force=False, **kwargs):
            # First check for "Stop" and return True if True
            if self.stop_measurement():
                return True
            # if force: self.apply_pause = True
            if self.apply_pause and self.running_status < self._stopping:
                store_state = self.running_status
                self.running_status = self._pausing
                ret = function(self, *args, **kwargs)
                # If running_status is not overwritten externally, restore whatever the state was before:
                if self.running_status == self._pausing:
                    self.running_status = store_state
                self.apply_pause = False  # reset flag
                return ret
            return False
        return wrapper_accepting_arguments

    def dummy_measurement_for_testing_gui_buttons(self):
        self.logger.info('Starting test measurement')
        self.reset_measurement_flags()
        self.running_status = self._running
        for outer in range(4):
            print('outer', outer)
            for inner in range(4):
                print('    inner', inner)
                time.sleep(1)
                # if self.stop_measurement(): return      # Use this line to check for stop
                if self.pause_measurement(): return  #: return     # Use this line to check for pause
            if self.break_measurement(): return      # Use this line to check for stop
        self.reset_measurement_flags()
        self.logger.info('Measurement finished')

    @check_stop  # This decorator makes sure the method is only executed if self.apply_stop is True
    def stop_measurement(self):
        """ The decorator also gives it one extra keyword argument 'force' which will set the apply_stop flag for you. """
        self.logger.info('Custom stop method: Override if you like. Just use @check_stop decorator')
        # Set the self._exit_status string:

        # Automatically call method set in self._finalize_measurement_method
        self._finalize_measurement_method({'Name': self._measurement_name}, lambda *args, **kwargs: None)
        # Reset self._finalize_measurement_method to a do nothing function:
        self._finalize_measurement_method = lambda *args, **kwargs: None
        # self.reset_measurement_flags()
        self.logger.info('Measurement stopped')

    @check_break  # This decorator makes sure that the break method it is applied to, is only executed if self.apply_break is True
    def break_measurement(self):
        self.logger.info('Custom break method: Override if you like. Just use @check_break decorator')
        # Do stuff
        # Should end with stopping:
        self.stop_measurement(force=True)

    @check_pause  # This decorator makes sure the method is only executed if self.apply_pause is True
    def pause_measurement(self):
        """
        Halts the flow of the measurement. While waiting it checks if checks if "Stop" signal is given.
        :return: (boolean) If measurement is "Stopped" while pausing it returns True
        """
        self.logger.info('Custom pause method. Override if you like. Just use @check_pause decorator')
        while self.apply_pause:
            # While in pause mode: check if stop is "pressed":
            if self.stop_measurement():
                return True        # in that case return True

    @property
    def exit_status(self):
        if self.apply_stop:
            return 'stopped'
        elif self.apply_break:
            return 'break'
        elif self.running_status == 1:
            return 'completed'
        else:
            return 'unknown'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finalize()

    def _validate_actionlist(self, actionlist, _complete=None, invalid_methods=0, invalid_names=0):
        """
        Returns a 'corrected' copy (does not modify input) and

        _validate_actionlist(complete_actionlist)
        _complete is used for recursion
        """
        local_actionlist = copy.deepcopy(actionlist)        # this is required for a new copy (without it the original gets modified)
        # recursive function
        if _complete is None:
            _complete = local_actionlist

        # Note: approach with 'for act in local_actionlist' would not change the list
        for indx in range(len(local_actionlist) - 1, -1, -1):
            local_actionlist[indx], method_invalid, name_invalid = self._validate_actiondict(local_actionlist[indx], _complete)
            invalid_methods += method_invalid
            invalid_names += name_invalid
            #            print(act)
            #            print(local_actionlist)
            if '~nested' in local_actionlist[indx]:
                local_actionlist[indx]['~nested'], invalid_methods, invalid_names = self._validate_actionlist(local_actionlist[indx]['~nested'], _complete, invalid_methods, invalid_names)
                # invalid_methods += method_invalid
                # invalid_names += name_invalid
        return local_actionlist, invalid_methods, invalid_names

    def _validate_actiondict(self, actiondictionary, complete_actionlist):
        """
        returns new corrected dictionary (does not alter the dictionary )
        """
        actiondict = copy.deepcopy(actiondictionary)

        # Auto generate a name if it doesn't exist
        invalid_name = 0
        all_names, unnamed = self.all_action_names(complete_actionlist)
        if 'Name' not in actiondict:
            invalid_name = 1
            if '_method' in actiondict:
                actiondict['Name'] = name_incrementer(actiondict['_method'], all_names, ' ')
            elif 'Type' in actiondict:
                actiondict['Name'] = name_incrementer(actiondict['Type'], all_names, ' ')
            else:
                actiondict['Name'] = name_incrementer('no Type or _method', all_names, ' ')
            self.logger.warning("Actiondict has no Name. Auto-generating: '{}'".format(actiondict['Name']))

        # Test if name is duplicate
        action_name = actiondict['Name']
        if all_names.count(action_name) > 1:
            invalid_name = 1
            actiondict['Name'] = name_incrementer(action_name, all_names, ' ')
            self.logger.warning("Duplicate Action Name. Changed '{}' to '{}'".format(action_name, actiondict['Name']))
        action_name = actiondict['Name']

        # Test if valid method specified
        # Intended behaviour:
        # - if method specified: us it if it exists, raise invalid_method flag if not
        # - if method not specified: try to find one in action type, raise invalid_method flag if anything goes wrong
        invalid_method = 1
        if '_method' in actiondict:
            method_name = actiondict['_method']
            if hasattr(self, method_name):
                invalid_method = 0
            else:
                self.logger.error("[Action: '{}'] _method '{}' doesn't exist".format(action_name,method_name))
        else:
            self.logger.info(
                "[Action: '{}'] No _method specified , (looking for _method in ActionType)".format(action_name))
            if 'Type' not in actiondict:
                self.logger.error("[Action: '{}'] No Type specified".format(action_name))
            elif "_method" not in self.actiontypes[actiondict['Type']]:
                self.logger.error("[Action: '{}']>[ActionType: {}] No _method specified".format(action_name, actiondict['Type']))
            elif not hasattr(self, self.actiontypes[actiondict['Type']]['_method']):
                self.logger.error("[ActionType: '{}'] _method '{}' also doesn't exist".format(actiondict['Type'], self.actiontypes[actiondict['Type']]['_method']))
            else:
                invalid_method = 0
                self.logger.info("[Action '{}'] Using _method '{}' from [ActionType: '{}']".format(action_name, self.actiontypes[actiondict['Type']]['_method'], actiondict['Type']))
        return actiondict, invalid_method, invalid_name

    def all_action_names(self, complete_actionlist):  # , name_list = [], unnamed=0):
        # outputlist = all_action_names(complete_actionlist)
        # recursive function to find all names in a measurement list/dict structure
        # outputs list of names and integer of unnamed actions
        name_list = []
        unnamed = 0
        for actiondict in complete_actionlist:
            if 'Name' in actiondict:
                name_list.append(actiondict['Name'])
            else:
                unnamed += 1
            if '~nested' in actiondict:
                nested_names, nested_unnamed = self.all_action_names(actiondict['~nested'])  # , name_list, unnamed)
                name_list += nested_names
                unnamed += nested_unnamed
        return name_list, unnamed

    def swap_actions(self, complete_actionlist, action1, action2):
        """
        Swaps two actions by name. Keeps nested items in place.
        Typically used when swapping the direction of a 2D loop
        """

        all_names, _ = self.all_action_names(complete_actionlist)
        for action in [action1, action2]:
            if action not in all_names:
                self.logger.warning("error: loop '{}' not in actionlist".format(action))
        placeholder = {'Name': '__placeholder_while_swapping_loops__'}
        act1 = self._exchange_action(complete_actionlist, action1, placeholder)
        act2 = self._exchange_action(complete_actionlist, action2, act1)
        self._exchange_action(complete_actionlist, '__placeholder_while_swapping_loops__', act2)

    def _exchange_action(self, actionlist, loopname, new_dict):
        """
        Helper function for swap_actions
        Exhanges dict with loopname for new_dict. But keeps original nested key if available.
        Returns the original key (without nested key)
        """
        # for indx, act in enumerate(actionlist)  # DON'T use this here!
        for indx in range(len(actionlist)):
            act = actionlist[indx]
            if '~nested' in act:
                aux = self._exchange_action(act['~nested'], loopname, new_dict)
                if aux is not None:
                    return aux
            if act['Name'] == loopname:
                # replace with new dict
                actionlist[indx] = new_dict
                if '~nested' in act:
                    # copy nested back into the dict
                    actionlist[indx]['~nested'] = act['~nested']
                    nested = act['~nested']  # s
                    # and remove it from act
                    del act['~nested']
                    return act
        return None

    def perform_measurement(self, measurement_name):
        self._measurement_name = measurement_name
        self.saver = None
        # new_action_list, invalid_methods, invalid_names = self._validate_actionlist(self.properties['Measurements'][measurement_name])


        if measurement_name in self.properties['Measurements']:
            self.logger.debug('Starting measurement: {}'.format(measurement_name))

            # Make dict with basic meta info to be added to the datafile.
            # default_saver will add this _saving_meta dict
            self._saving_meta = {'Hyperion': hyperion.__version__,
                                 'Experiment': self.__class__.__name__}
            if hasattr(self, 'version'):
                self._saving_meta['version'] = self.version
            self._saving_meta['Measurement'] = measurement_name

            self.reset_measurement_flags()
            self.running_status = self._running
            # self._exit_status = 'running'

            self.perform_actionlist(self.properties['Measurements'][measurement_name])

            self.reset_measurement_flags()
            self.logger.info('Measurement finished')

            if self.__store_properties:
                self.logger.info('Storing experiment properties in {}'.format(self.__store_properties))
                with open(self.__store_properties, 'w') as f:
                    yaml.dump(self.properties, f)
                self.__store_properties = None

            # If the gui has overwritten this function, this will update the incrementer-number in the gui
            # (it's not strictly necessary to do this, but it's nice if the gui updates)
            # Note that if the gui hasn't overwritten this function, it is an empty do-nothing function.
            self._saver_gui_incremeter()
        else:
            self.logger.error('Unknown measurement: {}'.format(measurement_name))

    # def perform_measurement(self, actionlist, parent_values = [], parents=[]):
    def perform_actionlist(self, actionlist, parents=[], save=True):
        """
        Used to perform a measurement based on the actionlist

        :param actionlist:
        :param parents:
        :param save:
        :return:
        """

        # if self.stop_measurement(): return
        if self.pause_measurement(): return  #: return     # Use this line to check for pause

        if parents == []:
            self._nesting_indices = []


        if len(parents) > len(self._nesting_indices):
            self._nesting_indices += [0]
        elif len(parents) == len(self._nesting_indices):
            if len(self._nesting_indices):
                self._nesting_indices[-1] += 1
        else:
            print('??????????????')

        # typically used on the whole list
        # In a an action that has nested Actions
        for actiondictionary in actionlist:
            # check for stop and pause

            actiondict = ActionDict(actiondictionary, exp=self)
            actionname = actiondict['Name']

            if '_method' not in actiondict:
                raise KeyError('No _method found in actiondict or actiontype')
            else:
                try:
                    method = getattr(self, actiondict['_method'])
                except AttributeError:
                    raise AttributeError('method {} not found in experiment object'.format(actiondict['_method']))

            self._nesting_parents = parents  # to make it available outside

            if '~nested' in actiondict:
                # without error checking for now:
                # else:
                #     indices += [0]  # append 0 to list  current_values
                if '_store_name' in actiondict:
                    new_parent = valid_python(actiondict['_store_name'])
                else:
                    new_parent = valid_python(actionname)
                nesting = lambda : self.perform_actionlist(actiondict['~nested'], parents+[new_parent])
                # store = lambda *args, **kwargs: self._datman.coord(*args, **kwargs, actiondict=actiondict, parents=parents, indices=self._nesting_indices)
            else:
                nesting = lambda *args, **kwargs: None        # a "do nothing" function
                # nesting = lambda *args, **kwargs: self.check_pause()  # a "do nothing" function


                # store = lambda *args, **kwargs: self._datman.add(*args, **kwargs, actiondict=actiondict, parents=parents, indices=self._nesting_indices)

            method(actiondict, nesting)
            # if self.stop_measurement(): return
            if self.pause_measurement(): return  #: return     # Use this line to check for pause

        if len(parents) < len(self._nesting_indices):
            del self._nesting_indices[-1]

    def save(self, data, auto=True, **kwargs):
        indx = self._nesting_indices[:len(self._nesting_parents)]

    def default_saver(self, actiondict, nesting):
        folder, basename = self._validate_folder_basename(actiondict)
        if actiondict['auto_increment']:
            existing_files = os.listdir(actiondict['folder'])
            basename = name_incrementer(actiondict['basename'], existing_files)
        filename_complete = os.path.join(folder, basename)
        self.datman.open_file(filename_complete, lowercase=True)
        if actiondict['comment']:  # This will not add comment if it's empty or non-existing
            self.datman.meta(dic={'comment':actiondict['comment']})
        if actiondict['store_properties']:
            self.__store_properties = os.path.splitext(filename_complete)[0]+'.yml'

    def _validate_folder_basename(self, actiondict):
        """
        Primarily intended to be used with actiondict as input (but also works with string.
        If actiondict contains folder key, that folder wil be used.
        If actiondict contains basename key, that basename will be used.
        Otherwise if folder actually included the filename, that will be used for basename.
        Otherwise the measurement name will be used as basename.

        If a string is passed instead of an actiondict, that string will be used as folder.
        If that string also includes the filename, that will be used for basename.
        Otherwise the measurement name will be used as basename.

        If the folder (ans its parent folders) don't exist they will be created.

        :param actiondict:
        :return: folder, basename
        """
        basename = None
        if type(actiondict) is str:
            folder = actiondict
        else:
            if 'folder' in actiondict:
                folder = actiondict['folder']
            else:
                folder = os.path.join(hyperion.parent_path , 'data')
            if 'basename' in actiondict:
                basename = actiondict['basename']
        # convert potential relative path to absolute path:
        folder = os.path.abspath(folder)
        # if it ends with an extension, remove filename
        if os.path.splitext(folder)[1]:
            folder = os.path.dirname()
            if not basename:
                basename = os.path.split(folder)[1]
        if not basename:
            basename = self._measurement_name
        # create the folder (and parent folders if necessary):
        if not os.path.isdir(folder):
            self.logger.info('Creating path: {}'.format(folder))
            os.makedirs(folder)
        # # if input was actiondict: update the values:
        # if type(actiondict) is not str:
        #     actiondict['folder'] =
        #     actiondict['basename']
        #
        return folder, basename

    # def create_saver(self, actiondict, nesting):
    #     version = actiondict['version'] if 'version' in actiondict else None
    #     folder = actiondict['folder'] if 'folder' in actiondict else os.path.join(hyperion.parent_path, 'data')
    #     filename = actiondict['filename'] if 'filename' in actiondict else self._measurement_name + '.h5'
    #     write_mode = actiondict['write_mode'] if 'write_mode' in actiondict else ['increment']
    #     self.saver = Saver(verion=version, default_folder=folder, default_filename=filename, write_mode=write_mode)
    #     self.saver.open_file()

    def load_config(self, filename):
        """Loads the configuration file to generate the properties of the Scan and Monitor.

        :param filename: Path to the filename. Defaults to Config/experiment.yml if not specified.
        :type filename: string
        """
        self.logger.debug('Loading configuration file: {}'.format(filename))
        self.config_filename = filename

        with open(filename, 'r') as f:
            d = yaml.load(f, Loader=yaml.FullLoader)
            self.logger.info('Using configuration file: {}'.format(filename))

        self.properties = d
        self.properties['config file'] = filename  # add to the class the name of the Config file used.

        if 'ActionTypes' in self.properties:
            self.actiontypes = self.properties['ActionTypes']
        else:
            self.logger.info('No ActionTypes specified in config file')
            self.actiontypes = {}

    def finalize(self):
        """
        Finalizes the experiment class.
        Closes all instruments in instrument_instances
        """
        self.logger.info('Finalizing the experiment base class. Closing all the devices connected')
        for name in self.instruments_instances:
            self.logger.info('Finalizing connection with device: {}'.format(name))
            self.instruments_instances[name].finalize()
        self.logger.debug('Closing open datafiles if there are any.')
        self.datman.close()
        self.logger.debug('Experiment object finalized.')

    def load_instrument(self, name):
        """ Loads a single instrument given by name.

        :param name: name of the instrument to load. It has to be specified in the config file under Instruments
        :type name: string
        :return: instance of instrument class and adds this instrument object to a dictionary.
        """
        self.logger.debug('Loading instrument: {}'.format(name))

        ### This is OLD CODE. I leave it here for some time while testing the NEW CODE below:
        # try:
        #     di = self.properties['Instruments'][name]
        #     module_name, class_name = di['instrument'].split('/')
        #     self.logger.debug('Module name: {}. Class name: {}'.format(module_name, class_name))
        #     MyClass = getattr(importlib.import_module(module_name), class_name)
        #     self.logger.debug('class: {}'.format(MyClass))
        #     self.logger.debug('settings used to create instrument: {}'.format(di))
        #     instance = MyClass(di)
        #     self.logger.debug('instance: {}'.format(instance))
        #     #self.instruments.append(name)
        #     self.instruments_instances[name] = instance
        #     return instance
        # except KeyError:
        #     self.logger.warning('The name "{}" does not exist in the config file'.format(name))
        #     return None
        ### NEW CODE:::::::::::::::::
        if name not in self.properties['Instruments']:
            self.logger.warning('Instrument not specified in config: {}'.format(name))
        elif 'instrument' not in self.properties['Instruments'][name]:
            self.logger.error('Missing instrument in config of Instrument: {}'.format(name))
        else:
            instr_class = get_class(self.properties['Instruments'][name]['instrument'])
            if instr_class is None:
                self.warning("Couldn't load instrument class: {}".format(self.properties['Instruments'][name]['instrument']))
                return None
            instance = instr_class(self.properties['Instruments'][name])  # added this line
            self.instruments_instances[name] = instance
            self.logger.debug('Instrument: {} has been loaded and added to instrument_instances'.format(name))
            return instance
        return None

    def load_instruments(self):
        """"
        SOME MODIFICATION:
        I've moved the bit of adding an instrument to instrument_instances to load_instrument.
        That way also manually loaded instruments will be closed by finalize()

        This method creates the instance of every instrument in the config file (under the key Instruments)
        and sets this instance in the self.instruments_instances (this is a dictionary).
        This way they are approachable via self.instruments_instances.items(),
        The option to set the instruments by hand is still possible, but not necessary because the pointer
        to the instrument is in the instruments_instances.

        The instruments in the self.instruments_instances are going to be finalized when  the exit happens,
        so if you load an instrument manually and do not add it to this dictionary, you need to take care of
        the closing.
        """
        for instrument in self.properties['Instruments']:
            self.load_instrument(instrument)  # this method from base_experiment adds intrument instance to self.instrument_instances dictionary

        # for instrument in self.properties['Instruments']:
        #     inst = self.load_instrument(instrument)  # this method from base_experiment adds intrument instance to self.instrument_instances dictionary
        #     if inst is None:
        #         self.logger.warning(" The instrument: {} is not connected to your computer".format(instrument))
        #     else:
        #         self.instruments_instances[instrument] = inst
        #         self.logger.debug('Object: {} has been loaded in '
        #                       'instrument_instances {}'.format(instrument, self.instruments_instances[instrument]))


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.warning("For testing it's better to run an example experiment from the examples folder.")

    with BaseExperiment() as e:

        from hyperion import repository_path
        config_file = os.path.join(repository_path, 'examples', 'example_experiment_config.yml')
        logger.info('Using the config file: {}.yml'.format(config_file))
        e.load_config(config_file)

        # read properties just loaded
        logger.info('\n {} \n'.format(e.properties))

