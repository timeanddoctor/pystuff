import math
import vtk

# Question: Can we use vtkSmoothPolyDataFilter or vtkWindowedSincPolyDataFilter

def main():
  inputFileName, isoValue = get_program_parameters()

  reader = vtk.vtkPNGReader()
  if not reader.CanReadFile(inputFileName):
    print("Error: Could not read %s ." % (inputFileName))
  reader.SetFileName(inputFileName)
  reader.Update()

  iso = vtk.vtkMarchingSquares()
  iso.SetInputConnection(reader.GetOutputPort())
  iso.SetValue(0, isoValue)

  # Test smoothing here
  if 1:
    # Remove duplicate points and join up lines to form polylines
    pCleaner = vtk.vtkCleanPolyData()
    pCleaner.SetInputConnection(iso.GetOutputPort())
    pStripper = vtk.vtkStripper()
    pStripper.SetInputConnection(pCleaner.GetOutputPort())

    # Downsample and smooth the polyline
    pSpline= vtk.vtkSplineFilter()
    mSplineResamplingLength = 50.0
    mReferenceLength = 40.0
    pSpline.SetLength(mSplineResamplingLength / mReferenceLength)
    pSpline.SetSubdivideToLength()
    pSpline.SetInputConnection(pStripper.GetOutputPort())

    pTriangle = vtk.vtkTriangleFilter()
    pTriangle.SetInputConnection(pSpline.GetOutputPort())
    pTriangle.Update()
    pCleaned = pTriangle.GetOutput()
    newMapper = vtk.vtkDataSetMapper()
    newMapper.SetInputConnection(pTriangle.GetOutputPort())
    newActor = vtk.vtkActor()
    newActor.SetMapper(newMapper)

  isoMapper = vtk.vtkDataSetMapper()
  isoMapper.SetInputConnection(iso.GetOutputPort())
  isoMapper.ScalarVisibilityOff()

  isoActor = vtk.vtkActor()
  isoActor.SetMapper(isoMapper)
  isoActor.GetProperty().SetColor(0.8900, 0.8100, 0.3400)

  poly = vtk.vtkContourTriangulator()
  poly.SetInputConnection(iso.GetOutputPort())

  polyMapper = vtk.vtkDataSetMapper()
  polyMapper.SetInputConnection(poly.GetOutputPort())
  polyMapper.ScalarVisibilityOff()

  polyActor = vtk.vtkActor()
  polyActor.SetMapper(polyMapper)
  polyActor.GetProperty().SetColor(1.0000, 0.3882, 0.2784)

  # Standard rendering classes
  renderer = vtk.vtkRenderer()
  renWin = vtk.vtkRenderWindow()
  renWin.SetMultiSamples(0)
  renWin.AddRenderer(renderer)
  iren = vtk.vtkRenderWindowInteractor()
  iren.SetRenderWindow(renWin)

  renderer.AddActor(polyActor) # Important
  renderer.AddActor(isoActor)
  renderer.AddActor(newActor)

  # Standard testing code.
  renderer.SetBackground(0.5,0.5,0.5)
  renWin.SetSize(800,800)

  camera = renderer.GetActiveCamera()
  renderer.ResetCamera()
  camera.Azimuth(180)

  renWin.Render()
  iren.Initialize()
  iren.Start()

def get_program_parameters():
  import argparse
  description = 'ContourTriangulator.'
  epilogue = '''
  '''
  parser = argparse.ArgumentParser(description=description, epilog=epilogue,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('filename', help='ContourTriangulator fullhead.png isoValue')
  parser.add_argument('isoValue', nargs='?', default=0, type=int)
  args = parser.parse_args()
  return args.filename, args.isoValue

if __name__ == '__main__':
  main()
