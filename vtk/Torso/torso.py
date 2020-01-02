import vtk

def CreateSkinActor(fileName):
  reader = vtk.vtkMetaImageReader()
  reader.SetFileName(fileName)
  reader.Update()
  
  isoValue = 300
  mcubes = vtk.vtkMarchingCubes()
  mcubes.SetInputConnection(reader.GetOutputPort())
  mcubes.ComputeScalarsOff()
  mcubes.ComputeGradientsOff()
  mcubes.ComputeNormalsOff()
  mcubes.SetValue(0, isoValue)

  if 0:
    smoothingIterations = 5
    passBand = 0.001
    featureAngle = 60.0
    smoother = vtk.vtkWindowedSincPolyDataFilter()
    smoother.SetInputConnection(mcubes.GetOutputPort())
    smoother.SetNumberOfIterations(smoothingIterations)
    smoother.BoundarySmoothingOff()
    smoother.FeatureEdgeSmoothingOff()
    smoother.SetFeatureAngle(featureAngle)
    smoother.SetPassBand(passBand)
    smoother.NonManifoldSmoothingOn()
    smoother.NormalizeCoordinatesOn()
    smoother.Update()

    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(smoother.GetOutputPort())
    normals.SetFeatureAngle(featureAngle)

    stripper = vtk.vtkStripper()
    stripper.SetInputConnection(normals.GetOutputPort())
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(stripper.GetOutputPort())
  else:
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(mcubes.GetOutputPort())
    mapper.ScalarVisibilityOff()

  actor = vtk.vtkActor()
  actor.SetMapper(mapper)

  return actor

def CreateOutline(fileName):
  reader = vtk.vtkMetaImageReader()
  reader.SetFileName(fileName)
  reader.Update()
  outlineData = vtk.vtkOutlineFilter()
  outlineData.SetInputConnection(reader.GetOutputPort());

  mapOutline = vtk.vtkPolyDataMapper()
  mapOutline.SetInputConnection(outlineData.GetOutputPort())

  actor = vtk.vtkActor()
  actor.SetMapper(mapOutline)
  actor.GetProperty().SetColor(colors.GetColor3d("Black"))
  return actor

colors = vtk.vtkNamedColors()

colors.SetColor("SkinColor", 255, 125, 64, 0)

renderer = vtk.vtkOpenGLRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer)
renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

fileName1 = '/home/jmh/github/data/MRI/MR-Abdomen.mhd'

skinActor = CreateSkinActor(fileName1)
skinActor.GetProperty().SetColor(colors.GetColor3d("SkinColor"))
skinActor.GetProperty().SetOpacity(.9) # 0.4
renderer.AddActor(skinActor)

outline = CreateOutline(fileName1)
renderer.AddActor(outline)


renderer.GetActiveCamera().SetViewUp(0, 0, -1)
renderer.GetActiveCamera().SetPosition(0, -1, 0)

renderer.GetActiveCamera().Azimuth(210)
renderer.GetActiveCamera().Elevation(30)
renderer.ResetCamera()
renderer.ResetCameraClippingRange()
renderer.GetActiveCamera().Dolly(1.5)
renderer.SetBackground(colors.GetColor3d("SlateGray"))

renderWindow.SetSize(640, 480)
renderWindow.Render()

renderWindowInteractor.Start()
