# Resample using ITK
import sys
import itk

PixelType = itk.ctype("unsigned char")
Dimension = 2
ImageType = itk.Image[PixelType, Dimension]

outputSize = [100, 100]

ReaderType = itk.ImageFileReader[ImageType]
# image = itk.imread('./Gourds18.png', PixelType)
reader = ReaderType.New()
reader.SetFileName('./Gourds18.png')
reader.UpdateOutputInformation()

inputImage = reader.GetOutput()
inputSize = inputImage.GetLargestPossibleRegion().GetSize()
print("Input Size: %s" + str(inputSize))

inputSpacing = inputImage.GetSpacing()
outputSpacing = Dimension * [0]
for i in range(Dimension):
  outputSpacing[i] = float(inputSpacing[i]) * float(inputSize[i]) / float(outputSize[i])

print("Output Size: %s" % str(outputSize))
print("Output Spacing: %s" % str(outputSpacing))
TransformPrecisionType = itk.ctype("double")
TransformType = itk.IdentityTransform[TransformPrecisionType, Dimension]
FilterType = itk.ResampleImageFilter[ImageType, ImageType]
_filter = FilterType.New()
_filter.SetInput(inputImage)
_filter.SetSize(outputSize)
_filter.SetOutputSpacing(outputSpacing)
_filter.SetOutputOrigin(inputImage.GetOrigin())
_filter.SetTransform(TransformType.New())
writerType = itk.ImageFileWriter[ImageType]
writer = writerType.New()
writer.SetFileName('hej.png')
writer.SetInput(_filter.GetOutput())
try:
  writer.Update()
except:
  print("Error: ")
  sys.exit(-1)
