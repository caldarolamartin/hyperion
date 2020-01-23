"""
    ==================
    Example Experiment
    ==================

    Example Experiment that uses automated scanning and saving

"""
import os
from hyperion.core import logman
# You could also import the logging manager as logging if you don't want to change your line: logger = logging.getLogger(__name_)
# from hyperion.core import logman as logging
# from hyperion import logging    # equivalent to line above
from time import sleep
from hyperion.experiment.base_experiment import BaseExperiment
from hyperion.tools.array_tools import *
from datetime import datetime
import sys

class MyExperiment(BaseExperiment):
    """ Example class that performs automated scanning and saving """

    def __init__(self):
        super().__init__()                      # Mandatory line
        self.logger = logman.getLogger(__name__)
        self.display_name = 'Hyperion Example Experiment'  # Title of the experimental setup
        # # Test logging messages:
        # self.logger.info('Initializing the ExampleExperiment object.')
        # self.logger.critical('test critical')
        # self.logger.error('test error')
        # self.logger.warning('test warning')
        # self.logger.info('test info')
        # self.logger.debug('test debug')

    def example_action_method(self, actiondict, nesting=lambda:None):
        """
        In automated measuring, a measurement is broken up into small independent methods.
        The order of execution is determined in the config file

        An action method always needs to have the inputs actiondict and nesting.
        The actiondict will contain all the information necessary to perform the action.
        And nesting is a method that is passed by the automated scanning procedure of BaseExperiment.

        If your action might might given nested action (defined in the config), place nesting() at the place where you
        would want those actions to occur. If there are no nested actions this method does nothing.

        If you also want to use an action method directly (not through automated scanning), you could pass
        'lambda: None' as the nesting function, or you could specify the method as:
        'example_action_method(self, actiondict, nesting=lambda:None):'

        :param actiondict: Holds all the information need to perform the action
        :type actiondict: ActionDictionary
        :param nesting: method automatically passed by automated scanning procedure
        """
        pass

    def initialize_example_measurement_A(self, actiondict, nesting):
        self.logger.info('Measurement specific initialization. Could be without GUI')
        # Do stuff to prepare your measurement

        # You could add some meta data if you like.
        # Here I add the start time:
        self.datman.meta(dic={'start_time':str(datetime.now())})
        # Note that you need to open a datafile before you can add stuff to it. In automatic approach this is done by
        # adding the saver type action at the beginning of your measurement

        # By assigning the finalize method to self._finalize_measurement_method, that method will also be executed when
        # the measurement is interrupted (by Stop or Break button):
        self._finalize_measurement_method = self.finalize_example_measurement_A
        # nesting()  # initialize will probably not have nested actions, but it wouldn't hurt to add the function anyway.

    def finalize_example_measurement_A(self, actiondict, nesting):
        self.logger.info('Measurement specific finalization. Probably be without GUI')
        # Do stuff to finalize your measurement (e.g. switch off laser)

        # Add finish time and exit status to meta attributes
        self.datman.meta(dic={'finish_time':str(datetime.now()), 'exit_status':self.exit_status})
        # Close datafile
        self.datman.close()

    def image_with_filter(self, actiondict, nesting):
        self.logger.info('Initialize filters')
        # self.instruments_instances['Filters'].filter_a(action_dict['filter_a'])
        # self.instruments_instances['Filters'].filter_b(action_dict['filter_b'])
        self.logger.info('LED on')
        # self.instruments_instances['LED'].enable = True

        self.logger.info('Set camera exposure')
        # self.instruments_instances['Camera'].set_exposure(actiondict['exposure'])
        self.logger.info('Acquire image')
        self.camera_image = self.instruments_instances['Camera'].return_fake_2D_data()
        self.flag_new_camera_image = True

        self.logger.info('LED off')
        # self.instruments_instances['LED'].enable = False
        self.logger.info('Clear filters')
        # self.instruments_instances['Filters'].filter_a(False)
        # self.instruments_instances['Filters'].filter_b(False)

        # Because this is higher dimensional data, create dimensions:
        self.datman.dim('im_y', self.camera_image.shape[0])     # add extra axes if they don't exist yet
        self.datman.dim('im_x', self.camera_image.shape[1])
        self.datman.var(actiondict, self.camera_image, extra_dims=('im_y', 'im_x') )
        self.datman.meta(actiondict, {'exposuretime': actiondict['exposuretime'], 'filter_a': actiondict['filter_a'], 'filter_b': actiondict['filter_b'] })
        # self.datman.meta(actiondict, expo='5s')
        # self.datman.meta(actiondict, actiondict)


    def sweep_atto(self, actiondict, nesting):
        # print('sweep_atto: ',actiondict['Name'])
        # print(actiondict['Name'], '   indices: ', self._nesting_indices, '  nest parents: ', self._nesting_parents)
        arr, unit = array_from_settings_dict(actiondict)
        if actiondict['axis'] == 'y':
            # It is possible to define coordinates in one go, with an array
            self.datman.dim_coord(actiondict, arr, meta={'units': str(unit), **actiondict})
        # self.datman.meta(actiondict, actiondict)
        # self.datman.meta(actiondict['Name'], units=str(unit))
        for s in arr:
            if actiondict['axis'] == 'x':
                # It is possible to add values to a coordinate on the fly (and let it grow as the measurement progresses:
                self.datman.dim_coord(actiondict, s, meta={'units': str(unit)})
            # In this example, add a line when x value changes (outer loop)
            if actiondict['axis']=='x':
                print('---------------------')
            print(actiondict['axis'],' : ', s, unit)

            nesting()  # NOTICE THE nesting() FUNCTION HERE INSIDE THE LOOP

            # Inside loops (or in slow actions you could place this line.
            # It will check for apply_stop (stop button) and for apply_pause (pause button)
            # For short action_methods this is not necessary because those things are also automatically checked between
            #
            if self.pause_measurement(): return  # Use this line to check for stop and pause

        # # After a loop you could choose to check for 'break':
        # if self.break_measurement(): return  # Use this line to check for break
        # # However, if you're nesting this method in itself and you would only like to apply it after the outer loop
        # # you may want use a separate action method to check for the break. And specify it in the config.

    def check_break(self, actiondict, nesting):
        # You could place 'if self.break_measurement(): return' anywhere you like, but if you want to have more control
        # over when a break would be applied you could point to it in the config file:
        # - Name: break_after_scanning_sample_XY
        #   _method: check_break
        if self.break_measurement(): return

    def measure_power(self, actiondict, nesting):
        fake_voltage = self.instruments_instances['PhotoDiode'].return_fake_voltage_datapoint()
        unit = fake_voltage.u
        value = fake_voltage.m_as(unit)
        self.datman.var(actiondict, value, meta=actiondict, units=str(unit))
        nesting()

    def fake_spectrum(self, actiondict, nesting):
        fake_wav_nm = np.arange(500, 600.001, 5)
        self.fake_counts = self.instruments_instances['Spectrometer'].return_fake_1D_data(len(fake_wav_nm))
        self.flag_new_spectral_data = True
        self.datman.dim_coord('wav', fake_wav_nm, meta={'units': 'nm'})
        self.datman.var(actiondict, self.fake_counts, extra_dims=('wav'), meta=actiondict, units='counts')
        nesting()


if __name__ == '__main__':
    # ### To change the logging level:
    # logman.stream_level(logman.WARNING)
    # logman.file_level('INFO')
    # ### To change the stream logging layout:
    # logman.set_stream(compact=0.2, color_scheme='dim') # and other parameters
    # ### To change the logging file:
    # logman.set_file('example_experiment.log')

    test_with_gui = True

    # prepare folders and configfile:
    this_folder = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(this_folder, 'my_experiment.yml')

    with MyExperiment() as e:
        # Load config and instruments
        e.load_config(config_file)
        e.load_instruments()

        if not test_with_gui:
            ### Test without gui:
            e.perform_measurement('Example Measurement A')

        else:
            ### Test with gui:

            from PyQt5.QtWidgets import QApplication


            app = QApplication(sys.argv)  # required "placeholder" for gui

            # # Without plotting:
            # from hyperion.view.base_guis import AutoMeasurementGui
            # q = AutoMeasurementGui(e, 'Automatic Measurement Example')

            # With plotting
            # (This is a bit "hacky" because this is intended to be done from the ExpGui object)
            from gui.measurement_gui import MyMeasurementGuiWithPlotting
            from hyperion.tools.loading import get_class

            # Create a dict of visualization guis (normally this is done automatically by ExpGui class)
            plotting_dict = {}
            for vis_name, vis_dict in e.properties['VisualizationGuis'].items():
                if vis_name not in e.properties['Measurements']['Automatic Measurement Example']['visualization_guis']:
                    continue
                vis_cls = get_class(vis_dict['view'])
                plotargs = {}
                if 'plotargs' in vis_dict:
                    plotargs = vis_dict['plotargs']
                plotting_dict[vis_name] = vis_cls(**plotargs)

            q = MyMeasurementGuiWithPlotting(e, 'Automatic Measurement Example', parent=None, output_guis=plotting_dict)


            # # Introduce corruption in actionlist for testing:
            # del(e.properties['Measurements']['Example Measurement A'][0]['Name'])

            app.exec_()

    print('-----------------   DONE with the experiment   -----------------')

