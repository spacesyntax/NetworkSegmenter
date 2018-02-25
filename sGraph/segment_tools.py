
# general imports
from qgis.core import QgsFeature, QgsGeometry, QgsSpatialIndex, QgsPoint, QgsVectorFileWriter, QgsField
from PyQt4.QtCore import QObject, pyqtSignal, QVariant, pyqtSlot

import traceback

# plugin module imports
try:
    from utilityFunctions import *
except ImportError:
    pass


class sEdge(QObject):

    def __init__(self, e_fid, geom, attrs, original_id):
        QObject.__init__(self)
        self.e_fid = e_fid
        self.original_id = original_id
        self.geom = geom
        self.attrs = attrs

    def get_startnode(self):
        return self.geom.asPolyline()[0]

    def get_startnode_point(self):
        startnd = self.get_startnode()
        return QgsGeometry.fromPoint(QgsPoint(startnd[0], startnd[1]))

    def get_endnode(self):
        return self.geom.asPolyline()[-1]

    def qgsFeat(self):
        edge_feat = QgsFeature()
        edge_feat.setGeometry(self.geom)
        edge_feat.setFeatureId(self.e_fid)
        edge_feat.setAttributes([attr_values for attr_name, attr_values in self.attrs.items()])
        return edge_feat


class segmentTool(QObject):

    finished = pyqtSignal(object)
    error = pyqtSignal(Exception, basestring)
    progress = pyqtSignal(float)
    warning = pyqtSignal(str)
    killed = pyqtSignal(bool)

    #TODO:
    def __init__(self, sEdgesFields):
        QObject.__init__(self)
        self.sNodesMemory ={} # xy: connectivity
        self.sEdges = {}  # id: sEdge object
        # TODO: clean sEdgesFields from e_fid and original_id
        self.sEdgesFields = sEdgesFields + [QgsField(i[0], i[1]) for i in [('e_fid', QVariant.Int),
                                                                           ('original_id', QVariant.String)]]  # list of QGgsfield objects
        self.unlinks = {}
        self.spIndex = QgsSpatialIndex()

        self.er = None
        self.trcb = None

    def addedges(self, layer):

        new_key_count = 0
        f_count = 1
        try:
            for f in layer.getFeatures():

                self.progress.emit(30 * f_count / layer.featureCount())
                f_count += 1

                if self.killed is True:
                    break

                f_geom = f.geometry()

                f_attrs = {fld.name(): f[fld.name()] for fld in self.sEdgesFields if fld.name() not in ['e_fid', 'original_id']}

                # drop 3rd dimension
                geom_type = f_geom.wkbType()
                if geom_type not in [5, 2, 1] and f_geom.geometry().is3D():
                    f_geom.geometry().dropZValue()
                    geom_type = f_geom.wkbType()

                # multilinestrings
                if geom_type == 5:
                    for multipart in f_geom.asGeometryCollection():
                        # explode
                        polyline = multipart.asPolyline()
                        for i, segm in enumerate(polyline[1:]):
                            new_key_count += 1
                            new_geom = QgsGeometry.fromPolyline([QgsPoint(polyline[i][0], polyline[i][1]), QgsPoint(segm[0], segm[1])])
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
                # exclude points
                elif geom_type == 1:
                    pass
                # exclude invalids
                elif not f_geom.isGeosValid():
                    pass
                # linestrings
                elif geom_type == 2:
                    # explode
                    polyline = f_geom.asPolyline()
                    for i, segm in enumerate(polyline[1:]):
                        new_geom = QgsGeometry.fromPolyline([QgsPoint(polyline[i][0], polyline[i][1]), QgsPoint(segm[0], segm[1])])

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
        except Exception, e:
            self.er = e
            self.trcb = traceback.format_exc()
            self.error.emit(e, traceback.format_exc()) #TODO: error
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
                inter_lines = [x for x in inter_lines if unlink_geom.distance(self.sEdges[x].geom) <= 0.0001]
            if len(inter_lines) == 2: # excluding invalid unlinks
                self.unlinks[inter_lines[0]].append(inter_lines[1])
                self.unlinks[inter_lines[1]].append(inter_lines[0])
            elif len(inter_lines) == 1: # self intersecting
                self.unlinks[inter_lines[0]].append(inter_lines[0])
        return

    def break_features(self, stub_ratio, getBreakPoints, unlinks_layer, buffer_threshold):

        if unlinks_layer:
            self.prepare_unlinks(unlinks_layer, buffer_threshold)

        f_count = 1
        segm_id = 0

        segments = []
        breakPoints = []

        try:
            for sedge in self.sEdges.values():

                if self.killed is True:
                    break

                f_geom = sedge.geom

                # intersecting lines
                gids = self.spIndex.intersects(f_geom.boundingBox())

                # crossing lines
                # exclude unlinks
                gids = [gid for gid in gids if f_geom.crosses(self.sEdges[gid].geom) and gid not in self.unlinks[sedge.e_fid] ]
                crossing_points = []
                startpntgeom = sedge.get_startnode_point()
                for gid in gids:
                    point = f_geom.intersection(self.sEdges[gid].geom)
                    if point.wkbType() == 4:
                        for p in point.asGeometryCollection():
                            crossing_points.append((p, p.distance(startpntgeom)))
                    elif point.wkbType() == 1:
                        crossing_points.append((point, point.distance(startpntgeom)))

                self.progress.emit((60 * f_count / max(self.sEdges.keys())) + 30)
                f_count += 1

                if len(crossing_points) == 0:
                    # new_feat
                    segm_id += 1
                    # add new segment id
                    sedge.e_fid = segm_id
                    new_attrs = dict(sedge.attrs)
                    new_attrs['e_fid'] = segm_id
                    segments.append(sEdge(segm_id, sedge.geom, new_attrs, sedge.original_id))
                else:

                    crossing_points_ordered = sorted(crossing_points, key=lambda tup: tup[1])
                    crossing_points_ordered = [i[0].asPoint() for i in crossing_points_ordered]
                    if getBreakPoints:
                        # not duplicates TODO?
                        # TODO: only geom, or plus line 1 & line 2
                        breakPoints += crossing_points_ordered
                    crossing_points_ordered = [sedge.get_startnode()] + crossing_points_ordered + [sedge.get_endnode()]
                    for i, cross_point in enumerate(crossing_points_ordered[1:]):
                        include = True
                        new_geom = QgsGeometry.fromPolyline([crossing_points_ordered[i], cross_point])
                        if stub_ratio:
                            if i == 0:
                                startnode = sedge.get_startnode()
                                # find if sharing vertex with intersecting lines
                                print self.sNodesMemory[(startnode[0], startnode[1])]
                                if self.sNodesMemory[(startnode[0], startnode[1])] == 1:
                                    print True, new_geom.length() / sedge.geom.length()
                                    if new_geom.length() / sedge.geom.length() <= (stub_ratio/float(100)):
                                        include = False
                                        print True
                            elif i == len(crossing_points_ordered) - 2:
                                endnode = sedge.get_endnode()
                                # find if sharing vertex with intersecting lines
                                print self.sNodesMemory[(endnode[0], endnode[1])]
                                if self.sNodesMemory[(endnode[0], endnode[1])] == 1:
                                    print True, new_geom.length() / sedge.geom.length()
                                    if new_geom.length() / sedge.geom.length() <= (stub_ratio/float(100)):
                                        include = False
                                        print True
                        if include:
                            # new_feat
                            segm_id += 1
                            segm_sedge = sEdge(segm_id, new_geom, sedge.attrs, sedge.original_id)
                            segm_sedge.attrs['e_fid'] = segm_id
                            segm_sedge.attrs['original_id'] = segm_sedge.original_id
                            segments.append(segm_sedge)

        except Exception, e:
            self.er = e
            self.trcb = traceback.format_exc()
            self.error.emit(e, traceback.format_exc())

        return segments, breakPoints

    def kill(self):
        self.killed = True