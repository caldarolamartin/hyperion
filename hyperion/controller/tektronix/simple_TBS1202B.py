import visa
import time
import numpy as np


class TBS1202B():
    """Tektronix TBS1202 200MHz 2 Channel Digital Storage Oscilloscope

    """
    rsc = None
    DEFAULTS = {'instrument_id': '0x0368'
                }

    def __init__(self, instrument_id):
        self.instrument_id = instrument_id

    def initiate(self):
        self.resource_name = 'USB0::0x0699::' + self.instrument_id + '::C020303::INSTR'
        rm = visa.ResourceManager()
        self.rsc = rm.open_resource(self.resource_name)
        time.sleep(0.5)

    def idn(self):
        """Identification

        """
        return self.rsc.query('*IDN?')

    def forcetrigger(self):
        """ Creates a trigger event.
        """
        self.rsc.write('TRIG:FORC')
        return

    def get_acquire_state(self):
        """ Gets the state of the acquisition

        """

        return osc.rsc.query('ACQUIRE:STATE?')

    def acquire_parameters(self):
        """ Acquire parameters of the osciloscope.
            It is intended for adjusting the values obtained in acquire_curve
        """
        values = 'XZE?;XIN?;PT_OF?;YZE?;YMU?;YOF?;'
        answer = self.rsc.query('WFMP:{}'.format(values))
        parameters = {}
        for v, j in zip(values.split('?;'), answer.split(';')):
            parameters[v] = float(j)
        return parameters

    def acquire_curve(self, start=1, stop=2500):
        """ Gets data from the oscilloscope. It accepts setting the start and
            stop points of the acquisition (by default the entire range).
        """
        parameters = self.acquire_parameters()
        self.rsc.write('DAT:ENC ASCI;WID 2')
        self.rsc.write('DAT:STAR {}'.format(start))
        self.rsc.write('DAT:STOP {}'.format(stop))
        data = self.rsc.query('CURV?')
        data = data.split(',')
        data = np.array(list(map(float, data)))
        ydata = (data - parameters['YOF']) * parameters['YMU'] + parameters['YZE']
        xdata = np.arange(len(data)) * parameters['XIN'] + parameters['XZE']
        return list(xdata), list(ydata)


if __name__ == "__main__":
    osc = TBS1202B('0x0368')
    osc.initiate()
    print('Osciloscope Identification: {}'.format(osc.idn()))

    print('Try to get a curve')
    data = osc.acquire_curve()
    print(data)
