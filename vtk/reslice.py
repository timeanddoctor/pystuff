from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk
import vtk
import numpy as np
import math

import matplotlib.pyplot as plt

plt.ion()

autoCrop = True
dimReduce = True
#autoCrop = False
#dimReduce = False
# Without autocrop and dimensionality, you can set output origin is always zero

def vtkToNumpy(data):
    temp = vtk_to_numpy(data.GetPointData().GetScalars())
    dims = data.GetDimensions()
    numpy_data = temp.reshape(dims[2], dims[1], dims[0])
    numpy_data = numpy_data.transpose(2,1,0) # avoid this
    return numpy_data

def numpyToVTK(data):
    flat_data_array = data.transpose(2,1,0).flatten() # avoid transpose
    vtk_data_array = numpy_to_vtk(flat_data_array)
    vtk_data = numpy_to_vtk(num_array=vtk_data_array, deep=True, array_type=vtk.VTK_FLOAT)
    img = vtk.vtkImageData()
    img.GetPointData().SetScalars(vtk_data)
    img.SetDimensions(data.shape)
    return img

img = np.zeros(shape=[512,512,120])
img[0:300,0:100,:] = 1

vtkImg = numpyToVTK(img)

reslice = vtk.vtkImageReslice()
reslice.SetInputData(vtkImg)
if autoCrop:
  reslice.SetAutoCropOutput(True)
else:
  reslice.SetAutoCropOutput(False)

if dimReduce:
  reslice.SetOutputDimensionality(2)

reslice.SetInterpolationModeToCubic()
reslice.SetSlabNumberOfSlices(1)
reslice.SetOutputSpacing(1.0,1.0,1.0)

if 1:
  a = math.pi/4
  center = [100, 254.5, 40]
else:
  a = 0.0
  center = [256, 1000, 100]

x = [math.cos(a),math.sin(a),0]
y = [-math.sin(a),math.cos(a),0]
z = [0,0,1]


axialElement = [
    x[0], y[0], z[0], center[0],
    x[1], y[1], z[1], center[1],
    x[2], y[2], z[2], center[2],
    0,    0,    0,    1
]
resliceAxes = vtk.vtkMatrix4x4()
resliceAxes.DeepCopy(axialElement)
reslice.SetResliceAxes(resliceAxes)
reslice.Update()

reslicedImg = reslice.GetOutput()

# SetAutoCropOutput(True) cause vtkImageReslice to choose and origin for the output slice

print("spacing %g %g %g" % reslicedImg.GetSpacing())
print("origin %g %g %g" % reslicedImg.GetOrigin())
print("extent %i %i %i %i %i %i" % reslicedImg.GetExtent())


# How to obtain coordinate of 3D image for (x,y) in reslicedNpImg?

# Pixel to input voxel

# Multiply output spacing (1,1,1)
# Add output origin
# Call vtkImageReslice.GetResliceAxes().MultiplyPoint()
# Subtract input origin and divide by input spacing

spacing = np.r_[reslicedImg.GetSpacing()]
origin = np.r_[reslicedImg.GetOrigin()]

pixel = np.r_[0,0]

# Multiply spacing
tmp = pixel * spacing[0:len(pixel)]

# Add origin
tmp = np.r_[tmp, 0] + origin

# 3D coordinate of pixel value
coord = reslice.GetResliceAxes().MultiplyDoublePoint([tmp[0],
                                                      tmp[1],
                                                      tmp[2],1])
print(coord)

reslicedNpImg = vtkToNumpy(reslicedImg)

plt.figure()
plt.imshow(reslicedNpImg[:,:,0])
plt.show()

# From 3D coordinates to pixel coordinates

invertAxes = vtk.vtkMatrix4x4()
vtk.vtkMatrix4x4.Invert(resliceAxes, invertAxes)
location = invertAxes.MultiplyDoublePoint([coord[0], coord[1], coord[2], 1])
print(location)
print([location[0]-origin[0],location[1]-origin[1],location[2]-origin[2]])
