==========
Experiment
==========

In the Experiment folder we have a special set of classes the
Experiments. This are classes talking to many instruments
simultaneously and actually doing what is needed to
measure some physical parameter of interest.

The basic example is to perform a scan: one physical parameter
is sweep and for each of these values some other quantity is
measured.

Every time we have to run an automatic experiment we write the
class that contains all the methods needed to set it up, run and save
the obtained data.

Of course, more complex experiments where many things are changed (or
fixed) can be done.

.. toctree::
    :maxdepth: 2
    :caption: Current experiments:



