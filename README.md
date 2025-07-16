# usbmeter

Extracts and graphs data from UM25C etc. USB power meters in Linux.

Based on the excellent reverse engineering found [here](https://sigrok.org/wiki/RDTech_UM_series).

![graph](/images/graph.png)

# Install using [uv](https://docs.astral.sh/uv/)

```
uv sync
```

# Run on Linux

Start the bluetooth service:

```
sudo systemctl start bluetooth
echo "power on" | bluetoothctl
```

It is then recommended to do the following, to view a live
graph of voltage, current and power:

```
usbmeter --addr <ADDRESS> --graph
```

# Save data

Data can be saved in a CSV file.
Timestamps are relative to the first record.
To save the power data to a file:

```
usbmeter --addr <ADDRESS> --graph --out out.csv
```

# Acknowledgements

The original version of this script was written by [anfractuosity](https://github.com/anfractuosity/usbmeter).
I've originally modified it to remove the dependency on PyBluez
as it is considered deprecated
and the functionality works pretty well with the socket functions from the standard library.
