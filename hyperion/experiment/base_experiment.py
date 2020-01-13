"""
    ===============
    Base Experiment
    ===============

    This is a base experiment class. The propose is put all the common methods needed for the experiment
    classes so they are shared and easily modified.

"""
import os
import yaml
import importlib
from hyperion.core import logman as logging
from hyperion.tools.saving_tools import save_metadata as save_meta


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
        self.filename = filename

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

    def save_metadata(self):
        """To save metadata in a yml file. It saves the input configuration file. """
        self.logger.info('Saving metadata into file: {}'.format(self.filename))
        save_meta(self.filename, self.properties)


if __name__ == '__main__':
    import hyperion
    logger = logging.getLogger(__name__)
    

    with BaseExperiment() as e:

        config_folder = os.path.join(hyperion.repository_path,'examples')
        name = 'example_experiment_config'
        config_file = os.path.join(config_folder, name)

        logger.info('Using the config file: {}.yml'.format(config_file))
        e.load_config(config_file + '.yml')
        # read properties just loaded
        logger.info('The config file has the dict: {}'.format(e.properties))

        e.save_metadata()

