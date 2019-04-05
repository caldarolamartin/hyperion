"""
==============
SK Polarimeter
==============

This class (polarimeter.py) is the model to connect to the SK Polarization analyzer from SK.

The model is similar to the controller, but it adds specific functionalities such as units with Pint
and error descriptions

"""
import logging
from time import time, sleep
import numpy as np
from hyperion.controller.sk.sk_pol_ana import Skpolarimeter
from hyperion.instrument.base_instrument import BaseInstrument
from hyperion import ur


class Polarimeter(BaseInstrument):
    """ This class is the model for the SK polarimeter.

    """

    def __init__(self):
        """
        Initialize the Model SK polarimeter


        """
        self.logger = logging.getLogger(__name__)

        self.DEFAULT_SETTINGS = {'wavelength': 601 * ur('nm'),
                                 }

        self.DATA_TYPES = {'0': 'First Stokes component (norm)',
                           '1': 'Second Stokes component (norm)',
                           '2': 'Third Stokes component (norm)',
                           '3': 'PER in units of dB',
                           '4': 'Lin. PER in units of dB as described in manual page 13',
                           '5': 'The angle of the main polarization axis. 0deg for vertical polarization',
                           '6': 'The degree of polarization in %',
                           '7': 'The intensity of the entrance bean in units of %',
                           '8': 'V as the ratio of power into the two principal states of polarization',
                           '9': 'LinV like V above but with DOP taken into account, page 13 from manual.',
                           '10': 'Ellipticity Etha as an angle, see manual page 33',
                           '11': 'Power split ratio the current polarization',
                           '12': 'Retardation of the current state of polarization',
                           }

        # instantiate the class
        self.driver = Skpolarimeter()
        self.wavelength = None

        # get info to initialize
        self.logger.debug('getting information from the device')
        self.get_information()


    def get_information(self):
        """ gets the information from the device: number of polarizers and id.

        """

        self.driver.get_number_polarizers()
        self.driver.get_device_information()
        self.id = self.driver.id

    def initialize(self, wavelength = None):
        """ This is to initialize the model by calling the initizialize function in the controller.
        It adds units for the wavelength

        :param wavelength: the working wavelength
        :type wavelength: pint quantity
        """
        self.logger.info('Initializing SK polarimeter. Device with id = {}'.format(self.id))

        if wavelength is None:
            w = self.DEFAULT_SETTINGS['wavelength']
            self.logger.debug('Using default setting for wavelength: {}'.format(w))
        else:
            w = wavelength
            self.logger.debug('Using wavelength = {}'.format(w))

        if w.m_as('nm') < self.driver.min_w or w.m_as('nm') > self.driver.max_w:
            raise Warning('The requested wavelength {} is outside the range supported for this device'.format(w))

        self.wavelength = w
        ans = self.driver.initialize(wavelength = w.m_as('nm'))

        if ans == 0:
            self.logger.debug(
                'No error found, device {} initialized with wavelength {}.'.format(self.id, self.wavelength))
        elif ans == -1:
            raise Warning('The device {} is already initialized.'.format(self.id))
        elif ans == -2:
            raise Warning('No Polarization analyzer is connected properly.')
        elif ans == -3:
            raise Warning('Wavelength asked is outside range.')
        elif ans == -5:
            raise Warning('Device ID: {} is invalid!'.format(self.id))

    def finalize(self):
        """ Finishes the connection to the SK polarimeter"""

        ans = self.driver.finalize()

        if ans == 0:
            self.logger.debug('No error found, connection closed.')
        elif ans == -5:
            raise Warning('Device ID: {} is invalid!'.format(self.id))

    def start_measurement(self):
        """ This method starts the measurement for the polarization analyzer.

        """
        self.logger.debug('Starting measurement.')
        ans = self.driver.start_measurement()

        if ans == 0:
            self.logger.debug('No error found, device {} started measurement')
        elif ans == -1:
            raise Warning('The device {} is not yet initialized.'.format(self.id))
        elif ans == -2:
            raise Warning('Polarization analyzer {} is already running.'.format(self.id))
        elif ans == -3:
            raise Warning('Connection to Polarization analyzer is lost.')
        elif ans == -5:
            raise Warning('Device ID: {} is invalid!'.format(self.id))

    def stop_measurement(self):
        """ This method stops the measurement for the polarization analyzer.

        """
        self.logger.debug('Stopping measurement.')
        self.driver.stop_measurement()

    def get_data(self):
        """ This methods gets the a single measurement point from the device.
        It reads all the types of data available, listed in DATA_TYPES.

        :return: a list with the data
        :rtype: list
        """
        self.logger.debug('Getting data from device')
        d = self.driver.get_measurement_point()

        while np.isinf(d).any():
            self.logger.info('Got an inf in the data!!!')
            self.stop_measurement()
            self.finalize()
            sleep(0.5)
            self.initialize(self.wavelength)
            self.start_measurement()
            d = self.driver.get_measurement_point()

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
            np.savetxt(f, data, fmt='%7.5f')

        self.logger.info('Data saved to {}'.format(file_path))

    def create_header(self):
        """ creates the header to save the data

        :return: header with the information of the data saved
        :rtype: string
        """
        self.logger.debug('Creating header with the meaning of the columns.')
        header = '# Data created with polarimeter.py, model for the SK polarization analyzer from PTFL by Authors. \n'
        header += '#    Meaning of the columns: \n'

        for k in self.DATA_TYPES:
            string = '# Col {}: {} \n'.format(k, self.DATA_TYPES[k])
            header += string
        header += '# --------------------- End of header --------------------- \n'

        return header

    def get_wavelength(self):
        """ asks the device the current wavelength.

        :return: current wavelength
        :rtype: pint quantity
        """
        ans = self.driver.get_wavelength()
        w = ans * ur('nm')
        return w

if __name__ == "__main__":
    from hyperion import _logger_format

    logging.basicConfig(level=logging.INFO, format=_logger_format,
                        handlers=[
                            logging.handlers.RotatingFileHandler("logger.log", maxBytes=(1048576 * 5), backupCount=7),
                            logging.StreamHandler()])


    with Polarimeter() as s:
        wavelengths = np.linspace(500,750,10)* ur('nm')

        for w in wavelengths:
            s.initialize(wavelength = w)
            s.start_measurement()
            t = time()

            print('Getting data for wavelength = {}.'.format(w))
            data = s.get_multiple_data(10)
            print(data)
            print('Elapsed time: {} s'.format(time()-t))
            t = time()

            s.stop_measurement()

    print('DONE')
