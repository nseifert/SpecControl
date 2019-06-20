import numpy as np
import queue
from PulseObj import *
from matplotlib import pyplot as plt

class PulseSeq(object):
    
    def add(self, pulse):
        try:
            style = pulse['type']
        except KeyError: # In case they forget to tell you what type of obj to add to seq
            raise 
        
        if style in ['chirp', 'Chirp', 'cp']:
            out = Chirp(SRATE = self.SRATE, 
                      time_multiplier = self.time_multiplier,
                      freq_multiplier = self.freq_multiplier,
                      t0 = pulse.get('t0', 0.0),
                      priority = pulse.get('priority', 'overwrite'),
                      channel = pulse.get('channel', 0),
                      v_i = pulse.get('v_i', 0.0),
                      v_f = pulse.get('v_f', 0.0),
                      length = pulse.get('length', 0.0),
                      amp = pulse.get('amp', 1.0),
                      phase = pulse.get('phase', 0.0),
                      )

        elif style in ['single_freq', 'transform_limited', 'onefreq']:
            out = SingleFreqPulse(SRATE = self.SRATE, 
                      time_multiplier = self.time_multiplier,
                      freq_multiplier = self.freq_multiplier,
                      t0 = pulse.get('t0', 0.0),
                      priority = pulse.get('priority', 'overwrite'),
                      channel = pulse.get('channel', 0),
                      freq = pulse.get('freq', 0.0),
                      length = pulse.get('length', 0.0),
                      amp = pulse.get('amp', 1.0),
                      phase = pulse.get('phase', 0.0),
                      window = pulse.get('window', 'square'),
                      trig_func = pulse.get('trig_func', None),
                      gauss_fwhm = pulse.get('gauss_fwhm', 0.0)
                      )

        elif style in ['TTL', 'ttl', 'dc']:
            out = TTL(SRATE = self.SRATE,
                    time_multiplier = self.time_multiplier,
                    freq_multiplier = self.freq_multiplier,
                    t0 = pulse.get('t0', 0.0),
                    priority = pulse.get('priority', 'overwrite'),
                    channel = pulse.get('channel', 0),
                    length = pulse.get('length', 0.0)
                    )

        elif style in ['deadtime', 'Deadtime', 'buffer', 'listen']:
            out = Deadtime(SRATE = self.SRATE,
                    time_multiplier = self.time_multiplier,
                    freq_multiplier = self.freq_multiplier,
                    t0 = pulse.get('t0', 0.0),
                    priority = pulse.get('priority', 'overwrite'),
                    channel = pulse.get('channel', 0),
                    length = pulse.get('length', 0.0)
                    )
        
        self.pulse_sequence_queue.put(out)
        self.pulse_sequence.append(out)
        return out.__repr__

    def compile(self):
        # 0) Check if pulse sequence is non-empty
        if not self.pulse_sequence_queue: 
            return None
        
        # 1) Determine number of channels needed 
        channels = set([pulse.channel for pulse in self.pulse_sequence])


        # 2) Build channel arrays
        channel_array = [[] for i in range(0, len(channels))]
        channel_sequences = [[pulse for pulse in self.pulse_sequence if pulse.channel == i] for i in range(0, len(channels))]

        for i,channel in enumerate(channel_sequences):
            length_counter = 0

            for j,pulse in enumerate(channel): 
                t0_pts = int(np.ceil(pulse.t0 * self.SRATE))

                if t0_pts > len(channel_array[i]): # Pulse starts beyond where channel is currently built, so it needs padding
                    channel_array[i].extend([0]*(t0_pts-len(channel_array[i])))
                    channel_array[i].extend(pulse.pulse)
                    length_counter += (t0_pts-length_counter) + len(pulse.pulse)

                elif t0_pts < len(channel_array[i]): # Channel already had content at this point, need to check priority
                    print('------')
                    print('Got a length conflict here for pulse %i in channel %i' %(j, i))
                    print('t0_pts is: %i and channel length is %i' %(t0_pts, len(channel_array[i])))
                    if pulse.priority == 'overwrite':
                        # Two cases: one, we need to overwrite but current length of channel is less than what the new pulse requires
                        # Two, we're overwriting a section in the middle.
                        
                        # Chan len < length_counter + pulse
                        if len(channel_array[i]) < t0_pts + len(pulse.pulse):
                            print('Got here')
                            channel_array[i][t0_pts:] = pulse.pulse[0:len(channel_array[i])-t0_pts]
                            channel_array[i].extend(pulse.pulse[len(channel_array[i])-t0_pts:])
                            length_counter += len(pulse.pulse[len(channel_array[i])-length_counter:])
                        
                        # Chan len >= length_counter+pulse
                        else:
                            print('Got here')
                            channel_array[i][t0_pts:t0_pts+len(pulse.pulse)] = pulse.pulse
                            length_counter += len(pulse.pulse)
                    elif pulse.priority == 'add': 
                        pass
                    elif pulse.priority == 'ignore': # Don't overwrite, just append what's left where there's zeroes
                        if len(channel_array[i]) < t0_pts + len(pulse.pulse):
                            channel_remainder = len(channel_array[i]) - t0_pts 
                            channel_array[i].extend(pulse.pulse[channel_remainder:])
                        else:
                            for j, val in enumerate(pulse.pulse):
                                if channel_array[i][t0_pts+j] == 0:
                                    channel_array[i][t0_pts+j] = pulse.pulse[j]

                    elif pulse.priority == 'multi':
                        pass
                    elif pulse.priority == 'subtract':
                        pass # Do these later

                else: # We're caught up, so just need to add current pulse
                    channel_array[i].extend(pulse.pulse)
                    length_counter += len(pulse.pulse)
        
        # Now, let's build a numpy array for the pulse sequence
        num_rows = max([len(channel) for channel in channel_array])
        self.compiled_sequence = np.zeros((num_rows,max(channels)+1))
        for i,chan in enumerate(channel_array):
            self.compiled_sequence[:len(chan),i] = chan
        
        return self.compiled_sequence



    def __init__(self, params=None):
        # Global parameters for pulse sequence
        self.SRATE = 25.0E9 
        self.time_multiplier = 1.0E-6 # microseconds
        self.freq_multiplier = 1.0E6 # MHz
        self.frames = 1 # Number of frames

        # Check to see if parameters from user are different
        if params:
            for k in params.keys():
                if k not in self.__dict__.keys():
                    continue
                else:
                    self.__setattr__(k, params[k])
        
        """ Pulse is created by building FIFO queue of user-supplied pulse operations,
        then compiled into a numpy array"""
        self.pulse_sequence = []
        self.pulse_sequence_queue = queue.Queue()


if __name__ == '__main__':
    # Generate example pulse sequence
    # Segmented -- 720 MHz worth of chirps from 4.0 to 4.72 GHz, split into 30 MHz segments

    # freq_array = np.arange(4000, 4720+30, 30)
    # freq_pairs = [(freq_array[i],freq_array[i+1]) for i in range(0,len(freq_array)-1)]
    
    # Pulse sequence is as follows:
    # Channel 0: 1 microsecond dead time, then 500ns chirp, then 5us deadtime for detection + prep
    # Channel 1: 200 ns TTL pulse that ends 100ns before chirp starts
    # Channel 2: 200 ns TTL pulse that starts 100ns after chirp
    # Total segment sequence time: 5us + 1 us + 500ns = 6.5 us
    # pulses = []
    # for i, pair in enumerate(freq_pairs):
    #     pulses.append({'type': 'deadtime', 'length': 1.0, 't0': 6.5*i, 'channel': 0})
    #     pulses.append({'type': 'chirp', 'v_i': pair[0], 'v_f': pair[1], 'channel': 0, 'length': 0.5, 't0':1.0+6.5*i})
    #     pulses.append({'type': 'deadtime', 'length': 5.0, 't0': 1.5+6.5*i, 'channel': 0})
    #     pulses.append({'type': 'ttl', 'channel': 1, 'length': 0.2, 't0': 0.7+6.5*i})
    #     pulses.append({'type': 'ttl', 'channel': 2, 'length': 0.2, 't0': 1.6+6.5*i})

    # seq = PulseSeq()
    # for pulse in pulses:
    #     seq.add(pulse)
    
    # pulse = seq.compile()
   
    # from matplotlib import pyplot as plt
    # t_scale = np.arange(0, pulse.shape[0]*1./seq.SRATE, 1./seq.SRATE)*1./seq.time_multiplier
    # colors = ['k', 'b','r']
    # for i, col in enumerate(pulse.T):
    #     plt.plot(t_scale,col,color=colors[i])
    # plt.show()
