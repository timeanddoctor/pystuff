import vtk
from vtk import (vtkSphereSource, vtkPolyData, vtkDecimatePro)
from vtk.util.colors import peacock, tomato, red


def decimation():
    sphereS = vtkSphereSource()
    sphereS.SetPhiResolution(20)
    sphereS.SetThetaResolution(20)
    sphereS.Update()
    inputPoly = vtkPolyData()
    inputPoly.ShallowCopy(sphereS.GetOutput())

    print("Before decimation\n"
          "-----------------\n"
          "There are " + str(inputPoly.GetNumberOfPoints()) + "points.\n"
          "There are " + str(inputPoly.GetNumberOfPolys()) + "polygons.\n")

    decimate = vtkDecimatePro()
    decimate.SetInputData(inputPoly)
    decimate.SetTargetReduction(.10)
    decimate.Update()

    decimatedPoly = vtkPolyData()
    decimatedPoly.ShallowCopy(decimate.GetOutput())

    print("After decimation \n"
          "-----------------\n"
          "There are " + str(decimatedPoly.GetNumberOfPoints()) + "points.\n"
          "There are " + str(decimatedPoly.GetNumberOfPolys()) + "polygons.\n")
    return inputPoly, decimatedPoly

if __name__ == "__main__":
    before, after = decimation()

    mapper0 = vtk.vtkPolyDataMapper()
    mapper0.ScalarVisibilityOff()

    mapper0.SetInputData(before)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper0)
    actor.GetProperty().SetColor(red)
    actor.GetProperty().SetLineWidth(3)
    actor.GetProperty().SetRepresentationToWireframe()

    actor.GetProperty().SetEdgeVisibility(1);
    actor.GetProperty().SetEdgeColor(0.9,0.9,0.4);
    actor.GetProperty().SetLineWidth(6);
    actor.GetProperty().SetPointSize(12);
    actor.GetProperty().SetRenderLinesAsTubes(1);
    actor.GetProperty().SetRenderPointsAsSpheres(1);
    actor.GetProperty().SetVertexVisibility(1);
    actor.GetProperty().SetVertexColor(0.5,1.0,0.8);

    ren = vtk.vtkRenderer()

    ren.GradientBackgroundOn()
    ren.SetBackground(1,1,1)
    ren.SetBackground2(0.5,0.5,0.5)

    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(ren)
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)

    ren.AddActor(actor)

    renWin.Render()
    iren.Start()
