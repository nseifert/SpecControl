import numpy as np

class ArbPulse(object):

    def generate_pulse(self):

        def chirp(t, v_min, v_max, chirp_len):
            return np.cos(v_min*t + 0.5*(v_max-v_min)/chirp_len*t**2)

        self.total_len = self.prebuffer + self.postbuffer + self.chirp_len
        if self.mk1:
            self.total_len += self.mk1_len + self.mk1_chirp_gap
        if self.mk2:
            self.total_len += self.mk2_len + self.mk2_chirp_gap

        pulse = np.zeros((self.total_len*self.time_multiplier * self.s_rate, 1+int(self.mk1)+int(self.mk2)))
        timebase = np.linspace(0, self.total_len * self.time_multiplier, np.shape(pulse)[0])


        if self.mk1:
            MK1_START = self.prebuffer * self.time_multiplier
            MK1_END = MK1_START + self.mk1_len * self.time_multiplier
            pulse[np.where(np.logical_and(timebase >= MK1_START, timebase <= MK1_END)), 1] = 1.0

            PULSE_START = MK1_END + self.mk1_chirp_gap * self.time_multiplier

        else:
            PULSE_START = self.prebuffer * self.time_multiplier

        PULSE_END = PULSE_START + self.chirp_len * self.time_multiplier
        pulse_mask = np.where(np.logical_and(timebase >= PULSE_START, timebase <= PULSE_END))
        pulse[pulse_mask,0] = chirp(timebase[pulse_mask],
                                  self.chirp_freq[0] * self.freq_multiplier,
                                  self.chirp_freq[1] * self.freq_multiplier,
                                  PULSE_END-PULSE_START)

        if self.mk2:
            MK2_START = PULSE_END + self.mk2_chirp_gap * self.time_multiplier
            MK2_END = MK2_START + self.mk2_len * self.time_multiplier
            pulse[np.where(np.logical_and(timebase >= MK2_START, timebase <= MK2_END)), 2] = 1.0

        return pulse

    def __init__(self, **kwargs):

        req_defaults = {'s_rate': 12.0E9,   # Sample Rate
                        'time_multiplier': 1.0E-6,  # Microseconds
                        'freq_multiplier': 1.0E6,  # MHz
                        'frames': 1,  # Number of frames

                        'chirp_freq': [1000.0, 3000.0],  # Frequency bounds of chirp
                        'chirp_len': 4.0, # Length of chirp in units of time_multiplier

                        'prebuffer': 1.0,  # Time between start of pulse seq and first non-zero bit
                        'postbuffer': 40.0,  # Time between last non-zero bit and the end of pulse seq

                        'mk1': False,  # Boolean for generating marker 1
                        'mk1_len': 0.5, # Length of marker 1 in units of time_multiplier
                        'mk1_chirp_gap': 0.1,  # Gap between end of marker 1 and pulse

                        'mk2': False,  # Same as mk1
                        'mk2_len': 0.5,
                        'mk2_chirp_gap': 0.1 # Gap between end of pulse and marker 2
                        }

        for k in kwargs.keys():
            if k not in req_defaults.keys():
                continue
            elif k in req_defaults.keys():
                self.__setattr__(k, kwargs[k])

        for k in set(req_defaults.keys())-set(kwargs.keys()):  # Restore defaults for required keywords not in kwargs
            self.__setattr__(k, req_defaults[k])

        self.pulse = self.generate_pulse()

