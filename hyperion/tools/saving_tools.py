# -*- coding: utf-8 -*-
"""
============
Saving tools
============

This is a collection of useful methods used along hyperion.

NOT DONE YET

"""
from hyperion import root_dir, ur
import os
import sys

def create_filename(self, file_path):
    """ creates the filename property in the class, so all the methods point to the same folder
    and save with the same name. The output does not include the extension but the input does.

    :param filename: config filename complete path
    :type filename: string (path)

    :return: filename
    :rtype: string

    """
    self.logger.debug('Input filename: {}'.format(file_path))
    i = 0
    ext = file_path[-4:]  # Get the file extension (it assumes is a dot and three letters)
    filename = file_path[:-4]
    self.root_path = os.path.split(filename)[0]

    while os.path.exists(file_path):
        file_path = '{}_{:03}{}'.format(filename, i, ext)
        i += 1

    self.filename = file_path[:-4]

    self.logger.debug('New filename: {}'.format(self.filename))
    return file_path


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