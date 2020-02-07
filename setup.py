import sys
import setuptools
version = '0.5'

# list of required packages
install_requires = [
        'pip>=19',          # Why >=19 ? Will 18 fail?
        'numpy>=1.16',
        'pyqtgraph>=0.10',  # For plotting in Qt
        'pyqt5>5.8,<=5.13.0',# 5.13.1 - 5.14 causes some weird wide layouts that take up too much space
        'colorama',         # used for logging with color in terminal
        'lantz_core',
        'lantz_drivers',
        'lantz_qt',
        'lantz_sims',
        'pyserial',         # for serial communication (COM, USB)
        'pynput',           # for detecting keyboard
        'netcdf4>=1.4',     # used for saving data
        'xarray',           # used opening saved data
        'matplotlib',       # When all plotting is changed to pyqtgraph this could be removed
        # 'scipy',            # removed this requirement because we're not using it
        # 'pyvisa-py',        # removed this requirement because we're not using it
        # 'sphinx',           # removed because it's not required for just depending on hyperion (keep it in environment.yml though)
    ]

# this is to check if the system is 32 or 64 bits and add the 32bit dependencies
if sys.maxsize < 2**33:
    install_requires.append('pywin32')

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Hyperion",
    version="{}".format(version),
    author="See Authors",
    license='BSD',
    description="A small python package to control devices in the Kuipers lab @ TU Delft",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/nanooptics-code/hyperion.git",
    python_requires='>=3.7',
    packages=setuptools.find_packages(),
    install_requires = install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries',
    ],
)