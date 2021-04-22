#!/usr/bin/env python

# This example shows how to load a 3D image into VTK and then reformat
# that image into a different orientation for viewing.  It uses
# vtkImageReslice for reformatting the image, and uses vtkImageActor
# and vtkInteractorStyleImage to display the image.  This InteractorStyle
# forces the camera to stay perpendicular to the XY plane.

import vtk

# Start by loading some data.
fileName = "c:/github/fis/data/Abdomen/CT-Abdomen.mhd"
reader = vtk.vtkMetaImageReader()
reader.SetFileName(fileName)
reader.UpdateWholeExtent()
reader.Update()

# Calculate the center of the volume
reader.Update()
(xMin, xMax, yMin, yMax, zMin, zMax) = reader.GetExecutive().GetWholeExtent(reader.GetOutputInformation(0))
(xSpacing, ySpacing, zSpacing) = reader.GetOutput().GetSpacing()
(x0, y0, z0) = reader.GetOutput().GetOrigin()

center = [x0 + xSpacing * 0.5 * (xMin + xMax),
          y0 + ySpacing * 0.5 * (yMin + yMax),
          z0 + zSpacing * 0.5 * (zMin + zMax)]

# Matrices for axial, coronal, sagittal, oblique view orientations
axial = vtk.vtkMatrix4x4()
axial.DeepCopy((1, 0, 0, center[0],
                0, 1, 0, center[1],
                0, 0, 1, center[2],
                0, 0, 0, 1))

coronal = vtk.vtkMatrix4x4()
coronal.DeepCopy((1, 0, 0, center[0],
                  0, 0, 1, center[1],
                  0,-1, 0, center[2],
                  0, 0, 0, 1))

sagittal = vtk.vtkMatrix4x4()
sagittal.DeepCopy((0, 0,-1, center[0],
                   1, 0, 0, center[1],
                   0,-1, 0, center[2],
                   0, 0, 0, 1))

oblique = vtk.vtkMatrix4x4()
oblique.DeepCopy((1, 0, 0, center[0],
                  0, 0.866025, -0.5, center[1],
                  0, 0.5, 0.866025, center[2],
                  0, 0, 0, 1))

# Extract a slice in the desired orientation
reslice = vtk.vtkImageReslice()
reslice.SetInputConnection(reader.GetOutputPort())
reslice.SetOutputDimensionality(2)
reslice.SetResliceAxes(axial)#sagittal)
reslice.SetInterpolationModeToLinear()
reslice.GenerateStencilOutputOn()
reslice.Update()

# Create a greyscale lookup table
table = vtk.vtkLookupTable()

#rng = reader.GetOutput().GetScalarRange()
rng = reslice.GetOutput().GetScalarRange()


table.SetRange(rng[0], rng[1]) # image intensity range
table.SetValueRange(0.0, 1.0) # from black to white
table.SetSaturationRange(0.0, 0.0) # no color saturation
table.SetRampToLinear()
table.Build()

if 0:
  # Map the image through the lookup table
  color = vtk.vtkImageMapToColors()
  color.SetLookupTable(table)
  color.SetInputConnection(reslice.GetOutputPort())
else:
  # Could we use vtk.vtkImageResliceToColors
  toColors = vtk.vtkImageResliceToColors()
  toColors.SetLookupTable(table)
  toColors.SetInputConnection(reslice.GetOutputPort())

  # Try a sphere
  bounds = reader.GetOutput().GetBounds()
  origin = [0,0,0]
  origin[0] = (bounds[1] + bounds[0]) / 2.0
  origin[1] = (bounds[2] + bounds[3]) / 2.0
  origin[2] = (bounds[4] + bounds[5]) / 2.0
  sphere = vtk.vtkSphereSource()
  sphere.SetPhiResolution(24)
  sphere.SetThetaResolution(24)
  sphere.SetCenter(origin)
  sphere.SetRadius(150)
  triangle = vtk.vtkTriangleFilter()
  triangle.SetInputConnection(sphere.GetOutputPort())
  stripper = vtk.vtkStripper()
  stripper.SetInputConnection(triangle.GetOutputPort())
  dataToStencil = vtk.vtkPolyDataToImageStencil()
  dataToStencil.SetInputConnection(stripper.GetOutputPort())
  dataToStencil.SetOutputSpacing(reader.GetOutput().GetSpacing())
  dataToStencil.SetOutputOrigin(reader.GetOutput().GetOrigin())
  stencil = vtk.vtkImageStencil()
  stencil.SetInputConnection(reslice.GetOutputPort())
  stencil.SetStencilConnection(dataToStencil.GetOutputPort())
  stencil.ReverseStencilOff()
  stencil.SetBackgroundValue(0)
  stencil.Update()
  
  #toColors.SetStencilData(reslice.GetStencilOutput())
  # Test using other stencil
  toColors.SetStencilData(stencil.GetStencil())
  

# Display the image
actor = vtk.vtkImageActor()
#actor.GetMapper().SetInputConnection(toColors.GetOutputPort())
actor.GetMapper().SetInputConnection(stencil.GetOutputPort())

renderer = vtk.vtkRenderer()
renderer.AddActor(actor)

window = vtk.vtkRenderWindow()
window.AddRenderer(renderer)

# Set up the interaction
interactorStyle = vtk.vtkInteractorStyleImage()
interactor = vtk.vtkRenderWindowInteractor()
interactor.SetInteractorStyle(interactorStyle)
window.SetInteractor(interactor)
window.Render()

# Create callbacks for slicing the image
actions = {}
actions["Slicing"] = 0

def ButtonCallback(obj, event):
    if event == "LeftButtonPressEvent":
        actions["Slicing"] = 1
    else:
        actions["Slicing"] = 0

def MouseMoveCallback(obj, event):
    global toggle
    (lastX, lastY) = interactor.GetLastEventPosition()
    (mouseX, mouseY) = interactor.GetEventPosition()
    if actions["Slicing"] == 1:
        deltaY = mouseY - lastY

        reslice.Update()
        sliceSpacing = reslice.GetOutput().GetSpacing()[2]
        matrix = reslice.GetResliceAxes()
        # move the center point that we are slicing through
        center = matrix.MultiplyPoint((0, 0, sliceSpacing*deltaY, 1))
        matrix.SetElement(0, 3, center[0])
        matrix.SetElement(1, 3, center[1])
        matrix.SetElement(2, 3, center[2])

        scenter = sphere.GetCenter()
        newCenter = (scenter[0], scenter[1], scenter[2]+sliceSpacing*deltaY)
        sphere.SetCenter(newCenter)
        
        window.Render()
    else:
        interactorStyle.OnMouseMove()


interactorStyle.AddObserver("MouseMoveEvent", MouseMoveCallback)
interactorStyle.AddObserver("LeftButtonPressEvent", ButtonCallback)
interactorStyle.AddObserver("LeftButtonReleaseEvent", ButtonCallback)

# Start interaction
interactor.Start()
