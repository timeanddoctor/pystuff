import math
import vtk


def main():
  filename, startLabel, endLabel = get_program_parameters()

  # Create all of the classes we will need
  reader = vtk.vtkMetaImageReader()
  histogram = vtk.vtkImageAccumulate()
  discreteCubes = vtk.vtkDiscreteMarchingCubes()
  smoother = vtk.vtkWindowedSincPolyDataFilter()
  selector = vtk.vtkThreshold()
  scalarsOff = vtk.vtkMaskFields()
  geometry = vtk.vtkGeometryFilter()
  writer = vtk.vtkXMLPolyDataWriter()

  # Define all of the variables

  filePrefix = "Label"
  smoothingIterations = 15
  passBand = 0.001
  featureAngle = 120.0

  # Generate models from labels
  # 1) Read the meta file
  # 2) Generate a histogram of the labels
  # 3) Generate models from the labeled volume
  # 4) Smooth the models
  # 5) Output each model into a separate file

  reader.SetFileName(filename)

  histogram.SetInputConnection(reader.GetOutputPort())
  histogram.SetComponentExtent(0, endLabel, 0, 0, 0, 0)
  histogram.SetComponentOrigin(0, 0, 0)
  histogram.SetComponentSpacing(1, 1, 1)
  histogram.Update()

  discreteCubes.SetInputConnection(reader.GetOutputPort())
  discreteCubes.GenerateValues(endLabel - startLabel + 1, startLabel, endLabel)

  smoother.SetInputConnection(discreteCubes.GetOutputPort())
  smoother.SetNumberOfIterations(smoothingIterations)
  smoother.BoundarySmoothingOff()
  smoother.FeatureEdgeSmoothingOff()
  smoother.SetFeatureAngle(featureAngle)
  smoother.SetPassBand(passBand)
  smoother.NonManifoldSmoothingOn()
  smoother.NormalizeCoordinatesOn()
  smoother.Update()

  selector.SetInputConnection(smoother.GetOutputPort())
  selector.SetInputArrayToProcess(0, 0, 0,
                                  vtk.vtkDataObject.FIELD_ASSOCIATION_CELLS,
                                  vtk.vtkDataSetAttributes.SCALARS)

  # Strip the scalars from the output
  scalarsOff.SetInputConnection(selector.GetOutputPort())
  scalarsOff.CopyAttributeOff(vtk.vtkMaskFields.POINT_DATA,
                              vtk.vtkDataSetAttributes.SCALARS)
  scalarsOff.CopyAttributeOff(vtk.vtkMaskFields.CELL_DATA,
                              vtk.vtkDataSetAttributes.SCALARS)

  geometry.SetInputConnection(scalarsOff.GetOutputPort())

  writer.SetInputConnection(geometry.GetOutputPort())

  for i in range(startLabel, endLabel):
    # see if the label exists, if not skip it
    frequency = histogram.GetOutput().GetPointData().GetScalars().GetTuple1(i)
    if frequency == 0.0:
      continue

    # select the cells for a given label
    selector.ThresholdBetween(i, i)

    # output the polydata
    ss = "%s%d.vtp" % (filePrefix, i)
    writer.SetFileName(ss)
    writer.Write()

def get_program_parameters():
  import argparse
  description = 'GenerateModelsFromLabels.'
  epilogue = '''
  '''
  parser = argparse.ArgumentParser(description=description, epilog=epilogue,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('filename', help='labels.mhd')
  parser.add_argument('startLabel', nargs='?', default=0, type=int)
  parser.add_argument('endLabel', nargs='?', default=1, type=int)
  args = parser.parse_args()
  return args.filename, args.startLabel, args.endLabel

if __name__ == '__main__':
  main()
