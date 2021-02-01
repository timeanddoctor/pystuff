import vtk

def main():
  # Create a black image with a red circle of radius 50 centered at (60, 60)
  drawing = vtk.vtkImageCanvasSource2D()
  drawing.SetScalarTypeToUnsignedChar() # PNGWriter requires unsigned char (or unsigned short)
  drawing.SetNumberOfScalarComponents(3)
  drawing.SetExtent(0, 150, 0, 120, 0, 0) # xmin, xmax, ymin, ymax, zmin, zmax
  drawing.SetDrawColor(255, 0, 0) # red
  drawing.DrawCircle(60, 60, 50) # parameters: x, y, radius

  # Create an image of text
  freeType = vtk.vtkFreeTypeTools.GetInstance()
  textProperty = vtk.vtkTextProperty()
  textProperty.SetColor(1.0, 1.0, 0.0) # yellow
  textProperty.SetFontSize(24)
  textImage = vtk.vtkImageData()
  freeType.RenderString(textProperty, "Test String", 50, textImage)

  # Combine the images
  blend = vtk.vtkImageBlend()
  blend.AddInputConnection(drawing.GetOutputPort())
  blend.AddInputData(textImage)
  blend.SetOpacity(0, 0.5) # background image: 50% opaque
  blend.SetOpacity(1, 1.0) # text: 100% opaque
  blend.Update()

  writer = vtk.vtkPNGWriter()
  writer.SetFileName("output.png")
  writer.SetInputConnection(blend.GetOutputPort())
  writer.Write()

if __name__ == '__main__':
   main()
