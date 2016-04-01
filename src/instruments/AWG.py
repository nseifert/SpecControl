import os
import sys

from Instrument import Instrument, MissingParameterError
from ..data_obj.ArbPulse import ArbPulse
import visa
import pyvisa.errors
import numpy as np
import paramiko
import collections
import tempfile

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
        rsa_key = paramiko.RSAKey.from_private_key_file(filename=self.key_path, password=read_pass(self.rsa_pass))

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=self.ip_addr, username='OEM', port=22, pkey=rsa_key, look_for_keys=False)

        return ssh, ssh.open_sftp()

    def upload_pulse(self, sock, pulse):

        local_file = os.path.abspath('C:\\Users\\jaeger\\AppData\\Local\\Temp\\'+pulse.filename)
        np.savetxt(local_file, pulse.pulse, delimiter='\t')
        remote_path = os.path.abspath('C:\Pulses\\'+pulse.filename)

        result = sock.put(local_file, remote_path)
        os.remove(local_file)

        return remote_path

    def get_pulses(self):
        return self._pulses

    def __init__(self, visa_connect = 1, **kwargs):

        if 'visa_connect' in kwargs.keys():
            super(AWG, self).__init__(**kwargs)

        acceptable_kwargs = ['ip_addr', 'key_path', 'pass_path', 'pulse', 'local_pulse', 'remote_pulse', 'rsa_pass']
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
                return obj
            else:
                return (obj,)

        conditions = [x in self.__dict__ for x in ['pulse', 'local_pulse', 'remote_pulse']]
        if sum(map(bool, conditions)) == 0:
            raise MissingParameterError("A pulse object or path was not specified.")

        elif sum(map(bool, conditions)) > 1:
            raise MissingParameterError("Please specify at most one pulse attribute during initialization.")

        else:
            print 'Init SFTP socket...'
            self.__sshclient, self.__transport = self.connect_sftp()
            print 'SFTP init successful.'
            try:
                for pul in get_iterable(self.pulse):
                    self.pulse_log = []
                    print 'Uploading pulse...'
                    res = self.upload_pulse(self.__transport, pul)
                    print 'Upload successful.'
                    self.pulse_log.append([res, repr(pul)])

            except AttributeError:
                raise

            self.__transport.close()

            # elif 'local_pulse' in self.__dict__:  # Process ASCII pulse file(s) locally
            #     self._transport = self.connect_sftp()
            #
            # else:  # Select pulse already on AWG. Should check for passing remote pulses here
            #     pass
