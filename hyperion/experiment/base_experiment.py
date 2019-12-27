"""
    ===============
    Base Experiment
    ===============

    TO DO:

    - stop copying everything when verifying list
    - grab type info while executing


    This is a base experiment class. The propose is put all the common methods needed for the experiment
    classes so they are shared and easily modified.

"""
import os
from hyperion.core import logman as logging
import yaml
import importlib
import hyperion
import time
from hyperion.tools.saving_tools import name_incrementer
# from hyperion.tools.saver import Saver
import copy
# import h5py
import numpy as np

# class autosaver:
#     """
#     :param filepath:
#     :param experiment:
#     :param version:
#     :param append:
#     """
#
#     file_version_compatability = {0.10:[0.1, 0.02, 0.01],
#                                   0.02:[0.1, 0.02, 0.01],
#                                   0.01:[0.01]}
#     def __init__(self, filepath, experiment, version=0.1, append=False, dialogs=None):
#         self.logger = logging.getLogger(__name__)
#         self.version = version
#         if version not in file_version_compatability.keys():
#             self.version = sorted(self.file_version_compatability.keys)[-1]
#             self.logger.warning("Invalid version {}, using version {} instead".format(version, self.version))
#         self.filepath = filepath
#         valid = False
#         while not valid:
#             if os.path.isfile(self.filepath):
#                 self.logger.warning('File exists: {}'.format(self.filepath))
#                 if not append:
#                     inp = input('File exists. choose [D]ifferent filename, try to [M]odify/append, or [Overwrite]: ')
#                     if inp[0].lower()=='d':
#                         self.filepath = input('New file name: ')
#                         continue
#                     if inp[0].lower()=='m': append=True
#                 else:
#                     try:
#                         self.h5 = h5py.File(filepath, 'a')
#                     except OSError as e:
#                         self.logger.warning("Can't open file. Exception: {}".format(e))
#                         continue
#                     if 'hyperion_file_version' not in self.h5.attrs:
#                         print("Can't try to append/modify file because not a hyperion file type.")
#                         self.h5.close()
#                         continue
#                     else:
#                         file_version = self.h5.attrs['hyperion_file_version']
#                         if file_version not in self.file_version_compatability{self.version}:
#                             print("Can't modify version {} file with version {} settings.".format(file_version, self.version))
#                             self.h5.close()
#                             continue
#                     print('Modifying existing file')
#                     self.h5.attrs['hyperion_file_modified'] = self.version
#                     valid = True
#             else:
#                 try:
#                     self.h5 = h5py.File(filepath, 'w')
#                 except OSError as e:
#                     self.logger.warning("Can't create file. Exception: {}".format(e))
#                     continue
#                 self.h5.attrs['hyperion_file_version'] = self.version
#                 valid = True
#
#     def __enter__(self):
#         return self
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#        self.h5.close()
#
#     def coord(self):
#         pass
#
#     def data(self, name, data, flush=True):
#         """
#
#
#         :param name: Unique name (suggested to use actiondict['Name'])
#         :return:
#         """
#         pass
#         # self.exp._nesting_parents
#         # self.exp._nesting_indices



class DefaultDict(dict):
    """
    Special dictionary that returns obj.default_dict[key] if obj.main_dict[key] doesn't exist.
    Writing and deleting always act on main_dict.
    Methods like keys(), values(), items() act on the combined list.
    Original default_dict is never changed. Also changes to default_dict after creation of obj are ignored.

    obj = DefaultDict(main_dict, default_dict)

    :param main_dict: dict
    :param default_dict: dict (defaults to {})
    """

    def __init__(self, main_dict, default_dict={}):
        self.logger = logging.getLogger(__name__)
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
        else:
            self.logger.error('DefaultDict: key not found: {}'.format(key))
            raise KeyError(key)

    def __setitem__(self, key, value):
        self.main_dict[key] = value
        super().__setitem__(key, value)

    def __delitem__(self, key):
        if key in self.main_dict:
            del self.main_dict[key]
        super().__delitem__(key)

    def __repr__(self):
        return self.__dict__.__repr__()

    def __str__(self):
        return self.__dict__.__str__()


class ActionDict(DefaultDict):
    def __init__(self, actiondict, types={}, exp=None):
        """
        Special dictionary similar to DefaultDict except it used actiondict['Type'] to extracts the default_dict either
        from types, a dictionary of ActionTypes, or from exp, an Experiment.
        See DefaultDict for more information.
        Note: if both types and experiment are specified, types is used.

        :param actiondict: dict (following the Action dictionary format)
        :param types: dict of ActionTypes (which are dicts following the Action dictionary format) (optional, defaults to {})
        :param exp: object of type BaseExperiment (which should contain .properties['ActionTypes']) (optional, defaults to None)

        """
        self.logger = logging.getLogger(__name__)
        if types == {} and exp is not None:
            types = exp.properties['ActionTypes']

        if 'Type' in actiondict and actiondict['Type'] in types:
            actiontype = types[actiondict['Type']]
        else:
            actiontype = {}
        super().__init__(actiondict, actiontype)


class BaseExperiment:
    """ Example class with basic functions """

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

        self._nesting_indices = []
        self._nesting_parents = []
        self._measurement_name = 'data'

        self._auto_save_store = None


    def reset_measurement_flags(self):
        self.apply_pause = False   # used for temporarily interrupting a measurement
        self.apply_break = False   # used for a soft stop (e.g. stop after current loop iteration)
        self.apply_stop =  False   # used for a hard stop
        self.running_status = 0  # 0 for not running, 1 for paused, 2 for breaking, 3 for stopping

    # Decorator for stopping function:
    # If optional keyword argument force is set to True it will set self.apply_stop to True
    def check_stop(function):
        def wrapper_accepting_arguments(self, *args, force=False, **kwargs):
            if force: self.apply_stop = True
            if (self.apply_stop or force) and self.running_status < self._stopping:
                self.running_status = self._stopping
                function(self, *args, **kwargs)
                self.reset_measurement_flags()
                return True
            return False
        return wrapper_accepting_arguments

    # Decorator for breaking function:
    # First checks for "Stop", then calls the break function if self.apply_break is True
    def check_break(function):
        def wrapper_accepting_arguments(self, *args, force=False, **kwargs):
            # First check for "Stop" and return True if True
            if self.stop_measurement():
                return True
            # if force: self.apply_break = True
            if self.apply_break and self.running_status < self._stopping:
                self.running_status = self._breaking
                function(self, *args, **kwargs)
                # self.reset_measurement_flags()      # maybe this line should go out
                return True
            return False
        return wrapper_accepting_arguments

    # def check_stop(self, stop_method=None, *args, **kwargs):
    #     if self.apply_stop:
    #         self.running_status = self._stopping        # the first line
    #         if stop_method is None:
    #             self.logger.info('Stopping measurement. Optional: input alternative method to call when Stopping.')
    #         else:
    #             stop_method( *args, **kwargs)
    #         self.reset_measurement_flags()              # the last line
    #         return True
    #     return False

    # Decorator for pausing function
    # First checks for "Stop", then calls the pause function if self.apply_pause is True
    def check_pause(function):
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
                self.apply_pause = False
                return ret
            return False
        return wrapper_accepting_arguments


    # def check_pause(self, pause_method=None, stop_method=None, *args, **kwargs):
    #     if self.apply_pause:
    #         store_state = self.running_status
    #         self.running_status = self._pausing
    #         self.logger.info('Pausing Measurement. Optional: input alternative method to call when pausing (or override default pause_measurment).')
    #         if pause_method is None:
    #             self.pause_measurement(*args, **kwargs)
    #         else:
    #             pause_method(*args, **kwargs)
    #         self.running_status = store_state
    #         self.apply_pause = False

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
        # Do stuff
        self.reset_measurement_flags()
        self.logger.info('Measurement stopped')

    @check_break  # This decorator makes sure the method is only executed if self.apply_break is True
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


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
       self.finalize()


    # SMARTSCAN METHODS: <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


    def _validate_actionlist(self, actionlist, _complete=None, invalid_methods=0, invalid_names=0):
        """
        returns a corrected copy (does not modify input) and

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


        # # It method is specified in actiondict, test if the method exists.
        # # If not, set a flag to overwrite it with the one in actiontype
        # method_name = None
        # invalid_method = False
        # if '_method' in actiondict:
        #     method_name = actiondict['_method']
        #     if not hasattr(self, method_name):
        #         self.logger.warning("[in Action: '{}'] _method '{}' doesn't exist, (trying default)".format(action_name, method_name))
        #         invalid_method = True
        #
        # # copy default parameters from action if they don't exist in actiondict
        # if 'Type' not in actiondict:
        #     if invalid_method or method_name is None:
        #         self.logger.warning("error: [in '{}'] if no ActionType is specified, a valid _method is required".format(method_name))
        #         # NOTE TO SELF: WHY method_name ??????????????
        # else:
        #     actiontype = actiondict['Type']
        #     if actiontype not in self.actiontypes:
        #         self.logger.warning("[in action: '{}'] unknown ActionType: '{}'".format(action_name, actiontype))
        #     else:
        #         # Copy parameters that don't exist in actiondict. Except '_method'
        #         for key in self.actiontypes[actiontype]:
        #             if key not in actiondict and key is not '_method':
        #                 actiondict[key] = self.actiontypes[actiontype][key]
        #         # Special case for '_method'
        #         #                type_has_method = '_method' in self.actiontypes[actiontype]
        #         #                if not type_has_method:
        #         #                    if invalid_method or method_name is None:
        #         #                        print('error: [in {}] no method specified'.format(actiontype))
        #         #                else:
        #         #                    if
        #
        #         if invalid_method or method_name is None:
        #             if '_method' in self.actiontypes[actiontype]:
        #                 method_name = self.actiontypes[actiontype]['_method']
        #                 if hasattr(self, method_name):
        #                     if invalid_method:
        #                         self.logger.debug('_method {} in [Action: {}] replaced with default _method {} from [ActionType: {}] overwriting Actiondict method with default from Actiontype: {}'.format(
        #                                 actiondict['_method'], action_name, method_name, actiontype))
        #                     actiondict['_method'] = method_name
        #                     invalid_method = False
        #                 else:
        #                     self.logger.warning("error: [in ActionType: {}] default _method {} doesn't exist".format(actiontype,
        #                                                                                               method_name))
        #                     method_name = None
        #             else:
        #                 self.logger.warning('error: [in ActionType: {}] no _method specified'.format(actiontype))
        #
        # #                if invalid_method and '_method' in self.actiontypes[actiontype]:
        # #                    methodname =  self.actiontypes[actiontype]['_method']
        # #                    if hasattr(self, methodname):
        # #                        actiondict['_method'] = methodname
        # #                        print('debug: overwriting actiondict method with default from actiontype: {}'.format(methodname))
        # #                        invalid_method = False
        # #                    else:
        # #                        methodname = None
        # #                        print("error: default method from actiontype {} also doesn't exist".format(methodname))
        # #                        raise Exception('_method doe')
        #
        # if method_name is None:
        #     self.logger.warning('No valid _method specified')
        #
        # return actiondict

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
            self.perform_actionlist(self.properties['Measurements'][measurement_name])
        else:
            self.logger.error('Unknown measurement: {}'.format(measurement_name))


    # def perform_measurement(self, actionlist, parent_values = [], parents=[]):
    def perform_actionlist(self, actionlist, parents=[], save=True):
        """
        Used to perform a measuement based on the actionlist

        :param actionlist:
        :param parents:
        :param save:
        :return:
        """

        if parents == []:
            self._nesting_indices = []


        if len(parents) > len(self._nesting_indices):
            self._nesting_indices += [0]
        elif len(parents) == len(self._nesting_indices):
            if len(self._nesting_indices):
                self._nesting_indices[-1] += 1
        else:
            print('??????????????')



        # print('parents: ', parents, 'values: ', parent_values)
        # typically used on the whole list
        # In a an action that has nested Actions
        for actiondictionary in actionlist:
            actionname = actiondictionary['Name']
            if 'Type' in actiondictionary:
                if actiondictionary['Type'] in self.actiontypes:
                    actiondict = copy.deepcopy(self.actiontypes[actiondictionary['Type']])
                else:
                    actiondict = {}
                    self.logger.warning('Ignoring unknown actiontype {}'.format(actiondictionary['Type']))
            else:
                actiondict = {}

            # merge dictionaries (actiondictionary overrides actiontype)
            actiondict.update(actiondictionary)

            try:
                method = getattr(self, actiondict['_method'])
            except KeyError:
                raise KeyError('No _method found in actiondict or actiontype')
            except AttributeError:
                raise AttributeError('method {} not found in experiment object'.format(actiondict['_method']))


            # # if a method is specified it overrules the default from actiontype
            # if '_method' in actiondict:
            #     self.logger.debug('Using direct _method {} for {}'.format(actiondict['_method'], actionname))
            #     method = getattr(self, actiondict['_method'])
            # # get default values from actiontype, but don't overwrite existing values in actiondict
            # if 'Type' in actiondict:
            #     actiontype = actiondict['Type']
            #     if actiontype in self.actiontypes:
            #         for key, value in self.actiontypes[actiontype].items():
            #             if key not in actiondict:
            #                 actiondict[key] = value
            #     if '_method' not in actiondict:
            #         self.logger.warning(
            #             'error: actiontype {} does not specify method (and actiondict {} also does not specify method)'.format(
            #                 actiontype))

            # if '_method' in actiondict:
            #
            #     # if parents == []:
            #     #     self._nesting_indices = []  # reset it just to be sure
            #     # # if it's a new parent, add a zero index to
            #     # elif len(self._nesting_indices) < len(parents):
            #     #     self._nesting_indices += [0]
            #
            #
            #     # else:
            #     #     print("what's going on")
            #
            #     # repeat this here so actions outside   NO this only works outside all loops
            #     # if parents == []:
            #     #     self._nesting_indices = []

            self._nesting_parents = parents  # to make it available outside

            if '~nested' in actiondict:
                # without error checking for now:
                # else:
                #     indices += [0]  # append 0 to list  current_values
                nesting = lambda  : self.perform_actionlist(actiondict['~nested'], parents+[actionname])
            else:
                nesting = lambda *args: None        # a "do nothing" function
            # method = getattr(self, actiondict['_method'])
            # print('                                       ', actionname, '   parents: ', parents, '   indices: ',self._nesting_indices)
            method(actiondict, nesting)



            # if len(parents) == len(self._nesting_indices) and len(self._nesting_indices):
            #         self._nesting_indices[-1] += 1
            #
            # if len(self._nesting_indices) > len(parents):
            #     del self._nesting_indices[-1]

            # else:
            #     self.logger.warning('in {}: actiondict requires either method or an actiontype that contains a method'.format(
            #         actiondict['Name']))


        if len(parents) < len(self._nesting_indices):
            del self._nesting_indices[-1]


    def save(self, data, auto=True, **kwargs):
        indx = self._nesting_indices[:len(self._nesting_parents)]
        # print(indx)


    def create_saver(self, actiondict, nesting):
        version = actiondict['version'] if 'version' in actiondict else None
        folder = actiondict['folder'] if 'folder' in actiondict else os.path.join(hyperion.parent_path, 'data')
        filename = actiondict['filename'] if 'filename' in actiondict else self._measurement_name + '.h5'
        write_mode = actiondict['write_mode'] if 'write_mode' in actiondict else ['increment']
        self.saver = Saver(verion=version, default_folder=folder, default_filename=filename, write_mode=write_mode)
        self.saver.open_file()

       # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SMARTSCAN METHODS





    def load_config(self, filename):
        """Loads the configuration file to generate the properties of the Scan and Monitor.

        :param filename: Path to the filename. Defaults to Config/experiment.yml if not specified.
        :type filename: string
        """
        self.logger.debug('Loading configuration file: {}'.format(filename))

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
        """ Finalizing the experiment class """
        self.logger.info('Finalizing the experiment base class. Closing all the devices connected')
        for name in self.instruments_instances:
            self.logger.info('Finalizing connection with device: {}'.format(name))
            self.instruments_instances[name].finalize()
        self.logger.debug('Experiment object finalized.')

    def load_instrument(self, name):
        """ Loads an instrument given by name

        :param name: name of the instrument to load. It has to be specified in the config file under Instruments
        :type name: string
        :return: instance of instrument class and adds this instrument object to a dictionary.
        """
        self.logger.debug('Loading instrument: {}'.format(name))

        try:
            di = self.properties['Instruments'][name]
            module_name, class_name = di['instrument'].split('/')
            self.logger.debug('Module name: {}. Class name: {}'.format(module_name, class_name))
            MyClass = getattr(importlib.import_module(module_name), class_name)
            self.logger.debug('class: {}'.format(MyClass))
            self.logger.debug('settings used to create instrument: {}'.format(di))
            instance = MyClass(di)
            self.logger.debug('instance: {}'.format(instance))
            #self.instruments.append(name)
            self.instruments_instances[name] = instance
            return instance
        except KeyError:
            self.logger.warning('The name "{}" does not exist in the config file'.format(name))
            return None

        # for inst in self.properties['Instruments']:
        #     self.logger.debug('Current instrument information: {}'.format(self.properties['Instruments'][inst]))
        #
        #     if name == inst:
        #         module_name, class_name = self.properties['Instruments']['instrument'].split('/')
        #         self.logger.debug('Module name: {}. Class name: {}'.format(module_name, class_name))
        #         my_class = getattr(importlib.import_module(module_name), class_name)
        #         instance = my_class(inst)
        #         self.instruments.append(inst)
        #         self.instruments_instances.append(instance)
        #         return instance
        #
        # self.logger.warning('The name "{}" does not exist in the config file'.format(name))
        # return None

    def load_instruments(self):
        """"
        This method creates the instance of every instrument in the config file (under the key Instruments)
        and sets this instance in the self.instruments_instances (this is a dictionary).
        This way they are approachable via self.instruments_instances.items(),
        The option to set the instruments by hand is still possible, but not necessary because the pointer
        to the instrument 'lives' in the instruments_instances.

        The instruments in the self.instruments_instances are going to be finalized when  the exit happens,
        so if you load an instrument manualy and do not add it to this dictionary, you need to take care of
        the closing.

        """
        for instrument in self.properties['Instruments']:
            inst = self.load_instrument(instrument)  # this method from base_experiment adds intrument instance to self.instrument_instances dictionary
            if inst is None:
                self.logger.warning(" The instrument: {} is not connected to your computer".format(instrument))
            else:
                self.instruments_instances[instrument] = inst
                self.logger.debug('Object: {} has been loaded in '
                              'instrument_instances {}'.format(instrument, self.instruments_instances[instrument]))


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

