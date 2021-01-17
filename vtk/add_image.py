def add_image(self, image):
        img_mapper = vtk.vtkImageMapper()
        img_actor = vtk.vtkActor2D()
        img_data = vtk.vtkImageData()
        img_data.SetDimensions(image.shape[0], image.shape[1], 1)
        img_data.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 3)
        for x in range(0, image.shape[0]):
            for y in range(0, image.shape[1]):
                pixel = img_data.GetScalarPointer(x, y, 0)
                pixel = np.array(image[x, y, :])
        img_mapper.SetInputData(img_data)
        img_mapper.SetColorWindow(255)
        img_mapper.SetColorLevel(127.5)
        img_actor.SetMapper(img_mapper)
        self.renderer.AddActor(img_actor)
