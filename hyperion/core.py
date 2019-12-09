import os


class Singleton(type):
    """
    Metaclass to use for classes of which you only want one instance to exist.
    use like: class MyClass(ParentClass, metaclass=Singleton):
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ANSIcolorFormat:
    """
    Class used as a wrapper function to apply colors to console prints.
    Arguments are the string followed by one or more color 'decorators':
    First letter of basic colors: r, g, y, b, m, c, w for white, k for black.
    Letter Preceded by an l means a lighter/brighter color (if supported).
    Letter(s) preceded by an underscore '_' means background color.
    Notes on PyCharm: 'emph' creates bold text. Darcula mode changes colors
    into bland "pastel-like" colors  and inverts pure white and black.
    Notes on general command/prompt window: 'emph' turns dark text to bright.
    Notes on Spyder: Does not support "light" colors with an "l", 'emph'/'norm'
    turns both text and background simultaneously to bright/dim.

    The 'decorators' can be passed as multiple arguments or a tuple or a list.
    A single string of ansi color code is also accepted (e.g. '1;46;31')
    If no additional arguments or the argument None is passed it returns the
    message without adding ansi color codes.
    The enabled property allows for toggling all color action of this object at once.
    The class method disable_all() allows to disable all color printing of all objects.

    Note: It's also possible to do from hyperion.core import ansicol
          Then you're using the same object (i.e. toggling that object will influence all)

    Example usage:
        from hyperion.core import ANSIcolorFormat
        ansicol = ANSIcolorFormat()
        print(ansicol('Hello World','emph','r','_y'))
        print(ansicol('Hello World')
        ansicol.enabled = False
        print(ansicol('Hello World','emph','r','_y'))
    """
    col_dict = {
        'emph': '1',  # bold or bright
        'norm': '2',  # normal / dim
        # Regular command window:
        # (Tested on Win7 and Win10: CMD, Anaconda prompt, Anaconda PowerShell propmt and PowerShell (Win10))
        # Does not make text bold, only makes foreground (text color) bright.
        # Spyder:
        # Making bright acts on both foreground and background simultaneous.
        # Black text on bright background is still possible by not specifying text color.
        # Does not make text bold
        # PyCharm:
        # Actually makes text bold, does not affect brightness

        'k': '30',  # black
        'r': '31',  # red
        'g': '32',  # green
        'y': '33',  # yellow
        'b': '34',  # blue
        'm': '35',  # magenta
        'c': '36',  # cyan
        'w': '37',  # white (grey)
        '_k': '40',  # black background
        '_r': '41',  # red background
        '_g': '42',  # green background
        '_y': '43',  # yellow background
        '_b': '44',  # blue background
        '_m': '45',  # magenta background
        '_c': '46',  # cyan background
        '_w': '47',  # white (grey) background
        # PyCharm in Darcula mode changes colors into bland "pastel-like" colors,
        # and inverts pure white and black

        'lk': '90',  # "light black"
        'lr': '91',  # light red
        'lg': '92',  # light green
        'ly': '93',  # light yellow
        'lb': '94',  # light blue
        'lm': '95',  # light magenta
        'lc': '96',  # light cyan
        'lw': '97',  # bright white
        '_lk': '100',  # "light black" background
        '_lr': '101',  # light red background
        '_lg': '102',  # light green background
        '_ly': '103',  # light yellow background
        '_lb': '104',  # light blue background
        '_lm': '105',  # light magenta background
        '_lc': '106',  # light cyan background
        '_lw': '107'  # bright white background
        # These are not always supported (e.g. not supported in Spyder IPython)
    }

    # class attributes:
    __disable_all = False
    __colorama_enabled = False
    __in_spyder = any('SPYDER' in name for name in os.environ)

    @staticmethod
    def disable_all(boolean):
        """
        Class Method (with boolean input) to disable all color printing of all ANSIcolorFormat objects at once.
        Useful if your system can't deal with ANSI color codes.
        Note that this will overrule the enabled state of individual objects.
        Being a class method this can be run both on an object and directly on the class, like
        ANSIcolorFormat.disable_all(False)
        """
        ANSIcolorFormat.__disable_all = boolean

    def __init__(self, enable=True):
        self.enabled = enable

    @property
    def enabled(self):
        """
        Boolean property to get or set whether this ANSIcolorFormat object is enabled.
        If enabled is false it will not print colors.
        Note that the class disabled_all state overrules this object state.
        To enable you may also have to do .disable_all(False) on the object or on the class.

        """
        return self._enabled and not ANSIcolorFormat.__disable_all

    @enabled.setter
    def enabled(self, boolean):
        if boolean:
            if ANSIcolorFormat.__disable_all:
                print('WARNING: also enable all by .disable_all(False)' )
            if not ANSIcolorFormat.__colorama_enabled and not ANSIcolorFormat.__in_spyder:
                import colorama
                colorama.init()
                ANSIcolorFormat.__colorama_enabled = True
        self._enabled = boolean

    def __call__(self, msg, *args):
        if not self.enabled or len(args) == 0 or args[0] is None:
            return msg
        try:
            if len(args) == 1:
                if type(args[0]) is str and args[0][0].isdigit():
                    return '\033[' + args[0] + 'm' + msg + '\033[0m'
                elif type(args[0]) is tuple or type(args[0]) is list:
                    args = args[0]
            if ANSIcolorFormat.__in_spyder and any('l' in c for c in args):
                print('WARNING: the "light" colors are not supported in Spyder')
            return '\033[' + ';'.join([self.col_dict[c] for c in args]) + 'm' + msg + '\033[0m'
        except KeyError:
            print('ERROR: incorrect color code')
            return msg

# Already create an object that can be imported if one prefers
ansicol = ANSIcolorFormat()