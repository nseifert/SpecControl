from Instrument import Instrument, MissingParameterError
from ..data_obj import ArbPulse
import visa
import pyvisa.errors
import paramiko
import os
import collections

class AWG(Instrument):
    """
    Plans:
    1) Use paramiko to transfer pulse, if needed, using SFTP.
    2) Loading local pulse is likely possible using VISA commands, will have to check.
    3) Need to implement necessary VISA setup.
    """

    def connect_sftp(self):

        def read_pass(path):
            if os.path.exists(path):
                return open(path, 'r').read().strip()
            else:
                return path

        _pkey = paramiko.RSAKey(filename=self.key_path, password=read_pass(self.rsa_pass))
        _transport = paramiko.Transport(sock=(self.ip_addr, 22))
        _transport.connect(hostkey=None, username="OEM", pkey=self._pkey)

        return _transport

    def upload_pulse(self, sock, pulse):
        pass

    def get_pulses(self):
        return self._pulses

    def __init__(self, visa_connect = 1, **kwargs):

        if 'visa_connect' in kwargs.keys():
            super(AWG, self).__init__(**kwargs)

        acceptable_kwargs = ['ip_addr', 'key_path', 'pass_path', 'pulse', 'local_pulse', 'remote_pulse']
        for k in kwargs.keys():
            if k in acceptable_kwargs:
                self.__setattr__(k, kwargs[k])

        """
        Here we want to specify how to do pulse handling. Potential options:
        - Input ArbPulse object
        - Specify name of pulse already on AWG
        - Specify path of previously made local AWG pulse

        """

        def get_iterable(obj):  # Helper function to process multiple pulses below
            if isinstance(obj, collections.Iterable) and not isinstance(x, basestring):
                return x
            else:
                return (x,)

        conditions = [x in self.__dict__ for x in ['pulse', 'local_pulse', 'remote_pulse']]

        if sum(map(bool, conditions)) == 0:
            raise MissingParameterError("A pulse object or path was not specified.")

        elif sum(map(bool, conditions)) > 1:
            raise MissingParameterError("Please specify at most one pulse attribute during initialization.")

        else:
            if 'pulse' in self.__dict__:  # Process ArbPulse object(s)
                self._transport = self.connect_sftp()

                for pul in get_iterable(self.pulse):
                    self._pulses = []
                    try:
                        self.upload_pulse(self._transport, pul)
                    except:
                        raise
                    else:
                        self._pulses.append(repr(pul))

            elif 'local_pulse' in self.__dict__: # Process ASCII pulse file(s) locally
                self._transport = self.connect_sftp()

            else:  # Select pulse already on AWG. Should check for passing remote pulses here
                pass

key_path = os.path.abspath('C:\\Users\\jaeger\\.ssh\\id_rsa')
pass_path = os.path.abspath('C:\\Users\\jaeger\\Desktop\\SpecControl\sec\pass.pass')
AWG(ip_addr='192.168.1.102', key_path=key_path, rsa_pass=pass_path)

