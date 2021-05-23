vtkSmartPointer<vtkContourWidget> ContourWidget[157];

class vtkSliderCallback2 : public vtkCommand {
 public:
  static vtkSliderCallback2 *New() {
    return new vtkSliderCallback2;
  }
  void SetImageViewer(vtkImageViewer2 *viewer) {
    this->Viewer =  viewer;
  }
  virtual void Execute(vtkObject *caller, unsigned long , void* ) {
    vtkSliderWidget *slider = static_cast<vtkSliderWidget *>(caller);
    vtkSliderRepresentation *sliderRepres = static_cast<vtkSliderRepresentation *>(slider->GetRepresentation());
    int pos = static_cast<int>(sliderRepres->GetValue());


    for (int j = 0; j < 157; j++) {
      if (pos == j) {
        ContourWidget[j]->SetEnabled(true);
      } else {
        ContourWidget[j]->SetEnabled(false);
      }
    }
    this->Viewer->SetSlice(pos);
  }
protected:
  vtkImageViewer2 *Viewer;
};

void ConvertPointSequenceToPolyData(vtkPoints *inPts,
                                    const int & closed,
                                    vtkPolyData *outPoly) {
  if ( !inPts || !outPoly ) {
    return;
  }

  int npts = inPts->GetNumberOfPoints();

  if ( npts < 2 ) {
    return;
  }

  double p0[3];
  double p1[3];
  inPts->GetPoint( 0, p0 );
  inPts->GetPoint( npts - 1, p1 );
  if ( p0[0] == p1[0] && p0[1] == p1[1] && p0[2] == p1[2] && closed ) {
    --npts;
  }

  vtkPoints *temp = vtkPoints::New();
  temp->SetNumberOfPoints( npts );
  for ( int i = 0; i < npts; ++i ) {
    temp->SetPoint( i, inPts->GetPoint( i ) );
  }

  vtkCellArray *cells = vtkCellArray::New();
  cells->Allocate( cells->EstimateSize( npts + closed, 2 ) );
  cells->InsertNextCell( npts + closed );

  for ( int i = 0; i < npts; ++i ) {
    cells->InsertCellPoint( i );
  }

  if ( closed ) {
    cells->InsertCellPoint( 0 );
  }

  outPoly->SetPoints( temp );
  temp->Delete();
  outPoly->SetLines( cells );
  cells->Delete();
}

// --------------------------------------------------------------------------
// assumes a piecwise linear polyline with points at discrete locations
//
int ReducePolyData2D(vtkPolyData *inPoly,
                     vtkPolyData *outPoly, const int & closed ) {
  if ( !inPoly || !outPoly ) {
    return 0;
  }

  vtkPoints *inPts = inPoly->GetPoints();
  if ( !inPts ) {
    return 0;
  }
  int n = inPts->GetNumberOfPoints();
  if ( n < 3 ) {
    return 0;
  }

  double p0[3];
  inPts->GetPoint( 0, p0 );
  double p1[3];
  inPts->GetPoint( n - 1, p1 );
  bool minusNth = ( p0[0] == p1[0] && p0[1] == p1[1] && p0[2] == p1[2] );
  if ( minusNth && closed ) {
    --n;
  }

  struct frenet {
    double t[3];  // unit tangent vector
    bool state;   // state of kappa: zero or non-zero  T/F
  };

  frenet *f;
  f = new frenet[n];
  double tL;

  // calculate the tangent vector by forward differences
  for ( int i = 0; i < n; ++i ) {
    inPts->GetPoint( i, p0 );
    inPts->GetPoint( ( i + 1 ) % n, p1 );
    tL = sqrt( vtkMath::Distance2BetweenPoints( p0, p1 ) );
    if ( tL == 0.0 ) { tL = 1.0; }
    for ( int j = 0; j < 3; ++j ) {
      f[i].t[j] = ( p1[j] - p0[j] ) / tL;
    }
  }

  // calculate kappa from tangent vectors by forward differences
  // mark those points that have very low curvature
  double eps = 1.e-10;

  for ( int i = 0; i < n; ++i ) {
    f[i].state = ( fabs( vtkMath::Dot( f[i].t, f[( i + 1 ) % n].t ) - 1.0 )
                   < eps );
  }

  vtkPoints *tempPts = vtkPoints::New();

  // mark keepers
  vtkIdTypeArray *ids = vtkIdTypeArray::New();

  // for now, insist on keeping the first point for closure
  ids->InsertNextValue( 0 );

  for ( int i = 1; i < n; ++i ) {
    bool pre = f[( i - 1 + n ) % n].state; // means fik != 1
    bool cur = f[i].state;                 // means fik = 1
    bool nex = f[( i + 1 ) % n].state;

    // possible vertex bend patterns for keep: pre cur nex
    // 0 0 1
    // 0 1 1
    // 0 0 0
    // 0 1 0

    // definite delete pattern
    // 1 1 1

    bool keep = false;

    if (  pre &&  cur &&  nex ) {
      keep = false;
    } else if ( !pre && !cur &&  nex ) {
      keep = true;
    } else if ( !pre &&  cur &&  nex ) {
      keep = true;
    } else if ( !pre && !cur && !nex ) {
      keep = true;
    } else if ( !pre &&  cur && !nex ) {
      keep = true;
    }

    if ( keep  ) {
      ids->InsertNextValue( i );
    }
  }

  for ( int i = 0; i < ids->GetNumberOfTuples(); ++i ) {
    tempPts->InsertNextPoint( inPts->GetPoint( ids->GetValue( i ) ) );
  }

  if ( closed ) {
    tempPts->InsertNextPoint( inPts->GetPoint( ids->GetValue( 0 ) ) );
  }

  ConvertPointSequenceToPolyData( tempPts, closed, outPoly );

  ids->Delete();
  tempPts->Delete();
  delete[] f;
  return 1;
}

namespace {
double PointsArea(vtkPoints *points)
{
  int       numPoints = points->GetNumberOfPoints();
  vtkIdType *ids = new vtkIdType[numPoints + 1];
  int       i;

  for ( i = 0; i < numPoints; i++ )
    {
    ids[i] = i;
    }
  ids[i] = 0;
  double normal[3];
  double rval( vtkPolygon::ComputeArea(points, numPoints, ids, normal) );
  delete[] ids;
  return rval;
}

double PolyDataArea(vtkPolyData *pd) {
  assert(pd->GetNumberOfLines() == 1);
  vtkIdType npts(0);
  vtkIdType *pts(0);
  double    normal[3];
  pd->GetLines()->InitTraversal();
  pd->GetLines()->GetNextCell(npts, pts);
  return vtkPolygon::ComputeArea(pd->GetPoints(),
                                 npts,
                                 pts,
                                 normal);
}

inline
void IdsMinusThisPoint(vtkIdType *ids, int PointCount, int i) {
  int k = 0;

  for ( int j = 0; j < PointCount; j++ ) {
    if ( j != i ) {
      ids[k] = j;
      k++;
    }
  }
  // leaving off first point? 1 is index of first point
  // in the reduced polygon;
  ids[k] = i == 0 ? 1 : 0;
}

void Cull(vtkPolyData *in, vtkPolyData *out) {
  //
  // Algorithm:
  // Error = 0
  // Create BTPolygon from points in input. Compute Original Area.
  //
  // while Error < MaxError
  //
  //    foreach vertex in input
  //      Create Polygon from input, minus this vertex
  //      Compute area.
  //      subtract area from original area.
  //    endfor
  //    find minimum error vertex, remove it.
  //    error = minimum error
  //

  //

  // do an initial point count reduction based on
  // curvature through vertices of the polygons.
  vtkPolyData *in2 = vtkPolyData::New();

  ReducePolyData2D(in, in2, 1);

  double originalArea( PolyDataArea(in2) );

  //
  // SWAG numbers -- accept
  // area change of 0.5%,
  // regard 0.005% as the same as zero
  double maxError = originalArea * 0.005;
  double errEpsilon = maxError * 0.001;

  vtkPoints *curPoints = vtkPoints::New();
  curPoints->DeepCopy( in2->GetPoints() );
  int       PointCount = curPoints->GetNumberOfPoints();
  vtkIdType *ids = new vtkIdType[PointCount];
  vtkIdType minErrorPointID = -1;

  for (;; ) {
    double minError = 10000000.00;
    //
    // remove each point, one at a time and find the minimum error
    for ( int i = 0; i < PointCount; i++ ) {
      // build id list, minus the current point;
      IdsMinusThisPoint(ids, PointCount, i);
      double normal[3];
      double curArea = vtkPolygon::ComputeArea(curPoints,
                                               PointCount - 1,
                                               ids,
                                               normal);
      double thisError = fabs(originalArea - curArea);
      if ( thisError < minError ) {
        minError = thisError;
        minErrorPointID = i;
        // if the area error is absurdly low, just get rid of
        // this point and move on.
        if ( thisError < errEpsilon ) {
          break;
        }
      }
    }
    //
    // if we have a new winner for least important point
    if ( minError <= maxError ) {
      vtkPoints *newPoints = vtkPoints::New();

      for ( int i = 0; i < PointCount; i++ ) {
        if ( i == minErrorPointID ) {
          continue;
        }
        double point[3];
        curPoints->GetPoint(i, point);
        newPoints->InsertNextPoint(point);
      }
      curPoints->Delete();
      curPoints = newPoints;
      --PointCount;
    }
    else {
      break;
    }
  }
  ConvertPointSequenceToPolyData(curPoints, 1, out);
  curPoints->Delete();
  in2->Delete();
  delete[] ids;
}
}  // namespace

int main (int argc, char *argv[])
{
  typedef    float    InputPixelType;
  typedef    float    OutputPixelType;
  typedef itk::Image< InputPixelType,  3 >   InputImageType;
  typedef itk::Image< OutputPixelType, 3 >   OutputImageType;
  typedef itk::Image< InputPixelType,       2 >   SliceImageType;

  typedef itk::ExtractImageFilter<InputImageType, SliceImageType> ExtractFilterType;

  // Load DICOM files
  typedef itk::ImageSeriesReader< InputImageType >     ReaderType;
  ReaderType::Pointer reader1 = ReaderType::New();
  ReaderType::Pointer reader2 = ReaderType::New();

  typedef itk::GDCMImageIO                        ImageIOType;
  typedef itk::GDCMSeriesFileNames                NamesGeneratorType;

  ImageIOType::Pointer gdcmIO = ImageIOType::New();
  //load original CT
  NamesGeneratorType::Pointer namesGenerator1 = NamesGeneratorType::New();
  namesGenerator1->SetInputDirectory( "C:/Users/User/Desktop/CT data/SHS/Diffusion_filter" );
  const ReaderType::FileNamesContainer & filenames1 =
                            namesGenerator1->GetInputFileNames();
  reader1->SetImageIO( gdcmIO );
  reader1->SetFileNames( filenames1 );
  reader1->Update();

  typedef itk::ImageToVTKImageFilter<InputImageType>FilterType;
  FilterType::Pointer connector1 = FilterType::New();

  connector1->SetInput(reader1->GetOutput());

  vtkSmartPointer<vtkLookupTable> table1 = vtkSmartPointer<vtkLookupTable>::New();
  table1->SetRange(0, 255); // image intensity range
  table1->SetValueRange(0.0, 1.0); // from black to white
  table1->SetSaturationRange(0.0, 0.0); // no color saturation
  table1->SetRampToLinear();
  table1->Build();

  vtkSmartPointer<vtkImageMapToColors> color1 = vtkSmartPointer<vtkImageMapToColors>::New();
  color1->SetLookupTable(table1);
  color1->SetInput(connector1->GetOutput());
  color1->Update();

  //load segmented CT
  NamesGeneratorType::Pointer namesGenerator2 = NamesGeneratorType::New();
  namesGenerator2->SetInputDirectory( "C:/Users/User/Desktop/CT data/SHS/Threshold_LS/Hole filled" );
  const ReaderType::FileNamesContainer & filenames2 =
                            namesGenerator2->GetInputFileNames();
  reader2->SetImageIO( gdcmIO );
  reader2->SetFileNames( filenames2 );
  reader2->Update();

  FilterType::Pointer connector2 = FilterType::New();

  connector2->SetInput(reader2->GetOutput());

  InputImageType::Pointer inputImage = reader2->GetOutput();
  InputImageType::PointType origin = inputImage->GetOrigin();
  InputImageType::SpacingType spacing = inputImage->GetSpacing();
  InputImageType::SizeType  size = inputImage->GetLargestPossibleRegion().GetSize();

  InputImageType::RegionType extractRegion;

  InputImageType::SizeType extractSize(size);
  extractSize[2] = 0;

  InputImageType::IndexType       extractIndex;
  ExtractFilterType::Pointer extractFilter = ExtractFilterType::New();
  extractFilter->SetInput(inputImage);
  double minArea = ( spacing[0] * spacing[1] ) / 0.1;

  vtkImageViewer2 *imageViewer1 = vtkImageViewer2::New();
  imageViewer1->SetInput(color1->GetOutput());
  imageViewer1->SetColorLevel(127);
  imageViewer1->SetColorWindow(255);

  vtkRenderWindowInteractor *iren = vtkRenderWindowInteractor::New();

  imageViewer1->SetupInteractor(iren);
  imageViewer1->GetRenderWindow()->SetMultiSamples(0);
  imageViewer1->GetRenderWindow()->SetSize(600, 600);

  vtkSliderRepresentation2D *SliderRepres1 = vtkSliderRepresentation2D::New();
  int min = imageViewer1->GetSliceMin();
  int max = imageViewer1->GetSliceMax();
  SliderRepres1->SetMinimumValue(min);
  SliderRepres1->SetMaximumValue(max);
  SliderRepres1->SetValue(71);//static_cast<int>((min + max) / 2)
  //SliderRepres->SetTitleText("Slice");
  SliderRepres1->GetPoint1Coordinate()->SetCoordinateSystemToNormalizedDisplay();
  SliderRepres1->GetPoint1Coordinate()->SetValue(0.3, 0.05);
  SliderRepres1->GetPoint2Coordinate()->SetCoordinateSystemToNormalizedDisplay();
  SliderRepres1->GetPoint2Coordinate()->SetValue(0.7, 0.05);
  SliderRepres1->SetSliderLength(0.02);
  SliderRepres1->SetSliderWidth(0.03);
  SliderRepres1->SetEndCapLength(0.01);
  SliderRepres1->SetEndCapWidth(0.03);
  SliderRepres1->SetTubeWidth(0.005);
  SliderRepres1->SetLabelFormat("%3.0lf");
  SliderRepres1->SetTitleHeight(0.02);
  SliderRepres1->SetLabelHeight(0.02);

  vtkSliderWidget *SliderWidget1 = vtkSliderWidget::New();
  SliderWidget1->SetInteractor(iren);
  SliderWidget1->SetRepresentation(SliderRepres1);
  SliderWidget1->KeyPressActivationOff();
  SliderWidget1->SetAnimationModeToAnimate();
  SliderWidget1->SetEnabled(true);

  vtkSliderCallback2 *SliderCb1 = vtkSliderCallback2::New();
  SliderCb1->SetImageViewer(imageViewer1);
  SliderWidget1->AddObserver(vtkCommand::InteractionEvent, SliderCb1);

  imageViewer1->SetSlice(static_cast<int>(SliderRepres1->GetValue()));
  imageViewer1->SetSliceOrientationToXY();

  vtkSmartPointer<vtkOrientedGlyphContourRepresentation> rep[157];

  for ( unsigned i = 0; i < 157; i++ ) {
    vtkExtractVOI * extract = vtkExtractVOI::New();
    extract->SetInput(connector2->GetOutput());
    extract->SetVOI(0,512,0,512,i,i);

    vtkContourFilter * contour = vtkContourFilter::New();
    contour->SetInput( extract->GetOutput() );
    contour->SetValue(0, 0.5);

    vtkStripper *stripper = vtkStripper::New();
    stripper->SetInput(contour->GetOutput());
    stripper->Update();

    vtkPolyData * pd = vtkPolyData::New();
    pd = stripper->GetOutput();

    vtkPolyData *pd3 = vtkPolyData::New();
    if ( pd->GetPoints()->GetNumberOfPoints() > 0 ) {
      vtkPoints *pts = pd->GetPoints();
      double    zPos = static_cast<double>( origin[2] )
          + ( static_cast<double>( i ) * spacing[2] );
      // std::cout << "Z Position " << zPos << std::endl;
      for ( int j = 0; j < pd->GetNumberOfPoints(); j++ ) {
        double point[3];
        pts->GetPoint(j, point);
        point[2] = zPos;
        pts->SetPoint(j, point);
      }

      vtkCellArray *lines = pd->GetLines();
      vtkIdType    numPoints;
      vtkIdType    *points;

      while ( lines->GetNextCell(numPoints, points) != 0 ) {
        vtkPoints *tmpPoints = vtkPoints::New();
        for ( int j = 0; j < numPoints; j++ ) {
          double point[3];
          pts->GetPoint(points[j], point);
          tmpPoints->InsertNextPoint(point);
        }
        if ( PointsArea(tmpPoints) < minArea ) {
          tmpPoints->Delete();
          continue;
        }
        vtkPolyData *pd2 = vtkPolyData::New();
        ConvertPointSequenceToPolyData(tmpPoints, 1, pd2);
        Cull(pd2, pd3);
      }
    }

    ContourWidget[i] = vtkSmartPointer<vtkContourWidget>::New();
    rep[i] = vtkSmartPointer<vtkOrientedGlyphContourRepresentation>::New();

    ContourWidget[i]->SetInteractor(iren);
    ContourWidget[i]->SetRepresentation(rep[i]);

    rep[i]->GetProperty()->SetColor(1,0,1);
    rep[i]->GetProperty()->SetPointSize(5);
    rep[i]->GetLinesProperty()->SetColor(0,1,1);
    rep[i]->GetLinesProperty()->SetLineWidth(3);

    ContourWidget[i]->On();
    ContourWidget[i]->Initialize(pd3);
    ContourWidget[i]->SetEnabled(false);
  }

  imageViewer1->Render();
  imageViewer1->GetRenderer()->ResetCamera();

  iren->Initialize();
  iren->Start();

  return 0;
}
