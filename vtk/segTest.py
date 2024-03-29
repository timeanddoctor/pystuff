import os
import sys
import vtk

from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk
from vtk.util.colors import red, yellow

from vtkUtils import numpyTypeToVTKType, toVtkImageData

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# This is for demonstration only. For the production code, we will do
# something radically different
from skimage.segmentation import (morphological_chan_vese,
                                  checkerboard_level_set)

reader = vtk.vtkMetaImageReader()
reader.SetFileName('./output.mhd')
reader.Update()

arg = reader.GetOutput()
# Convert VTK to NumPy image
dims = arg.GetDimensions()
vtk_array = arg.GetPointData().GetScalars()
nComponents = vtk_array.GetNumberOfComponents()


# dims[2] == 1
#temp = vtk_to_numpy(vtk_array).reshape(dims[2], dims[1], dims[0], nComponents)
#npData = temp[:,:,:,0].reshape(dims[1], dims[0])
npData = vtk_to_numpy(vtk_array).reshape(dims[2], dims[1], dims[0], nComponents)[:,:,:,0].reshape(dims[1],dims[0])
init_ls = checkerboard_level_set(npData.shape, 6)

contours = morphological_chan_vese(npData, 4, init_level_set=init_ls,
                                smoothing=2)
# Add singleton to get 3-dimensional data
data = contours[None, :]

importer = vtk.vtkImageImport()
importer.SetDataScalarType(vtk.VTK_SIGNED_CHAR)
importer.SetDataExtent(0,data.shape[2]-1,
                       0,data.shape[1]-1,
                       0,data.shape[0]-1)
importer.SetWholeExtent(0,data.shape[2]-1,
                        0,data.shape[1]-1,
                        0,data.shape[0]-1)
importer.SetImportVoidPointer(data.data)
importer.Update()
vtkData = importer.GetOutput()
  
vtkData.SetOrigin(0,0,0)
vtkData.SetSpacing(arg.GetSpacing())
vtkData.Modified()

contourFilter = vtk.vtkContourFilter()
normals = vtk.vtkPolyDataNormals()
stripper = vtk.vtkStripper()
mapper = vtk.vtkPolyDataMapper()

iso_value = 0.5
contourFilter.SetInputData(vtkData)
contourFilter.SetValue(0, iso_value)
contourFilter.Update()
contourFilter.ReleaseDataFlagOn()

normals.SetInputConnection(contourFilter.GetOutputPort())
normals.SetFeatureAngle(60.0)
normals.ReleaseDataFlagOn()

stripper.SetInputConnection(normals.GetOutputPort())
stripper.ReleaseDataFlagOn()
stripper.Update()

# Transform polydata using matrix

nextContour = stripper.GetOutput()

sys.stdout.write('No of points: ')
print(nextContour.GetNumberOfPoints())
print(nextContour.GetPoint(0))

mapper.SetInputData(nextContour)

contourActor = vtk.vtkActor()
contourActor.SetMapper(mapper)
contourActor.GetProperty().ShadingOff()
contourActor.GetProperty().SetColor(red)

renderer = vtk.vtkRenderer()
renderer.AddViewProp(contourActor)
renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer)
renderWindow.Render()

interactor = vtk.vtkRenderWindowInteractor()
interactor.SetRenderWindow(renderWindow)

interactor.Start()


sys.exit(0)
# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
    
