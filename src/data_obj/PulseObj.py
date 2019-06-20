import numpy as np
from scipy.signal import gaussian

class PulseObj:
                                
        def __init__(self, SRATE, time_multiplier, freq_multiplier, t0, priority, **kwargs):
            self.SRATE = SRATE
            self.time_multiplier = time_multiplier
            self.freq_multiplier = freq_multiplier
            self.priority = priority
            self.t0 = t0 * self.time_multiplier

            self.channel = kwargs['channel']

class TTL(PulseObj):
    def ttl(self, length):
        return np.ones(int(np.ceil(length * self.time_multiplier * self.SRATE)))

    def __init__(self, *args, **kwargs):
        super(TTL, self).__init__(*args, **kwargs)
        self.length = kwargs.get('length', 0.0)
        self.pulse = self.ttl(self.length)

class Deadtime(PulseObj): 
    def deadtime(self, length):
        return np.zeros(int(np.ceil(length * self.time_multiplier * self.SRATE)))
    def __init__(self, *args, **kwargs):
        super(Deadtime, self).__init__(*args, **kwargs)
        self.length = kwargs.get('length', 0.0)
        self.pulse = self.deadtime(self.length)  

class SingleFreqPulse(PulseObj):

    def single_freq(self, v, l, a, p, window=None, trig=None, **kwargs):
        t = np.arange(0, l*self.time_multiplier, 1./self.SRATE)

        if trig == 'sin':
            pulse = a * np.sin(2 * np.pi * v * self.freq_multiplier * t + p)
        elif trig == 'cos' or not trig:
            pulse = a * np.cos(2 * np.pi * v * self.freq_multiplier * t + p)

        if window in ['gauss', 'gaussian']:
            
            fwhm = self.fwhm * self.time_multiplier * self.SRATE / 2.3548
            pulse = pulse * gaussian(len(t), fwhm)
        
        return pulse
            

    def __init__(self, *args, **kwargs):
        super(SingleFreqPulse, self).__init__(*args, **kwargs)
        
        self.freq = kwargs['freq']
        self.amp = kwargs['amp']
        self.length = kwargs['length']
        self.phi = kwargs['phase']
        self.window = kwargs['window']
        self.trig_func = kwargs['trig_func']

        if self.window in ['gauss', 'gaussian']:

            self.fwhm = kwargs['gauss_fwhm']
        
        self.pulse = self.single_freq(self.freq, self.length, self.amp, self.phi, self.window, self.trig_func)

class Chirp(PulseObj):
    def chirp(self, v0, v1, l, a, p):
        # Generate time base to calc chirp
        t = np.arange(0, l*self.time_multiplier, 1./self.SRATE)
        return a * np.cos(p + (2*np.pi*v0*t)*self.freq_multiplier + (2*np.pi*(v1-v0))*(t**2)*self.freq_multiplier/(2*l*self.time_multiplier))
    
    def __init__(self, *args, **kwargs):
        super(Chirp, self).__init__(*args, **kwargs)

        self.v_i = kwargs['v_i']
        self.v_f = kwargs['v_f']
        self.length = kwargs['length']
        self.amp = kwargs['amp']
        self.phi = kwargs['phase']

        self.pulse = self.chirp(self.v_i, self.v_f, self.length, self.amp, self.phi)
        