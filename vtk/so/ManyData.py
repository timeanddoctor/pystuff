# TODO: Use vtkPolyData

import vtk
import random as rnd


def two_line(p0, p1):
    # Create the polydata where we will store all the geometric data
    linesPolyData = vtk.vtkPolyData()

    # Create three points
    origin = [0.0, 0.0, 0.0]
    # p0 = [1.0, 0.0, 0.0]
    # p1 = [0.0, 1.0, 0.0]

    # Create a vtkPoints container and store the points in it
    pts = vtk.vtkPoints()
    pts.InsertNextPoint(origin)
    pts.InsertNextPoint(p0)
    pts.InsertNextPoint(p1)

    # Add the points to the polydata container
    linesPolyData.SetPoints(pts)

    # Create the first line (between Origin and P0)
    line0 = vtk.vtkLine()
    line0.GetPointIds().SetId(0, 0)  # the second 0 is the index of the Origin in linesPolyData's points
    line0.GetPointIds().SetId(1, 1)  # the second 1 is the index of P0 in linesPolyData's points

    # Create the second line (between Origin and P1)
    line1 = vtk.vtkLine()
    line1.GetPointIds().SetId(0, 0)  # the second 0 is the index of the Origin in linesPolyData's points
    line1.GetPointIds().SetId(1, 2)  # 2 is the index of P1 in linesPolyData's points

    # Create a vtkCellArray container and store the lines in it
    lines = vtk.vtkCellArray()
    lines.InsertNextCell(line0)
    lines.InsertNextCell(line1)

    # Add the lines to the polydata container
    linesPolyData.SetLines(lines)

    namedColors = vtk.vtkNamedColors()

    # Create a vtkUnsignedCharArray container and store the colors in it
    colors = vtk.vtkUnsignedCharArray()
    colors.SetNumberOfComponents(3)
    try:
        colors.InsertNextTupleValue(namedColors.GetColor3ub("DarkRed"))
        colors.InsertNextTupleValue(namedColors.GetColor3ub("Gold"))
    except AttributeError:
        # For compatibility with new VTK generic data arrays.
        colors.InsertNextTypedTuple(namedColors.GetColor3ub("DarkRed"))
        colors.InsertNextTypedTuple(namedColors.GetColor3ub("Gold"))

    # Color the lines.
    # SetScalars() automatically associates the values in the data array passed as parameter
    # to the elements in the same indices of the cell data array on which it is called.
    # This means the first component (red) of the colors array
    # is matched with the first component of the cell array (line 0)
    # and the second component (green) of the colors array
    # is matched with the second component of the cell array (line 1)
    linesPolyData.GetCellData().SetScalars(colors)

    # Setup the visualization pipeline
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(linesPolyData)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetLineWidth(1)

    return actor

def render_scene(my_actor_list):

    renderer = vtk.vtkRenderer()
    for arg in my_actor_list:
        renderer.AddActor(arg)
    namedColors = vtk.vtkNamedColors()
    renderer.SetBackground(namedColors.GetColor3d("SlateGray"))

    window = vtk.vtkRenderWindow()
    window.SetWindowName("Colored Lines")
    window.AddRenderer(renderer)

    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(window)

    # Visualize
    window.Render()
    interactor.Start()

if __name__ == '__main__':
    gen = 100
    lst = []
    for i in range(gen):
        up = rnd.randint(-5, 5)
        low = rnd.randint(-5, 5)
        p0 = [rnd.uniform(low, up), rnd.uniform(low, up), rnd.uniform(low, up)]
        p1 = [rnd.uniform(low, up), rnd.uniform(low, up), rnd.uniform(low, up)]
        my_actor = two_line(p0, p1)
        lst.append(my_actor)
    render_scene(lst)
