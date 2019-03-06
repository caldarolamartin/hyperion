import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="NanoCD",
    version="0.1-dev",
    author="Martin Caldarola",
    license='BSD',
    author_email="m.caldarola@tudelft.nl",
    description="A small package to control the NanoCD setup",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/nanooptics-code/experiments/nanocd.git",
    python_requires='==3.7',
    packages=setuptools.find_packages(),
    install_requires = [
        'numpy==1.15',
        'scipy',
        'sphinx',
        'pyqt==5.9.2',
        'pyqtgraph==0.10.0',
        'lantz_core',
        'lantz_drivers',
        'lantz_qt',
        'lantz_sims',
        'lantz',
        'pyvisa-py'],
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