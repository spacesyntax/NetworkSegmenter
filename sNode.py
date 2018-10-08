import itertools
from PyQt4.QtCore import QObject, pyqtSignal, QVariant
from qgis.core import QgsSpatialIndex, QgsGeometry, QgsDistanceArea, QgsFeature, QgsField, QgsFields

class sNode(QObject):

    def __init__(self, feature, id, topology):
        QObject.__init__(self)
        self.feature = feature
        self.id = id
        self.topology = topology
