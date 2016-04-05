import os
import sys
from Instrument import *
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

    def set_srate(self, chan, srate="12E9"):
        self.execute(":AWGC:RRAT 22.222222E+3")  # Set max repetition rate for DAC
        self.execute(":SOUR%s:FREQ %.1g" %(chan, srate))

    def set_ref(self, chan):
        self.execute(":AWGC:CLOC:SOUR INT")
        self.execute(":SOUR%d:ROSC:SOUR EXT" % chan)
        self.execute(":SOUR%d:ROSC:TYPE FIX" % chan)
        self.execute(":SOUR%d:ROSC:FREQ 10MHz" % chan)

    def set_trig(self, level=1.4, pol='POS', imped='1kohm'):
        self.execute(":TRIG:SOUR EXT")
        self.execute(":TRIG:LEV %.1f" % level)  # Set voltage min cutoff for trig in V
        if pol not in ['POS', 'NEG']:
            self.execute(":TRIG:SLOP POS")
        else:
            self.execute(":TRIG:SLOP %s" % pol)
        if imped not in ['1kohm', '50ohm']:
            self.execute(":TRIG:IMP 1kohm")
        else:
            self.execute(":TRIG:IMP %s" % imped)

    def run_mode(self, attrib):
        valid_cont_vals = ['cont', 'continuous']
        valid_trig_vals = ['trig', 'triggered']
        if attrib.lower() in valid_cont_vals:
            self.execute(":AWGC:RMOD CONT")
        elif attrib.lower() in valid_trig_vals:
            self.execute(":AWGC:RMOD TRIG")
        else:
            raise IllegalParameterError("Run Mode Setting %s is an illegal attribute. "
                                        "Please use CONT or TRIG." % attrib)

    def prep_pulse(self, pulse):
        self.set_srate(pulse.channel)
        self.run_mode('TRIG')
        self.set_ref(pulse.channel)
        self.set_trig()

    def load_pulse(self, pulse):
        try:
            path = self.__REMOTE_PATH_WIN + '\\' + pulse.filename
            name = '.'.join(pulse.filename.split('.')[:-1])
            self.execute(":MMEM:IMP \"%s\",\"%s\",TXT" % (name, path))
            self.execute(":SOUR%d:WAV \"%s\"" % (pulse.channel, name))
        except:
            raise

    def unload_pulse(self, pulse):
        if isinstance(self, ArbPulse):
            self.execute(':WLIS:WAV:DEL \"%s\"' % '.'.join(pulse.filename.split('.')[:-1]))
        else:
            self.execute(':WLIS:WAV:DEL \"%s\"' % pulse)

    def get_pulses_in_memory(self):
        num_pulses = int(self.query(":WLIS:SIZE?"))
        pulse_names = []
        for i in range(25, num_pulses):
            pulse_names.append(self.query("WLIS:NAME? %d" % i).strip().replace('"', ''))

        return pulse_names

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

    def get_remote_pulses(self):
        """
        get_remote_pulses(): Returns list of pulses available on AWG.
        :return: list of str
        """

        stdin, stdout, stderr = self.__sshclient.exec_command(command='ls %s' % self.__REMOTE_PATH_BASH)

        return [x for x in stdout.read().split('\n') if x]

    def disconnect(self):
        """
        disconnect(): Disconnects SSH client
        :return:
        """
        self.__sshclient.close()

    def get_pulses(self):
        """
        get_pulses: Returns internal list of local pulses instantiated in AWG object.
        :return: list of pulse metadata dictionaries
        """
        return self.pulse_log

    def __init__(self, **kwargs):

        self.__REMOTE_PATH_BASH = '/c/Pulses'
        self.__REMOTE_PATH_WIN = 'C:\Pulses'

        for k in ['ssh_connect', 'new_pulse']:
            if k in kwargs.keys():
                self.__setattr__(k, kwargs[k])
            else:
                self.__setattr__(k, 1)

        if 'visa_connect' in kwargs.keys():
            if kwargs['visa_connect']:
                super(AWG, self).__init__(**kwargs)
        else:
            super(AWG, self).__init__(**kwargs)

        acceptable_kwargs = ['ip_addr', 'key_path', 'pass_path', 'rsa_pass',
                             'pulse', 'local_pulse', 'remote_pulse']

        for k in kwargs.keys():
            if k in acceptable_kwargs:
                self.__setattr__(k, kwargs[k])

        """
        Here we want to specify how to do pulse handling. Potential options:
        - Input ArbPulse object
        - Specify name of pulse already on AWG
        - Specify path of previously made local AWG pulse

        """
        if self.ssh_connect:
            print 'Init SSH/SFTP socket...'
            self.__sshclient, self.__transport = self.connect_sftp()
            print 'SSH/SFTP init successful.'

        def get_iterable(obj):  # Helper function to process multiple pulses below
            if isinstance(obj, collections.Iterable) and not isinstance(x, basestring):
                return obj
            else:
                return (obj,)

        conditions = [x in self.__dict__ for x in ['pulse', 'local_pulse', 'remote_pulse']]
        if sum(map(bool, conditions)) == 0 and self.new_pulse:
            raise MissingParameterError("A pulse object or path was not specified.")

        elif sum(map(bool, conditions)) == 1 and self.new_pulse and not self.ssh_connect:
            raise MissingParameterError("You have specified a pulse but disabled ssh connectivity. "
                                        "Please set ssh_connect = 1.")

        elif sum(map(bool, conditions)) > 1:
            raise MissingParameterError("Please specify at most one pulse attribute during initialization.")

        elif self.new_pulse:

            if 'pulse' in self.__dict__:
                try:
                    for pul in get_iterable(self.pulse):
                        self.pulse_log = []
                        print 'Uploading pulse...'
                        res = self.upload_pulse(self.__transport, pul)
                        print 'Upload successful.'
                        self.pulse_log.append(repr(pul))

                        print 'Loading pulse into AWG memory...'
                        self.load_pulse(pul)
                        self.prep_pulse(pul)
                        print 'Loading successful.'

                except AttributeError:
                    raise

            elif 'local_pulse' in self.__dict__:  # Process ASCII pulse file(s) locally
                self._transport = self.connect_sftp()

            else:  # Select pulse already on AWG. Should check for passing remote pulses here
                pass
