# -*- coding: utf-8 -*-
"""
============
Saving tools
============

This is a collection of useful methods related to saving data and metadata
used along hyperion.



"""
import os
import netCDF4
import time
import matplotlib.pyplot as plt
import xarray as xr
from hyperion.core import logman
from hyperion import __version__, ur, Q_

logger = logman.getLogger(__name__)


def name_incrementer(basename, list_of_existing, separator='_', fill_zeros=0, use_number_for_first=None,
                     only_larger_number=True):
    """
    This function is meant to avoid rewriting existing files.

    :param basename: The basename. May include extension.
    :param list_of_existing: List of names to avoid
    :param separator: Optional separator between basename and number, DEFAULT is '_'
    :param fill_zeros: If you set this to 4, numbers will look like 0012, 0013. Special case 0 (DEFAULT) will match the longest one in list_of_existing
    :param use_number_for_first: 0, 1, None. If the name does not occur yet it will get 0, 1 or no sufix, DEFAULT is None
    :param only_larger_number: If name_1 and name_3 exist and only_larger_number is True DEFAULT, name_4 will be suggested, otherwise name_2
    :return: The suggested name.
    """

    if basename.lower() in (name.lower() for name in list_of_existing):
        exact_match = True
    else:
        exact_match = False

    # identify and strip extension if there is one
    if '.' in basename:
        ext = '.' + basename.split('.')[-1].lower()
        extlen = len(ext)
        basename = basename[:(len(basename) - extlen)]
    else:
        ext = ''
        extlen = 0

    baselen = len(basename)
    seplen = len(separator)

    similar = [name.lower()[(baselen + seplen):(len(name) - extlen)] for name in list_of_existing if
               name.lower().startswith(basename.lower() + separator) and name.lower().endswith(ext)]

    # try to convert the suffixes to numbers
    # if succeeds: add the number to numbers, if fails: remove from similar list
    numbers = []
    maxlen = 0
    for index in range(len(similar) - 1, -1, -1):
        chunk = similar[index]
        try:
            numbers.insert(0, int(chunk))
            maxlen = max(maxlen, len(chunk))
        except:
            del (similar[index])

    if not exact_match:
        new_number = use_number_for_first
    else:
        new_number = 1

    if only_larger_number and len(numbers):
        new_number = max(numbers) + 1

    while new_number in numbers:
        new_number += 1

    if fill_zeros==0:
        fill_zeros = maxlen
    formatstring = separator + '{:0' + str(fill_zeros) + '}'
    if new_number is not None:
        basename += formatstring.format(new_number)

    return basename + ext

def create_filename(file_path):
    """ Creates the filename, so all the methods point to the same folder
    and save with the same name. The output does not include the extension but the input does.

    :param filename: config filename complete path (INCLUDING the extension)
    :type filename: string (path)

    :return: filename with a number appended so it would not be overwritten.
    :rtype: string

    """

    i = 0
    ext = file_path[-4:]  # Get the file extension (it assumes is a dot and three letters)
    filename = file_path[:-4]
    root_path = os.path.split(filename)[0]

    while os.path.exists(file_path):
        file_path = '{}_{:03}{}'.format(filename, i, ext)
        i += 1

    filename = file_path[:-4]

    return filename

def save_metadata(self):
    """ Saves the config file information with the same name as the data and extension .yml


    """
    self.create_filename(self.properties['config file'])

    self.logger.debug('Filename: {}'.format(self.filename))
    file_path = self.filename + '.yml'
    self.logger.debug('Complete file path: {}'.format(file_path))

    with open(file_path, 'w') as f:
        yaml.dump(self.properties, f, default_flow_style=False)

    self.logger.info('Metadata saved to {}'.format(file_path))

def save(self, data):
    pass

def save_netCDF4(filename, detectors, data, axes, axes_name, errors=None, extra_dims=None, description=None):
    """ This function saves the data in a netCDF4 format, including units and
    the axes corresponding to the data. For more info about the package used,
    please see http://unidata.github.io/netcdf4-python/netCDF4/index.html.
    For info on the format itself, refer to: https://www.unidata.ucar.edu/software/netcdf/docs/index.html


    :param detectors: list of the detectors used
    :type detectors: list of strings
    :param data: list with the actual data corresponding to each detector
    :type data: list of numpy ndarrays of pint quantities
    :param axes: corresponding coordinates for the data. the dimension of the i element
    in the list has to match the dimension of the i-th dimension of data.
    :type axes: list of vectors of pint quantity
    :param axes_name: the name of each of the axes
    :type axes_name: list of strings
    :param errors: measured errors for each of the detectors. t has to have the same dimensions as data.
    :type errors: list of numpy ndarrays of pint quantities
    :param extra_dims: A dict containing extra values fixed and all the same for the set.
    :type extra_dims: dict
    :param description: an extra descriptive message can be put here.
    :type description: string

    """
    logger.info(f'Saving data with netCDF4 into file: {filename}')
    logger.debug('Checking the input')
    assert len(data) == len(detectors)
    assert len(axes) == len(axes_name)

    if errors is not None:
        assert len(errors)==len(data)
        for index, e in enumerate(errors):
            assert np.shape(e)==np.shape(data[index])
        logger.info('Checked the errors dimensions: OK')

    rootgrp = netCDF4.Dataset(filename, "w", format="NETCDF4")
    dims = {}
    dim_vars = {}

    logger.debug('Creating dimensions.')
    # create the dimensions
    for i, (ax, name) in enumerate(zip(axes, axes_name)):
        dim = rootgrp.createDimension(name, len(ax))
        dim_var = rootgrp.createVariable(name, 'f8', (name,))
        dim_var[:] = ax.m
        dim_var.units = '{}'.format(ax.u)

        dims[name] = dim
        dim_vars[name] = dim_var

    # logger.debug('Creating extra dimensions.')
    # # create extra variables and dimensions for other parameters,
    # # fixed in the dataset
    # ex_dims = {}
    # ex_dim_vars = {}
    # if extra_dim is not None:
    #     for name, value in extra_dim:
    #         logger.debug('Adding coordinate: {}, with value: {}'.format(name, value))
    #         dim = rootgrp.createDimension(name, 1)
    #         dim_var = rootgrp.createVariable(name, 'f8', (name,))
    #         if isinstance(value, Q_):
    #             dim_var[:] = value.m
    #             dim_var.units = '{}'.format(value.u)
    #         else:
    #             dim_var[:] = value
    #
    #         ex_dims[name] = dim
    #         ex_dim_vars[name] = dim_var

    # fill the data

    logger.debug('Saving the data.')

    if errors is not None:
        logger.info('Data with errors. ')
        # append to detectors the errors
        #logger.debug('Appending to detectors: {} the errors.'.format(detectors))
        for index, e in enumerate(errors):
            detectors.append('error {}'.format(detectors[index]))
            data.append(e)
        #logger.debug('Detectors after appending: {}'.format(detectors))


    for detector, data in zip(detectors, data):
        u = data.u
        var = rootgrp.createVariable(detector, data.m.dtype, tuple(dims.keys())[::1])
        var[:] = data.m
        var.units = '{}'.format(u)

    # metadata
    logger.debug('Creating metadata in the netCDF4.')

    for k, v in extra_dims.items():
        logger.debug('Adding extra dimension: {} with value {}'.format(k, v))
        s = '{!s}'.format(v)
        #logger.debug('The value as a type = {} is {}'.format(type(s), s))

        if not isinstance(s, (str, float, int)):
            logger.warning("not saving extra dimension {} = {}".format(k, repr(s)))
            continue

        setattr(rootgrp, k, s)

    if description is None:
        rootgrp.description = 'No description given'
    else:
        rootgrp.description = description

    rootgrp.history = "Saved on {}".format(time.ctime(time.time()))
    rootgrp.creator = f'Hyperion package, version: {__version__}'
    # save
    rootgrp.sync()
    rootgrp.close()

def read_netcdf4_and_plot(filename):
    """Reads the file in filename and plots all the detectors """
    ds = xr.open_dataset(filename)
    logger.info('The dataset contains: {}'.format(ds))

    for index, name in enumerate(ds.data_vars):
        plt.figure(figsize=((12, 6)))
        ds[name].plot()
        plt.axes.set_axis = 'equal'
        plt.tight_layout()

    return ds

if __name__ == '__main__':
    import numpy as np
    import os
    import hyperion

    # uncomment the next line according to the test you would like to run.
    m = 'write and read'
    # m = 'read'

    # if to decide which mode to test
    if m == 'read':
        ## read
        folder = hyperion.log_path
        filename = os.path.join(folder, 'test_netcdf4_output.nc')
        logger.info(f'Now reading the data in file: {filename} ')
        # %% read the data
        ds = read_netcdf4_and_plot(filename)

    elif m == 'write and read':
        # write
        folder = hyperion.log_path
        filename = os.path.join(folder, 'test_netcdf4_output_with_error.nc')
        logger.info('Filename to save and read: {}'.format(filename))

        # fake dataset
        logger.info('Create a fake dataset to test the saving functions.')
        wavelength = 551 * ur('nm')
        extra_dim = {'wavelength': wavelength, 'temp': 300*ur('K'), 'points to average': 10, 'percent': ur('75 percent')}
        size = (300, 212)
        axes = []
        axes_name = []

        for index, s in enumerate(size):
            axes.append(np.linspace(0, 1, s) * ur('um'))
            axes_name.append('x{}'.format(index + 1))

        detectors = ['Photothermal', 'APD']
        units = ['V', 'cps']

        data_matrix = np.random.random(size)
        data = [data_matrix * ur(units[0]), data_matrix * 1e3 * ur(units[1])]
        logger.debug('The data is: {}'.format(data))
        error = [data_matrix * 0.01 * ur(units[0]), data_matrix * 0.01 * 1e3 * ur(units[1])]

            # data description
        data_description = []
        for i in range(len(data)):
            data_description.append('description for data {}'.format(i+1))
        logger.debug('The data description is: {}'.format(data_description))

        # save
        logger.info('Now saving the data...')
        save_netCDF4(filename, detectors, data, axes, axes_name, errors = error,
                     extra_dims = extra_dim,
                     description='This is fake data to test the saving process')

        # read the data
        logger.info('Now reading the data... ')
        ds = read_netcdf4_and_plot(filename)


