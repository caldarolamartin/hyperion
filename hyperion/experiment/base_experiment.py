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
import logging
import yaml
import importlib
import hyperion
from hyperion.tools.saving_tools import name_incrementer
from hyperion.tools.saver import Saver
import copy     # used in action validation methods
import h5py
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



class BaseExperiment():
    """ Example class with basic functions """

    def __init__(self):
        """ initialize the class"""
        self.logger = logging.getLogger(__name__)
        self.logger.info('Initializing the BaseExperiment class.')

        self.properties = {}    # this is to load the config yaml file and store all the
                                # settings for the experiement. see load config

        # this variable is to keep track of all the instruments that are connected and
        # properly close connections with them at the end
        self.instruments_instances = {}
        # these next variables are for the master gui.
        self.view_instances = {}
        self.graph_view_instance = {}

        self.filename = ''

        self._nesting_indices = []
        self._nesting_parents = []
        self._measurement_name = 'data'

        self._auto_save_store = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
       self.finalize()


    # SMARTSCAN METHODS: <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


    def _validate_actionlist(self, actionlist, _complete=None):
        """
        returns a corrected copy (does not modify input)

        _validate_actionlist(complete_actionlist)
        _complete is used for recursion
        """
        local_actionlist = copy.deepcopy(actionlist)        # this is required for a new copy (without it the original gets modified)
        # recursive function
        if _complete is None:
            _complete = local_actionlist
        # Note: approach with 'for act in local_actionlist' would not change the list
        for indx in range(len(local_actionlist) - 1, -1, -1):
            local_actionlist[indx] = self._validate_actiondict(local_actionlist[indx], _complete)
            #            print(act)
            #            print(local_actionlist)
            if '~nested' in local_actionlist[indx]:
                local_actionlist[indx]['~nested'] = self._validate_actionlist(local_actionlist[indx]['~nested'], _complete)
        return local_actionlist

    def _validate_actiondict(self, actiondictionary, complete_actionlist):
        """
        returns new corrected dictionary (does not alter the dictionary )
        """
        actiondict = copy.deepcopy(actiondictionary)
        # auto gerate a name if it doesn't exist
        all_names, unnamed = self.all_action_names(complete_actionlist)
        if 'Name' not in actiondict:
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
            actiondict['Name'] = name_incrementer(action_name, all_names, ' ')
            self.logger.warning("Duplicate Action Name. Changed '{}' to '{}'".format(action_name, actiondict['Name']))
        action_name = actiondict['Name']

        # It method is specified in actiondict, test if the method exists.
        # If not, set a flag to overwrite it with the one in actiontype
        method_name = None
        invalid_method = False
        if '_method' in actiondict:
            method_name = actiondict['_method']
            if not hasattr(self, method_name):
                self.logger.warning("[in Action: '{}'] _method '{}' doesn't exist, (trying default)".format(action_name, method_name))
                invalid_method = True

        # copy default parameters from action if they don't exist in actiondict
        if 'Type' not in actiondict:
            if invalid_method or method_name is None:
                self.logger.warning("error: [in '{}'] if no ActionType is specified, a valid _method is required".format(method_name))
                # NOTE TO SELF: WHY method_name ??????????????
        else:
            actiontype = actiondict['Type']
            if actiontype not in self.actiontypes:
                self.logger.warning("[in action: '{}'] unknown ActionType: '{}'".format(action_name, actiontype))
            else:
                # Copy parameters that don't exist in actiondict. Except '_method'
                for key in self.actiontypes[actiontype]:
                    if key not in actiondict and key is not '_method':
                        actiondict[key] = self.actiontypes[actiontype][key]
                # Special case for '_method'
                #                type_has_method = '_method' in self.actiontypes[actiontype]
                #                if not type_has_method:
                #                    if invalid_method or method_name is None:
                #                        print('error: [in {}] no method specified'.format(actiontype))
                #                else:
                #                    if

                if invalid_method or method_name is None:
                    if '_method' in self.actiontypes[actiontype]:
                        method_name = self.actiontypes[actiontype]['_method']
                        if hasattr(self, method_name):
                            if invalid_method:
                                self.logger.debug('_method {} in [Action: {}] replaced with default _method {} from [ActionType: {}] overwriting Actiondict method with default from Actiontype: {}'.format(
                                        actiondict['_method'], action_name, method_name, actiontype))
                            actiondict['_method'] = method_name
                            invalid_method = False
                        else:
                            self.logger.warning("error: [in ActionType: {}] default _method {} doesn't exist".format(actiontype,
                                                                                                      method_name))
                            method_name = None
                    else:
                        self.logger.warning('error: [in ActionType: {}] no _method specified'.format(actiontype))

        #                if invalid_method and '_method' in self.actiontypes[actiontype]:
        #                    methodname =  self.actiontypes[actiontype]['_method']
        #                    if hasattr(self, methodname):
        #                        actiondict['_method'] = methodname
        #                        print('debug: overwriting actiondict method with default from actiontype: {}'.format(methodname))
        #                        invalid_method = False
        #                    else:
        #                        methodname = None
        #                        print("error: default method from actiontype {} also doesn't exist".format(methodname))
        #                        raise Exception('_method doe')

        if method_name is None:
            self.logger.warning('No valid _method specified')

        return actiondict

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
        print(indx)


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

    # Note: this logging section will be updated when merging with the new logging
    import hyperion
    hyperion.set_logfile(__file__)                    # not required, but recommended


    logger = logging.getLogger(__name__)

    logger.warning("For testing it's better to run an example experiment from the examples folder.")

    # print('')
    # print("WARNING: Base experiment is not intended to be run directly.")
    # print("         For testing it's better to run an example experiment from the examples folder.")
    # print('')

    with BaseExperiment() as e:

        from hyperion import repository_path
        config_file = os.path.join(repository_path, 'examples', 'example_experiment_config.yml')
        logger.info('Using the config file: {}.yml'.format(config_file))
        e.load_config(config_file)

        # read properties just loaded
        logger.info('\n {} \n'.format(e.properties))

