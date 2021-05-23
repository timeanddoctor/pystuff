import vtk

tf = vtk.vtkTransform()
tf.Translate(1.0, 0.0, 0.0)
tf0 = vtk.vtkTransform()
tf.Concatenate(tf0)

tf.Push()
tf.Identity()
print(tf)
tf.Pop()
print(tf)
