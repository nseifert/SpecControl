from src.data_obj.ArbPulse import ArbPulse
from src.instruments.AWG import AWG
import os

if __name__ == "__main__":
    key_path = os.path.abspath('C:\\Users\\jaeger\\.ssh\\id_rsa')
    pass_path = os.path.abspath('C:\\Users\\jaeger\\Desktop\\SpecControl\sec\pass.pass')

    AWG(ip_addr='192.168.1.102', key_path=key_path, rsa_pass=pass_path, pulse=ArbPulse())

