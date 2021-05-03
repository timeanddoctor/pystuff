import sys
import vtk

if __name__ == "__main__":
  inputPolyData = vtk.vtkPolyData()
  if len(sys.argv) > 1:
      reader = vtk.vtkXMLPolyDataReader()
      reader.SetFileName(sys.argv[1])
      triangles = vtk.vtkTriangleFilter()
      triangles.SetInputConnection(reader.GetOutputPort())
      triangles.Update()
      inputPolyData = triangles.GetOutput()
  else:
      sphereSource = vtk.vtkSphereSource()
      sphereSource.SetThetaResolution(30)
      sphereSource.SetPhiResolution(15)
      sphereSource.Update()
      inputPolyData = sphereSource.GetOutput()

  reduction = 0.9 # 90% reduction
  if len(sys.argv) > 2:
    reduction = float(sys.argv[2])

  colors = vtk.vtkNamedColors()
  print("Before decimation")
  print("------------")
  print("There are %d points." % (inputPolyData.GetNumberOfPoints()))
  print("There are %d polygons." % (inputPolyData.GetNumberOfPolys()))

  decimate = vtk.vtkDecimatePro()
  decimate.SetInputData(inputPolyData)
  decimate.SetTargetReduction(reduction)
  decimate.PreserveTopologyOn()
  decimate.Update()

  fillHoles = vtk.vtkFillHolesFilter()
  fillHoles.SetInputConnection(decimate.GetOutputPort())
  fillHoles.SetHoleSize(20.0)
  fillHoles.Update()

  smoothen = vtk.vtkSmoothPolyDataFilter()
  smoothen.SetInputConnection(fillHoles.GetOutputPort())
  smoothen.SetNumberOfIterations(5)
  smoothen.FeatureEdgeSmoothingOn()
  smoothen.BoundarySmoothingOff()
  smoothen.SetFeatureAngle(60)
  smoothen.SetEdgeAngle(90)
  smoothen.SetConvergence(0.001)
  smoothen.SetRelaxationFactor(0.001)
  smoothen.Update()
  
  cleaner = vtk.vtkCleanPolyData()
  cleaner.SetInputConnection(smoothen.GetOutputPort())
  cleaner.Update()
  
  output = cleaner
#  output = fillHoles
  
  decimated = vtk.vtkPolyData()
  decimated.ShallowCopy(output.GetOutput())

  print("After decimation")
  print("------------")
  print("There are %d points." % (decimated.GetNumberOfPoints()))
  print("There are %d polygons." % (decimated.GetNumberOfPolys()))

  print("Reduction: %f" % (float(inputPolyData.GetNumberOfPolys() -
                                 decimated.GetNumberOfPolys()) /
                           float(inputPolyData.GetNumberOfPolys())))

  save = True
  if (save):
      writer = vtk.vtkXMLPolyDataWriter()
      writer.SetFileName('./ProperlyReduced.vtp')
      writer.SetInputConnection(output.GetOutputPort())
      writer.Update()
      writer.Write()
  
  inputMapper = vtk.vtkPolyDataMapper()
  inputMapper.SetInputData(inputPolyData)

  backFace = vtk.vtkProperty()
  backFace.SetColor(colors.GetColor3d("Gold"))

  inputActor = vtk.vtkActor()
  inputActor.SetMapper(inputMapper)
  inputActor.GetProperty().SetInterpolationToFlat()
  inputActor.GetProperty().SetColor(
      colors.GetColor3d("NavajoWhite"))
  inputActor.SetBackfaceProperty(backFace)

  decimatedMapper = vtk.vtkPolyDataMapper()
  decimatedMapper.SetInputData(decimated)

  decimatedActor = vtk.vtkActor()
  decimatedActor.SetMapper(decimatedMapper)
  decimatedActor.GetProperty().SetColor(
      colors.GetColor3d("NavajoWhite"))
  decimatedActor.GetProperty().SetInterpolationToFlat()
  decimatedActor.SetBackfaceProperty(backFace)

  # There will be one render window
  renderWindow = vtk.vtkRenderWindow()
  renderWindow.SetSize(600, 300)
  renderWindow.SetWindowName("Decimation")

  # And one interactor
  interactor = vtk.vtkRenderWindowInteractor()
  interactor.SetRenderWindow(renderWindow)

  # Define viewport ranges
  # (xmin, ymin, xmax, ymax)
  leftViewport = [0.0, 0.0, 0.5, 1.0]
  rightViewport = [0.5, 0.0, 1.0, 1.0]

  # Setup both renderers
  leftRenderer = vtk.vtkRenderer()
  renderWindow.AddRenderer(leftRenderer)
  leftRenderer.SetViewport(leftViewport)
  leftRenderer.SetBackground(colors.GetColor3d("Peru"))

  rightRenderer = vtk.vtkRenderer()
  renderWindow.AddRenderer(rightRenderer)
  rightRenderer.SetViewport(rightViewport)
  rightRenderer.SetBackground(colors.GetColor3d("CornflowerBlue"))

  # Add the sphere to the left and the cube to the right
  leftRenderer.AddActor(inputActor)
  rightRenderer.AddActor(decimatedActor)

  # Shared camera
  # Shared camera looking down the -y axis
  camera = vtk.vtkCamera()
  camera.SetPosition(0, -1, 0)
  camera.SetFocalPoint(0, 0, 0)
  camera.SetViewUp(0, 0, 1)
  camera.Elevation(30)
  camera.Azimuth(30)

  leftRenderer.SetActiveCamera(camera)
  rightRenderer.SetActiveCamera(camera)

  leftRenderer.ResetCamera()
  leftRenderer.ResetCameraClippingRange()

  renderWindow.Render()
  interactor.Start()
