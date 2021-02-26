import sys
import vtk

def main(argv):
    scale = 1.0
    if len(argv) > 1:
        reader = vtk.vtkXMLPolyDataReader()
        reader.SetFileName(argv[1])
        reader.Update()
        inputPolyData = reader.GetOutput()
    if len(argv) > 2:
        scale = float(argv[2])
    else:
        sphereSource = vtk.vtkSphereSource()
        sphereSource.SetPhiResolution(15)
        sphereSource.SetThetaResolution(15)
        sphereSource.Update()
        inputPolyData = sphereSource.GetOutput()

    clean = vtk.vtkCleanPolyData()
    clean.SetInputData(inputPolyData)

    # Generate normals
    normals =vtk.vtkPolyDataNormals()
    normals.SetInputConnection(clean.GetOutputPort())
    normals.SplittingOff()
    
    # Warp using the normals
    warp = vtk.vtkWarpVector()
    warp.SetInputConnection(normals.GetOutputPort())
    warp.SetInputArrayToProcess(0, 0, 0,
                                 vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS,
                                 vtk.vtkDataSetAttributes.NORMALS)
    warp.SetScaleFactor(scale)
    warp.Modified()
    
    # Visualize the original and warped models
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(warp.GetOutputPort())
    mapper.ScalarVisibilityOff()
    
    warpedActor = vtk.vtkActor()
    warpedActor.SetMapper(mapper)
    
    originalMapper = vtk.vtkPolyDataMapper()
    originalMapper.SetInputConnection(normals.GetOutputPort())
    originalMapper.ScalarVisibilityOff()
    
    originalActor = vtk.vtkActor()
    originalActor.SetMapper(originalMapper)
    originalActor.GetProperty().SetInterpolationToFlat()
    
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetSize(640, 480)
    
    # Create a camera for all renderers
    camera = vtk.vtkCamera()
    
    # Define viewport ranges
    # (xmin, ymin, xmax, ymax)
    leftViewport = (0.0, 0.0, 0.5, 1.0)
    rightViewport = (0.5, 0.0, 1.0, 1.0)
    
    # Setup both renderers
    leftRenderer = vtk.vtkRenderer()
    leftRenderer.SetViewport(leftViewport)
    leftRenderer.SetBackground(.6, .5, .4)
    leftRenderer.SetActiveCamera(camera)
    
    rightRenderer = vtk.vtkRenderer()
    rightRenderer.SetViewport(rightViewport)
    rightRenderer.SetBackground(.4, .5, .6)
    rightRenderer.SetActiveCamera(camera)
    
    leftRenderer.AddActor(originalActor)
    rightRenderer.AddActor(warpedActor)
    
    rightRenderer.ResetCamera()
    
    renderWindow.AddRenderer(rightRenderer)
    renderWindow.AddRenderer(leftRenderer)
    
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(renderWindow)
    
    renderWindow.Render()
    interactor.Start()

if __name__ == '__main__':
    main(sys.argv)
