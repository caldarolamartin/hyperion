"""
=======================
Hydraharp400 controller
=======================
Taken on Fri Nov 10 15:36:48 2017 from Colin Brosseau

changed by Irina Komen

"""
import numpy as np
import ctypes
from hyperion import root_dir
from hyperion.controller.base_controller import BaseController
import os
import warnings
import sys
from enum import Enum
import time
import yaml
import logging

c_int_p = ctypes.POINTER(ctypes.c_int)

class Hydraharp(BaseController):
    """ Hydraharp 400 controller """

    def __init__(self, devidx=0, mode='Histogram', clock='Internal'):
        """
        Initialise communication with hydraharp400 device
      
        :param devidx: index of the device
        :type devidx: int
        
        :param mode: operation mode, can be: 'Histogram'(default), 'T2','T3','Continuous'
        :type mode: string
        
        :param clock: source of the clock, can be: 'External'(default), 'Internal'
        :type clock: string
               
        """
        self.logger = logging.getLogger(__name__)
        self._is_initialized = False
        self.logger.info('0. hello, this is the hydraharp (controller) speaking')
        self.settings = {}
        self.load_config()
        #print(self.settings)
      
        if sys.platform == 'linux':
            try: 
                self.hhlib = ctypes.CDLL("hhlib.so")
            except OSError:
                print("Import local library")
                self.hhlib = ctypes.CDLL("./hhlib.so")
        elif sys.platform == 'win32':
            try: 
                self.hhlib = ctypes.WinDLL("hhlib.dll")
            except OSError:
                print("Import local library")
                self.hhlib = ctypes.WinDLL("./hhlib.dll")
        else:
            raise NotImplementedError("Not (yet) implemented on your system ({}).".format(sys.platform))
        assert devidx in range(self.settings['MAXDEVNUM']), "devidx should be a int in range 0 ... 8."
        self.__devidx = devidx  # index of device DO NOT MODIFY THAT FROM OUTSIDE
        self.error_code = 0  # current error code
        self._histoLen = 65536  # default histogram length = 65536
        assert self.library_version is not self.settings['LIB_VERSION'], "Current code (version {}) may not be compatible with system library (version {})".format(LIB_VERSION, self.library_version)
        self._open_device()  # initialize communication
        self.initialize(mode=mode, clock=clock)  # initialise the instrument
        self.calibrate()  # calibrate it
        self.histogram_length = self._histoLen
        self._binning(0)  # default binning to 0
        self._base_resolution = self.resolution  # base resolution of the device
     
    def load_config(self, filename = None):
        """ Loads the yml configuration file of default intrument settings that probably nobody is going to change
        File in folder \controller\picoquant\Hydraharp_controller.yml
        
        :param filename: the name of the configuration file
        :type filename: string
        
        """
        if filename is None:
            filename = os.path.join(root_dir,'controller','picoquant','Hydraharp_config.yml')
      
        with open(filename, 'r') as f:
            d = yaml.load(f)
    
        self.settings = d['settings']
       
    @property     
    def library_version(self):
        """
        Version of the library
        """
        func = self.hhlib.HH_GetLibraryVersion
        func.argtypes = [ctypes.c_char_p]
        func.restype = ctypes.c_int
        data = ctypes.create_string_buffer(8)   
        self.error_code = func(data)
        if self.error_code == 0:
           return data.value.decode('utf-8')
        else:
           warnings.warn(self.error_string)
   
    def _open_device(self):
        """
        Initialise the communication with the device
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        func = self.hhlib.HH_OpenDevice
        func.argtypes = [ctypes.c_int, ctypes.c_char_p]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.create_string_buffer(8)   
        self.error_code = func(data, data2)
        if self.error_code == 0:
           return data2.value
        else:
            warnings.warn(self.error_string)
      
    @property
    def error_string(self):
        """
        Error messages
        """
        func = self.hhlib.HH_GetErrorString
        func.argtypes = [ctypes.c_char_p, ctypes.c_int]
        func.restype = ctypes.c_int
        data = ctypes.create_string_buffer(40)   
        data2 = ctypes.c_int(self.error_code)
        self.error_code = func(data, data2)
        # error handling
        # what happens if we have an eror in an error ?
        return data.value.decode('utf-8')
   
    def initialize(self, mode='Histogram', clock='Internal'):
        """
        Initialise the device
        
        :param devidx: index of the device
        :type devidx: int
        
        :param mode: operation mode, can be: 'Histogram'(default), 'T2','T3','Continuous'
        :type mode: string
        
        :param clock: source of the clock, can be: 'External'(default), 'Internal'
        :type clock: string
        """
        self.logger.info('Opening connection to device.')
        self._is_initialized = True     # this is to prevent you to close the device connection if you
                                        # have not initialized it inside a with statement        
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        assert mode in Measurement_mode._member_names_
        assert clock in Reference_clock._member_names_
        func = self.hhlib.HH_Initialize
        func.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.c_int(Measurement_mode[mode].value)
        data3 = ctypes.c_int(Reference_clock[clock].value)
        self.error_code = func(data, data2, data3)
        if self.error_code is not 0:
            warnings.warn(self.error_string)

    @property
    def hardware_info(self):
        """ Information about the device  """
        # =============================================================================
        #                 model, partno, version = hardware_info
        #
        #         model
        #              Model name of the device
        #
        #              partno
        #              Serial number (?) of the device
        #
        #         version
        #              Hardware version (?) of the device
        # =============================================================================
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        func = self.hhlib.HH_GetHardwareInfo
        func.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.create_string_buffer(16)   
        data3 = ctypes.create_string_buffer(8)   
        data4 = ctypes.create_string_buffer(8)   
        self.error_code = func(data, data2, data3, data4)
        if self.error_code == 0:
            return data2.value, data3.value, data4.value
        else:
            warnings.warn(self.error_string)

    @property
    def number_input_channels(self):
        """
        Number of installed input channels
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        func = self.hhlib.HH_GetNumOfInputChannels
        func.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.c_int()
        self.error_code = func(data, data2)
        if self.error_code == 0:
            return data2.value
        else:
            warnings.warn(self.error_string)

    def calibrate(self):
        """
        Calibrate the device
        
        :param devidx: Index of the device
        :type devidx: int
             
                   
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        func = self.hhlib.HH_Calibrate
        func.argtypes = [ctypes.c_int]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        self.error_code = func(data)
        if self.error_code is not 0:
            warnings.warn(self.error_string)
   
   
    def sync_divider(self, divider=1):
        """
        Divider of the sync
        
        sync_divider(divider)
        
        The sync divider must be used to keep the effective sync rate at values ≤ 12.5 MHz. It should only be used with sync sources
        of stable period. Using a larger divider than strictly necessary does not do great harm but it may result in slightly larger timing
        jitter. The readings obtained with HH_GetCountRate are internally corrected for the divider setting and deliver the external
        (undivided) rate. The sync divider should not be changed while a measurement is running.
        
        devidx
             Positive integer  (default 0)
             
             Index of the device      
             
        divider
            1, 2, 4, 8 or 16
         
        Sync rate divider
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        assert divider in 2**np.arange(np.log2(self.settings['SYNCDIVMIN']), np.log2(self.settings['SYNCDIVMAX'])+1), "Invalid value for SetSyncDiv"
        func = self.hhlib.HH_SetSyncDiv
        func.argtypes = [ctypes.c_int, ctypes.c_int]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.c_int(divider)
        self.error_code = func(data, data2)
        if self.error_code is not 0:
            warnings.warn(self.error_string)
      
    def sync_CFD(self, level=50, zerox=0):
        """
        Parameters of the sync CFD (constant fraction divicriminator)
      
        level
            CFD discriminator level in millivolts

        zerox
            CFD zero cross level in millivolts
      
        Values are given as a positive number although the electrical signals are actually negative.      
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        assert (level >= self.settings['DISCRMIN']) and (level <= self.settings['DISCRMAX'])
        assert (zerox >= self.settings['ZCMIN']) and (zerox <= self.settings['ZCMAX'])
        func = self.hhlib.HH_SetSyncCFD
        func.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.c_int(level)
        data3 = ctypes.c_int(zerox)
        self.error_code = func(data, data2, data3)
        if self.error_code is not 0:
            warnings.warn(self.error_string)
      
    def sync_offset(self, value=0):
        """
        Sync offset in time
        
        offset
             -99999, ..., 99999
             
        Sync time offset in ps      
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        assert (value >= self.settings['CHANOFFSMIN']) and (value <= self.settings['CHANOFFSMAX']), "SyncChannelOffset outside of valid values."
        func = self.hhlib.HH_SetSyncChannelOffset
        func.argtypes = [ctypes.c_int, ctypes.c_int]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.c_int(value)
        self.error_code = func(data, data2)
        if self.error_code is not 0:
            warnings.warn(self.error_string)
      
    def input_CFD(self, channel=0, level=50, zerox=0):
        """
        Parameters of the input CFD (constant fraction divicriminator)
      
        channel
            0, 1, ... 
             
        Input channel index
         
        level
            CFD discriminator level in millivolts

        zerox
            CFD zero cross level in millivolts
      
        Values are given as a positive number although the electrical signals are actually negative.      
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        assert channel in range(self.number_input_channels), "SetInputCFD, Channel not valid."
        assert (level >= self.settings['DISCRMIN']) and (level <= self.settings['DISCRMAX']), "SetInputCFD, Level not valid."
        assert (zerox >= self.settings['ZCMIN']) and (zerox <= self.settings['ZCMAX']), "SetInputCFD, ZeroCross not valid."
        func = self.hhlib.HH_SetInputCFD
        func.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.c_int(channel)
        data3 = ctypes.c_int(level)
        data4 = ctypes.c_int(zerox)
        self.error_code = func(data, data2, data3, data4)
        if self.error_code is not 0:
            warnings.warn(self.error_string)
 
    def input_offset(self, channel=0, offset=0):
        """
        Input offset in time
        
        channel
            0, 1, ... 
         
            Input channel index
         
        offset
            -99999, ..., 99999
         
            Input time offset in ps      
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        assert channel in range(self.number_input_channels), "SetInputChannelOffset, Channel not valid."
        assert (offset >= self.settings['CHANOFFSMIN']) and (offset <= self.settings['CHANOFFSMAX']), "SetInputChannelOffset, Offset not valid."
        func = self.hhlib.HH_SetInputChannelOffset
        func.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.c_int(channel)
        data3 = ctypes.c_int(offset)
        self.error_code = func(data, data2, data3)
        if self.error_code is not 0:
            warnings.warn(self.error_string)

    @property
    def histogram_length(self):
        return self._histoLen
   
    @histogram_length.setter
    def histogram_length(self, length=65536):
        """
        Set the histograms length
        
        actual_length = histogram_length(devidx, length)
        
        length
            1024, 2048, 4096, 8192, 16384, 32768 or 65536  (default 65536)
             
        Length (time bin count) of histograms
         
        Output:
             
        actual_length
        Actual length of the histograms
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        lencode = int(np.log2(length/1024))
        assert (lencode >= 0) and (lencode <= self.settings['MAXLENCODE'])
        func = self.hhlib.HH_SetHistoLen
        func.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.c_int(lencode)
        data3 = ctypes.c_int()
        self.error_code = func(data, data2, data3)
        self._histoLen = data3.value
        if self.error_code == 0:
            return self._histoLen
        else:
            warnings.warn(self.error_string)
   
   
    def _binning(self, binning=0):
        """
        Binning of the histograms
        
        binning
            positive integer
            0 = 1x base resolution,
            1 = 2x base resolution,
            2 = 4x base resolution,
            3 = 8x base resolution, and so on.
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        assert (binning >= 0) and (binning <= self.settings['BINSTEPSMAX'])
        func = self.hhlib.HH_SetBinning
        func.argtypes = [ctypes.c_int, ctypes.c_int]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.c_int(binning)
        self.error_code = func(data, data2)
        if self.error_code is not 0:
            warnings.warn(self.error_string)
   
    def histogram_offset(self, offset=0):
        """
        Histogram time offset    
        
        offsetZ
            0, ... 500000
            Positive integer

            Histogram time offset in ps.
            (Documentation say ns, but it's most probably a typo.)
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        assert (offset >= self.settings['OFFSETMIN']) and (offset <= self.settings['OFFSETMAX'])
        func = self.hhlib.HH_SetOffset
        func.argtypes = [ctypes.c_int, ctypes.c_int]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.c_int(offset)
        self.error_code = func(data, data2)
        if self.error_code is not 0:
            warnings.warn(self.error_string)
   
    @property
    def resolution(self):
        """
        Resolution (in ps) at the current binning
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        func = self.hhlib.HH_GetResolution
        func.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.c_double()
        self.error_code = func(data, data2)
        if self.error_code == 0:
            return data2.value
        else:
            warnings.warn(self.error_string)
         
    @resolution.setter
    def resolution(self, resolution):
        """
        Resolution (in ps)
        
        resolution
            1, 2, 4, 8, ... 2^26
             
            Resolution in ps
            """
        self._binning(int(np.log2((resolution/self._base_resolution))))
      

    def sync_rate(self):
        """
        Current sync rate
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        func = self.hhlib.HH_GetSyncRate
        func.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.c_int()
        self.error_code = func(data, data2)
        if self.error_code == 0:
            return data2.value
        else:
            warnings.warn(self.error_string)
   
    def count_rate(self, channel=0):
        """
        Current count rate of the input channel
        
        channel
             0, 1, ... 
         
        Input channel index
        """
        # Allow at least 100 ms after HH_Initialize or HH_SetSyncDivider to get a stable rate meter readings.
        # Similarly, wait at least 100 ms to get a new reading. This is the gate time of the counters.
        time.sleep(0.1)
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        assert channel in range(self.number_input_channels), "SetInputChannelOffset, Channel not valid."
        func = self.hhlib.HH_GetCountRate
        func.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.c_int(channel)
        data3 = ctypes.c_int()
        self.error_code = func(data, data2, data3)
        if self.error_code == 0:
            return data3.value
        else:
            warnings.warn(self.error_string)

    @property
    def warnings(self):
        """
        Warnings, bitwise encoded (see phdefin.h)
        """
        # TODO
        #  You must call HH_GetCoutRate and HH_GetCoutRate for all channels prior to this call.
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        func = self.hhlib.HH_GetWarnings
        func.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.c_int()
        self.error_code = func(data, data2)
        self.warning_code = data2.value
        if self.error_code == 0:
            return data2.value
        else:
            warnings.warn(self.error_string)

    @property
    def warnings_text(self, ):
        """
        Human readable warnings
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        self.warnings  # Get the warning codes
        func = self.hhlib.HH_GetWarningsText
        func.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.create_string_buffer(16384)   
        data3 = ctypes.c_int(self.warning_code)
        self.error_code = func(data, data2, data3)
        if self.error_code == 0:
            return data2.value
        else:
            warnings.warn(self.error_string)

    def stop_overflow(self, stop_at_overflow=0, stop_count=0):
        """
        Determines if a measurement run will stop if any channel reaches the maximum set by stopcount. 

        stop_at_overflow
             Bool  (default True)
             False: do not stop. Measurement will continue but counts above stop_count in any bin will be clipped.
             True: do stop on overflow
         
        Stop if any channel reaches the maximum set by stopcount. 
         
        stop_count
             Integer
             1, ... 4294967295  (default 4294967295)
        """
        stop_count = self.settings['STOPCNTMAX']
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        assert isinstance(stop_at_overflow, bool), "stop_overflow, stop_at_overflow must be a bool."
        assert (stop_count >= self.settings['STOPCNTMIN']) and (stop_count <= self.settings['STOPCNTMAX']), "HH_SetStopOverflow, stopcount not valid."
        func = self.hhlib.HH_SetStopOverflow
        func.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.c_int(stop_at_overflow)
        data3 = ctypes.c_int(stop_count)
        self.error_code = func(data, data2, data3)
        if self.error_code is not 0:
            warnings.warn(self.error_string)

    def clear_histogram(self):
        """
        Clear histogram from memory
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        func = self.hhlib.HH_ClearHistMem
        func.argtypes = [ctypes.c_int]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        self.error_code = func(data)
        if self.error_code is not 0:
            warnings.warn(self.error_string)

    def start_measurement(self, acquisition_time=1000):
        """
        Start acquisition
        
        acquisition_time
            Float
            0.001, ... 360000
        
            Acquisition time in second
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        tacq = int(acquisition_time*1000)  # acquisition time in milisecond
        assert (tacq >= self.settings['ACQTMIN']) and (tacq <= self.settings['ACQTMAX']), "HH_StartMeas, tacq not valid."
        func = self.hhlib.HH_StartMeas
        func.argtypes = [ctypes.c_int, ctypes.c_int]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.c_int(tacq)
        self.error_code = func(data, data2)
        if self.error_code is not 0:
            warnings.warn(self.error_string)

    @property
    def ctc_status(self):
        """
        Acquisition time state
        
        Output:
            False: acquisition time still running
            True: acquisition time has ended
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        func = self.hhlib.HH_CTCStatus
        func.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.c_int()
        self.error_code = func(data, data2)
        if self.error_code == 0:
            return bool(data2.value)
        else:
            warnings.warn(self.error_string)

    def stop_measurement(self):
        """
        Stop acquisition
        
        Can be used before the acquisition time expires.
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        func = self.hhlib.HH_StopMeas
        func.argtypes = [ctypes.c_int]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        self.error_code = func(data)
        if self.error_code is not 0:
            warnings.warn(self.error_string)

    def histogram(self, channel=0, clear=True):
        """
        Histogram of channel
        
        channel
            0..nchannels-1  (default 0)
         
            input channel index 
         
        clear
            Bool (default True)
         
            denotes the action upon completing the reading process
            False: keeps the histogram in the acquisition buffer
            True: clears the acquisition buffer
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        assert channel in range(self.number_input_channels), "HH_GetHistogram, Channel not valid."
        assert isinstance(clear, bool), "HH_GetHistogram, clear must be a bool."
        func = self.hhlib.HH_GetHistogram
        func.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_uint), ctypes.c_int, ctypes.c_int]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = (ctypes.c_uint*self._histoLen)() 
        data3 = ctypes.c_int(channel)
        data4 = ctypes.c_int(clear)
        self.error_code = func(data, data2, data3, data4)
        if self.error_code == 0:
            return np.array(data2)
        else:
            warnings.warn(self.error_string)

    @property
    def flags(self):
        """
        Use the predefined bit mask values in hhdefin.h (e.g. FLAG_OVERFLOW) to extract individual bits through a bitwise AND.
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        func = self.hhlib.HH_GetFlags
        func.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        data2 = ctypes.c_int()
        self.error_code = func(data, data2)
        if self.error_code == 0:
            return data2.value
        else:
            warnings.warn(self.error_string)

    def close_device(self):
        """
        Closes and releases the device for use by other programs.
        """
        devidx = self.__devidx
        assert devidx in range(self.settings['MAXDEVNUM'])
        func = self.hhlib.HH_CloseDevice
        func.argtypes = [ctypes.c_int]
        func.restype = ctypes.c_int
        data = ctypes.c_int(devidx)
        self.error_code = func(data)
        if self.error_code is not 0:
            warnings.warn(self.error_string)

    def finalize(self):
        
        self.close_device()
        
        
class Measurement_mode(Enum):
    Histogram = 0
    T2 = 2
    T3 = 3
    Continuous = 8
   
class Reference_clock(Enum):
    Internal = 0
    External = 1

   
if __name__ == "__main__":
    from hyperion import _logger_format
    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
        handlers=[logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576*5), backupCount=7),
                  logging.StreamHandler()])
    
    with Hydraharp() as q:
        q.initialize()
        
        q.calibrate()
        
        print('The sync rate is: ' , q.sync_rate())
        
        print('The count rate is: ' , q.count_rate(0))
        
        q.clear_histogram()
        
        q.histogram_length = 1024
        
        q.start_measurement(acquisition_time = 10)
        
        print(q.ctc_status)
        
        hist = q.histogram(channel = 0)
        
        print(hist)
        
        q.close_device()