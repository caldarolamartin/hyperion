from hyperion.controller.thorlabs.TDC001 import TDC001
checkdevices = TDC001()
checkdevices.list_available_device()
[(31,81818251)]
motorx = TDC001()
motorx.initialize(81818251)
motorx.move_home(True)
motorx.move_by(0.01)