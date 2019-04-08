=====================
Hyperion Architecture
=====================


In this project we try to use general structure known as **MVC**: **Model**, **View**, **Controller**,
used for websites. We take some ideas from there and put it together with some of our ideas.

In a nutshell, we use an onion principle to isolate the code that interacts
with the instruments directly from the code that builds up the user interface.

The **controller** refers to the lowest level, where the actual
communication with the devices happens. We use the language
of the devices at this level.

The **instrument** is an intermediate layer where we abstract the
specifics of the device into a more general mode.
This helps to adapt to the view layer.

The **view** is all that concerns the graphical user interface (GUI) of the
applications. It consist of files that build up the GUI and some extra python
files to load all the modules needed to run it. Under the hook, this uses the
classes from the lower levels.

There is an intermediate layer that puts models together and uses them
in combination that we call **experiment**. Such classes are designed
for a specific aim, for example, a calibration experiment, taking a spectra or
performing a scan of one of the parameters available. Such tasks usually need
the use of many devices that are controlled through their respective models.