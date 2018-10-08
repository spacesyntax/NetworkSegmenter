import itertools
from PyQt4.QtCore import QObject, pyqtSignal, QVariant
from qgis.core import QgsSpatialIndex, QgsGeometry, QgsDistanceArea, QgsFeature, QgsField, QgsFields

class sEdge(QObject):

    def __init__(self, feature, id, startid, endid):
        QObject.__init__(self)
        self.feature = feature
        self.id = id
        self.startid = startid
        self.endid = endid

    def updateStartNode(self, new_node):
        self.startid = new_node.id
        self.feature.setGeometry([new_node.geometry().asPoint()] + QgsGeometry.fromPolyline(self.feature.geometry().asPolyline()[1:]))
        return

    def updateEndNode(self, new_node):
        self.endid = new_node.id
        self.feature.setGeometry(QgsGeometry.fromPolyline(self.feature.geometry().asPolyline()[:-1] + [new_node.geometry().asPoint()]))
        return
