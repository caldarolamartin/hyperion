# -*- coding: utf-8 -*-
"""

WORK IN PROGRESS <<<<<<<<<<<<<<<<<<<<<<<<<<

Created on Mon Dec  2 13:33:11 2019

@author: aopheij


The idea for saving is to have:
    - One BaseSaver class that holds only basic functionality and version compatability.
    - Multiple different versions classes that can inherit from BaseSaver and from eachother.
    - One wrapper function that returns the right saver version.

from hyperion.tools import Saver
datastore = Saver('filename.h5', version=0.1)

"""
# import hyperion
import os
import logging
import h5py
import time


class BaseSaver:
    """
    Base class to handle a few basic
    """

    # Default version to use
    default_version = 0.123

    # Valid version identifier floats:
    #    valid_versions = [0.1, 0.02, 0.01]
    # Compatability: per version specify which range of old (and new) versions are silimar enough
    #    file_version_compatability = {
    #            0.10: valid_versions,
    #            0.02: [v for v in valid_versions if 0.01<=v<=0.02],
    #            0.01: [0.01] }

    def __init__(self, filepath, version=default_version, write_mode='w'):
        self.logger = logging.getLogger(__name__)
        self.version = version
        self.filepath = filepath
        self.write_mode = write_mode
        print('BaseSaver init')

    @classmethod
    def valid_versions(cls):
        """ Returns dictionary of valid versions of Saver classes. """
        valid = {}
        for sub in cls.__subclasses__():
            valid[sub.version] = sub
        return valid

    @classmethod
    def compatible(cls, v1, v2):
        """ Returns tuple """
        valid = BaseSaver.valid_versions()
        print(valid)
        #        if v1 not in valid.keys():
        #            raise Exception(('{} is not a known valid version'.format(v1))
        #        if v2 not in valid.keys():
        #            raise Exception(('{} is not a known valid version'.format(v2))
        b1 = valid[v1].backward_compatible
        if type(b1) is str and b1[0].lower() == 'a':
            b1 = [v for v in sorted(valid.keys()) if v <= v1]
        f1 = valid[v1].forward_compatible
        if type(f1) is str and f1[0].lower() == 'a':
            f1 = [v for v in sorted(valid.keys()) if v >= v1]
        return v2 in b1, v2 in f1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.h5.close()

    def close(self):
        self.h5.close()


def Saver(*args, version=BaseSaver.default_version, **kwargs):
    """
    Wrapper to use different classes based on the version.
    If an unknown version is specified, the newest will be used.
    See the different versions for details on how to use them.
    """
    # Get all child classes of BaseSaver and their version number:
    versions = [cl.version for cl in BaseSaver.__subclasses__()]
    if version not in versions:
        invalid = version
        version = sorted(versions)[-1]
        logging.getLogger(__name__).warning('Unknown version {}, using {} instead'.format(invalid, version))
    return BaseSaver.__subclasses__()[versions.index(version)](*args, **kwargs)


class Saver_v0p1(BaseSaver):
    # IMPORTANT: When inheriting from other version, ALSO inherit from BaseSaver
    version = 0.1  # manditory unique identification float
    # Specify version compatabilities (list of floats or 'all' or [])
    backward_compatible = 'all'
    forward_compatible = [0.2]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print('init v0.1')

    def open_file(self):
        valid = True
        version = self.version
        if version not in self.file_version_compatability.keys():
            self.version = sorted(self.file_version_compatability.keys)[-1]
            self.logger.warning("Invalid version {}, using version {} instead".format(version, self.version))
        valid = False
        while not valid:
            if os.path.isfile(self.filepath) and self.write_mode is not 'w':
                self.logger.warning('File exists: {}'.format(self.filepath))
                time.sleep(1)
                if not append:
                    inp = input('File exists. choose [D]ifferent filename, try to [M]odify/append, or [Overwrite]: ')
                    if len(inp) and inp[0].lower() == 'd':
                        self.filepath = input('New file name: ')
                        continue
                    if len(inp) and inp[0].lower() == 'm': self.write_mode = 'a'
                else:
                    try:
                        self.h5 = h5py.File(filepath, 'a')
                    except OSError as e:
                        self.logger.warning("Can't open file. Exception: {}".format(e))
                        continue
                    if 'hyperion_file_version' not in self.h5.attrs:
                        print("Can't try to append/modify file because not a hyperion file type.")
                        self.h5.close()
                        append = False
                        time.sleep(1)
                        continue
                    else:
                        file_version = self.h5.attrs['hyperion_file_version']
                        if file_version not in self.file_version_compatability[self.version]:
                            print("Can't modify version {} file with version {} settings.".format(file_version,
                                                                                                  self.version))
                            self.h5.close()
                            append = False
                            time.sleep(1)
                            continue
                    print('Modifying existing file')
                    self.h5.attrs['hyperion_file_modified'] = self.version
                    valid = True
            else:
                try:
                    self.h5 = h5py.File(filepath, 'w')
                except OSError as e:
                    self.logger.warning("Can't create file. Exception: {}".format(e))
                    continue
                self.h5.attrs['hyperion_file_version'] = self.version


class Saver_v0p2(Saver_v0p1, BaseSaver):
    # IMPORTANT: When inheriting from other version, ALSO inherit from BaseSaver
    version = 0.2  # manditory unique identification float
    # Specify version compatabilities (list of floats or 'all' or [])
    backward_compatible = 'all'
    forward_compatible = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print('init v0.2')

#
# class autosaver:
#    """
#    :param filepath:
#    :param experiment:
#    :param version:
#    :param append:
#    """
#
#    file_version_compatability = {0.10:[0.1, 0.02, 0.01],
#                                  0.02:[0.1, 0.02, 0.01],
#                                  0.01:[0.01]}
#    def __init__(self, filepath, experiment=None, version=0.1, write_mode='?', dialogs=None):
#        self.logger = logging.getLogger(__name__)
#        self.version = version
#        self.filepath = filepath
#        self.write_mode = write_mode
#
#
#    def open_file_v0p1(self):
#        version = self.version
#        if version not in self.file_version_compatability.keys():
#            self.version = sorted(self.file_version_compatability.keys)[-1]
#            self.logger.warning("Invalid version {}, using version {} instead".format(version, self.version))
#        valid = False
#        while not valid:
#            if os.path.isfile(self.filepath) and self.write_mode is not 'w':
#                self.logger.warning('File exists: {}'.format(self.filepath))
#                time.sleep(1)
#                if not append:
#                    inp = input('File exists. choose [D]ifferent filename, try to [M]odify/append, or [Overwrite]: ')
#                    if len(inp) and inp[0].lower()=='d':
#                        self.filepath = input('New file name: ')
#                        continue
#                    if len(inp) and inp[0].lower()=='m': self.write_mode='a'
#                else:
#                    try:
#                        self.h5 = h5py.File(filepath, 'a')
#                    except OSError as e:
#                        self.logger.warning("Can't open file. Exception: {}".format(e))
#                        continue
#                    if 'hyperion_file_version' not in self.h5.attrs:
#                        print("Can't try to append/modify file because not a hyperion file type.")
#                        self.h5.close()
#                        append = False
#                        time.sleep(1)
#                        continue
#                    else:
#                        file_version = self.h5.attrs['hyperion_file_version']
#                        if file_version not in self.file_version_compatability[self.version]:
#                            print("Can't modify version {} file with version {} settings.".format(file_version, self.version))
#                            self.h5.close()
#                            append = False
#                            time.sleep(1)
#                            continue
#                    print('Modifying existing file')
#                    self.h5.attrs['hyperion_file_modified'] = self.version
#                    valid = True
#            else:
#                try:
#                    self.h5 = h5py.File(filepath, 'w')
#                except OSError as e:
#                    self.logger.warning("Can't create file. Exception: {}".format(e))
#                    continue
#                self.h5.attrs['hyperion_file_version'] = self.version
#                valid = True
#
#    def __enter__(self):
#        return self
#
#    def __exit__(self, exc_type, exc_val, exc_tb):
#       self.h5.close()
#
#    def coord(self):
#        pass
#
#    def data(self, name, data, flush=True):
#        """
#
#
#        :param name: Unique name (suggested to use actiondict['Name'])
#        :return:
#        """
#        pass
#        # self.exp._nesting_parents
#        # self.exp._nesting_indices
#
#
#
#
if __name__=='__main__':
    import os.path
    import hyperion

    fname = os.path.join(hyperion.parent_path, 'savedir', 'test_01.h5')
    s = Saver(fname, version=0.1)