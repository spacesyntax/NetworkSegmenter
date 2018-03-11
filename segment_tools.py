
# general imports
from PyQt4.QtCore import QObject, pyqtSignal, QVariant
from qgis.core import QgsGeometry, QgsSpatialIndex, QgsField, QgsDistanceArea, QgsFeature

# plugin module imports
try:
    from utilityFunctions import *
except ImportError:
    pass

class sGraph(QObject):

    finished = pyqtSignal(object)
    error = pyqtSignal(Exception, basestring)
    progress = pyqtSignal(float)
    warning = pyqtSignal(str)
    killed = pyqtSignal(bool)

    def __init__(self, sEdgesFields):
        QObject.__init__(self)
        self.sEdges = {} # id: sedge
        self.sNodes = {} # xy: connectivity
        self.sEdgesFields = sEdgesFields # list of QGgsfield objects
        self.unlinks = {}
        self.spIndex = QgsSpatialIndex()
        self.breakages = []
        self.segm_id = 0

        try:
            self.atEdgeCounter = max(self.sEdges.keys())
        except ValueError:
            self.atEdgeCounter = 0

    # inside class to control for stop iteration when user cancels
    def iter_from_layer(self, layer):
        for f in layer.getFeatures():
            if self.killed is True: break
            else:
                f_geom = f.geometry()
                if f_geom.wkbType() in [2, 5]:
                    yield f

    def addedge(self, f_geom, f_attrs):

        # self.progress.emit((60 * f_count / max(self.explodedFeatures.keys())) + 30)

        # sp Index
        self.atEdgeCounter += 1
        feat = getQgsFeat(f_geom, self.atEdgeCounter)
        self.spIndex.insertFeature(feat)
        self.unlinks[self.atEdgeCounter] = []
        f_geom_pl = f_geom.asPolyline()
        for i in [f_geom_pl[0], f_geom_pl[-1]]:
            try:
                self.sNodes[(i.x(), i.y())] += 1
            except KeyError:
                self.sNodes[(i.x(), i.y())] = 1
        self.sEdges[self.atEdgeCounter] = sEdge(self.atEdgeCounter, f_geom, f_attrs)
        return True

    def explodeedge(self, f_geom, f_attrs):
        res = map(lambda polyline: map(lambda line : self.addedge(line, f_attrs), get_lines(polyline)), get_polylines(f_geom))
        del res
        return True

    # add edges from any_iter - has to be ls - no multils
    def addedges(self, any_iter):

        res = map(lambda (f_id, f_geom, f_attrs): self.addedge(f_geom, f_attrs + [f_id]), any_iter)
        del res
        return

    # add exploded edges from any_iter
    def addexpledges(self, any_iter, leng):
        self.progress_count = 0
        self.total_count = leng
        res = map(lambda f: self.explodeedge(f.geometry(), f.attributes() + [f.id()]), any_iter)
        del res
        return

    def readunlink(self, unlink, buffer_threshold):
        unlink_geom = unlink.geometry()
        if buffer_threshold:
            unlink_geom = QgsGeometry(unlink_geom.buffer(buffer_threshold, 22))
        # network tolerance todo user input
        inter_lines = filter(lambda x: unlink_geom.distance(self.sEdges[x].geom) <= 0.0001, self.spIndex.intersects(unlink_geom.boundingBox()))
        if len(inter_lines) == 2:  # excluding invalid unlinks
            self.unlinks[inter_lines[0]].append(inter_lines[1])
            self.unlinks[inter_lines[1]].append(inter_lines[0])
        return True

    def readunlinks(self, unlinks_layer, buffer_threshold):
        print 'preparing unlinks..'
        res = map(lambda unlink: self.readunlink(unlink, buffer_threshold), unlinks_layer.getFeatures())
        print 'unlinks identified', len([x for x in self.unlinks.values() if len(x) > 0])
        del res
        return

    def createsegmfeat(self, segm_geom, attrs):
        self.segm_id += 1
        segm_attrs = attrs + [self.segm_id]
        feat = QgsFeature()
        feat.setAttributes(segm_attrs)
        feat.setFeatureId(self.segm_id)
        feat.setGeometry(segm_geom)
        return feat

    def generatesegments(self, sedge):
        crossing_points = self.getcrossings(sedge.geom, sedge.id)
        # new_feat
        return map(lambda segm_geom: self.createsegmfeat(segm_geom, sedge.attrs), get_geoms(crossing_points))

    def segmentedges(self, unlinks_layer, buffer_threshold):
        self.progress_count = 0
        self.total_count = len(self.sEdges)

        if unlinks_layer:
            self.hasunlinks = True
            self.readunlinks(unlinks_layer, buffer_threshold)

        segments = map(lambda edge: self.generatesegments(edge), self.sEdges.values())
        # segments = sum(res, []) # list of features
        self.sEdgesFields.append(QgsField('segm_id', QVariant.Int))
        return segments, self.breakages

    def getcrossings(self, f_geom, f_id):

        self.progress_count += 1
        self.progress.emit((60 * self.progress_count /self.total_count) + 30)

        gids = self.spIndex.intersects(f_geom.boundingBox())
        if self.hasunlinks:
            gids = filter(lambda gid: gid not in self.unlinks[f_id], gids)

        ggeoms = filter(lambda g_geom: f_geom.crosses(g_geom) or f_geom.touches(g_geom), map(lambda gid: self.sEdges[gid].geom, gids))

        # crossing lines
        # exclude unlinks
        crossing_points = filter(lambda p: p.wkbType() == 1, map(lambda g_geom: f_geom.intersection(g_geom), ggeoms)) # mlpoints should not exist

        if self.getBreakPoints:
            # not duplicates TODO: only geom, or plus line 1 & line 2
            self.breakages += crossing_points  # list of features

        startpoint = f_geom.asPolyline()[0]
        startpntgeom = QgsGeometry.fromPoint(startpoint)
        endpoint = f_geom.asPolyline()[-1]

        crossing_points.sort(key=lambda x: x.distance(startpntgeom))
        crossing_points = map(lambda p: p.asPoint(), crossing_points)

        # check for stubs
        if self.stub_ratio and len(crossing_points) > 0:
            max_stub_length = (self.stub_ratio / float(100)) * f_geom.length()
            if self.sNodes[(startpoint.x(), startpoint.y())] == 1:
                if QgsDistanceArea().measureLine(startpoint, crossing_points[0]) > max_stub_length:
                    crossing_points = [startpoint] + crossing_points
            if self.sNodes[(endpoint.x(), endpoint.y())] == 1:
                if QgsDistanceArea().measureLine(endpoint, crossing_points[-1]) > max_stub_length:
                    crossing_points = crossing_points + [endpoint]
        else:
            crossing_points = [startpoint] + crossing_points + [endpoint]

        return crossing_points

    def kill(self):
        self.killed = True