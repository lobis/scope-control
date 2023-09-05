import pyvisa
import numpy as np
import matplotlib.pyplot as plt
import time


def main():
    rm = pyvisa.ResourceManager("")
    print(f"Printing resources: {rm.list_resources()}")

    scope = rm.open_resource(
        "TCPIP::192.168.0.106::INSTR"
    )  # Replace with your resource string

    scope.read_termination = "\n"
    scope.write_termination = "\n"

    identity = scope.query("*IDN?")
    if not identity:
        print("Failed to connect to device")
        return
    print(f"Connected to: {identity}")

    # Configure the oscilloscope for Channel 1
    # scope.write("HORIZONTAL:MAIN:SAMPLERATE 5E9")  # Set the sample rate to 1 GSa/s

    scope.write("WFMOutpre:FORMat BYTE")  # Set the waveform format to BYTE
    scope.write("WFMOutpre:BYT_Nr 1")  # Set the byte order to LSB

    # set trigger to auto
    # scope.write("TRIGger:A:MODE AUTO")

    # Acquire data
    print("Acquiring data...")
    while True:
        scope.write("*CLS")  # Clear the event register
        scope.write("ACQ:STATE STOP")  # Ensure acquisition is stopped
        scope.write("ACQ:STATE RUN")  # Start acquisition
        while True:
            acquisition_state = scope.query("ACQ:STATE?")  # Query the acquisition state
            if acquisition_state == "0":
                break
            time.sleep(0.1)  # Wait for the acquisition to complete
            break
        print("Acquisition complete")
        scope.write("ACQ:STATE STOP")  # Stop acquisition
        # scope get data
        scope.write("DATA:SOURCE CH1")

        buffer_length = scope.query(
            "WFMOutpre:NR_PT?"
        )  # Get the length of the waveform buffer
        print(f"Buffer length: {buffer_length}")

        # use buffer length to get all bytes
        scope.write("CURVe?")

        # convert it into a numpy array
        waveform_data = scope.query_binary_values(
            "CURVe?", datatype="b", is_big_endian=True, container=np.array
        )

        # get correct time scale
        time_scale = scope.query("HORizontal:SCAle?")
        print(f"Time scale: {time_scale}")

        # get correct voltage scale
        voltage_scale = scope.query("CH1:SCAle?")
        print(f"Voltage scale: {voltage_scale}")

        # get trigger time
        # trigger_time = scope.query("TRIGger:MAIn:POSition?")
        # print(f"Trigger time: {trigger_time}")

        # rescale waveform data
        waveform_data = waveform_data * float(voltage_scale) / 25.0
        time_values = np.arange(len(waveform_data)) * float(time_scale)

        plt.figure(figsize=(8, 6))
        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude (V)")
        # fonts of the axis labels to 14
        # plt.rc('xtick', labelsize=14)
        # plt.rc('ytick', labelsize=14)

        # use matplotlib to plot the signal (as steps)
        plt.plot(
            time_values, waveform_data, color="blue", label="Channel 1", linewidth=2.0
        )
        plt.legend(loc="upper right")
        plt.tight_layout()

        # plt.savefig("channel1_waveform.png", dpi=600, bbox_inches='tight')
        plt.show()

        time.sleep(5)


if __name__ == "__main__":
    main()
