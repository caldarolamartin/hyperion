"""
==============
SK Polarimeter
==============

This class (polarization.py) is the model to connect to the SK Polarization analyzer from SK.

The model is similar to the controller, but it adds specific functionalities such as units with Pint
and error descriptions

:copyright: by Hyperion Authors, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.

"""
from hyperion import logging
from time import time, sleep
import numpy as np
from hyperion import ur
from hyperion.tools.saving_tools import save_netCDF4
from hyperion.instrument.base_instrument import BaseInstrument


class Polarimeter(BaseInstrument):
    """ This class is the model for the SK polarization.

    """
    DEFAULT_SETTINGS = {'wavelength': 532 * ur('nm')}

    DATA_TYPES = ['First Stokes component (norm)',
                  'Second Stokes component (norm)',
                  'Third Stokes component (norm)',
                  'PER in logaritmic units: log(I_V/I_H)',
                  'Linear PER in logaritmic units: log(I_total/I_H) (see manual page 13)',
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

    DATA_TYPES_UNITS = ['','','',
                        '','','deg',
                        'percent', 'percent', '',
                        '', 'deg', '',
                        '']

    def __init__(self, settings):
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
        if self._wavelength==w:
            self.logger.debug('Not changing the wavelength, it is already set to {}'.format(w))
        else:
            self.logger.info('Now changing wavelength.')
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
                self.logger.debug('No error found, device {} started measurement'.format(self._id))
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

        #self.logger.debug('Getting data from device')
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
        # if data[0, 7] > 99:
        #     self.logger.warning('The intensity is too high! Please reduce intensity!')
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

        :return: av, array with dim 13 containing the average of the N measurements for each property in DATA_TYPES, and the std
        :rtype: numpy array
        :return: st, array with dim 13 containing the std of the N measurements for each property in DATA_TYPES, and the std
        :rtype: numpy array

        Example:
            >>> av, st = get_average_data(10)
            >>> print('Values: {} +/- {}'.format(av, st))
            Values


        """
        self.logger.debug('Getting average data: {} points.'.format(N))
        data = self.get_multiple_data(N)
        av = np.average(data, axis=0)
        st = np.std(data, axis=0)

        if np.isinf(av).any():
            self.looger.warning('We got an inf!!!!')
        return av, st

    def save_data(self, data, extra=[None, None, None, None], file_path = 'polarimeter_test.txt'):
        """ saves the data. It assumes that the data comes from the SK so it is a matrix of 13 rows and
        an arbitrary number of columns.


        :param data: array of (N,13)
        :type data: numpy array
        :param extra: list containing the extra vector to save (1xN), the name of the extra data and
        the unit. For example: [np.array([1,2,3]),'time','second','elapsed time'].
        :type extra: list
        """
        self.logger.info('Saving data to {}'.format(file_path))
        self.logger.debug('The data is of shape: {}'.format(np.shape(data)))

        if extra[0] is not None:
            header = self.create_header(extra_name=extra[1], extra_unit=extra[2], extra_description=extra[3])
            self.logger.debug('The EXTRA data is of shape: {}'.format(np.shape(extra[0])))
            aux = np.zeros((1, np.max(np.shape(extra[0]))))
            aux[0,:] = extra[0]
            to_save = np.hstack((np.transpose(aux), data))
        else:
            header = self.create_header()
            to_save = data

        with open(file_path, 'wb') as f:
            f.write(header.encode('ascii'))
            np.savetxt(f, to_save, fmt='%7.5f')

        self.logger.info('Data saved to {}'.format(file_path))

    def create_header(self, errors= False, extra_name = None, extra_unit = None, extra_description = None):
        """ creates the header to save the data

        :param extra_name: if a first column has to be added, this is the name
        :type extra_name: str
        :param extra_unit: if a first column has to be added, this is the unit
        :type extra_unit: str
        :param extra_description: if a first column has to be added, this is the description
        :type extra_description: str

        :return: header with the information of the data saved
        :rtype: string
        """
        self.logger.debug('Creating header with the meaning of the columns.')
        header = '# Data created with polarimeter.py, instrument class for the SK polarization analyzer from Hyperion by Authors. \n'
        header += '# Meaning of the columns: \n'

        N = 0
        if extra_name is None and extra_unit is None:
            self.logger.debug('Making header without extra')

        elif extra_unit is not None and extra_name is not None and extra_description:
            self.logger.debug('Making header with an extra column')
            string = '#   Column number 0 is {} [{}]. Physical meaning: {} \n'.format(extra_name, extra_unit,
                                                                                      extra_description)
            header += string
            N = 1
        else:
            raise Warning('The parameters for the extra column named extra_unit and extra_name have to be both'
                          'None or both a string.')

        for k in range(len(self.DATA_TYPES)):
            string = '#   Column number {} is {} [{}]. Physical meaning: {} \n'.format(k + N,
                                                                                       self.DATA_TYPES_NAME[k],
                                                                                       self.DATA_TYPES_UNITS[k],
                                                                                       self.DATA_TYPES[k])
            header += string
            ind = k + N + 1

        # to add the errors
        if errors:
            for k in range(len(self.DATA_TYPES)):
                string = '#   Column number {} is the std for {} [{}]. Physical meaning: {} \n'.format(k + ind,
                                                                                           self.DATA_TYPES_NAME[k],
                                                                                           self.DATA_TYPES_UNITS[k],
                                                                                           self.DATA_TYPES[k])
                header += string



        header += '# \n'
        header += '# --------------------- End of header --------------------- \n'

        return header

    def save_as_netCDF4(self, filename, data):
        """ Saves the data from the polarimeter measurement into a netCDF4 file. """
        self.logger.info(f'Saving into netCDF4 file: {filename}')
        detectors = self.DATA_TYPES_NAME
        self.logger.debug(f'The detectors are {detectors}')

        DATA = []
        for index, unit_name in enumerate(self.DATA_TYPES_UNITS):
            unit = ur(unit_name)
            self.logger.debug(f'The unit for the detector {detectors[index]} is: {unit}')
            DATA.append( data[:,index] * unit )

        self.logger.debug(f'The data to save is: {DATA}')

        # create axes
        axis = np.array(range(np.shape(data)[0]))*ur('')
        extra = {'wavelength':self._wavelength}

        description = 'This is a description of the variables: \n'

        for index, s in enumerate(self.DATA_TYPES):

            to_add = f'{self.DATA_TYPES_NAME[index]} : {s} \n'
            description += to_add

        save_netCDF4(filename, detectors, DATA, axes=(axis, ) , axes_name=('Measurement index',), extra_dims=extra,
                     description = description)

    def get_wavelength(self):
        """ asks the device the current wavelength.

        :return: current wavelength
        :rtype: pint quantity
        """
        ans = self.controller.get_wavelength()
        w = ans * ur('nm')
        return w

if __name__ == "__main__":
    import hyperion
    import os
    from hyperion.tools.saving_tools import read_netcdf4_and_plot_all

    path = hyperion.parent_path
    filename = 'polarimeter_output'

    with Polarimeter(settings = {'dummy' : False,
                                 'controller': 'hyperion.controller.sk.sk_pol_ana/Skpolarimeter',
                                 'dll_name': 'SKPolarimeter'}) as s:

        wavelengths = np.linspace(500,750,1)* ur('nm')
        Npts = 5
        for w in wavelengths:
            s.change_wavelength(w)
            t0 = time()
            print('Getting data for wavelength = {}.'.format(w))
            data = s.get_multiple_data(Npts)
            print(data)
            t = time()-t0
            print('Elapsed time: {} s'.format(t))
            s.stop_measurement()
            T = np.array([t]*Npts)
            print('T vector: {}'.format(T))

            # save txt
            s.save_data(data)
            # save txt with extra info
            s.save_data(data, extra = [np.zeros(Npts),'Time','second','Elapsed time'],
                        file_path = os.path.join(path, filename + '_with_extra.txt') )
            # save netCDF4
            s.save_as_netCDF4(os.path.join(path, filename + '.nc'), data)
            read_netcdf4_and_plot_all(os.path.join(path,filename+'.nc'))

        print('DONE')
