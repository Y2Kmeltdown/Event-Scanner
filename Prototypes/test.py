import scipy
import numpy as np

x = np.array([10, 7, 6, 3])

print(x)

output = np.exp(x)/sum(np.exp(x))
print(output)
