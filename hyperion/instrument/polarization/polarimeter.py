"""
==============
SK Polarimeter
==============

This class (polarization.py) is the model to connect to the SK Polarization analyzer from SK.

The model is similar to the controller, but it adds specific functionalities such as units with Pint
and error descriptions

"""
import logging
from time import time, sleep
import numpy as np
from hyperion.instrument.base_instrument import BaseInstrument
from hyperion import ur


class Polarimeter(BaseInstrument):
    """ This class is the model for the SK polarization.

    """
    DEFAULT_SETTINGS = {'wavelength': 532 * ur('nm')}

    DATA_TYPES = ['First Stokes component (norm)',
                  'Second Stokes component (norm)',
                  'Third Stokes component (norm)',
                  'PER in units of dB',
                  'Lin. PER in units of dB as described in manual page 13',
                  'The angle of the main polarization axis. 0deg for vertical polarization',
                  'The degree of polarization in %',
                  'The intensity of the entrance bean in units of %',
                  'V as the ratio of power into the two principal states of polarization', #8
                  'LinV like V above but with DOP taken into account, page 13 from manual.', #9
                  'Ellipticity Etha as an angle, see manual page 33', #10
                  'Power split ratio the current polarization', # 11
                  'Retardation of the current state of polarization'] # 12

    DATA_TYPES_NAME = ['S1', 'S2', 'S3',
                       'PER', 'LIN', 'ANGLE',
                       'POL_DEG','INT','V',
                       'LINV','ELLIP','POWER_SPLIT',
                       'RETARDATION']

    DATA_TYPES_UNITS = ['norm','norm','norm',
                        'dB','dB','deg',
                        '%', '%', 'norm',
                        'norm', 'deg', 'norm',
                        'norm']

    def __init__(self, settings = {'dummy' : False,
                                   'controller': 'hyperion.controller.sk.sk_pol_ana/Skpolarimeter',
                                   'dll_name': 'SKPolarimeter'} ):
        """
        Init of the class.

        It needs a settings dictionary that contains the following fields (mandatory)

            * dummy: logical to say if the connection is real or dummy (True means dummy)
            * controller: this should point to the controller to use and with / add the name of the class to use

        Note: When you set the setting 'dummy' = True, the controller to be loaded is the dummy one by default,
        i.e. the class will automatically overwrite the 'controller' with 'hyperion.controller.sk.sk_pol_ana/SkpolarimeterDummy

        """
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)
        self._wavelength = None
        # get info to initialize
        self.logger.debug('getting information from the device')
        self.get_information()
        self._measuring = False
        self.initialize(wavelength = self._wavelength)

    def change_wavelength(self, w):
        """Change the current wavelegnth to w

        :param w: wavelength
        :type w: pint quantity (distance)

        :return: current wavelength
        :rtype: pint quantity (distance)
        """
        self.logger.info('Now changing wavelength.')
        if self._wavelength==w:
            self.logger.debug('Not changing the wavelength, it is already set to {}'.format(w))
        else:
            self.finalize()
            sleep(0.1)
            self.initialize(wavelength = w)
            self.logger.info('Current wavelength: {}'.format(w))

        return self._wavelength

    def get_information(self):
        """ gets the information from the device: number of polarizers and id.

        """
        self.controller.get_number_polarizers()
        self.controller.get_device_information()
        self._id = self.controller.id

    def initialize(self, wavelength = None):
        """ This is to initialize the model by calling the initizialize function in the controller.
        It adds units for the wavelength

        :param wavelength: the working wavelength
        :type wavelength: pint quantity
        """
        self.logger.info('Initializing SK polarization. Device with id = {}'.format(self._id))
        self.logger.debug('Is initialized: {}'.format(self.controller._is_initialized))

        ans = None

        if wavelength is None:
            self._wavelength = self.DEFAULT_SETTINGS['wavelength']
            self.logger.info('Using default setting for wavelength')
        else:
            self._wavelength = wavelength

        if self._wavelength.m_as('nm') < self.controller.min_w or self._wavelength.m_as('nm') > self.controller.max_w:
            self.logger.warning('The requested wavelength {} is outside the range supported for this device'.format(self._wavelength))
            self.logger.warning('Using default setting instead')
            self._wavelength = self.DEFAULT_SETTINGS['wavelength']

        if not self.controller._is_initialized:
            self.logger.info('Initializing SK polarization with wavelength {}'.format(self._wavelength))
            ans = self.controller.initialize(wavelength = self._wavelength.m_as('nm'))


        if ans == 0:
            self.logger.debug(
                'No error found, device {} initialized with wavelength {}.'.format(self._id, self._wavelength))
        elif ans == -1:
            raise Warning('The device {} is already initialized.'.format(self._id))
        elif ans == -2:
            raise Warning('No Polarization analyzer is connected properly.')
        elif ans == -3:
            raise Warning('Wavelength asked is outside range.')
        elif ans == -5:
            raise Warning('Device ID: {} is invalid!'.format(self._id))
        elif ans is None:
            self.logger.warning('Ans is None')

        sleep(0.1)

    def finalize(self):
        """ Finishes the connection to the SK polarization"""

        ans = self.controller.finalize()

        if ans == 0:
            self.logger.debug('No error found, connection closed.')
        elif ans == -5:
            raise Warning('Device ID: {} is invalid!'.format(self._id))

    def start_measurement(self):
        """ This method starts the measurement for the polarization analyzer.

        """
        if self._measuring:
            self.logger.debug('Already measuring.')
        else:
            self.logger.debug('Starting measurement.')

            ans = self.controller.start_measurement()

            if ans == 0:
                self.logger.debug('No error found, device {} started measurement')
                self._measuring = True
            elif ans == -1:
                raise Warning('The device {} is not yet initialized.'.format(self._id))
            elif ans == -2:
                raise Warning('Polarization analyzer {} is already running.'.format(self._id))
            elif ans == -3:
                raise Warning('Connection to Polarization analyzer is lost.')
            elif ans == -5:
                raise Warning('Device ID: {} is invalid!'.format(self._id))


    def stop_measurement(self):
        """ This method stops the measurement for the polarization analyzer.

        """
        self.logger.debug('Stopping measurement.')
        self.controller.stop_measurement()
        self._measuring = False

    def get_data(self):
        """ This methods gets the a single measurement point from the device.
        It reads all the types of data available, listed in DATA_TYPES.

        :return: a list with the data
        :rtype: list
        """
        if not self._measuring:
            self.start_measurement()

        self.logger.debug('Getting data from device')
        d = self.controller.get_measurement_point()

        # this is to catch when a Nan value is generated
        while np.isinf(d).any():
            self.logger.warning('Got an inf in the data!!!')
            self.stop_measurement()
            self.finalize()
            sleep(0.5)
            self.initialize(self._wavelength)
            self.start_measurement()
            d = self.controller.get_measurement_point()

        data = np.zeros((1, len(d)))
        data[0, :] = d
        return data

    def get_multiple_data(self, N):
        """ This is to get a stream of data directly from the device.

        :param N: number of data points needed
        :type N: int

        :return: a np array
        """
        self.logger.debug('Getting multiple data: {} points'.format(N))
        data = np.zeros((N, 13))    # initialize the data matrix with zeros.

        for i in range(N):
            d = self.get_data()
            data[i, :] = np.array(d)

        return data

    def get_average_data(self, N):
        """ Takes N data points and gives back the average and the error (std)

        :return: array with dim 13 containing the average of the N measurements for each property in DATA_TYPES, and the std
        :rtype: numpy array
        """
        self.logger.debug('Getting average data: {} points.'.format(N))
        data = self.get_multiple_data(N)
        av = np.average(data, axis=0)
        st = np.std(data, axis=0)

        if np.isinf(av).any():
            self.looger.info('We got an inf!!!!')
        return av, st

    def save_data(self, data, file_path = 'polarimeter_test.txt'):
        """ saves the data

        """
        self.logger.debug('Saving data to {}'.format(file_path))
        header = self.create_header()

        with open(file_path, 'wb') as f:
            f.write(header.encode('ascii'))
            np.savetxt(f, np.transpose(data), fmt='%7.5f')

        self.logger.info('Data saved to {}'.format(file_path))

    def create_header(self):
        """ creates the header to save the data

        :return: header with the information of the data saved
        :rtype: string
        """
        self.logger.debug('Creating header with the meaning of the columns.')
        header = '# Data created with polarimeter.py, instrument class for the SK polarization analyzer from Hyperion by Authors. \n'
        header += '# Meaning of the columns: \n'

        for k in range(len(self.DATA_TYPES)):
            string = '#   Column number {} is {} [{}]. Physical meaning: {} \n'.format(k, self.DATA_TYPES_NAME[k],
                                                                                      self.DATA_TYPES_UNITS[k],
                                                                                      self.DATA_TYPES[k])
            header += string

        header += '# \n'
        header += '# --------------------- End of header --------------------- \n'

        return header

    def get_wavelength(self):
        """ asks the device the current wavelength.

        :return: current wavelength
        :rtype: pint quantity
        """
        ans = self.controller.get_wavelength()
        w = ans * ur('nm')
        return w

if __name__ == "__main__":
    from hyperion import _logger_format

    logging.basicConfig(level=logging.DEBUG, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576 * 5), backupCount=7),
                            logging.StreamHandler()])


    with Polarimeter(settings = {'dummy' : False,
                                 'controller': 'hyperion.controller.sk.sk_pol_ana/Skpolarimeter',
                                 'dll_name': 'SKPolarimeter'}) as s:

        wavelengths = np.linspace(500,750,3)* ur('nm')
        for w in wavelengths:
            s.change_wavelength(w)
            #s.start_measurement()
            t = time()

            print('Getting data for wavelength = {}.'.format(w))
            data = s.get_multiple_data(2)
            print(data)
            print('Elapsed time: {} s'.format(time()-t))
            t = time()

            s.stop_measurement()

        print('DONE')
