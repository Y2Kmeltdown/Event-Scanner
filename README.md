# Event Scanner

The contents of this github page outline the Event barcode standard and methods for scanning event data to extract event barcodes.

## Installation:

1. Clone the git repository
```
git clone repo
```

2. Install the following libraries

```
pip install numpy event-stream
```

3. For live event data, follow install instructions for PSEE14 and tread carefully on the Neuromorphic systems github.

## Usage:

To use the event scanner, prepare the data to input into the system like this example:

```python
import event_stream
import numpy
import time
from event_barcode import eventScanner

tStep = 800
tIter = tStep
eventAxis = 600

#Initialise Class
evBarcodeReader = eventScanner(threshold = 200, error = 20)

decoder = event_stream.Decoder('path/to/esfile')

for chunk in decoder:
    
    # Get specific range in the x axis for input events
    fChunk = chunk[chunk["x"] >= eventAxis-2]
    fChunk = fChunk[fChunk["x"] <= eventAxis+2]

    if fChunk["t"].any():
        
        # get most current timestep in the event list
        tlast = fChunk["t"][-1]

        # Loop until iterator is greater then last timestamp in chunk
        while tIter < tlast+tStep:
            # Segment events into smaller time chunks
            # filter chunk by time chunk prevIter <-> currentIter
            nestedChunk = fChunk[fChunk["t"] < tIter]
            nestedChunk = nestedChunk[fChunk["t"] >= tIter-tStep]

            if nestedChunk["t"].any():

                # THIS IS WHERE READABLE DATA IS PRODUCED
                data = nestedChunk["on"]
                t = nestedChunk["t"][0]
                if evBarcodeReader.readEvents(data, t):

                    # Get message from event scanner
                    message = evBarcodeReader.getMessage()
    # event Scanner timer used to determine timeouts
    evBarcodeReader.timing()
```

The eventScanner class is initialised with a threshold and error. The threshold indicates what number of events the scanner will consider as a spike. The error is a percentage error that is used to determine if a header is detected.

## Methods

### eventScanner.readEvents(data, t)

Takes event polarity data and a time value of the last timestamp of the polarity data.

readEvents returns true when a message has been extracted from the data otherwise returns nothing.

### eventScanner.getMessage()

Returns the last message eventScanner compiled in the form of a list of tuples which contain total message characteristics.

```
              _____________________________________________________________
Full Message | Message Bits | Message Start | Message End | Message Length |
             |--------------|---------------|-------------|----------------|
Start Header | Bit Number 0 | Header Start  | Header End  | Header Length  |
             |--------------|---------------|-------------|----------------|
Bit 1        | Bit Number 1 | Bit Start     | Bit End     | Bit Length     |
             |--------------|---------------|-------------|----------------|
             |       :      |       :       |      :      |        :       |
             |--------------|---------------|-------------|----------------|
Bit n        | But Number N | Bit Start     | Bit End     | Bit Length     |
             |--------------|---------------|-------------|----------------|
End Header   | Last Bit     | Header Start  | Header End  | Header Length  |
             |______________|_______________|_____________|________________|

```

### eventScanner.timing()

Method is called to check timeouts for the event scanners error checking. When an event byte is being detected a end time is set in the event byte in which the whole byte needs to be completed. If the time exceeds this set time the byte is discarded.

## Other information

This github also contains images of event barcodes and some datasets for testing the event barcodes. Here is an example of an event barcode. There is also some previous versions which can still be used which can be found in the prototypes folder.

<h1  align="center">
<img width="200" src="Images/Barcode%202.png" alt="Material Bread logo">
</h1>