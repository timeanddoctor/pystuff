void iterate(const QModelIndex & index, const QAbstractItemModel * model,
             const std::function<void(const QModelIndex&, int)> & fun,
             int depth = 0) {
  if (index.isValid())
    fun(index, depth);
  if (!model->hasChildren(index) || (index.flags() & Qt::ItemNeverHasChildren)) return;
  auto rows = model->rowCount(index);
  auto cols = model->columnCount(index);
  for (int i = 0; i < rows; ++i)
    for (int j = 0; j < cols; ++j)
      iterate(model->index(i, j, index), model, fun, depth+1);
}

void dumpData(QAbstractItemView * view) {
  iterate(view->rootIndex(), view->model(), [](const QModelIndex & idx, int depth){
      qDebug() << depth << ":" << idx.row() << "," << idx.column() << "=" << idx.data();
    });
}
