from src.data_obj.ArbPulse import ArbPulse
from src.instruments.AWG import AWG
import os

if __name__ == "__main__":
    key_path = os.path.abspath('C:\\Users\\jaeger\\.ssh\\id_rsa')
    pass_path = os.path.abspath('C:\\Users\\jaeger\\Desktop\\SpecControl\sec\pass.pass')

    custom_pulse = ({'type': 'sine',
                     'channel': 'pulse',
                     'freq': 2500.0,
                     'amplitude': 1.0,
                     'length': 4.0,
                     'start_time': 8.0},)
    inp_pulse = ArbPulse(channel=1, additional_pulses=custom_pulse)

    # import scipy.fftpack as sfft
    # import numpy as np
    #
    # data = np.append(inp_pulse.pulse[:,0], np.zeros(len(inp_pulse.pulse[:,0])))
    # data = np.column_stack((sfft.fftfreq(len(data),1.0/inp_pulse.s_rate)/(inp_pulse.freq_multiplier),abs(sfft.fft(data))/100.0))
    #
    from matplotlib import pyplot as plt
    # print inp_pulse.get_params()
    #
    plt.plot(inp_pulse.pulse[:,0])
    plt.plot(inp_pulse.pulse[:,1] + 2)
    plt.plot(inp_pulse.pulse[:,2] - 2)
    plt.show()

    # test = AWG(ip_addr='192.168.1.102', connect_type='instr', key_path=key_path, rsa_pass=pass_path, pulse=inp_pulse)



