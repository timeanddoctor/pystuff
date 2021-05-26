import numpy as np

m0 = np.c_[[0.99962   ,-0.0268019, -0.00642822, -5.16867],
           [0.0267226 , 0.999569, -0.0121134, 1.76983],
           [0.00675012, 0.0119371, 0.999906, 2.53002],
           [0, 0, 0, 1]]

m1 = np.c_[[0.99962, 0.0267226, 0.00675012, 5.16914],
           [ -0.0268019, 0.999569, 0.0119371, 0.561127],
           [ -0.00642822, -0.0121134, 0.999906, -2.57185],
           [ 0, 0, 0, 1]]

m2 = np.dot(m0,m1)


 1 0 0 0
    0 1 0 -2.5
    0 0 1 0
    0 0 0 1


vtkMatrix4x4 (000002034CAC34B0)
  Debug: Off
  Modified Time: 1643792
  Reference Count: 1
  Registered Events: (none)
  Elements:
    0.99984 -0.0143521 -0.0107123 -4.29338
    0.0143037 0.999887 -0.00458406 2.55135
    0.0107769 0.00443009 0.999932 1.66727
    0 0 0 1
