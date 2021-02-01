import vtk


from vtk.util.colors import red



def rendering(mapper):

    """Takes mapper and handles the rendering."""

    actor = vtk.vtkActor()
    mapper.ScalarVisibilityOff()

    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(red)
    actor.GetProperty().SetLineWidth(3)


    # Create a renderer, render window, and interactor

    renderer = vtk.vtkRenderer()

    renderWindow = vtk.vtkRenderWindow()

    renderWindow.AddRenderer(renderer)

    renderWindowInteractor = vtk.vtkRenderWindowInteractor()

    renderWindowInteractor.SetRenderWindow(renderWindow)

    # Add the actors to the scene

    renderer.AddActor(actor)

    # Render and interact

    renderWindow.Render()

    renderWindowInteractor.Start()

    return



pts = vtk.vtkPoints()

pts.SetNumberOfPoints(4)

pts.SetPoint(0, 0.5, 0, 0)

pts.SetPoint(1, 1, 0.5, 0)

pts.SetPoint(2, 0.5, 1, 0)

pts.SetPoint(3, 0, 0.5, 0)



lines = vtk.vtkCellArray()

lines.InsertNextCell(5)

lines.InsertCellPoint(0)

lines.InsertCellPoint(1)

lines.InsertCellPoint(2)

lines.InsertCellPoint(3)

lines.InsertCellPoint(0)



poly = vtk.vtkPolyData()

poly.SetPoints(pts)

poly.SetLines(lines)



tubes = vtk.vtkTubeFilter()

tubes.SetInputData(poly)

tubes.CappingOn()

tubes.SidesShareVerticesOff()

tubes.SetNumberOfSides(4)

tubes.SetRadius(0.1)

tubes.Update()



mapper = vtk.vtkPolyDataMapper()

mapper.SetInputData(tubes.GetOutput())

rendering(mapper)

# Use vtkCleanPolyData to fix this
