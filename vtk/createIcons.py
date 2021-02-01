import vtk
from vtk.util import numpy_support
import numpy as np

images = []

data = {0 : {'color' : (255.0/4, 0.0, 0.0),
             'letter' : 'S'},
        1 : {'color' : (0.0, 255.0/4, 0.0),
             'letter' : 'C'},
        2 : {'color' : (0.0, 0.0, 255.0/4),
             'letter' : 'A'}}
dpi = 200
arr = 0

for i in range(3):
  freeType = vtk.vtkFreeTypeTools.GetInstance()
  textProperty = vtk.vtkTextProperty()
  textProperty.SetColor(data[i]['color'])
  textProperty.SetFontSize(36)
  textProperty.BoldOn()
  textProperty.SetBackgroundOpacity(0.0)
  textProperty.SetJustificationToCentered()
  textProperty.SetFontFamilyAsString("Courier")
  textProperty.Modified()
  
  textImage = vtk.vtkImageData()

  sz = [0, 0]
  freeType.RenderString(textProperty, data[i]['letter'], dpi, textImage, sz)

  dims = textImage.GetDimensions()
  print(dims)
  nxy = max(dims)
  arr = np.zeros((nxy, nxy, 4),dtype=np.uint8)

  arr0 = numpy_support.vtk_to_numpy(textImage.GetPointData().GetScalars())
  arr0 = arr0.reshape(dims[1], dims[0],-1)

  offset0 = (nxy - dims[1])//2
  offset1 = (nxy - dims[0])//2
  
  arr[offset0:nxy-offset0,offset1:nxy-offset1,:] = arr0
  colors = numpy_support.numpy_to_vtk(arr.ravel(), deep=False,
                                      array_type=vtk.VTK_UNSIGNED_CHAR)
  
  newImage = vtk.vtkImageData()
  newImage.SetDimensions(nxy, nxy, 1)
  colors.SetNumberOfComponents(4)
  colors.SetNumberOfTuples(newImage.GetNumberOfPoints())
  newImage.GetPointData().SetScalars(colors)
  
  writer = vtk.vtkPNGWriter()
  writer.SetFileName(data[i]['letter']+".png")
  writer.SetInputData(newImage)
  writer.Write()

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
