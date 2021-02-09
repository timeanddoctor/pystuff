#!/usr/bin/env python

import os.path

import vtk


def get_program_parameters():
    import argparse
    description = 'Clip polydata using a plane.'
    epilogue = '''
    This is an example using vtkClipPolyData to clip input polydata, if provided, or a sphere otherwise.
    '''
    parser = argparse.ArgumentParser(description=description, epilog=epilogue)
    parser.add_argument('filename', nargs='?', default=None, help='Optional input filename e.g cow.g.')
    args = parser.parse_args()
    return args.filename


def main():
    filePath = get_program_parameters()

    # Define colors
    colors = vtk.vtkNamedColors()
    backgroundColor = colors.GetColor3d("steel_blue")
    boundaryColor = colors.GetColor3d("Banana")
    clipColor = colors.GetColor3d("Tomato")
    restColor = colors.GetColor3d("Red")

    if filePath and os.path.isfile(filePath):
        polyData = ReadPolyData(filePath)
        if not polyData:
            polyData = GetSpherePD()
    else:
        polyData = GetSpherePD()

    plane = vtk.vtkPlane()
    plane.SetOrigin(polyData.GetCenter())
    plane.SetNormal(1.0, -1.0, -1.0)

    clipper = vtk.vtkClipPolyData()
    clipper.SetInputData(polyData)
    clipper.SetClipFunction(plane)
    clipper.SetValue(0)
    clipper.Update()

    polyData = clipper.GetOutput()

    clipMapper = vtk.vtkDataSetMapper()
    clipMapper.SetInputData(polyData)

    clipActor = vtk.vtkActor()
    clipActor.SetMapper(clipMapper)
    clipActor.GetProperty().SetDiffuseColor(clipColor)
    clipActor.GetProperty().SetInterpolationToFlat()
    clipActor.GetProperty().EdgeVisibilityOn()

    # Now extract feature edges
    boundaryEdges = vtk.vtkFeatureEdges()
    boundaryEdges.SetInputData(polyData)
    boundaryEdges.BoundaryEdgesOn()
    boundaryEdges.FeatureEdgesOff()
    boundaryEdges.NonManifoldEdgesOff()
    boundaryEdges.ManifoldEdgesOff()

    boundaryStrips = vtk.vtkStripper()
    boundaryStrips.SetInputConnection(boundaryEdges.GetOutputPort())
    boundaryStrips.Update()

    # Change the polylines into polygons
    boundaryPoly = vtk.vtkPolyData()
    boundaryPoly.SetPoints(boundaryStrips.GetOutput().GetPoints())
    boundaryPoly.SetPolys(boundaryStrips.GetOutput().GetLines())


    append = vtk.vtkAppendPolyData()
    append.AddInputData(boundaryPoly)
    append.AddInputData(polyData)
    cleanFilter = vtk.vtkCleanPolyData()
    cleanFilter.SetInputConnection(append.GetOutputPort())
    cleanFilter.Update()

    boundaryMapper = vtk.vtkPolyDataMapper()
    boundaryMapper.SetInputData(boundaryPoly)

    boundaryActor = vtk.vtkActor()
    boundaryActor.SetMapper(boundaryMapper)
    boundaryActor.GetProperty().SetDiffuseColor(boundaryColor)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(cleanFilter.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetDiffuseColor(restColor)
    actor.GetProperty().SetInterpolationToFlat()

    # create renderer render window, and interactor
    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.AddRenderer(renderer)
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(renderWindow)

    # set background color and size
    renderer.SetBackground(backgroundColor)
    renderWindow.SetSize(640, 480)

    # add our actor to the renderer
    #renderer.AddActor(clipActor)
    #renderer.AddActor(boundaryActor)
    renderer.AddActor(actor)

    # Generate an interesting view
    renderer.ResetCamera()
    renderer.GetActiveCamera().Azimuth(30)
    renderer.GetActiveCamera().Elevation(30)
    renderer.GetActiveCamera().Dolly(1.2)
    renderer.ResetCameraClippingRange()

    # Print number of open edges
    featureEdges = vtk.vtkFeatureEdges()
    featureEdges.FeatureEdgesOff()
    featureEdges.BoundaryEdgesOn()
    featureEdges.NonManifoldEdgesOn()

    featureEdges.Update()
    print("Number of open edges: % d" % (featureEdges.GetOutput().GetNumberOfCells()))

    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName('./output.vtp')
    writer.SetInputConnection(cleanFilter.GetOutputPort())
    writer.Update()

    renderWindow.Render()
    renderWindow.SetWindowName('CapClip')
    renderWindow.Render()

    interactor.Start()


def ReadPolyData(file_name):
    import os
    path, extension = os.path.splitext(file_name)
    extension = extension.lower()
    if extension == ".ply":
        reader = vtk.vtkPLYReader()
        reader.SetFileName(file_name)
        reader.Update()
        poly_data = reader.GetOutput()
    elif extension == ".vtp":
        reader = vtk.vtkXMLPolyDataReader()
        reader.SetFileName(file_name)
        reader.Update()
        poly_data = reader.GetOutput()
    elif extension == ".obj":
        reader = vtk.vtkOBJReader()
        reader.SetFileName(file_name)
        reader.Update()
        poly_data = reader.GetOutput()
    elif extension == ".stl":
        reader = vtk.vtkSTLReader()
        reader.SetFileName(file_name)
        reader.Update()
        poly_data = reader.GetOutput()
    elif extension == ".vtk":
        reader = vtk.vtkpoly_dataReader()
        reader.SetFileName(file_name)
        reader.Update()
        poly_data = reader.GetOutput()
    elif extension == ".g":
        reader = vtk.vtkBYUReader()
        reader.SetGeometryFileName(file_name)
        reader.Update()
        poly_data = reader.GetOutput()
    else:
        # Return a None if the extension is unknown.
        poly_data = None
    return poly_data


def GetSpherePD():
    """
    :return: The PolyData representation of a sphere.
    """
    source = vtk.vtkSphereSource()
    source.SetThetaResolution(20)
    source.SetPhiResolution(11)
    source.Update()
    return source.GetOutput()


if __name__ == '__main__':
    main()
