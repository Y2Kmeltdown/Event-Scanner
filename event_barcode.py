import datetime
import pathlib
import psee413
import time
import numpy as np
import tread_carefully

# Event Scanner Class
class eventScanner():
    def __init__(self, threshold, error):
        self.threshold = threshold
        self.error = error
        self.wait = None
        self.messageUnitLength = 8
        self.messageContents = []
        self.header = self.eventCode()
        self.message = self.eventCode()
        self.msgBit = self.eventCode()
        self.reset()

    def readEvents(self, data, t):
        events = np.shape(data)[0]

        if events >= self.threshold:
            self.dataOn = np.sum(data)
            self.dataOff = events - self.dataOn
            self.t = int(t)

            if self.mode == 0:
                self.findByte(self.header)
                if self.header.complete:
                    self.setMode(1)
                    self.initMsg()
                    print("Scanning Barcode")

            elif self.mode == 1:
                self.findByte(self.msgBit)

                if self.msgBit.complete:
                    if self.compareBytes(self.header, self.msgBit):
                        prototypeMsg = self.testMsg(self.messageContents)
                        if self.compareBytes(self.message, prototypeMsg):
                            self.closeMsg(prototypeMsg)
                            self.setMode(2)
                            return True
                        
                    else:
                        self.messageContents.append(self.msgBit)
                        self.resetMsgBit()
                        
            elif self.mode == 2:
                self.wait = time.time() + 2               

    class eventCode():
        def __init__(self):
            self.start = None
            self.end = None
            self.length = None
            self.timeout = None
            self.detected = False
            self.complete = False
            self.data = None

        def reset(self):
            self.start = None
            self.end = None
            self.length = None
            self.timeout = None
            self.detected = False
            self.complete = False
            self.data = None
         
    def reset(self):
        self.resetHeader()
        self.resetMsg()
        self.resetMsgBit()
        self.messageContents = []
        self.wait = None
        self.setMode(0)

    def resetHeader(self):
        self.header.reset()

    def resetMsg(self):
        self.message.reset()

    def resetMsgBit(self):
        self.msgBit.reset()

    def findByte(self, eventMsg:eventCode):
        #If Off events spike larger then on events, locate header start and set start bit flag
        if self.dataOff > self.dataOn:
            eventMsg.detected = True
            eventMsg.start = self.t
            eventMsg.timeout = time.time() + 2
        
        #If On events spike larger then off events and start bit was created, Close header and begin logging
        if self.dataOn > self.dataOff and eventMsg.detected:
            eventMsg.end = self.t
            eventMsg.length = eventMsg.end - eventMsg.start
            eventMsg.timeout = None
            eventMsg.complete = True
            eventMsg.detected = False

    def compareBytes(self, byte1:eventCode, byte2:eventCode):
        lengthError = abs((byte1.length-byte2.length)/byte1.length)*100
        if lengthError < self.error:
            return True
        else:
            return False

    def getHeader(self):
        return self.header

    def initMsg(self):
        self.message.detected = True
        self.message.start = self.t
        self.message.timeout = time.time()+5
        self.message.length = self.header.length*self.messageUnitLength - 2*self.header.length
        self.message.end = self.t + self.header.length

    def testMsg(self, messageContents:list):
        msg = self.eventCode()
        msg.start = messageContents[0].start
        msg.end = messageContents[-1].end
        msg.length = msg.end - msg.start
        msg.complete = True
        return msg

    def closeMsg(self, prototype:eventCode()):
        self.message.end = prototype.end
        self.message.length = prototype.length
        self.message.data = prototype
        self.message.timeout = None
        self.message.complete = True
        self.message.detected = False
        self.completedHeader = self.header
        self.completedMessage = self.message

    def getMessage(self):
        def coallateData(eventMsg:self.eventCode, index):
            return (index, eventMsg.start, eventMsg.end, eventMsg.length)
        if self.completedMessage:
            totalBits = len(self.completedMessage.data)
            message = [coallateData(self.completedMessage, totalBits)]
            index = 0
            message.append(coallateData(self.completedHeader, index))
            index += 1
            for bit in self.completedMessage.data:
                message.append(coallateData(bit, index))
                index += 1
            message.append(coallateData(self.completedHeader, index))
            return message
        
    def setMode(self, mode:int):
        # Mode 0 = Searching Mode
        # Mode 1 = Scanning Mode
        # Mode 2 = Cool down Mode
        self.mode = mode

    def checkByteTimeout(self, eventMsg:eventCode):
        if eventMsg.timeout:
            if eventMsg.timeout < time.time():
                eventMsg.reset()
                return True
            else:
                return False
        else:
            return False

    def timing(self):
        if self.wait:
            if self.wait < time.time():
                self.reset()
                print("Cooldown Finished Scanner Reset")

        if self.checkByteTimeout(self.header):
            print("Header Timeout")

        if self.checkByteTimeout(self.msgBit):
            print("Bit Timeout")

        if self.checkByteTimeout(self.message):
            self.reset()
            print("Message Timeout")

if __name__ == "__main__":
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

    actuatorTimeout = 3
    actuatorTimeStart = 0

    tStep = 800
    tIter = tStep
    eventAxis = 600

    #Initialise Class
    evBarcodeReader = eventScanner(threshold = 200, error = 20)

    #Loop through events
    while True:
        events = camera.next_packet()

        # Get specific range in the x axis for input events
        filteredChunk = events[events["x"] >= eventAxis-2]
        filteredChunk = filteredChunk[filteredChunk["x"] <= eventAxis+2]

        if filteredChunk["t"].any():
            
            # get most current timestep in the event list
            tlast = filteredChunk["t"][-1]

            # Loop until iterator is greater then last timestamp in chunk
            while tIter < tlast+tStep:
                # Segment events into smaller time chunks
                # filter chunk by time chunk prevIter <-> currentIter
                nestedChunk = filteredChunk[filteredChunk["t"] < tIter]
                nestedChunk = nestedChunk[filteredChunk["t"] >= tIter-tStep]

                if nestedChunk["t"].any():

                    # THIS IS WHERE READABLE DATA IS PRODUCED
                    data = nestedChunk["on"]
                    t = nestedChunk["t"][0]

                    # When the scanner completes a barcode the message can be retrieved from the eventScanner class
                    if evBarcodeReader.readEvents(data, t):

                        # Get message from event scanner
                        message = evBarcodeReader.getMessage()
                        
                        # Check message length
                        if message[0][0] == 7:
                            actuator.move(-300)
                            actuatorTimeStart = time.time()
                        elif message[0][0] == 5:
                            actuator.move(300)
                            actuatorTimeStart = time.time()

        # event Scanner timer used to determine timeouts
        evBarcodeReader.timing()

        if actuatorTimeStart:
            if actuatorTimeout <= time.time()-actuatorTimeStart:
                print("Actuator Returning to rest")
                actuator.move(0)
                actuatorTimeStart = 0

