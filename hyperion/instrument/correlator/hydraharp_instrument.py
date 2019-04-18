"""
================
Hydraharp Instrument
================

This is the instrument level of the correlator Hydraharp400 from Picoquant

"""

import logging
import yaml           #for the configuration file
import os             #for playing with files in operation system
import sys
import time
#sys.path.append('D:/TMDmaterials/')

from hyperion.instrument.base_instrument import BaseInstrument
from hyperion import ur
ureg = ur

#from TMD.Controller.Hydraharp_controller import Hydraharp 
#from TMD import ureg, Unit_

#time = ureg('1s')
#print(time)
#time = Unit_(1,'s')
#print(time)

class HydraInstrument(BaseInstrument):  
    def __init__(self, settings = {'controller': 'hyperion.controller.picoquant.hydraharp/Hydraharp'}):
        """ init of the class"""
        self.logger = logging.getLogger(__name__)
        self.logger.info('1. welcome to the instrument level')
        self.logger.debug('Creating the instance of the controller')
        self.controller_class = self.load_controller(settings['controller'])
        self.controller = self.controller_class()
        self.sync = 0
        self.count = 0
        self.hist = []
        #maybe add the initialize here
        #self.initialize()

    def initialize(self):
        """ Starts the connection to the device
        """        
        self.logger.info('Opening connection to hydraharp.')
        self.controller.initialize()
        self.controller.calibrate()
        self.configurate()
        #contains both initialize and calibrate


    def configurate(self, filename = None):
        """ Loads the yml configuration file of default intrument settings that probably nobody is going to change
        File in folder \instrument\correlator\HydrahaInstrument_config.yml
        
        :param filename: the name of the configuration file
        :type filename: string
        
        """

        if filename is None:
            filename = os.path.join(root_dir,'instrument','correlator','HydraInstrument_config.yml')
      
        with open(filename, 'r') as f:
            d = yaml.load(f)
    
        self.settings = d['settings']
        
        #put units after all things in config file
        for key in self.settings:
            self.settings[key] = ureg(self.settings[key])
            
        print('Status info:')
        print('number of input channels: ' + str(self.controller.number_input_channels))
        
        self.controller.sync_divider(self.settings['sync_div'])
        self.controller.sync_CFD(self.settings['sync_disc'].m_as('mV'),self.settings['sync_zero'].m_as('mV'))#.m_as('mV'))
        self.controller.sync_offset(self.settings['sync_offset'].m_as('ps'))
        
        self.controller.input_CFD(0,self.settings['chan1_disc'].m_as('mV'),self.settings['chan1_zero'].m_as('mV'))
        self.controller.input_offset(0,self.settings['chan1_offset'].m_as('ps'))
        
        self.controller.input_CFD(1,self.settings['chan2_disc'].m_as('mV'),self.settings['chan2_zero'].m_as('mV'))
        self.controller.input_offset(1,self.settings['chan2_offset'].m_as('ps'))
        
        self.controller.histogram_offset(self.settings['hist_offset'].m_as('ps'))
        
    
    def sync_rate(self):
        """ 
        
        """
        self.sync = self.controller.sync_rate()*ureg('cps')
        return self.sync
        #basically the same as the controller, now adding units maybe?
        
    def count_rate(self,channel):
        self.count = self.controller.count_rate(channel)*ureg('cps')
        return self.count
        
        #basically the same as the controller, now adding units maybe?
    
    def set_histogram(self,leng,res):
        self.controller.clear_histogram()
        self.controller.histogram_length = leng
        self.controller.resolution = res.m_as('ps')
    
    def make_histogram(self,tijd,count_channel):
        self.controller.start_measurement(tijd.m_as('s'))
        
        ended = False
        t = round(tijd.m_as('s')/10)
        
        while ended == False:
            ended = self.controller.ctc_status
            time.sleep(t)
            print(ended)
                
        self.hist = self.controller.histogram(count_channel)
        return self.hist
    
    
    def finalize(self):
        """ this is to close connection to the device."""
        self.logger.info('Closing connection to device.')
        self.controller.close_device()
        #close the device


if __name__ == "__main__":
    
    q = HydraInstrument()
    
    q.initialize()
    
    q.configurate()
    
    print('The sync rate is: ' , q.sync_rate())
    
    print('The count rate is: ' , q.count_rate(0))
    
    q.set_histogram(leng = 65536,res = 8.0*ureg('ps'))

    hist = q.make_histogram(tijd = 5*ureg('s'), count_channel = 0)
    
    print(hist)
    
     
    q.finalize()
