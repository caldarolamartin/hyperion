# -*- coding: utf-8 -*-
"""
============
Saving tools
============

This is a collection of useful methods related to saving data and metadata
used along hyperion.

:copyright: by Hyperion Authors, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.

"""
import os
import yaml
import copy
import netCDF4
import datetime as dt
import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
from hyperion.core import logman
from hyperion import __version__, ur, Q_

logger = logman.getLogger(__name__)


def yaml_dump_builtin_types_only(object, stream=None, mode='remove', replace_with='_invalid_', dump = True):
    """
    A replacement for yaml.dump that skips object that can't be dumped safely.
    Dictionaries and lists are searched recursively.
    It has 3 modes how to handle invalid entries:
    remove: removes the entry
    repr: replaces the object with object.__repr__()
    replace: replaces with the value in replace_with
    To return the modified object instead of dumping it, set dump to False

    :param object: The object to dump
    :param stream: The stream to save the yaml dump (default: None)
    :param mode (str): 'remove' (default), 'repr', 'replace'
    :param replace_with: What to replace the invalid entry with (default '_invalid_')
    :param dump (bool): Dumps to stream when True, returns modified object when False. (default: True)
    :return:
    """
    _mode = 0
    if mode.lower() == 'replace':
        _mode = 1
    elif mode.lower() == 'repr':
        _mode = 2
    elif mode.lower != 'remove':
        logger.warning('unknown mode {}, using default mode: remove'.format(mode))

    def _yaml_checker(object, parent=None, k=None):
        if type(object) is dict:
            for key in list(object):
                value = object[key]
                _yaml_checker(value, object, key)
        elif type(object) is list:
            for k, element in enumerate(object):
                _yaml_checker(element, object, k)
        else:
            try:
                yaml.safe_dump(object)
            except yaml.YAMLError:
                logger.info(['removed', 'replaced'][bool(_mode)]+' object of type {} (dict key or list element: {})'.format(type(object), k))
                if parent is None:
                    parent = object
                if _mode == 1:
                    parent[k] = replace_with
                elif _mode == 2:
                    parent[k] = parent[k].__repr__()
                else:
                    del parent[k]

    modified = copy.deepcopy(object)
    _yaml_checker(modified)
    if dump:
        yaml.safe_dump(modified, stream)
    else:
        return modified


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

    # If the name already exists and it looks like has an incrementer number, strip that incrementer number from the name
    # This avoid the case that if you put in name_1 and name_1 already exists that it will return name_1_1.
    # Now it would return name_2
    base_inc = basename.split(separator)
    if exact_match and len(base_inc) > 1 and str.isdigit(base_inc[-1]):
        basename = separator.join(base_inc[:-1])

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

    while os.path.exists(file_path):
        file_path = '{}_{:03}{}'.format(filename, i, ext)
        i += 1

    filename = file_path[:-4]

    return filename

def save_metadata(file_path, properties):
    """ Saves the the properties in a yml file at the file file_path

    :type file_path: str
    :param properties: dictionary containing the me    :param file_path: complete filepath to the location to be saved.
tadata
    :type properties: dict


    """
    filename = create_filename(file_path)

    logger.debug('Filename: {}'.format(filename))
    file_path = filename + '.yml'
    logger.debug('Complete file path: {}'.format(file_path))

    with open(file_path, 'w') as f:
        yaml.dump(properties, f, default_flow_style=False)

    logger.info('Metadata saved to {}'.format(file_path))

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
    :param errors: measured errors for each of the detectors. It has to have the same dimensions as data.
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

    # I create a dummy variable to avoid changing the detectors structure with the addition of errors
    detectors_to_save = []
    for d in detectors:
        detectors_to_save.append(d)

    data_to_save = []
    for d in data:
        data_to_save.append(d)

    _error_status = False

    if errors is not None:
        _error_status = True
        logger.info('Data with erros.')
        assert len(errors)==len(data)
        for index, e in enumerate(errors):
            assert np.shape(e)==np.shape(data[index])
        logger.info('Checked the errors dimensions: OK')

    with netCDF4.Dataset(filename, "w", format="NETCDF4") as rootgrp:

        # add an attribute to indicate the presence of errors
        rootgrp.setncatts({'_error_present': str(_error_status)})

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

        # fill the data
        logger.debug('Saving the data.')

        if errors is not None:
            logger.info('Data with errors. ')
            # append to detectors the errors
            #logger.debug('Appending to detectors: {} the errors.'.format(detectors))
            for index, e in enumerate(errors):
                detectors_to_save.append('error {}'.format(detectors[index]))
                data_to_save.append(e)
            #logger.debug('Detectors after appending: {}'.format(detectors))

        # save data and errors (if present)
        for detector, data in zip(detectors_to_save, data_to_save):
            u = data.u
            var = rootgrp.createVariable(detector, data.m.dtype, tuple(dims.keys())[::1])
            var[:] = data.m_as(u)
            var.units = '{}'.format(u)

        # metadata
        logger.debug('Creating metadata in the netCDF4.')

        for k, v in extra_dims.items():
            # if to avoid writing the data and the errors as atributes too.
            if k=='data' or k=='error' or k=='errors':
                logger.debug('Ignoring extra dimension: {}'.format(k))
            else:
                logger.debug('Adding extra dimension: {} with value {}'.format(k, v))
                s = '{!s}'.format(v)

                if not isinstance(s, (str, float, int)):
                    logger.warning("not saving extra dimension {} = {}".format(k, repr(s)))
                    continue

                setattr(rootgrp, k, s)

        if description is None:
            rootgrp.description = 'No description given'
        else:
            rootgrp.description = description

        rootgrp.history = "Saved on {}".format(dt.datetime.now().strftime("%Y/%m/%d, %H:%M:%S"))
        rootgrp.creator = f'Hyperion package, version: {__version__}'
        # save
        rootgrp.sync()
    # rootgrp.close()

def read_netcdf4_and_plot_all(filename):
    """Reads the file in filename and plots all the detectors """

    # handle errors to plot with errors
    _error = False
    # read the dataset
    ds = xr.open_dataset(filename)
    logger.info('The dataset contains: {}'.format(ds))

    if '_error_present' in ds.attrs.keys():
        if ds.attrs['_error_present'] in ('True', 'true','yes'):
            _error = True
        else:
            _error = False

    logger.debug('The error state is: {}'.format(_error))

    # plot according to the presence of errors or not.
    if _error:
        logger.info('The dataset contains errors.')
        for index, name in enumerate(ds.data_vars):
            if index == len(ds.data_vars.items()) / 2:
                break
            plt.figure(figsize=((9, 7)))
            plt.subplot(2, 1, 1)
            ds[name].plot()
            plt.axes.set_axis = 'equal'
            plt.subplot(2, 1, 2)
            ds['error {}'.format(name)].plot()
            plt.axes.set_axis = 'equal'
            plt.tight_layout()
    else:
        logger.info('The dataset does not contain errors.')
        for index, name in enumerate(ds.data_vars):
            plt.figure(figsize=((10, 6)))
            ds[name].plot()
            plt.axes.set_axis = 'equal'
            plt.tight_layout()

    return ds

if __name__ == '__main__':
    # this are examples of reading and writing dummy data. NOTE: it saves in the log path!
    
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
        ds = read_netcdf4_and_plot_all(filename)

    elif m == 'write and read':
        # write
        folder = hyperion.log_path
        filename = 'test_netcdf4_output'

        logger.info('Filename to save and read: {}'.format(os.path.join(folder,filename+'.nc')))

        # fake dataset
        logger.info('Create a fake dataset to test the saving functions.')
        wavelength = 551 * ur('nm')
        extra_dim = {'wavelength': wavelength, 'temp': 300*ur('K'), 'points to average': 10, 'percent': ur('75 percent')}
        size = (3, 2, 4)
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
        logger.info('Now saving the data without errors...')
        save_netCDF4(os.path.join(folder,filename+'.nc'), detectors, data, axes, axes_name, errors = None,
                     extra_dims = extra_dim,
                     description='This is fake data to test the saving process')

        logger.info('Now saving the data with errors...')
        save_netCDF4(os.path.join(folder,filename+'with_errors.nc'), detectors, data, axes, axes_name, errors = error,
                     extra_dims = extra_dim,
                     description='This is fake data to test the saving process')

        # read the data
        logger.info('Now reading the data and ploting withOUT errors... ')
        ds = read_netcdf4_and_plot_all(os.path.join(folder, filename+'.nc'))

        logger.info('Now reading the data and ploting with errors... ')
        ds = read_netcdf4_and_plot_all(os.path.join(folder,filename+'with_errors.nc'))



