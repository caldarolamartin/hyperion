"""
    ==================
    Example Experiment
    ==================



    This is an example of an experiment class.
"""
import os
from hyperion.core import logman
# You could also import the logging manager as logging if you don't want to change your line: logger = logging.getLogger(__name_)
# from hyperion.core import logman as logging
# from hyperion import logging    # equivalent to line aboveimport numpy as np
import winsound
from time import sleep
# from hyperion import ur, root_dir
from hyperion.experiment.base_experiment import BaseExperiment
from hyperion.tools.array_tools import *
from datetime import datetime
import sys

class ExampleExperiment(BaseExperiment):
    """ Example class with basic functions """

    def __init__(self):
        """ initialize the class"""
        super().__init__()                      # Mandatory line
        self.logger = logman.getLogger(__name__)
        self.logger.info('Initializing the ExampleExperiment object.')
        self.logger.critical('test critical')
        self.logger.error('test error')
        self.logger.warning('test warning')
        self.logger.info('test info')
        self.logger.debug('test debug')

        #initialize dictionaries where instances of instruments and gui's can be found
        self.devices = {}
        self.properties = {}
        self.instruments_instances = {}
        self.view_instances = {}
        self.graph_view_instance = {}

        # scanning variables
        self.scan = {}
        self.stop_monitor = False
        self.scan['detectors'] = []
        self.scan['detector_units'] = []
        self.scan['number detectors'] = len(self.scan['detectors'])
        self.scan['running'] = False

        # data
        self.xdata = np.zeros(0)
        self.ydata = np.zeros(0)
        self.zdata = np.zeros(0)
        self.wavelength = []
        # to save the time
        self.tdata_h_scan = np.zeros(0)
        self.tdata_m_scan = np.zeros(0)
        self.tdata_s_scan = np.zeros(0)

        # to save the data of the scan
        self.xdata_scan = np.zeros(0)
        self.xdata_scan_v = np.zeros(0)
        self.ydata_scan = np.zeros(0)
        self.ydata_scan_error = np.zeros(0)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
       self.finalize()

    def make_sound(self):
        """ This methods makes a sound to call the attention of humans
            This method is by far the best method Martin has made, trust me, I am an expert
        """
        self.logger.debug('Making sound')
        winsound.Beep(3000, 800)  # (frequency in Hz, Duration in ms)
        winsound.Beep(1500, 200)
        winsound.Beep(3000, 500)
        sleep(0.1)
    def measurement(self):
        for i in range(1, 10):
            print(i)


    # def load_instruments(self):
    #     """"
    #     This method gets the instance of every instrument and sets this instance
    #     in the self.instruments_instances(this is a dictionary). This way they are approachable via self.instruments_instances.items(),
    #     The option to set the instruments by hand is still possible, but not necessary because the pointer
    #     to the instrument 'lives' in the instruments_instances.
    #     """
    #
    #     for instrument in self.properties['Instruments']:
    #         try:
    #             self.instruments_instances[instrument] = self.load_instrument(instrument)  # this method from base_experiment adds intrument instance to self.instrument_instances dictionary
    #             self.logger.debug('Class: '+instrument+" has been loaded in instrument_instances {}".format(self.instruments_instances[instrument]))
    #         except Exception:
    #             self.logger.warning("The instrument: "+str(instrument)+" is not connected to your computer")
    #             self.instruments_instances[instrument] = None
    #     # self.instruments_instances["vwp"] = self.load_instrument('VariableWaveplate')
    #     # self.logger.debug('Class vwp: {}'.format(self.vwp))
    #     # self.instruments_instances["example_instrument"] = self.load_instrument('ExampleInstrument')
    #     # self.logger.debug('Class example_instrument: {}'.format(self.example_instrument))

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    def image(self, actiondict, nesting):
        # print('performing action of Name {} with exposuretime {}'.format(actiondict['Name'],actiondict['exposuretime']))
        print(actiondict['Name'], '   indices: ',self._nesting_indices, '  nest parents: ', self._nesting_parents)
        self.save(0)
        # self._data.auto(data, actiondict)
        nesting()       # either takes care of nested actions or checks for pause state
        # data = np.array([[0,1],[2,3]])
        # return data

    def image_modified(self, actiondict, nesting):
        #print('image: ',actiondict['Name'])
        print(actiondict['Name'], '   indices: ',self._nesting_indices, '  nest parents: ', self._nesting_parents)
        self.save(0)
        nesting()

    def spectrum(self, actiondict, nesting):
        # print('spectrum: ',actiondict['Name'])
        print(actiondict['Name'], '   indices: ',self._nesting_indices, '  nest parents: ', self._nesting_parents)
        self.save(0)
        nesting()

    def spectrum_modified(self, actiondict, nesting):
        # print('spectrum: ',actiondict['Name'])
        print(actiondict['Name'], '   indices: ',self._nesting_indices, '  nest parents: ', self._nesting_parents)

        self.save(0)
        nesting()

    def histogram(self, actiondict, nesting):
        # print('histogram: ',actiondict['Name'])
        print(actiondict['Name'], '   indices: ',self._nesting_indices, '  nest parents: ', self._nesting_parents)
        self.save(0)
        #store_data
        nesting()



    def insideXafterY(self, actiondict, nesting):
        print(actiondict['Name'], '   indices: ',self._nesting_indices, '  nest parents: ', self._nesting_parents)
        self.save(0)

    def initialize_example_measurement_A(self, actiondict, nesting):
        self.logger.info('Measurement specific initialization. Could be without GUI')
        # Open datafile with data manager (datman):
        self.datman.open_file('test.nc')
        self.datman.meta(dic={'start_time':str(datetime.now())})
        # # test
        # self.datman.meta(dic=self._saving_meta)

        # self.datman.meta(measurement_name = 'initialize_example_measurement_A')
        # By assigning the finalize method to self._finalize_measurement_method, that method will also be executed when
        # the Stop button is pressed:
        self._finalize_measurement_method = self.finalize_example_measurement_A
        # nesting()

    def finalize_example_measurement_A(self, actiondict, nesting):
        self.logger.info('Measurement specific finalization. Probably be without GUI')
        # Do stuff to finalize your measurement (e.g. switch off laser)

        # Close datafile
        # self.datman.meta(dic={'finish_time': str(datetime.now())})
        self.datman.meta(None, None, False, finish_time=str(datetime.now()))
        self.datman.meta(None, None, False, finish_time=str(datetime.now()))
        # self.datman.meta(dic={'finish_time': str(datetime.now())})
        self.datman.meta(dic={'finish_time':str(datetime.now())})
        self.datman.close()
        nesting()

    def image_with_filter(self, actiondict, nesting):
        self.logger.info('Initialize filters')
        # self.instruments_instances['Filters'].filter_a(action_dict['filter_a'])
        # self.instruments_instances['Filters'].filter_b(action_dict['filter_b'])
        self.logger.info('LED on')
        # self.instruments_instances['LED'].enable = True

        self.logger.info('Set camera exposure')
        # self.instruments_instances['Camera'].set_exposure(actiondict['exposure'])
        self.logger.info('Acquire image')
        # camera_image = self.instruments_instances['Camera'].acquire_image()

        self.logger.info('LED off')
        # self.instruments_instances['LED'].enable = False
        self.logger.info('Clear filters')
        # self.instruments_instances['Filters'].filter_a(False)
        # self.instruments_instances['Filters'].filter_b(False)

        fake_data = np.random.random((20,60))
        # Because this is higher dimensional data, create dimensions:
        self.datman.dim('im_y', fake_data.shape[0])     # add extra axes if they don't exist yet
        self.datman.dim('im_x', fake_data.shape[1])
        self.datman.var(actiondict, fake_data, extra_dims=('im_y', 'im_x') )
        self.datman.meta(actiondict, {'exposuretime': actiondict['exposuretime'], 'filter_a': actiondict['filter_a'], 'filter_b': actiondict['filter_b'] })

    def sweep_atto(self, actiondict, nesting):
        # print('sweep_atto: ',actiondict['Name'])
        # print(actiondict['Name'], '   indices: ', self._nesting_indices, '  nest parents: ', self._nesting_parents)
        arr, unit = array_from_settings_dict(actiondict)
        self.datman.dim_coord(actiondict, arr, meta={'units': str(unit), **actiondict})
        # self.datman.meta(actiondict, actiondict)
        # self.datman.meta(actiondict['Name'], units=str(unit))
        for s in arr:
            print(actiondict['axis'],' : ', s)
            #store_coord()

            nesting()
            self.check_pause()

    def measure_power(self, actiondict, nesting):
        fake_data = np.random.random()
        self.datman.var(actiondict, fake_data, meta=actiondict, unit='mW')
        nesting()

    def fake_spectrum(self, actiondict, nesting):
        fake_wav_nm = np.arange(500, 601, 10)
        fake_data = np.random.random(11)
        self.datman.dim_coord('wav', fake_wav_nm, meta={'unit': 'nm'})
        self.datman.var(actiondict, fake_data, extra_dims=('wav'), meta=actiondict, unit='counts')



if __name__ == '__main__':
    # ### To change the logging level:
    # logman.stream_level(logman.WARNING)
    # logman.file_level('INFO')
    # ### To change the stream logging layout:
    # logman.set_stream(compact=0.2, color_scheme='dim') # and other parameters
    # ### To change the logging file:
    # logman.set_file('example_experiment.log')

    # with ExampleExperiment() as e:
    #
    #     name = 'second_example_experiment_config_'
    #     config_folder = os.path.dirname(os.path.abspath(__file__))
    #     config_file = os.path.join(config_folder, name)
    #
    #     print('Using the config file: {}.yml'.format(config_file))
    #     e.load_config(config_file + '.yml')
    #
    #     # read properties just loaded
    #     #print('\n {} \n'.format(e.properties))
    #
    #     #  remember you can change these values directly here
    #     #e.properties['Scan']['start'] = '0.5V'
    #
    #
    #     # # Initialize devices
    #     print('\n-------------- LOADING DEVICES ----------------\n')
    #     e.load_instruments()
    #     print(e.instruments_instances.keys())
    #     print('-------------- DONE LOADING DEVICES ----------------')
    #     #
    #
    #     # save metadata
    #
    #     #e.save_scan_metadata()
    #     #e.save_scan_metadata()
    #     #e.VariableWaveplate.set_analog_value(1,2.25*ur('volt'))
    #     # perform scan
    #     # e.set_scan()
    #     # e.do_scan()
    #     # e.make_sound()
    #
    #     # # save data
    #     # e.save_scan_data()
    #
    #
    # print('--------------------- DONE with the experiment')

    e = ExampleExperiment()

    name = 'my_experiment.yml'
    # config_folder = os.path.dirname(os.path.abspath(__file__))
    # config_file = os.path.join(config_folder, name)
    config_file = name

    print('Using the config file: {}'.format(config_file))
    e.load_config(config_file)

    # # read properties just loaded
    # print('\n {} \n'.format(e.properties))
    #
    # #  remember you can change these values directly here
    # #e.properties['Scan']['start'] = '0.5V'
    #
    #
    # # # Initialize devices
    # print('\n-------------- LOADING DEVICES ----------------\n')
    e.load_instruments()
    # print(e.instruments_instances.keys())
    # print('-------------- DONE LOADING DEVICES ----------------')
    # #
    #
    # #print(e._validate_actionlist(e.properties['Measurements']['Measurement A']))
    # e.swap_actions(e.properties['Measurements']['Measurement A'], 'atto X','atto Y')
    #
    e.perform_measurement('Example Measurement A')
    # save metadata
    # print(yaml.dump(e.properties['Measurements']['Measurement A']))


    print('--------------------- DONE with the experiment')


######### testing gui stuff

    # from PyQt5.QtWidgets import QApplication
    # from hyperion.view.base_guis import BaseMeasurementGui, ModifyMeasurement
    #
    # app = QApplication(sys.argv)
    # # q = ModifyMeasurement(e,'Measurement A')
    # # q.show()
    #
    # ## Introduce corruption in actionlist for testing:
    # # del(e.properties['Measurements']['Measurement A'][0]['Name'])
    # # del (e.properties['Measurements']['Measurement A'][0])
    #
    # # q = BaseMeasurementGui(e, 'Example Measurement A')
    # q = BaseMeasurementGui(e, 'Example Measurement A')
    # app.exec_()


