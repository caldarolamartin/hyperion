# -*- coding: utf-8 -*-
"""
==================
Osa Instrument
==================

This is the osa instrument, created to have a place where the view can send requests and
the controller can get the data the view want's to show. so data flows controller > instrument > view

"""
#TODO is de optical resolution(en sample points misschien) in nanometers of in iets anders?
import logging
import sys

from hyperion.instrument.base_instrument import BaseInstrument
from hyperion.controller.osa.osacontroller import OsaController
from hyperion.view.osa import osa_view
from hyperion import ur, root_dir

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
        if not self.__wav_in_range(start_wav.m_as('nm')):
            self.controller.start_wav = start_wav.m_as('nm')
    @property
    def end_wav(self):
        return self.controller.end_wav * ur('nm')

    @end_wav.setter
    def end_wav(self, end_wav):
        if not self.__wav_in_range(end_wav.m_as('nm')):
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


def is_end_wav_bigger_than_start_wav(end_wav, start_wav):
    if float(end_wav) < float(start_wav):
        return True
    else:
        print("start_wav value is bigger than the end_wav value, that is not what you want!")
        return False

def is_end_wav_value_correct(end_wav):
    if float(end_wav) >= 600.00 and float(end_wav) <= 1750.00:
        return True
    else:
        print("end_wav value is bigger or smaller than it must be.\n De value must be between 600.00 and 1750.00.")
        return False

def is_start_wav_value_correct(start_wav):
    if float(start_wav) >= 600.00 and float(start_wav) <= 1750.00:
        return True
    else:
        print("the start_wav value is bigger than or smaller than it should be.\n The value must be between 600.00 and 1750.00.")
        return False

def get_values_from_textboxs(self):
    # get all the values from the textfields
    start_wav = get_start_wav(self)
    end_wav = get_end_wav(self)
    optical_resolution = get_optical_resolution(self)
    sample_points = get_sample_points(self)
    return end_wav, optical_resolution, sample_points, start_wav

def get_sample_points(self):
    sample_points = self.textbox_sample_points.text()
    return sample_points

def get_optical_resolution(self):
    optical_resolution = self.dropdown_optical_resolution.currentText()
    return optical_resolution

def get_end_wav(self):
    end_wav = self.textbox_end_wav.text()
    return end_wav

def get_start_wav(self):
    start_wav = self.textbox_start_wav.text()
    return start_wav


def get_recommended_sample_points(self):
    self.textbox_sample_points.setText(
        str(1 + (2 * (float(self.textbox_end_wav.text()) - float(self.textbox_start_wav.text())) / float(
            self.dropdown_optical_resolution.currentText()))))


if __name__ == "__main__":
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
        dev.start_wav = 0.8 * ur('um')
        #set_settings_for_osa(dev)
        #app = osa_view.QApplication(sys.argv)
        #ex = osa_view.App()

        #dev.wait_for_osa(5)
        #dev.perform_single_sweep()
        #dev.get_data()
        dev.finalize()


        #sys.exit(app.exec_())




