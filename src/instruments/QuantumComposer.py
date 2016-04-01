from Instrument import Instrument, MissingParameterError
import visa
import string
import pyvisa.errors
import datetime


class QuantumComposer(Instrument):

    def configure(self, channels):
        al_dict = dict(zip(string.letters, [ord(c) % 32 for c in string.letters]))
        chan_cmd = {"Width": "WIDT", 'Delay': 'DEL', 'Mode': 'CMOD',
                      'Polarity': 'POL', 'Sync': 'SYNC'}
        global_cmd = {'ExtTrig': 'TRIG:MOD', 'TrigEdge': 'TRIG:EDG', 'TrigLevel': 'TRIG:LEV',
                      'ExtRef': 'CL'}

        # Process global values, which are in the first entry of channels
        global_sys = channels['global']
        for global_sett in global_sys:
            self.execute(":PULSE0:%s %s" %(global_cmd[global_sett], global_sys[global_sett]))

        global_loc = channels['local']
        for chan in global_loc:

            chan_id = al_dict[chan['Channel']]
            self.execute(":PULSE%i:STATE ON" % chan_id)

            # Default commands that are globally necessary
            self.execute(":PULSE%i:OUTP:MOD TTL" % chan_id)

            for setting in chan:
                if setting == "Channel":
                    continue
                else:
                    self.execute(":PULSE%i:%s %s" %(chan_id, chan_cmd[setting], chan[setting]))
        return 1

    def start(self):
        self.execute(":PULSE0:STATE ON")

    def stop(self):
        self.execute(":PULSE0:STATE OFF")

    def __init__(self, **kwargs):

        # For converting from alphabetic channels to numeric
        self.alpha_to_num = {chr(i): i+1 for i in range(ord("a"), ord("a")+26)}
        self.cmd_log = []

        super(QuantumComposer, self).__init__(**kwargs)

        acceptable_kwargs = ['channels']
        for k in kwargs.keys():
            if k in acceptable_kwargs:
                self.__setattr__(k, kwargs[k])

        if 'channels' not in self.__dict__.keys():
            raise MissingParameterError('You did not specify any configuration settings for the Quantum Composer.')
        else:
            configuration_result = self.configure(self.channels)
            if configuration_result:
                print '%s configured successfully.' % self.name


if __name__ == '__main__':

    channels = {'global': {'ExtTrig': 'TRIG', 'TrigEdge': 'RIS', 'TrigLevel': 1.0,
                 },
                'local': [{'Channel': 'A', 'Width': 0.02, 'Delay': 0.005,
                 'Mode': 'SING', 'Polarity': 'NORM'}
                          ]
                }

    QC = QuantumComposer(ip_addr="192.168.1.101", name='QC9520 Pulse Gen', channels=channels, connect_raw=1)
    QC.print_log()