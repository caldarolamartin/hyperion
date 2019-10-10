"""
====================
Hydraharp Instrument
====================

This is the instrument level of the correlator Hydraharp400 from Picoquant

"""
import logging
import yaml           #for the configuration file
import os             #for playing with files in operation system
import time
from hyperion import root_dir, ur
#sys.path.append('D:/TMDmaterials/')

from hyperion.instrument.base_instrument import BaseInstrument
ureg = ur

#from TMD.Controller.Hydraharp_controller import Hydraharp 
#from TMD import ureg, Unit_

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
        #self.initialize()

    def initialize(self):
        """ Starts the connection to the device, calibrates it and configurates based on the yml file
        """        
        self.logger.info('Opening connection to correlator.')
        self.controller.calibrate()
        self.configurate()

    def configurate(self, filename = None):
        """ | Loads the yml configuration file of default intrument settings that probably nobody is going to change
        | File in folder \instrument\correlator\HydrahaInstrument_config.yml
        
        :param filename: the name of the configuration file
        :type filename: string
        """

        if filename is None:
            filename = os.path.join(root_dir,'instrument','correlator','HydraInstrument_config.yml')
      
        with open(filename, 'r') as f:
            d = yaml.load(f, Loader=yaml.FullLoader)
    
        self.settings = d['settings']
        
        #put units after all things in config file
        for key in self.settings:
            self.settings[key] = ureg(self.settings[key])

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
        """Asks the controller the rate of counts on the sync channel and adds units

        :return: counts per second on the sync channel
        :rtype: pint quantity
        """
        self.sync = self.controller.sync_rate()*ureg('cps')
        return self.sync

        
    def count_rate(self,channel):
        """ Asks the controller the rate of counts on the count channels and adds units
        
        :param channel: count rate channel 1 or 2 connected to the photon counter
        :type channel: int
        
        :return: count rate that is read out in counts per second
        :rtype: pint quantity
        """
        self.count = self.controller.count_rate(channel)*ureg('cps')
        return self.count

    def set_histogram(self,leng,res):
        """ | Clears the possible previous histogram, sets the histogram length and resolution
        | *Has also to do with the binning and the length of the histogram*
        | In the correlator software, the length is fixed to 2^16 and the resolution determines the binning and thus the time axis that is plot
        
        :param leng: length of histogram
        :type leng: int
        
        :param res: resolution in the histogram in ps
        :type res: pint quantity        
        """
        self.controller.clear_histogram()
        self.controller.histogram_length = leng
        self.controller.resolution = res.m_as('ps')
        self.logger.debug('Set the parameters for taking a histogram')
    
    def make_histogram(self, tijd, count_channel):
        """ | Does the histogram measurement, checking for the status, saving the histogram
        | **It is not clear however whether you need to start measurement and than make the histogram**
        | The start measurement method of the controller is called in prepare_to_take_histogram
        
        :param count_channel: number of channel that is correlated with the sync channel, 1 or 2
        :type count_channel: int

        :param tijd: acquisition time of the histogram; **please don't use the English word**
        :type tijd: pint quantity

        :return: array containing the histogram
        """
        self.logger.info('Remaining time: ' + str(self.prepare_to_take_histogram(tijd)))
        self.hist = self.controller.histogram(int(count_channel))

        self.logger.debug('Make the actual histogram')
        return self.hist

    def prepare_to_take_histogram(self, tijd):
        """This communicates with the controller method start_measurement and then in theory should wait untill it is finished

        :param tijd: acquisition time of the histogram; **please don't use the English word**
        :type tijd: pint quantity

        :return: time that is left until the histogram is finished
        """
        self.logger.debug('Start the histogram measurement')

        self.controller.start_measurement(tijd.m_as('s'))
        return (self.wait_till_finished(tijd))

    def wait_till_finished(self, tijd):
        """| This method should ask the device its status and keep asking until it's finished
        | Doesn't work completely yet

        :param tijd: integration time of histogram in s **(please don't use the English word for tijd)**
        :type tijd: pint quantity

        :return: remaining time in seconds
        :rtype: pint quantity
        """
        ended = False
        t = round(float(tijd.magnitude) / 5)
        total_time_passed = ur('0s')
        while ended == False:
            ended = self.controller.ctc_status
            self.logger.debug('Is the histogram finished? ' +  str(ended))
            time.sleep(t)
            total_time_passed += t * ur('s')
            #this line returns a pint quantity which tells the user how much time the program needs before it can take the histogram
            self.logger.debug('Is the histogram finished? ' + str(ended))
            return (tijd - total_time_passed,ended)

    def finalize(self):
        """ this is to close connection to the device."""
        self.logger.info('Closing connection to device.')
        self.controller.finalize()

if __name__ == "__main__":
    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
        handlers=[logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576*5), backupCount=7),
                  logging.StreamHandler()])

    with HydraInstrument(settings = {'devidx':0, 'mode':'Histogram', 'clock':'Internal',
                                   'controller': 'hyperion.controller.picoquant.correlator/Hydraharp'}) as q:
        q.initialize()

        print('The sync rate is: ' , q.sync_rate())
        print('The count rate is: ' , q.count_rate(0))

        # use the hist
        q.set_histogram(leng = 65536,res = 8.0*ureg('ps'))
        hist = q.make_histogram(20*ur('s'), count_channel = 0)
        print('The histogram: ', hist)

