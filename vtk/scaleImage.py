import vtk
from vtk.util import numpy_support
import numpy as np

nxy = 10
arr = 20+100.0*np.random.rand(100).astype(np.float32)
arr.reshape((nxy,nxy)).copy()

values = numpy_support.numpy_to_vtk(arr.ravel(), deep=False,
                                        array_type=vtk.VTK_FLOAT)
newImage = vtk.vtkImageData()
newImage.SetDimensions(nxy, nxy, 1)
newImage.AllocateScalars(vtk.VTK_FLOAT, 1)
newImage.GetPointData().SetScalars(values)

shiftScale = vtk.vtkImageShiftScale()
shiftScale.SetShift(-arr.min())
shiftScale.SetScale(255.0 / (arr.max() - arr.min()))
shiftScale.SetInputData(newImage)

cast = vtk.vtkImageCast()
cast.SetInputConnection(shiftScale.GetOutputPort())
cast.SetOutputScalarTypeToUnsignedChar()
cast.Update()

outImage = cast.GetOutput()
rng = outImage.GetScalarRange()
