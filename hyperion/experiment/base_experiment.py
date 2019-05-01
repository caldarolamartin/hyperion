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


class BaseExperiment():
    """ Example class with basic functions """

    def __init__(self):
        """ initialize the class"""

        self.logger = logging.getLogger(__name__)
        self.logger.info('Initializing the BaseExperiment class.')
        self.properties = {}
        self.instruments= []
        self.instruments_instances = []

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

        if 'Scan' in d:
            self.scan['properties'] = d['Scan']

    def finalize(self):
        """ Finalizing the experiment class """
        self.logger.info('Finalizing the experiment base class')
        for inst in self.instruments_instances:
            inst.finalize()



    def load_instrument(self, name):
        """ Loads instrument

        :param name: name of the instrument to load
        :type name: string
        """
        self.logger.debug('Loading instrument: {}'.format(name))
        for inst in self.properties['Instruments']:
            self.logger.debug('instrument name: {}'.format(inst))

            if name in inst:
                module_name, class_name = inst[name]['instrument'].split('/')
                self.logger.debug('Module name: {}. Class name: {}'.format(module_name, class_name))
                my_class = getattr(importlib.import_module(module_name), class_name)
                instance = my_class(inst[name])
                self.instruments.append(inst)
                self.instruments_instances.append(instance)
                return instance

        self.logger.warning('The name "{}" does not exist in the config file'.format(name))
        return None

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

    def save_scan_metadata(self):
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
    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576 * 5), backupCount=7),
                            logging.StreamHandler()])

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
