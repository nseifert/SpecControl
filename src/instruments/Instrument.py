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

class IllegalParameterError(Exception):
    def __init__(self, message, errors, *args):

        self.message = message
        self.errors = errors

        super(MissingParameterError, self).__init__(message, errors, *args)

class Instrument(object):

    def connect(self, ip, name, type):
        rm = visa.ResourceManager()
        try:
            if type == 'raw':
                print 'Attempting connection to... TCPIP0::%s::2001::SOCKET' % ip
                inst = rm.open_resource("TCPIP0::%s::2001::SOCKET" % ip,
                                        write_termination='\r\n', read_termination='\r\n')
            elif type == 'ip':
                print 'Attempting connection to... %s' % ip
                inst = rm.open_resource(ip)
            elif type == 'instr':
                print 'Attempting connection to... TCPIP0::%s::inst0::INST' % ip
                inst = rm.open_resource('TCPIP0::%s::inst0::INSTR' % ip)

        except VisaIOError:
            print 'Problem with connection to %s' %name
            raise
        else:
            inst.timeout = 30000

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

    def execute(self, cmd, log_read=0):
        try:
            self.instrument.write(b"%s" %cmd)
        except:
            print 'Problem with command.'
            self.log_it(cmd, 'Failed.')
            raise
        else:
            time.sleep(0.05)
            if log_read:
                self.log_it(cmd, self.instrument.read_raw())
            else:
                self.log_it(cmd, 'Successful.')

    def query(self, cmd):
        try:
            self.instrument.write(b"%s" %cmd)
        except:
            print 'Problem with query.'
            raise
        else:
            res = self.instrument.read_raw()
            time.sleep(0.05)
            self.log_it(cmd, res)

            return res

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
        required_keys = ['ip_addr', 'name', 'connect_type']

        for k in kwargs.keys():
            if k in required_keys:
                self.__setattr__(k, kwargs[k])

        if 'name' not in self.__dict__.keys():
            self.name = 'Default'
        if 'connect_type' not in self.__dict__.keys():
            self.connect_type = 'instr'

        try:
            self.instrument = self.connect(self.ip_addr, self.name, type=self.connect_type)
        except AttributeError:
            raise MissingParameterError('Missing required parameter',
                                        'IP Address Missing. Use ip_addr as keyword argument')

