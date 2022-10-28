import datetime
import pathlib
import psee413
import time
import numpy as np
import tread_carefully

actuator = tread_carefully.Actuator("COM6")

actuator.reset()



dirname = pathlib.Path(__file__).resolve().parent

camera = psee413.Camera(
    recordings_path=dirname / "recordings",
    log_path=dirname / "recordings" / "log.jsonl",
)
camera.set_parameters(
    psee413.Parameters(
        biases=psee413.Biases(
            diff_on=140,  # default 115
            diff=80,
            diff_off=30,  # default 52
        )
    )
)

camera.start_recording_to(
    f'{datetime.datetime.now(tz=datetime.timezone.utc).isoformat().replace("+00:00", "Z").replace(":", "-")}.es'
)

timeout = 2
actuatorTimeout = 3
messageRatio = 8
message = []
threshold = 200
tStep = 800
tIter = tStep
Active = False
timeStart = 0
headerTimeStart = 0
actuatorTimeStart = 0
startBit = False
previous = None
allowedError = 20


ts = np.zeros(1)
d = np.zeros(1)

def msgOut(message, headerLength):
    totalBits = (len(message)-1)/2
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
    return msgCapsule


while True:
    events = camera.next_packet()
    # next_packet returns an empty array immediately if no events are available
    #print(f"{len(events)=}, {camera.backlog()=}, {camera.recording_status()=}")
    
    
    filteredChunk = events[events["x"] >= 600]
    filteredChunk = filteredChunk[filteredChunk["x"] <= 605]

    #Check Event data after filter exists
    if filteredChunk["t"].any():

        tlast = filteredChunk["t"][-1]
        
        # Loop until iterator is greater then last timestamp in chunk
        while tIter < tlast+tStep:

            # filter chunk by time chunk prevIter <-> currentIter
            nestedChunk = filteredChunk[filteredChunk["t"] < tIter]
            filteredChunk = filteredChunk[filteredChunk["t"] >= tIter-tStep]

            # If data exists after this filter check data
            if nestedChunk["t"].any():
                t = nestedChunk["t"][0]

                # Count events in time chunk
                data = np.shape(nestedChunk["t"])[0]
                #print(data)

                # Check if event count is larger then a threshold
                if data >= threshold:
                    # Count on and off events
                    dataOn = np.sum(nestedChunk["on"])
                    dataOff = data - dataOn
                    

                    # Run in watching mode
                    if not Active:
                        #print("Checking for Barcode")
                        
                        
                        #If Off events spike larger then on events, locate header start and set start bit flag
                        if dataOff >= threshold and dataOff > dataOn:
                            startBit = True
                            headerStart = int(t)
                            headerStartRate = dataOff
                            headerTimeStart = time.time()
                        
                        #If On events spike larger then off events and start bit was created, Close header and begin logging
                        if dataOn >= threshold and dataOn > dataOff and startBit:
                            startBit = False
                            headerEnd = int(t)
                            headerLength = headerEnd - headerStart
                            headerRate = headerStartRate + dataOn

                            messageLength = headerLength*messageRatio

                            previous = 1
                            print("Scanning Barcode")
                            Active = True
                            timeStart = time.time()
                            #Standardise Event barcode relative length and use for error checking
                            
                    # Run in reading mode
                    else:

                        # Check if Off event spike is higher then on event spike
                        if dataOff >= dataOn:

                            # If Previous Spike was different log Off event
                            if previous != 0:
                                message.append((0,t))

                            # Set previous spike to Off
                            previous = 0

                            #Start Checking closing header length
                            headerCheckStart = int(t)
                            headerRateCheckStart = dataOff

                        elif dataOn >= dataOff and previous != 1:

                            #Get closing header end length
                            headerCheckEnd = int(t)

                            #Get closing header length
                            headerCheck = headerCheckEnd - headerCheckStart

                            headerRateCheck = headerRateCheckStart + dataOn

                            #Get recorded Message Length
                            messageCheck = headerCheckEnd -headerStart

                            #Get percentage error from starting header length
                            headerCheckError = abs((headerCheck-headerLength)/headerLength)*100
                            messageCheckError = (messageCheck-messageLength)/messageLength*100
                            #print(headerCheckError)
                            #print(messageCheckError)
                            # If header is inside allowable error close message
                            if headerCheckError < allowedError and messageCheckError > -allowedError:
                                print("Message Complete")
                                outputMsg = msgOut(message, headerLength)
                                if outputMsg[0][0] == 7:
                                    actuator.move(-300)
                                    actuatorTimeStart = time.time()
                                elif outputMsg[0][0] == 5:
                                    actuator.move(300)
                                    actuatorTimeStart = time.time()
                                message = []
                                Active = False
                                timeStart = 0
                                previous = 1
                            else:
                                # Log on event. Not difference checked since on and off events get paired
                                print("Bit Read")
                                message.append((1,t))
                                previous = 1
                                if messageCheckError >= allowedError:
                                    print("Message Exceeds Bounds")
                                    print("Packet Discarded")
                                    message = []
                                    Active = False
                                    timeStart = 0
                            
                            


                #ts = np.vstack((ts, np.array([t])))
                #d = np.vstack((d, np.array([data])))
            tIter += tStep

    if headerTimeStart:
        if timeout <= time.time()-headerTimeStart:
            startBit = False

    if timeStart:
        if timeout <= time.time()-timeStart:
            print("Timeout")
            print("Packet Discarded")
            message = []
            Active = False
            timeStart = 0

    if actuatorTimeStart:
        if actuatorTimeout <= time.time()-actuatorTimeStart:
            print("Actuator Returning to rest")
            actuator.move(0)
            actuatorTimeStart = 0


    if len(events) == 0:
        time.sleep(0.1)
