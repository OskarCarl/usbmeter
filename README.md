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

To save the power data to a file:

```
usbmeter --addr <ADDRESS> --graph --out out.dat
usbmeter --addr <ADDRESS> --graph --out out.csv
```

To process this pickled data, you can do:

```
#!/usr/bin/python3
import pickle
objects = []

with open('out.dat', 'rb') as f:
    while True:
        try:
            objects.append(pickle.load(f))
        except EOFError:
            break

for x in objects:
    print("%s,%f,%f" % (x['time'],x['Volts'],x['Amps']))
```

# Acknowledgements

The original version of this script was written by [anfractuosity](https://github.com/anfractuosity/usbmeter).
