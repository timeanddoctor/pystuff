from qt import *

from qtpy.QtCore import (Qt, QVariant, QAbstractItemModel, QModelIndex)
from qtpy import QtCore, QtGui
from qtpy.QtWidgets import QItemDelegate, QLineEdit

import numpy as np

class TreeItem(object):
  def __init__(self, data, parent=None):
    self.parentItem = parent
    self.itemData = data
    self.childItems = []

  def child(self, row):
    if row < 0 or row >= len(self.childItems):
      return None
    return self.childItems[row]

  def childCount(self):
    return len(self.childItems)

  def childNumber(self):
    if self.parentItem != None:
      return self.parentItem.childItems.index(self)
    return 0

  def columnCount(self):
    return len(self.itemData)

  def data(self, column):
    if column < 0 or column >= len(self.itemData):
      return None
    return self.itemData[column]

  def insertChildren(self, position, count, columns):
    if position < 0 or position > len(self.childItems):
      return False

    for row in range(count):
      data = [None for v in range(columns)]
      item = TreeItem(data, self)
      self.childItems.insert(position, item)

    return True

  def insertColumns(self, position, columns):
    if position < 0 or position > len(self.itemData):
      return False

    for column in range(columns):
      self.itemData.insert(position, None)

    for child in self.childItems:
      child.insertColumns(position, columns)

    return True

  def parent(self):
    return self.parentItem

  def removeChildren(self, position, count):
    if position < 0 or position + count > len(self.childItems):
      return False

    for row in range(count):
      self.childItems.pop(position)

    return True

  def removeColumns(self, position, columns):
    if position < 0 or position + columns > len(self.itemData):
      return False

    for column in range(columns):
      self.itemData.pop(position)

    for child in self.childItems:
      child.removeColumns(position, columns)

    return True

  def setData(self, column, value):
    if column < 0 or column >= len(self.itemData):
      return False

    self.itemData[column] = value

    return True

class TreeModel(QAbstractItemModel):
  def __init__(self, headers, parent=None):
    super(TreeModel, self).__init__(parent)

    rootData = [header for header in headers]
    self.rootItem = TreeItem(rootData)
    self.setupModelData(self.rootItem)

  def columnCount(self, parent=QModelIndex()):
      return self.rootItem.columnCount()

  def data(self, index, role):
    if not index.isValid():
      return None

    if role != Qt.DisplayRole and role != Qt.EditRole:
      return None

    item = self.getItem(index)
    return item.data(index.column())

  def flags(self, index):
    if not index.isValid():
      return 0

    return Qt.ItemIsEditable | super(TreeModel, self).flags(index)

  def getItem(self, index):
    if index.isValid():
      item = index.internalPointer()
      if item:
        return item
    return self.rootItem

  def headerData(self, section, orientation, role=Qt.DisplayRole):
    if orientation == Qt.Horizontal and role == Qt.DisplayRole:
      return self.rootItem.data(section)

    return None

  def index(self, row, column, parent=QModelIndex()):
    if parent.isValid() and parent.column() != 0:
      return QModelIndex()

    parentItem = self.getItem(parent)
    childItem = parentItem.child(row)
    if childItem:
      return self.createIndex(row, column, childItem)
    else:
      return QModelIndex()

  def insertColumns(self, position, columns, parent=QModelIndex()):
    self.beginInsertColumns(parent, position, position + columns - 1)
    success = self.rootItem.insertColumns(position, columns)
    self.endInsertColumns()

    return success

  def insertRows(self, position, rows, parent=QModelIndex()):
    parentItem = self.getItem(parent)
    self.beginInsertRows(parent, position, position + rows - 1)
    success = parentItem.insertChildren(position, rows,
                                        self.rootItem.columnCount())
    self.endInsertRows()

    return success

  def parent(self, index):
    if not index.isValid():
      return QModelIndex()

    childItem = self.getItem(index)
    parentItem = childItem.parent()

    if parentItem == self.rootItem:
      return QModelIndex()

    return self.createIndex(parentItem.childNumber(), 0, parentItem)

  def removeColumns(self, position, columns, parent=QModelIndex()):
    self.beginRemoveColumns(parent, position, position + columns - 1)
    success = self.rootItem.removeColumns(position, columns)
    self.endRemoveColumns()

    if self.rootItem.columnCount() == 0:
      self.removeRows(0, self.rowCount())

    return success

  def removeRows(self, position, rows, parent=QModelIndex()):
    parentItem = self.getItem(parent)

    self.beginRemoveRows(parent, position, position + rows - 1)
    success = parentItem.removeChildren(position, rows)
    self.endRemoveRows()

    return success

  def rowCount(self, parent=QModelIndex()):
    parentItem = self.getItem(parent)

    return parentItem.childCount()

  def setData(self, index, value, role=Qt.EditRole):
    if role != Qt.EditRole:
      return False

    item = self.getItem(index)
    result = item.setData(index.column(), value)

    if result:
      self.dataChanged.emit(index, index)

    return result

  def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
    if role != Qt.EditRole or orientation != Qt.Horizontal:
      return False

    result = self.rootItem.setData(section, value)
    if result:
      self.headerDataChanged.emit(orientation, section, section)

    return result

  def setupModelData(self, parent):
    return


# TODO: Use a proxy model and connect signals properly
class TransformModel(QtGui.QStandardItemModel):
  def __init__(self, data, horzHeader=None, vertHeader=None, parent=None):
    """
    Args:
        datain:    a list of lists\n
        horHeader: a list of strings
        verHeader: a list of strings
    """
    QtGui.QStandardItemModel.__init__(self, len(data), len(data[0]), parent)

    self.arraydata = data

    for row in range(self.rowCount()):
      for col in range(self.columnCount()):
        index = self.index(row,col)
        self.setData(index, QVariant('%5.2f' % (float(data[row][col]))))
    self.horzHeader = horzHeader
    self.vertHeader = vertHeader

  def flags(self, index):
    f = Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
    return f

  def on_itemChanged(self, item):
    return
  def getData(self):
    output = np.zeros((4,4))
    for i in range(self.rowCount()):
      for j in range(self.columnCount()):
        output[i,j] = self.data(self.index(i,j), Qt.DisplayRole)
    return output

class TransformDelegate(QItemDelegate):

  """
  Uses type alone for distinction
  """
  def __init__(self, parent=None):
    QItemDelegate.__init__(self, parent)

  def createEditor(self, parent, option, index):
    if index.row() < 4:
      editor = QLineEdit(parent)
    return editor

  def setEditorData(self, editor, index):
    value = index.model().data(index,Qt.EditRole)
    lineedit = editor
    if type(value) == float:
      lineedit.setText('%5.2f' % float(value))
    else:
      lineedit.setText(value)

  def setModelData(self, editor, model, index):
    lineedit = editor
    value = lineedit.text()
    model.setData(index, value, Qt.EditRole)

  def updateEditorGeometry(self, editor, option, index):
    editor.setGeometry(option.rect)


# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
