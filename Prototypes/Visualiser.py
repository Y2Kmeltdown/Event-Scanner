import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import time
import event_stream


decoder = event_stream.Decoder('CODE-Ev Dataset\Speed 1\\2022-10-11T12-13-23.es')
if decoder.type == 'generic':
    print('generic events')
else:
    print(f'{decoder.type} events, {decoder.width} x {decoder.height} sensor')

#plt.ion()

#figure, ax = plt.subplots(figsize=(10, 8))

data = np.full(decoder.height, 0.5)
x = np.arange(decoder.height)
#line1, = ax.plot(x, data)
#plt.ylim([-0.1, 1.1])


dataSurface = data
for chunk in decoder:
    filteredChunk = chunk[chunk["x"] == 600]
    if filteredChunk["t"].any():
        
        data[filteredChunk["y"]] = filteredChunk["on"]
        dataSurface = np.vstack((dataSurface, data))
    
        #line1.set_ydata(data)
        #figure.canvas.draw()

        #figure.canvas.flush_events()

        #time.sleep(0.01)
            
fig1 = plt.figure()
ha = fig1.add_subplot(111, projection='3d')
print(np.shape(dataSurface))
xRange = np.arange(np.shape(dataSurface)[0])
yRange = np.arange(np.shape(dataSurface)[1])
X, Y = np.meshgrid(yRange, xRange)  # `plot_surface` expects `x` and `y` data to be 2D
ha.plot_surface(X, Y, dataSurface, cmap=cm.coolwarm,
                       linewidth=0, antialiased=False)

plt.show()

