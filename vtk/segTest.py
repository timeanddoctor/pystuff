import os
import sys
import vtk

from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk
from vtk.util.colors import red, yellow

from vtkUtils import numpyTypeToVTKType, toVtkImageData

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

plt.ion()

# This is for demonstration only. For the production code, we will do
# something radically different
from skimage.segmentation import (morphological_chan_vese,
                                  morphological_geodesic_active_contour,
                                  inverse_gaussian_gradient,
                                  checkerboard_level_set)

writer = vtk.vtkMetaImageReader()
writer.SetFileName('./output.mhd')
writer.Update()

arg = writer.GetOutput()
# Convert VTK to NumPy image
dims = arg.GetDimensions()
vtk_array = arg.GetPointData().GetScalars()
nComponents = vtk_array.GetNumberOfComponents()
temp = vtk_to_numpy(vtk_array).reshape(dims[2], dims[1], dims[0], nComponents)
npData = temp[:,:,:,0].reshape(dims[1], dims[0])


init_ls = checkerboard_level_set(npData.shape, 6)

contours = morphological_chan_vese(npData, 8, init_level_set=init_ls,
                                smoothing=2)
#data = 255*contours[None, :]
data = contours[None, :]

#importer = vtk.vtkImageImport()
#importer.SetDataScalarType(numpyTypeToVTKType(data.dtype))
#importer.SetDataExtent(0, data.shape[0]-1,
#                       0, data.shape[1]-1,
#                       0, data.shape[2]-1)
#importer.SetWholeExtent(0, data.shape[0]-1,
#                       0, data.shape[1]-1,
#                       0, data.shape[2]-1)
#importer.SetImportVoidPointer(data)
#importer.Update()
#vtkData = importer.GetOutput()

# TODO: Do this without toVtkImageData
vtkData = toVtkImageData(data)
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



#contours[None, :]
plt.imshow(contours)
sys.exit(0)

#from skimage.filters import gaussian
#image = gaussian(npData,4)
image = npData

init_ls = 1-checkerboard_level_set(image.shape, 6)

evolution = []
callback = store_evolution_in(evolution)

iterations = np.r_[2,7,20]

def store_evolution_in(lst):
  """Returns a callback function to store the evolution of the level sets in
  the given list.
  """
  def _store(x):
    lst.append(np.copy(x))
  return _store

lines = morphological_chan_vese(image, iterations[-1], init_level_set=init_ls,
                                smoothing=2,
                                iter_callback=callback)



fh, axes = plt.subplots(1, 2, figsize=(8, 8))
ax = axes.flatten()

ax[0].imshow(image, cmap="gray")
ax[0].set_axis_off()
ax[0].contour(lines, [0.5], colors='r')
ax[0].set_title("Morphological ACWE segmentation", fontsize=12)

ax[1].imshow(lines, cmap="gray")
ax[1].set_axis_off()

plt.show()

sys.exit(0)

def create_rainbow():
  ax = plt.gca()
  rainbow = [next(ax._get_lines.prop_cycler)['color']]
  while True:
    nextval = next(ax._get_lines.prop_cycler)['color']
    if nextval not in rainbow:
      rainbow.append(nextval)
    else:
      return rainbow

rainbow = create_rainbow()

for it in range(len(iterations)):
  contour = ax[1].contour(evolution[iterations[it]], [0.5],
                          colors=rainbow[it])
  contour.collections[0].set_label("Iteration %d" % (iterations[it]))

ax[1].legend(loc="upper right")
title = "Morphological ACWE evolution"
ax[1].set_title(title, fontsize=12)


# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
    