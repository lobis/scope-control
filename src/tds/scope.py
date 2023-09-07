import pyvisa
import numpy as np
import time


class Scope:
    def __init__(self, ip_address: str):
        self.rm = pyvisa.ResourceManager("@py")
        self.scope = self.rm.open_resource(
            f"TCPIP::{ip_address}::INSTR"
        )
        self.scope.read_termination = "\n"
        self.scope.write_termination = "\n"

        # timeout to 10 seconds
        self.scope.timeout = 10 * 1000

        self.command_history = []

        self.write("BUSY?")
        self.write("WFMOutpre:FORMat BYTE")  # Set the waveform format to BYTE
        self.write("WFMOutpre:BYT_Nr 1")  # Set the byte order to LSB

    def reset(self):
        self.write("*RST")

    def write(self, command):
        self.command_history.append((time.time(), command))
        print(f"Writing: {command}")
        self.scope.write(command)

    def print_command_history(self):
        for timestamp, command in self.command_history:
            timestring = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
            print(f"- {timestring}: {command}")

    @property
    def resource(self):
        return self.scope

    @property
    def identity(self):
        return self.scope.query("*IDN?")
