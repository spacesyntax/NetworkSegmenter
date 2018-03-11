
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

    #TODO:
    def __init__(self, sEdgesFields):
        QObject.__init__(self)
        self.sEdges = {} # id: sedge
        self.sNodes = {} # xy: connectivity
        self.sEdgesFields = sEdgesFields # list of QGgsfield objects
        self.unlinks = {}
        self.spIndex = QgsSpatialIndex()

        try:
            self.atEdgeCounter = max(self.sEdges.keys())
        except ValueError:
            self.atEdgeCounter = 0

    def wrap_iter(self, any_iter):
        for i in any_iter:
            if s:
                break
            else:
                yield i

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
        return sEdge(self.atEdgeCounter, f_geom, f_attrs)

    def explode_sedge(self, f_geom, f_attrs):
        segms = map(lambda polyline: map(lambda line : self.addedge(line, f_attrs), get_lines(polyline)), get_polylines(f_geom))
        return sum(segms, [])

    # add edges from any_iter - has to be ls - no multils
    def addedges(self, any_iter):

        sedges = map(lambda (f_id, f_geom, f_attrs): self.addedge(f_geom, f_attrs + [f_id]), self.wrap_iter(any_iter))
        self.sEdges.update(dict(zip([e.id for e in sedges], sedges)))

        return

    # add exploded edges from any_iter
    def addexpledges(self, any_iter):

        expl = map(lambda f: self.explode_sedge(f.geometry(), f.attributes() + [f.id()]), any_iter)
        print len(expl)
        expl_sedges = sum(expl, [])

        self.sEdges.update(dict(zip([e.id for e in expl_sedges], expl_sedges)))

        return

    def prepare_unlinks(self, unlinks_layer, buffer_threshold):
        print 'preparing unlinks..'
        for unlink in unlinks_layer.getFeatures():
            # find two intersecting lines
            unlink_geom = unlink.geometry()
            if buffer_threshold:
                unlink_geom = unlink_geom.buffer(buffer_threshold, 22)
            inter_lines = self.spIndex.intersects(unlink_geom.boundingBox())
            inter_lines = [x for x in inter_lines if unlink_geom.distance(self.explodedFeatures[x].geometry()) <= 0.0001]  # network tolerance todo user input??
            if len(inter_lines) == 2:  # excluding invalid unlinks
                self.unlinks[inter_lines[0]].append(inter_lines[1])
                self.unlinks[inter_lines[1]].append(inter_lines[0])
        return

    def get_breakages(self, f_geom, e_fid, unlinks_layer, getBreakPoints, stub_ratio):

        gids = self.spIndex.intersects(f_geom.boundingBox())
        crossing_points = []

        startpoint = f_geom.asPolyline()[0]
        endpoint = f_geom.asPolyline()[-1]
        startpntgeom = QgsGeometry.fromPoint(startpoint)
        # crossing lines
        # exclude unlinks
        for gid in gids:
            g_geom = self.explodedFeatures[gid].geometry()
            if f_geom.crosses(g_geom) or f_geom.touches(g_geom):
                if unlinks_layer and gid in self.unlinks[e_fid]:
                    pass
                else:
                    point = f_geom.intersection(g_geom)
                    if point.wkbType() == 4:
                        for p in point.asGeometryCollection():
                            crossing_points.append(p)
                    elif point.wkbType() == 1:
                        crossing_points.append(point)

        crossing_points.sort(key=lambda x: x.distance(startpntgeom))

        if getBreakPoints:
            # not duplicates TODO: only geom, or plus line 1 & line 2
            self.breakages += crossing_points

        crossing_points = [i.asPoint() for i in crossing_points]

        # check for stubs
        if stub_ratio and len(crossing_points) > 0:
            max_stub_length = (stub_ratio / float(100)) * f_geom.length()
            if self.explodedTopology[(startpoint.x(), startpoint.y())] == 1:
                if QgsDistanceArea().measureLine(startpoint, crossing_points[0]) > max_stub_length:
                    crossing_points = [startpoint] + crossing_points
            if self.explodedTopology[(endpoint.x(), endpoint.y())] == 1:
                if QgsDistanceArea().measureLine(endpoint, crossing_points[-1]) > max_stub_length:
                    crossing_points = crossing_points + [endpoint]
        else:
            crossing_points = [startpoint] + crossing_points + [endpoint]

        return crossing_points

    def break_features(self, stub_ratio, getBreakPoints, unlinks_layer, buffer_threshold):

        if unlinks_layer:
            self.prepare_unlinks(unlinks_layer, buffer_threshold)

        f_count = 1
        segm_id = 0
        segments = []

        for expl_feat in self.explodedFeatures.values():

            if self.killed is True: break
            self.progress.emit((60 * f_count / max(self.explodedFeatures.keys())) + 30)
            f_count += 1
            f_geom = expl_feat.geometry()
            crossing_points = self.get_breakages(f_geom, expl_feat.id(), unlinks_layer, getBreakPoints, stub_ratio)

            # if no crossing points
            for i, cross_point in enumerate(crossing_points[1:]):
                new_geom = QgsGeometry.fromPolyline([crossing_points[i], cross_point])
                # new_feat
                segm_id += 1
                segm_feat = QgsFeature()
                segm_feat.setGeometry(new_geom)
                # if new_geom.isGeosValid():
                segm_feat.setFeatureId(segm_id)
                segm_feat.setAttributes(expl_feat.attributes() + [segm_id])
                segments.append(segm_feat)

        self.sEdgesFields.append(QgsField('segm_id', QVariant.Int))
        return segments, self.breakages

    def kill(self):
        self.killed = True

