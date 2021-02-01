import vtk
from vtk.util import numpy_support
import numpy as np

freeType = vtk.vtkFreeTypeTools.GetInstance()
textProperty = vtk.vtkTextProperty()
textProperty.SetColor(1.0, 0.0, 0.0) # red
textProperty.SetFontSize(36)
textProperty.BoldOn()
textProperty.SetBackgroundOpacity(0.0)
textProperty.SetJustificationToCentered()
#textProperty.SetFrameWidth(8) # Round-up to nearest power of 2
#textProperty.SetFrameColor(0,0,0)
#textProperty.FrameOn()
#textProperty.SetFontFamilyAsString("Arial")
#textProperty.SetFontFamilyAsString("Times")
textProperty.SetFontFamilyAsString("Courier")
textProperty.Modified()

nxy = 40
arr = np.zeros((nxy, nxy, 4),dtype=np.uint8)
arr[:,:,:] = [0,255,0,255]
colors = numpy_support.numpy_to_vtk(arr.ravel(), deep=False,
                                      array_type=vtk.VTK_UNSIGNED_CHAR)
textImage = vtk.vtkImageData()

dpi = 200
sz = [0, 0]
freeType.RenderString(textProperty, "R", dpi, textImage, sz)
print(sz)

changeInformation = vtk.vtkImageChangeInformation()
changeInformation.SetInputData(textImage)
#changeInformation.CenterImageOn()
changeInformation.Update()
  
image0 = changeInformation.GetOutput()
print(image0.GetDimensions())

backGround = vtk.vtkImageData()
backGround.SetDimensions(nxy, nxy, 1)
colors.SetNumberOfComponents(4)
colors.SetNumberOfTuples(backGround.GetNumberOfPoints())
backGround.GetPointData().SetScalars(colors)

blend = vtk.vtkImageBlend()
blend.AddInputData(backGround)
blend.AddInputData(textImage)
blend.SetOpacity(0, 0.5) # background image: 50% opaque
blend.SetOpacity(1, 1.0) # text: 100% opaque
blend.Update()

writer = vtk.vtkPNGWriter()
writer.SetFileName("testMe.png")
#writer.SetInputConnection(blend.GetOutputPort())
writer.SetInputData(textImage)
writer.Write()
