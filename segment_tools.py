
# general imports
from PyQt4.QtCore import QObject, pyqtSignal, QVariant
from qgis.core import QgsGeometry, QgsSpatialIndex, QgsField

# plugin module imports
try:
    from utilityFunctions import *
except ImportError:
    pass

class segmentTool(QObject):

    finished = pyqtSignal(object)
    error = pyqtSignal(Exception, basestring)
    progress = pyqtSignal(float)
    warning = pyqtSignal(str)
    killed = pyqtSignal(bool)

    #TODO:
    def __init__(self, sEdgesFields):
        QObject.__init__(self)
        self.sNodesMemory = {} # xy: connectivity
        self.sEdges = {}  # id: sEdge object
        # TODO: clean sEdgesFields from e_fid and original_id
        self.sEdgesFields = sEdgesFields # list of QGgsfield objects
        self.unlinks = {}
        self.spIndex = QgsSpatialIndex()

        self.breakagescount = 0
        self.breakages = []
        self.breakagesFields = [QgsField('id', QVariant.Int)]

    def addedges(self, layer):

        new_key_count = 0
        f_count = 1
        for f in layer.getFeatures():

            self.progress.emit(30 * f_count / layer.featureCount())
            f_count += 1

            if self.killed is True:
                break

            f_geom = f.geometry()
            f_attrs = {}
            for fld in self.sEdgesFields:
                fld_name = fld.name()
                f_attrs[fld_name] = f[fld_name]

            # drop 3rd dimension
            if f_geom.geometry().is3D(): # geom_type not in [5, 2, 1]
                f_geom.geometry().dropZValue()
            geom_type = f_geom.wkbType()

            # multilinestrings
            if geom_type == 5:
                for multipart in f_geom.asGeometryCollection():
                    # explode
                    polyline = multipart.asPolyline()
                    for i, segm in enumerate(polyline[1:]):
                        new_key_count += 1
                        new_geom = QgsGeometry.fromPolyline([polyline[i], segm])
                        feat = feat_from_geom_id(new_geom, new_key_count)
                        self.spIndex.insertFeature(feat)
                        f_attrs['e_fid'] = new_key_count
                        f_attrs['original_id'] = f.id()
                        expl_sedge = sEdge(new_key_count, new_geom, f_attrs, f.id())
                        self.unlinks[new_key_count] = []
                        for i in (expl_sedge.get_startnode(), expl_sedge.get_endnode()):
                            try:
                                self.sNodesMemory[(i[0], i[1])] += 1
                            except KeyError:
                                self.sNodesMemory[(i[0], i[1])] = 1
                        self.sEdges[new_key_count] = expl_sedge
            # exclude points & invalids and other
            elif geom_type == 2:
                # explode
                polyline = f_geom.asPolyline()
                for i, segm in enumerate(polyline[1:]):
                    new_geom = QgsGeometry.fromPolyline([polyline[i], segm])

                    new_key_count += 1
                    feat = feat_from_geom_id(new_geom, new_key_count)
                    self.spIndex.insertFeature(feat)
                    f_attrs['e_fid'] = new_key_count
                    f_attrs['original_id'] = f.id()
                    expl_sedge = sEdge(new_key_count, new_geom, f_attrs, f.id())
                    for i in (expl_sedge.get_startnode(), expl_sedge.get_endnode()):
                        try:
                            self.sNodesMemory[(i[0], i[1])] += 1
                        except KeyError:
                            self.sNodesMemory[(i[0], i[1])] = 1
                    self.sEdges[new_key_count] = expl_sedge
                    self.unlinks[new_key_count] = []
        self.sEdgesFields += [QgsField(i[0], i[1]) for i in [('e_fid', QVariant.Int),
                                                                           ('original_id', QVariant.String)]]
        return

    def prepare_unlinks(self, unlinks_layer, buffer_threshold):
        print 'preparing..'
        for unlink in unlinks_layer.getFeatures():
            # find two intersecting lines
            unlink_geom = unlink.geometry()
            if buffer_threshold:
                unlink_geom = unlink_geom.buffer(buffer_threshold, 22)
            inter_lines = self.spIndex.intersects(unlink_geom.boundingBox())
            if unlinks_layer.geometryType() in [0,2]:
                inter_lines = [x for x in inter_lines if unlink_geom.distance(self.sEdges[x].geom) <= 0.0001] # network tolerance todo user input??
            if len(inter_lines) == 2: # excluding invalid unlinks
                self.unlinks[inter_lines[0]].append(inter_lines[1])
                self.unlinks[inter_lines[1]].append(inter_lines[0])
            elif len(inter_lines) == 1: # self intersecting
                self.unlinks[inter_lines[0]].append(inter_lines[0])
        return

    def get_breakages(self, f_geom, e_fid, unlinks_layer, getBreakPoints):

        gids = self.spIndex.intersects(f_geom.boundingBox())
        crossing_points = []

        if self.killed is True:
            return

        startpntgeom = QgsGeometry.fromPoint(f_geom.asPolyline()[0])
        # crossing lines
        # exclude unlinks
        for gid in gids:
            if f_geom.crosses(self.sEdges[gid].geom) or f_geom.touches(self.sEdges[gid].geom):
                if unlinks_layer and gid in self.unlinks[e_fid]:
                    pass
                else:
                    point = f_geom.intersection(self.sEdges[gid].geom)
                    if point.wkbType() == 4:
                        for p in point.asGeometryCollection():
                            crossing_points.append(p)
                    elif point.wkbType() == 1:
                        crossing_points.append(point)

        crossing_points.sort(key=lambda x: f_geom.distance(startpntgeom))

        if getBreakPoints:
            # not duplicates TODO?
            # TODO: only geom, or plus line 1 & line 2
            self.breakages += crossing_points

        return crossing_points

    def break_features(self, stub_ratio, getBreakPoints, unlinks_layer, buffer_threshold):

        if unlinks_layer:
            self.prepare_unlinks(unlinks_layer, buffer_threshold)

        f_count = 1
        segm_id = 0
        segments = []

        for sedge in self.sEdges.values():

            if self.killed is True:  break
            self.progress.emit((60 * f_count / max(self.sEdges.keys())) + 30)
            f_count += 1
            print 'start brkgs'
            f_geom = sedge.geom
            crossing_points = self.get_breakages(f_geom, sedge.e_fid, unlinks_layer, getBreakPoints)
            print 'done brkgs'

            # if no crossing points
            crossing_points = [sedge.get_startnode()] + \
                                          [i.asPoint() for i in crossing_points] + \
                                          [sedge.get_endnode()]
            print 'start segms'
            for i, cross_point in enumerate(crossing_points[1:]):
                include = True
                new_geom = QgsGeometry.fromPolyline([crossing_points[i], cross_point])
                print 'stubs'
                if stub_ratio:
                    max_stub_length = (stub_ratio/float(100))*sedge.geom.length()
                    if i == 0:
                        startnode = sedge.get_startnode()
                        # find if sharing vertex with intersecting lines
                        if self.sNodesMemory[(startnode[0], startnode[1])] == 1:
                            if new_geom.length() <= max_stub_length:
                                include = False
                    elif i == len(crossing_points) - 2:
                        endnode = sedge.get_endnode()
                        # find if sharing vertex with intersecting lines
                        if self.sNodesMemory[(endnode[0], endnode[1])] == 1:
                            if new_geom.length() <= max_stub_length:
                                include = False
                if include:
                    print 'include'
                    # new_feat
                    segm_id += 1
                    segm_sedge = sEdge(segm_id, new_geom, sedge.attrs, sedge.original_id)
                    segm_sedge.attrs['original_id'] = segm_sedge.original_id

                    segments.append(segm_sedge)

        return segments, self.breakages

    def kill(self):
        self.killed = True

