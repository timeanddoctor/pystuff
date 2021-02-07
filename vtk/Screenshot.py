import vtk


sphereSource = vtk.vtkSphereSource()
sphereSource.SetCenter(0.0, 0.0, 0.0)
sphereSource.SetRadius(5.0)
sphereSource.Update()

# Visualize
mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(sphereSource.GetOutputPort())

actor = vtk.vtkActor()
actor.SetMapper(mapper)

renderer = vtk.vtkRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer)
renderWindow.SetAlphaBitPlanes(1) #enable usage of alpha channel

renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

renderer.AddActor(actor)
renderer.SetBackground(1,1,1) # Background color white

renderWindow.Render()

# Screenshot  
windowToImageFilter = vtk.vtkWindowToImageFilter()
windowToImageFilter.SetInput(renderWindow)
if vtk.VTK_VERSION >= '8.0.0' or vtk.VTK_VERSION >= '8.9.0':
  windowToImageFilter.SetScale(2) # image quality
else:
  windowToImageFilter.SetMagnification(2) #set the resolution of the output image (3 times the current resolution of vtk render window)

windowToImageFilter.SetInputBufferTypeToRGBA() #also record the alpha (transparency) channel
windowToImageFilter.ReadFrontBufferOff() # read from the back buffer
windowToImageFilter.Update()
  
writer = vtk.vtkPNGWriter()
writer.SetFileName("screenshot2.png")
writer.SetInputConnection(windowToImageFilter.GetOutputPort())
writer.Write()
  
renderWindow.Render()  
renderer.ResetCamera()
renderWindow.Render()
renderWindowInteractor.Start()

