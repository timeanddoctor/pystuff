import vtk

class InteractorStyle(vtk.vtkInteractorStyleRubberBandPick):
    def __init__(self, parent=None):
        self.SelectedMapper = vtk.vtkDataSetMapper()
        self.SelectedActor = vtk.vtkActor()
        self.SelectedActor.SetMapper(self.SelectedMapper)
        self.AddObserver("LeftButtonReleaseEvent", self.onLeftButtonUp)

        self.Points = None

    def onLeftButtonUp(self, obj, event):
      # Forward events
      self.OnLeftButtonUp()

      frustum = self.GetInteractor().GetPicker().GetFrustum()

      extractGeometry = vtk.vtkExtractGeometry()
      extractGeometry.SetImplicitFunction(frustum)
      extractGeometry.SetInputData(self.Points)
      extractGeometry.Update()

      glyphFilter = vtk.vtkVertexGlyphFilter()
      glyphFilter.SetInputConnection(extractGeometry.GetOutputPort())
      glyphFilter.Update()

      selected = glyphFilter.GetOutput()
      print("Selected " + str(selected.GetNumberOfPoints()) + " points.")
      print("Selected " + str(selected.GetNumberOfCells()) + " cells.")
      self.SelectedMapper.SetInputData(selected)
      self.SelectedMapper.ScalarVisibilityOff()

      ids = selected.GetPointData().GetArray("OriginalIds")

      for i in range(ids.GetNumberOfTuples()):
          print("Id " + str(i) + str(ids.GetValue(i)))

      self.SelectedActor.GetProperty().SetColor(1.0, 0.0, 0.0) #(R,G,B)
      self.SelectedActor.GetProperty().SetPointSize(3)

      self.GetCurrentRenderer().AddActor(self.SelectedActor)
      self.GetInteractor().GetRenderWindow().Render()
      self.HighlightProp(None)

    def SetPoints(self, points):
        self.Points = points


pointSource = vtk.vtkPointSource()
pointSource.SetNumberOfPoints(20)
pointSource.Update()

idFilter = vtk.vtkIdFilter()
idFilter.SetInputConnection(pointSource.GetOutputPort())
idFilter.SetPointIdsArrayName("OriginalIds")
idFilter.Update()

surfaceFilter = vtk.vtkDataSetSurfaceFilter()
surfaceFilter.SetInputConnection(idFilter.GetOutputPort())
surfaceFilter.Update()

input0 = surfaceFilter.GetOutput()

# Create a mapper and actor
mapper = vtk.vtkPolyDataMapper()
mapper.SetInputData(input0)
mapper.ScalarVisibilityOff()

actor = vtk.vtkActor()
actor.SetMapper(mapper)

# Visualize
renderer = vtk.vtkRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer)

areaPicker = vtk.vtkAreaPicker()
renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetPicker(areaPicker)
renderWindowInteractor.SetRenderWindow(renderWindow)

renderer.AddActor(actor)
#renderer.SetBackground(1,1,1) # Background color white

renderWindow.Render()

style = InteractorStyle()
style.SetPoints(input0)
renderWindowInteractor.SetInteractorStyle( style )

renderWindowInteractor.Start()
