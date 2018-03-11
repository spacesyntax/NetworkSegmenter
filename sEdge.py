from PyQt4.QtCore import QObject
from qgis.core import QgsFeature

class sEdge(QObject):

    def __init__(self, id, geom, attrs):
        QObject.__init__(self)
        self.id = id
        self.geom = geom
        self.attrs = attrs

    def qgsFeat(self):
        feat = QgsFeature()
        feat.setGeometry(self.geom)
        feat.setAttributes(self.attrs)
        return feat