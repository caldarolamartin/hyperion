=====================
Hyperion Architecture
=====================

In this project we try to use general structure known as **MVC**: **Model**, **View**, **Controller**,
used for websites. We take some ideas from there and put it together with some of our ideas.

In a nutshell, we use an onion principle to isolate the code that interacts
with the instruments directly from the code that builds up the user interface.

General structure
=================

The **controller** refers to the lowest level, where the actual
communication with the devices happens. We use the language
of the devices at this level.

The **instrument** is an intermediate layer where we abstract the
specifics of the device into a more general mode.
This helps to adapt to the view layer. It is the name we give to the model layer in
the MVC, since it is more suitable for instrumentation projects.

Several instruments are condensed together to form an **experiment**
where you can perform different measurements. In the folder examples
you can find a few explanatory files that show how to use the complete package.

The **view** is all that concerns the graphical user interface (GUI) of the
applications. It consist of files that build up the GUI and some extra python
files to load all the modules needed to run it. Under the hook, this uses the
classes from the lower levels. You can have a GUI for an instrument, that
connects only to one device or a GUI for an experiment that connects to several
devices. The design principle here is that any experiment and measurement should
be independent of the view layer and thus can be run by just running code up to the
experiment layer (not using the view layer). Then the view layer can be
optional for users that require the graphical control of their experiment.

Important concepts
==================

Controller:

Instrument:

Meta-Instrument:

Experiment:

View:


.. toctree::
    :maxdepth: 2
    :caption: General structure:

    controllers
    experiment
    instrument
    test
    tools
    view
    core



