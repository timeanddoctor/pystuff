# from vtk import vtkUnsignedCharArray
# from vtk.util.numpy_support import vtk_to_numpy
# 
# array = vtkUnsignedCharArray()
# array.SetNumberOfTuples(numBytes)
# array.SetVoidArray(image.GetScalarPointer(), numBytes, 1)
# frame = vtk_to_numpy(array)

import vtk
from vtk.util.numpy_support import vtk_to_numpy

transform = vtk.vtkTransform()
mat = transform.GetMatrix()

arr = vtk.vtkDoubleArray()
arr.SetNumberOfValues(16)
arr.SetVoidArray(mat.GetData(), 16, 4)
npArr = vtk_to_numpy(arr)
npArr[0] = 0.0
npArr[1] = 1.0

print(mat)
