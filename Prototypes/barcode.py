import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
from time import time
import event_stream

# Decoder's only argument is an Event Stream file path
# decoder is an iterator with 3 additional properties: type, width and height
#     type is one of 'generic', 'dvs', 'atis' and 'color'
#     if type is 'generic', both width and height are None
#     otherwise, width and height represent the sensor size in pixels
decoder = event_stream.Decoder('CODE-Ev Dataset\Speed 1\\2022-10-11T12-13-23.es')
if decoder.type == 'generic':
    print('generic events')
else:
    print(f'{decoder.type} events, {decoder.width} x {decoder.height} sensor')

# chunk is a numpy array whose dtype depends on the decoder type:
#     generic: [('t', '<u8'), ('bytes', 'object')]
#     dvs: [('t', '<u8'), ('x', '<u2'), ('y', '<u2'), ('on', '?')]
#     atis: [('t', '<u8'), ('x', '<u2'), ('y', '<u2'), ('exposure', '?'), ('polarity', '?')]
#     color: [('t', '<u8'), ('x', '<u2'), ('y', '<u2'), ('r', '?'), ('g', '?'), ('b', '?')]
# chunk always contains at least one event
surface = np.zeros((decoder.width, decoder.height))
#data = 0



message = []
threshold = 100
tStep = 3000
tIter = tStep
Active = False
startBit = False
previous = None
allowedError = 20


ts = np.zeros(1)
d = np.zeros(1)
for chunk in decoder:
    filteredChunk = chunk[chunk["x"] >= 600]
    filteredChunk = filteredChunk[filteredChunk["x"] <= 605]
    if filteredChunk["t"].any():
        tlast = filteredChunk["t"][-1]
        while tIter < tlast+tStep:
            nestedChunk = filteredChunk[filteredChunk["t"] < tIter]
            filteredChunk = filteredChunk[filteredChunk["t"] >= tIter-tStep]
            #print(np.shape(nestedChunk)[0])
            if nestedChunk["t"].any():
                t = nestedChunk["t"][0]
                #delT = nestedChunk["t"][-1] - nestedChunk["t"][0]
                #print(delT)
                data = np.shape(nestedChunk["t"])[0]
                if data >= threshold:
                    dataOn = np.sum(nestedChunk["on"])
                    dataOff = data - dataOn
                    if not Active:
                        if dataOn >= threshold and dataOn > dataOff and startBit:
                            startBit = False
                            headerEnd = int(t)
                            headerLength = headerEnd - headerStart
                            previous = 1
                            Active = True
                            pass
                        if dataOff >= threshold and dataOff > dataOn:
                            startBit = True
                            headerStart = int(t)
                    else:
                        if dataOff >= dataOn:
                            if previous != 0:
                                message.append((0,t))
                            previous = 0
                            headerCheckStart = int(t)
                        elif dataOn >= dataOff and previous != 1:
                            message.append((1,t))
                            previous = 1
                            headerCheckEnd = int(t)
                            headerCheck = headerCheckEnd - headerCheckStart
                            headerCheckError = abs((headerCheck-headerLength)/headerLength)*100
                            if headerCheckError < allowedError:
                                Active = False


                
                


                ts = np.vstack((ts, np.array([t])))
                d = np.vstack((d, np.array([data])))
            tIter += tStep
    
#print(headerLength)
#print(message)
totalBits = len(message)/2
messageLength = message[-1][1]-message[0][1]
msgCapsule = [[totalBits, messageLength, headerLength]]
for bit in range(len(message)):
    if message[bit][0]:
        bitEnd = message[bit][1]
        bitLength = bitEnd - bitStart
        msgCapsule.append([int(bit/2), bitStart, bitEnd, bitLength])
    else:
        bitStart = message[bit][1]

print(msgCapsule)
plt.plot(ts, d)
plt.show()
    #surface[chunk["x"], chunk["y"]] += 1




    



    
    
        
    
#index = np.arange(len(data)) + 0.3
#coords = np.linspace(0,1279,1280)
#plt.bar(x=index, height=data)
#plt.show()

#print(series)
#plt.imshow(series)
#print(list(data))
#plt.show()