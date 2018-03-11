from PyQt4.QtCore import QObject

class sEdge(QObject):

    def __init__(self, id, geom, attrs):
        QObject.__init__(self)
        self.id = id
        self.geom = geom
        self.attrs = attrs