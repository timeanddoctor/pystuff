import vtk
import sys
import os

def main(argv):
  fileName, fileExtension = os.path.splitext(argv[1])
  fileExtension = fileExtension.lower()
  if fileExtension in ['.mha', '.mhd']:
    reader = vtk.vtkMetaImageReader()
    reader.SetFileName(argv[1])
    reader.Update()
  elif fileExtension in ['.png']:
    reader = vtk.vtkPNGReader()
    reader.SetFileName(argv[1])
    reader.Update()

  imgData = reader.GetOutput()
  low, high = imgData.GetPointData().GetScalars().GetRange()
  print("low: %f, high: %f" % (low, high))
  print(imgData.GetDimensions())
  image = vtk.vtkImageActor()
  image.GetMapper().SetInputConnection(reader.GetOutputPort())

  image.GetProperty().SetColorWindow(high-low)
  image.GetProperty().SetColorLevel(0.5*(low+high))

  renderer = vtk.vtkRenderer()
  renderer.AddActor(image)

  window = vtk.vtkRenderWindow()
  window.AddRenderer(renderer)

  interactor = vtk.vtkRenderWindowInteractor()
  interactor.SetRenderWindow(window)

  style = vtk.vtkInteractorStyleImage()
  interactor.SetInteractorStyle(style)

  interactor.Start()

if __name__ == '__main__':
  main(sys.argv)
