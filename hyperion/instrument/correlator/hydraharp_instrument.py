"""
====================
Hydraharp Instrument
====================

This is the instrument level of the correlator Hydraharp400 from Picoquant

"""
from hyperion import logging
import yaml           #for the configuration file
import os             #for playing with files in operation system
import time
from hyperion import root_dir, ur
import matplotlib.pyplot as plt
import numpy as np

from hyperion.instrument.base_instrument import BaseInstrument

class HydraInstrument(BaseInstrument):
    """
    A class for the Hydraharp instrument.

    :param settings: to parse the needed settings.
    :type settings: dict
    """
    def __init__(self, settings):
        """ init of the class"""
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)

        self.logger.info('1. welcome to the instrument level')
        self.logger.debug('Creating the instance of the controller')
        self.sync = 0
        self.count = 0
        self.hist = []
        self.initialize()

        self.stop = False
        self.hist_ended = False
        #self.remaining_time = 0*ur('s')
        self.time_passed = 0*ur('s')

    def initialize(self):
        """ Starts the connection to the device, calibrates it and configures based on the yml file.
        """        
        self.logger.info('Opening connection to correlator.')
        self.controller.calibrate()
        self.configurate()

    def configurate(self, filename = None):
        """ | Loads the yml configuration file of default instrument settings that probably nobody is going to change.
        | File in folder \instrument\correlator\HydrahaInstrument_config.yml.
        
        :param filename: the name of the configuration file
        :type filename: string
        """

        if filename is None:
            filename = os.path.join(root_dir,'instrument','correlator','HydraInstrument_config.yml')
      
        with open(filename, 'r') as f:
            d = yaml.safe_load(f)
    
        self.settings = d['settings']
        
        #put units after all things in config file
        for key in self.settings:
            self.settings[key] = ur(self.settings[key])

        self.logger.info('Status info:')
        self.logger.info('number of input channels: ' + str(self.controller.number_input_channels))
        
        self.controller.sync_divider(self.settings['sync_div'])
        self.controller.sync_CFD(self.settings['sync_disc'].m_as('mV'),self.settings['sync_zero'].m_as('mV'))#.m_as('mV'))
        self.controller.sync_offset(self.settings['sync_offset'].m_as('ps'))
        
        self.controller.input_CFD(0,self.settings['chan1_disc'].m_as('mV'),self.settings['chan1_zero'].m_as('mV'))
        self.controller.input_offset(0,self.settings['chan1_offset'].m_as('ps'))
        
        self.controller.input_CFD(1,self.settings['chan2_disc'].m_as('mV'),self.settings['chan2_zero'].m_as('mV'))
        self.controller.input_offset(1,self.settings['chan2_offset'].m_as('ps'))
        
        self.controller.histogram_offset(self.settings['hist_offset'].m_as('ps'))
        
    
    def sync_rate(self):
        """Asks the controller the rate of counts on the sync channel and adds units.

        :return: counts per second on the sync channel
        :rtype: pint quantity
        """
        self.sync = self.controller.sync_rate() * ur('cps')
        return self.sync

        
    def count_rate(self,channel):
        """ Asks the controller the rate of counts on the count channels and adds units.
        
        :param channel: count rate channel 0 or 1 (1 or 2 on device) connected to the photon counter
        :type channel: int
        
        :return: count rate that is read out in counts per second
        :rtype: pint quantity
        """
        self.count = self.controller.count_rate(channel) * ur('cps')
        return self.count

    def set_histogram(self,leng,res):
        """ | Clears the possible previous histogram, sets the histogram length and resolution.
        | *Has also to do with the binning and the length of the histogram.*
        | In the correlator software, the length is fixed to 2^16 and the resolution determines the binning and thus the time axis that is plot.
        
        :param leng: length of histogram
        :type leng: int
        
        :param res: resolution in the histogram in ps
        :type res: pint quantity        
        """
        self.controller.clear_histogram()
        self.controller.histogram_length = leng
        self.controller.resolution = res.m_as('ps')
        self.logger.debug('Set the parameters for taking a histogram')
    
    def make_histogram(self, integration_time, count_channel):
        """ | Does the histogram measurement, checking for the status, saving the histogram.
        | **You need to start the measurement and than you could collect the histogram.**
        | This communicates with the controller method start_measurement and than goes to the wait_till_finished method. 
        
        :param count_channel: number of channel that is correlated with the sync channel, 1 or 2
        :type count_channel: int

        :param integration_time: acquisition time of the histogram; **(please don't use the word time)**
        :type integration_time: pint quantity

        :return: array containing the histogram
        :rtype: array
        """
        #self.logger.info('Remaining time: ' + str(self.prepare_to_take_histogram(tijd)))
        #self.prepare_to_take_histogram(tijd)

        self.logger.debug('Start the histogram measurement')
        self.controller.start_measurement(int(integration_time.m_as('ms')))

        self.wait_till_finished(integration_time, count_channel)
        self.logger.debug('Time passed: ' + str(self.time_passed))

        self.hist = self.controller.histogram(int(count_channel), True)     #Last time, put the histogram memory to 0

        self.logger.debug('Collect the histogram after taking it.')

        self.hist_ended = False
        return self.hist

    def show_time_passed(self, integration_time, time_passed):
        self.time_passed = time_passed
        #print(self.time_passed)
        remaining_time = integration_time - time_passed
        return self.time_passed

    def wait_till_finished(self, integration_time, count_channel):
        """| This method should ask the device its status and keep asking until it's finished.
        | However, the remaining time is printed but not shown with the timer in the gui.
        | The loop breaks if self.stop is put to True, which could be done in a higher level with a thread.

        :param integration_time: integration time of histogram **(please don't use the word time)**
        :type integration_time: pint quantity

        :param count_channel: number of channel that is correlated with the sync channel, 1 or 2
        :type count_channel: int

        :return: remaining time in seconds
        :rtype: pint quantity

        """
        # ended = self.hist_ended
        #t = round(float(tijd.magnitude) / 20)

        t = 1       # in s
        total_time_passed = ur('0s')

        self.logger.debug('Ended?: ' + str(self.hist_ended))
        total_time_passed += t * ur('s')

        self.logger.debug('time passed: {}'.format(self.show_time_passed(integration_time, total_time_passed)))

        time.sleep(1)

        while self.hist_ended == False:
            self.hist_ended = self.controller.ctc_status
            self.logger.debug('Is the histogram finished? ' + str(self.hist_ended))

            total_time_passed += t * ur('s')
            #this line returns a pint quantity which tells the user how much time the program needs before it can collect the histogram
            self.logger.debug('time passed ' + str(total_time_passed))

            self.show_time_passed(integration_time, total_time_passed)
            self.logger.debug('time_passed value: {}'.format(self.time_passed))

            self.hist = self.controller.histogram(int(count_channel), False)        #Dont let the histogram memory be cleared
            time.sleep(t)

            if self.stop:
                self.logger.info('Stopping the histogram')
                self.stop = False
                break

        self.logger.debug('Time passed: ' + str(self.show_time_passed(integration_time, total_time_passed)))
        self.logger.debug('Ended? ' + str(self.hist_ended))

    def stop_histogram(self):
        """| This method stops taking the histogram, could be used in higher levels with a thread.
        """
        self.controller.stop_measurement()

    def finalize(self):
        """ This method is to close connection to the device."""
        self.logger.info('Closing connection to device.')
        self.controller.finalize()

if __name__ == "__main__":

    with HydraInstrument(settings = {'devidx':0, 'mode':'Histogram', 'clock':'Internal',
                                   'controller': 'hyperion.controller.picoquant.hydraharp/Hydraharp'}) as q:

        print('The sync rate is: ' , q.sync_rate())
        print('The count rate is: ' , q.count_rate(0))

        # use the hist
        q.set_histogram(leng = 65530, res =8.0 * ur('ps'))
        q.make_histogram(5*ur('s'), count_channel = 0)
        print('The histogram: ', q.hist)

        print('size histogram {}'.format(np.shape(q.hist)))

        plt.figure()
        plt.plot(q.hist)
        plt.show()
