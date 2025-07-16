#!/usr/bin/python3

# sudo systemctl start bluetooth
# echo "power on" | bluetoothctl

import collections
import argparse
import datetime
import time
import csv
import os
import struct
import socket
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter


# Process socket data from USB meter and extract volts, amps etc.
def process_data(d):
    data = {}

    data["Volts"] = struct.unpack(">h", d[2 : 3 + 1])[0] / 1000.0  # volts
    data["Amps"] = struct.unpack(">h", d[4 : 5 + 1])[0] / 10000.0  # amps
    data["Watts"] = struct.unpack(">I", d[6 : 9 + 1])[0] / 1000.0  # watts
    data["temp_C"] = struct.unpack(">h", d[10 : 11 + 1])[0]  # temp in C
    data["temp_F"] = struct.unpack(">h", d[12 : 13 + 1])[0]  # temp in F

    utc_dt = datetime.datetime.now(datetime.timezone.utc)  # UTC time
    dt = utc_dt.astimezone()  # local time
    data["time"] = dt

    g = 0
    for i in range(16, 95, 8):
        ma, mw = struct.unpack(">II", d[i : i + 8])  # mAh,mWh respectively
        gs = str(g)
        data[gs + "_mAh"] = ma
        data[gs + "_mWh"] = mw
        g += 1

    data["data_line_pos_volt"] = struct.unpack(">h", d[96: 97 + 1])[0] / 100.0
    data["data_line_neg_volt"] = struct.unpack(">h", d[98: 99 + 1])[0] / 100.0
    data["resistance"] = struct.unpack(">I", d[122: 125 + 1])[0] / 10.0  # resistance
    return data

def setup():
    # Parse arguments
    parser = argparse.ArgumentParser(description="CLI for USB Meter")
    parser.add_argument("--addr", dest="addr", type=str, help="Address of USB Meter", required=True)
    parser.add_argument("--graph", dest="graph", help="Live graphing", nargs="?", default=False)
    parser.add_argument(
        "--out",
        dest="out",
        type=str,
        help="Filename to output data to. If it exists, it is overwritten",
        required=False,
        default="",
    )

    args = parser.parse_args()
    graph = not (args.graph == False)
    outfile = None

    sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM) # pyright: reportAttributeAccessIssue=false
    sock.connect((args.addr, 1))

    if args.out != "":
        if os.path.exists(args.out):
            print("File {} already exists. It will be overwritten.".format(args.out))
            os.remove(args.out)
        outfile = open(args.out, "w")

    return sock, graph, outfile

def loop(sock: socket.socket, graph=False, outfile=None):
    # Initialise variables for graph
    l = 20
    volts = collections.deque(maxlen=l)
    currents = collections.deque(maxlen=l)
    watts = collections.deque(maxlen=l)
    times = collections.deque(maxlen=l)

    f, ax1, ax2, ax3 = None, None, None, None
    if graph:
        f, (ax1, ax2, ax3) = plt.subplots(3, sharex=True)
        plt.show(block=False)

    csv_file = None
    if outfile is not None:
        csv_file = csv.writer(outfile)
        csv_file.writerow(["time", "Volts", "Amps", "Watts"])
        first = 0

    d = b""
    ct = 0
    while True:

        # Send request to USB meter
        sock.send((0xF0).to_bytes(1, byteorder="big"))

        d += sock.recv(130)

        if len(d) != 130:
            continue

        data = process_data(d)
        volts.append(data["Volts"])
        currents.append(data["Amps"])
        watts.append(data["Watts"])
        times.append(data["time"])

        if graph and plt.get_fignums():
            assert isinstance(ax1, Axes)
            assert isinstance(ax2, Axes)
            assert isinstance(ax3, Axes)
            assert isinstance(f, Figure)

            ax1.clear()
            ax1.plot(times, volts)
            ax2.clear()
            ax2.plot(times, currents)
            ax3.clear()
            ax3.plot(times, watts)

            ax1.title.set_text("Voltage")
            ax1.xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))
            ax1.fmt_xdata = DateFormatter("%H:%M:%S")
            f.autofmt_xdate()

            ax2.title.set_text("Current")
            ax3.title.set_text("Wattage")

            f.canvas.draw()
            f.canvas.flush_events()
            plt.pause(0.001)

        print("{}: {:.3f}V {:.3f}A {:.3f}W".format(data["time"], data["Volts"], data["Amps"], data["Watts"]))

        if csv_file is not None:
            assert outfile is not None
            if first == 0: # pyright: reportPossiblyUnboundVariable=false
                first = data["time"]
            csv_file.writerow([data["time"] - first, data["Volts"], data["Amps"], data["Watts"]])
            if ct % 10 == 0:
                outfile.flush()
            ct += 1

        d = b""
        time.sleep(0.01)

def main():
    sock, graph, outfile = setup()
    try:
        loop(sock, graph, outfile)
    except KeyboardInterrupt:
        print("\nReceived Ctrl+C, shutting down gracefully...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if outfile is not None:
            outfile.close()
        sock.close()

if __name__ == "__main__":
    main()
