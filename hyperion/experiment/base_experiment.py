"""
    ===============
    Base Experiment
    ===============

    This is a base experiment class. The propose is put all the common methods needed for the experiment
    classes so they are shared and easily modified.

"""
import os
import logging
import yaml
import importlib
from hyperion.tools.saving_tools import name_incrementer


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
        import copy
        local_actionlist = copy.deepcopy(actionlist)
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
        import copy
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

    def perform_measurement(self, actionlist):
        # typically used on the whole list
        # In a an action that has nested Actions
        for actiondict in actionlist:
            actionname = actiondict['Name']
            # if a method is specified it overrules the default from actiontype
            if '_method' in actiondict:
                self.logger.debug('Using direct _method {} for {}'.format(actiondict['_method'], actionname))
                method = getattr(self, actiondict['_method'])
            # get default values from actiontype, but don't overwrite existing values in actiondict
            if 'Type' in actiondict:
                actiontype = actiondict['Type']
                if actiontype in self.actiontypes:
                    for key, value in self.actiontypes[actiontype].items():
                        if key not in actiondict:
                            actiondict[key] = value
                if '_method' not in actiondict:
                    self.logger.warning(
                        'error: actiontype {} does not specify method (and actiondict {} also does not specify method)'.format(
                            actiontype))

            if '_method' in actiondict:

                if '~nested' in actiondict:
                    # without error checking for now:
                    nesting = lambda: self.perform_measurement(actiondict['~nested'])
                else:
                    nesting = lambda *args: None

                method = getattr(self, actiondict['_method'])
                method(actiondict, nesting)
            else:
                self.logger.warning('in {}: actiondict requires either method or a type that contains a method'.format(
                    actiondict['Name']))


    def image(self, actiondict, nesting):
        print('image: ',actiondict['Name'])
        nesting()

    def image_modified(self, actiondict, nesting):
        print('image: ',actiondict['Name'])
        nesting()

    def spectrum(self, actiondict, nesting):
        print('spectrum: ',actiondict['Name'])
        nesting()

    def spectrum_modified(self, actiondict, nesting):
        print('spectrum: ',actiondict['Name'])
        nesting()

    def histogram(self, actiondict, nesting):
        print('histogram: ',actiondict['Name'])
        nesting()

    def sweep_atto(self, actiondict, nesting):
        print('sweep_atto: ',actiondict['Name'])
        for s in range(3):
            print(actiondict['axis'],' : ', s)
            nesting()

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

    # this next two methods should be moved to tools
    def create_filename(self, file_path):
        """ creates the filename property in the class, so all the methods point to the same folder
        and save with the same name. The output does not include the extension but the input does.

        :param filename: config filename complete path
        :type filename: string (path)

        :return: filename
        :rtype: string

        """
        self.logger.debug('Input filename: {}'.format(file_path))
        i = 0
        ext = file_path[-4:]  # Get the file extension (it assumes is a dot and three letters)
        filename = file_path[:-4]
        self.root_path = os.path.split(filename)[0]

        while os.path.exists(file_path):
            file_path = '{}_{:03}{}'.format(filename, i, ext)
            i += 1

        self.filename = file_path[:-4]

        self.logger.debug('New filename: {}'.format(self.filename))
        return file_path

    def save_metadata(self):
        """ Saves the config file information with the same name as the data and extension .yml


        """
        self.create_filename(self.properties['config file'])

        self.logger.debug('Filename: {}'.format(self.filename))
        file_path = self.filename + '.yml'
        self.logger.debug('Complete file path: {}'.format(file_path))

        with open(file_path, 'w') as f:
            yaml.dump(self.properties, f, default_flow_style=False)

        self.logger.info('Metadata saved to {}'.format(file_path))

if __name__ == '__main__':
    import hyperion

    hyperion.set_logfile(__file__)                    # not required, but recommended
    # hyperion.file_logger.setLevel(logging.DEBUG)      # change logging level for the file (DEBUG, INFO, WARNING, ERROR)
    # hyperion.stream_logger.setLevel(logging.DEBUG)    # change logging level for the screen


    with BaseExperiment() as e:

        config_folder = 'D:/mcaldarola/Data/2019-04-17_hyperion/'  # this should be your path for the config file you use
        name = 'example_experiment_config'
        config_file = os.path.join(config_folder, name)

        logging.info('Using the config file: {}.yml'.format(config_file))
        e.load_config(config_file + '.yml')

        # read properties just loaded
        print('\n {} \n'.format(e.properties))

        e.properties['Scan']['start'] = '0.5V'

        print('\n {} \n'.format(e.properties))
