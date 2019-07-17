"""
general_worker class, this class is used for
threading the GUI, the instrument needs to get a different thread.
The class is named general because it will run anything you say it must run.
"""
from PyQt5 import QtCore


class WorkThread(QtCore.QThread):
    def __init__(self, function, *args, **kwargs):
        """
        When the WorkThread is called a function is being given to the class
        to run. Besides there is no limit of arguments that can be given with the given function.
        :param function: this is the function the thread is going to run.
        :param args: a way of notation to get any number of variables(with the *args)
        :param kwargs: a way of notation to get any number of variables(with the *kwargs)
        :param is_running: a parameter to see if the function is still running. 
        """
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False

    def __del__(self):
        self.is_running = False
        self.wait()

    def run(self):
        self.is_running = True
        self.function(*self.args,**self.kwargs)
        return

