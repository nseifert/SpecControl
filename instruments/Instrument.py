import visa
import pyvisa.resources
import time
import datetime
from pyvisa.errors import VisaIOError

class MissingParameterError(Exception):
    def __init__(self, message, errors, *args):

        self.message = message
        self.errors = errors

        super(MissingParameterError, self).__init__(message, errors, *args)

class Instrument(object):

    def connect(self, ip, name):
        rm = visa.ResourceManager()
        try:
            print 'Attempting connection to... "TCPIP0::%s::2001::SOCKET"' %ip
            inst = rm.open_resource("TCPIP0::%s::2001::SOCKET" %ip, write_termination='\r\n', read_termination='\r\n')
        except VisaIOError:
            print 'Problem with connection'
            raise
        else:
            inst.timeout = 10000

        # Test block with default identity command
        try:
            test = inst.write(b"*IDN?")
            res = inst.read_raw()

            self.log_it("*IDN?", res)
            print "Connection successful for device %s; response: %s" %(name, res[8:].encode('utf-8'))
        except:
            raise
        else:
            return inst

    def execute(self, cmd):
        try:
            self.instrument.write(b"%s" %cmd)
        except:
            print 'Problem with command.'
            raise
        else:
            time.sleep(0.05)
            self.log_it(cmd, self.instrument.read_raw())

    def query(self, cmd):
        try:
            self.instrument.write(b"%s" %cmd)
        except:
            print 'Problem with query.'
            raise
        else:
            time.sleep(0.05)
            self.log_it(cmd, self.instrument.read_raw())

    def close(self):
        try:
            self.instrument.close()
            print 'Successfully closed instrument connection.'
        except:
            print 'Problem with closing connection.'
            raise

    def log_it(self, cmd, output):
        self.log.append([cmd.strip('\r\n'), output.strip('\r\n'), datetime.datetime.utcnow().strftime("%H:%M:%S\t %m-%d-%y")])


    def print_log(self):
        fmt = '{:30} \t {:30} \t {:50}'
        out = fmt.format('Time', 'Command', 'Response') + '\n' +  fmt.format('-'*15, '-'*15, '-'*10) + '\n'
        for entry in self.log:
           out += fmt.format(entry[2], entry[0], entry[1]) + "\n"
        print out


    def __init__(self, **kwargs):

        self.log = []
        required_keys = ['ip_addr', 'name']

        for k in kwargs.keys():
            if k in required_keys:
                self.__setattr__(k, kwargs[k])

        if 'name' not in self.__dict__.keys():
            self.name = 'Default'

        try:
            self.instrument = self.connect(self.ip_addr, self.name)
        except AttributeError:
            raise MissingParameterError('Missing required parameter',
                                        'IP Address Missing. Use ip_addr as keyword argument')


# QC = Instrument(ip_addr="192.168.1.101", name='QC9520 Pulse Gen')

# print QC.query(":PULSE1:WIDT?")
# QC.execute(":PULSe2:STATe ON")
# QC.execute(":PULSe2:WIDTh 0.0001")
# QC.execute(":PULSe2:DELay 0.05")
# QC.execute(":PULSe1:STATe ON")
