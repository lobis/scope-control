import pyvisa
import numpy as np
import matplotlib.pyplot as plt
import argparse
from tds import __version__ as version
from tds import Scope


# https://download.tek.com/manual/077011000web_0.pdf


def get_resources():
    rm = pyvisa.ResourceManager("@py")
    resources = rm.list_resources()
    rm.close()
    return resources


def main():
    parser = argparse.ArgumentParser(description="HVPS control")
    parser.add_argument("--version", action="version", version=version)

    args = parser.parse_args()

    resources = get_resources()
    print(f"Available resources: {resources}")

    if len(resources) == 0:
        print("No resources found")
        return

    scope = Scope(ip_address="192.168.0.106")
    identity = scope.identity

    print(f"Connecting to: {identity}")
    if not identity.startswith("TEKTRONIX,TDS"):
        print("Not a TDS scope", identity)
        return

    # get the number of channels

    # scope.reset()

    scope.write("ACQ:STATE STOP")  # Ensure acquisition is stopped
    scope.write("*CLS")  # Clear the event register

    scope.write("ACQUIRE:MODE SAMPLE")
    scope.write("ACQUIRE:SAMPLINGMODE RT")
    scope.write("HEADER OFF")
    # enable only channel 1
    scope.write("SEL:CH1 ON")
    scope.write("SEL:CH2 OFF")
    scope.write("SEL:CH3 OFF")
    scope.write("SEL:CH4 OFF")

    # set coupling to 50 ohm for all channels
    scope.write("CH1:TERmination 50")
    scope.write("CH2:TERmination 50")
    scope.write("CH3:TERmination 50")
    scope.write("CH4:TERmination 50")

    scope.write("CH1:SCAle 0.5")
    scope.write("CH1:COUPling DC")

    # set time scale to 10 ns / div
    scope.write("HORizontal:SCAle 10e-9")

    # retrieve the horizontal scale
    time_scale = scope.resource.query("HORizontal:SCAle?")
    print(f"Time scale: {time_scale}")

    # DC coupling

    scope.write("TRIGGER:A:EDGE:SOURCE CH1")
    scope.write("TRIGGER:A:EDGE:LEVEL -0.30")
    scope.write("TRIGGER:A:EDGE:SLOPE FALL")

    scope.write("HORizontal:MAIN:SAMPLERate 5e9")
    scope.write("HORizontal:RECOrdlength 2000")
    scope.write("HORizontal:TRIGger:POSition 20")

    trigger_position = float(scope.resource.query("HORizontal:TRIGger:POSition?"))
    print(f"Trigger position: {trigger_position}")

    scope.write("DATA:ENCDG RIBinary")
    scope.write("DATA:START 1")
    scope.write("DATA:STOP 2000")
    scope.write("DATA:SOURCE CH1")

    sequence_count = 2
    scope.write(f"HORIZONTAL:FASTFRAME:COUNT {sequence_count:d}")

    scope.write("ACQUIRE:STOPAFTER SEQUENCE")
    scope.write("HORIZONTAL:FASTFRAME:STATE ON")

    # retrieve the time scale
    time_scale = scope.resource.query("HORizontal:SCAle?")
    time_position = scope.resource.query("HORizontal:POSition?")

    channel_scale = scope.resource.query("CH1:SCAle?")
    channel_position = scope.resource.query("CH1:POSition?")

    scope.write("ACQUIRE:STATE RUN")

    buffer_length = int(scope.resource.query("WFMOutpre:NR_PT?"))

    print("Acquiring data...")

    scope.write("*OPC")
    scope.write("*WAI")

    print("Acquisition complete")

    scope.write("ACQ:STATE STOP")  # Stop acquisition

    scope.write("CURVe?")

    print("Reading waveform data...")
    # convert it into a numpy array
    waveform_data = scope.resource.query_binary_values(
        "CURVe?", datatype="b", is_big_endian=True, container=np.array
    )

    print("Plotting waveform data...")
    print(f"Waveform data length: {len(waveform_data)}")

    expected_bytes = buffer_length * sequence_count
    assert (
        len(waveform_data) == expected_bytes
    ), f"Buffer length mismatch: {len(waveform_data)} != {expected_bytes}"

    # split it into the individual waveforms
    waveform_data = waveform_data.reshape(sequence_count, buffer_length)

    # rescale waveform data
    waveform_data = waveform_data * float(channel_scale) - float(channel_position)
    time_values = np.arange(buffer_length) * float(time_scale) - float(time_position)

    plt.figure(figsize=(8, 6))
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude (V)")

    # use matplotlib to plot the signal (as steps)
    plt.plot(
        time_values, waveform_data[0], color="blue", label="Channel 1", linewidth=2.0
    )
    plt.legend(loc="upper right")
    plt.tight_layout()

    plt.show()

    scope.resource.close()


if __name__ == "__main__":
    main()
