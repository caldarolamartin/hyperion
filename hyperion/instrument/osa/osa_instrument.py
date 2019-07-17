# -*- coding: utf-8 -*-
"""
==================
Osa Instrument
==================

This is the osa instrument, created to have a place where the view can send requests and
the controller can get the data the view want's to show. so data flows controller > instrument > view

"""
#TODO is de optical resolution(en sample points misschien) in nanometers of in iets anders?
"""
TODO de osa_instrument maak geen gebruik van de osaController. Dit zorgt ervoor dat er geen functies van
de osacontroller in de osa_instrument gebruikt kunnen worden wat niet handig is. 
"""


import logging
import sys

from hyperion.instrument.base_instrument import BaseInstrument
#from hyperion.controller.osa.osacontroller import OsaController
#from hyperion.view.osa import osa_view
from hyperion import ur, root_dir, Q_


class OsaInstrument(BaseInstrument):
    """ OsaInstrument

    """
    def __init__(self, settings = {'port':'COM10', 'dummy': False,
                                   'controller': 'hyperion.controller.osa/OsaController'}):
        """ init of the class"""
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)
        self.logger.info('Class OsaInstrument has been created.')

    def initialize(self):
        """ Starts the connection to the device"
        """
        self.logger.info('Opening connection to OSA machine.')
        self.controller.initialize()

    def finalize(self):
        """ this is to close connection to the device."""
        self.logger.info('Closing connection to OSA machine.')
        self.controller.finalize()

    def idn(self):
        """ Identify command

        :return: identification for the device
        :rtype: string

        """
        self.logger.debug('Ask IDN to device.')
        return self.controller.idn


    @property
    def start_wav(self):
        return self.controller.start_wav * ur('nm')

    @start_wav.setter
    def start_wav(self, start_wav):
        if self.__wav_in_range(start_wav.m_as('nm')):
            self.controller.start_wav = start_wav.m_as('nm')
    @property
    def end_wav(self):
        return self.controller.end_wav * ur('nm')

    @end_wav.setter
    def end_wav(self, end_wav):
        if self.__wav_in_range(end_wav.m_as('nm')):
            self.controller.end_wav = end_wav.m_as('nm')

    @property
    def optical_resolution(self):
        #is de optical resolution in nanometers of in iets anders?
        return self.controller.optical_resolution

    @optical_resolution.setter
    def optical_resolution(self, optical_resolution):
        if optical_resolution in [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]:
            self.controller.optical_resolution = optical_resolution

    @property
    def sample_points(self):
        return self.controller.sample_points

    @sample_points.setter
    def sample_points(self, sample_points):
        self.controller.sample_points = sample_points

    @property
    def sensitivity(self):
        return self.controller.sensitivity

    @sensitivity.setter
    def sensitivity(self, sensitivity_string):
        if sensitivity_string in ['high1', 'high2', 'high3', 'norm_hold', 'norm_auto', 'mid']:
            self.controller.sensitivity = sensitivity_string

    def __wav_in_range(self, wav):
        return (wav<1750.0 and wav>600.0)


    def is_end_wav_bigger_than_start_wav(self, end_wav, start_wav):
        if end_wav.m_as('nm') < start_wav.m_as('nm'):
            return True
        else:
            print("start_wav value is bigger than the end_wav value, that is not what you want!")
            return False

    def is_end_wav_value_correct(self, end_wav):
        if end_wav.m_as('nm') >= 600 and end_wav.m_as('nm') <= 1750:
            return True
        else:
            print("end_wav value is bigger or smaller than it must be.\n De value must be between 600.00 and 1750.00.")
            return False

    def is_start_wav_value_correct(self, start_wav):
        if start_wav.m_as('nm') >= 600 and start_wav.m_as('nm') <= 1750:
            return True
        else:
            print("the start_wav value is bigger than or smaller than it should be.\n The value must be between 600.00 and 1750.00.")
            return False
    def take_spectrum(self):
        print('inside instrument: take_spectrum()')
        #self.logging.info('taking spectrum')
        self.controller.perform_single_sweep()
        self.controller.wait_for_osa()

        wav, spec = self.controller.get_data()
        self.logger.info("spectrum retrieved")
        return wav,spec



if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from hyperion import _logger_format, _logger_settings
    logging.basicConfig(level=logging.INFO, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler(_logger_settings['filename'],
                                                                 maxBytes=_logger_settings['maxBytes'],
                                                                 backupCount=_logger_settings['backupCount']),
                            logging.StreamHandler()])

    dummy = False
    with OsaInstrument(settings={'dummy': dummy, 'controller':'hyperion.controller.osa.osacontroller/OsaController'}) as dev:
        dev.initialize()

        print(dev.start_wav)
        print(dev.end_wav)

        dev.start_wav = 0.9 * ur('um')
        dev.end_wav = 1.0 * ur('um')
        dev.sample_points = 201.0
        dev.optical_resolution = 1.0
        dev.sensitivity = "mid"
        #app = osa_view.QApplication(sys.argv)
        #ex = osa_view.App()

        wav, spec = dev.take_spectrum()
        plt.plot(wav, spec)
        plt.show()


        dev.finalize()
        #sys.exit(app.exec_())




