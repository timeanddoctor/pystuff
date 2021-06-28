#!/usr/bin/env python
import vtk

# Inherits PolyDataToImageStencil

# A script to test the vtkLassoStencilSource
reader = vtk.vtkMetaImageReader()
reader.SetFileName("./testImage.mhd")
reader.Update()
img = reader.GetOutput()

reader1 = vtk.vtkXMLPolyDataReader()
reader1.SetFileName("./testPoints.vtp")
reader1.Update()
points = reader1.GetOutput().GetPoints()

roiStencil1 = vtk.vtkLassoStencilSource()
roiStencil1.SetShapeToPolygon()
roiStencil1.SetSlicePoints(0,points)
roiStencil1.SetInformationInput(reader.GetOutput()) # Spacing, Origin, and WholeExtent

print(reader.GetOutput().GetSpacing())
print(reader.GetOutput().GetOrigin())
#print(reader.GetOutput().GetWholeExtent())

stencil1 = vtk.vtkImageStencil()
stencil1.SetInputConnection(reader.GetOutputPort())
stencil1.SetBackgroundValue(0)
stencil1.SetStencilConnection(roiStencil1.GetOutputPort())

table = vtk.vtkLookupTable()
table.SetRange(0, 100) # image intensity range
table.SetValueRange(0.0, 1.0) # from black to white
table.SetSaturationRange(0.0, 0.0) # no color saturation
table.SetRampToLinear()
table.Build()

# Map the image through the lookup table
color = vtk.vtkImageMapToColors()
color.SetLookupTable(table)
color.SetInputConnection(stencil1.GetOutputPort())

actor1 = vtk.vtkImageActor()
actor1.GetMapper().SetInputConnection(color.GetOutputPort())
imager1 = vtk.vtkRenderer()
imager1.AddActor(actor1)

imgWin = vtk.vtkRenderWindow()
imgWin.AddRenderer(imager1)

iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(imgWin)
imgWin.SetSize(512,512)

iren.Initialize()
imgWin.Render()
iren.Start()

# --- end of script --
