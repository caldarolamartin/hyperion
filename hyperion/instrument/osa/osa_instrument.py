# -*- coding: utf-8 -*-
"""
==================
Osa Instrument
==================

This is the osa instrument, created to have a place where the view can send requests and
the controller can get the data the view want's to show. so data flows controller > instrument > view

"""
import logging
from hyperion.instrument.base_instrument import BaseInstrument
from hyperion.controller.osa.osa import Osa
from hyperion.view.osa import osa_view
from hyperion import ur

class OsaInstrument(BaseInstrument):
    """ Example instrument. it is a fake instrument

    """
    def __init__(self, settings = {'port':'COM10', 'dummy': True,
                                   'controller': 'hyperion.controller.example_controller/ExampleController'}):
        """ init of the class"""
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)
        self.logger.info('Class ExampleInstrument created.')

    def initialize(self):
        """ Starts the connection to the device"
        """
        self.logger.info('Opening connection to device.')
        self.controller.initialize()

    def finalize(self):
        """ this is to close connection to the device."""
        self.logger.info('Closing connection to device.')
        self.controller.finalize()

    def idn(self):
        """ Identify command

        :return: identification for the device
        :rtype: string

        """
        self.logger.debug('Ask IDN to device.')
        return self.controller.idn

    def is_end_wav_bigger_than_start_wav(self, end_wav, start_wav):
        if float(end_wav) > float(start_wav):
            # end_wav is groter dan start_wav wat je verwacht. dit is goed
            pass
        else:
            print("start_wav is groter dan end_wav, dit is niet de bedoeling!")

            return

    def is_optical_resolution_correct(self, optical_resolution):
        if float(optical_resolution) in get_list_with_possible_optical_resolution():
            # de waarde zit in de lijst, dus dat is goed
            pass
        else:
            print("de opgegeven waarde van optische resolutie is niet mogelijk.\n "
                  "Zie deze lijst voor opties:"+ str(get_list_with_possible_optical_resolution()))
            return

    def is_end_wav_value_correct(self, end_wav):
        if float(end_wav) > 600.00 and float(end_wav) < 1750.00:
            # de opgegeven waarde is goed
            pass
        else:
            print("end_wav is groter of kleiner dan hij mag zijn.\n De waarde mag zitten tussen de 600.00 en 1750.00")
            return

    def is_start_wav_value_correct(self, start_wav):
        if float(start_wav) > 600.00 and float(start_wav) < 1750.00:
            # de opgegeven waarde is goed
            pass
        else:
            print("start_wav is groter of kleiner dan hij mag zijn.\n De waarde mag zitten tussen 600.00 en 1750.00")
            return


def get_list_with_possible_optical_resolution():
    return [0.01,0.02,0.05,0.1,0.2,0.5,1.0,2.0,5.0]

def set_settings_for_osa(dev):
    """
    in this method the parameters for the osa machine are set
    :param dev: the osa device.
    :return:
    """
    dev.start_wav = 600.00
    dev.end_wav = 900.00
    # allowed are 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0
    dev.optical_resolution = 1.00
    dev.sample_points = get_recommended_sample_points(dev)


def get_recommended_sample_points(dev):
    # recommend at the very least 1 + 2*(end_wav-start_wav)/optical_resolution
    return 1 + 2 * ((dev.end_wav - dev.start_wav) / dev.optical_resolution)


if __name__ == "__main__":
    from hyperion import _logger_format, _logger_settings
    logging.basicConfig(level=logging.INFO, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler(_logger_settings['filename'],
                                                                 maxBytes=_logger_settings['maxBytes'],
                                                                 backupCount=_logger_settings['backupCount']),
                            logging.StreamHandler()])
    dummy = False

    with Osa(settings={'dummy': dummy}) as dev:
        dev.initialize()
        set_settings_for_osa(dev)

        dev.wait_for_osa(5)
        dev.perform_single_sweep()
        #dev.get_data()
        dev.finalize()


    """
    dummy = [False]
    for d in dummy:
        with ExampleInstrument(settings = {'port':'COM8', 'dummy' : d,
                                   'controller': 'hyperion.controller.example_controller/ExampleController'}) as dev:
            dev.initialize()
            print(dev.amplitude)
            # v = 2 * ur('volts')
            # dev.amplitude = v
            # print(dev.amplitude)
            # dev.amplitude = v
            # print(dev.amplitude)

    print('done')
    """


