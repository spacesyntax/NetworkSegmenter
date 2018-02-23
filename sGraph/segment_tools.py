
# general imports
from qgis.core import QgsFeature, QgsGeometry, QgsSpatialIndex, QgsPoint, QgsVectorFileWriter, QgsField
from PyQt4.QtCore import QObject, pyqtSignal, QVariant


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

    def get_endnode(self):
        return self.geom.asPolyline()[-1]


class segmentTool(QObject):

    finished = pyqtSignal(object)
    error = pyqtSignal(Exception, basestring)
    progress = pyqtSignal(float)
    warning = pyqtSignal(str)
    killed = pyqtSignal(bool)

    #TODO:
    def __init__(self,sEdgesFields):
        QObject.__init__(self)
        self.sNodesMemory ={} # xy: connectivity
        self.sEdges = {}  # id: sEdge object
        self.sEdgesFields = sEdgesFields + [QgsField(i[0], i[1]) for i in [('e_fid', QVariant.Int),
                                                                           ('ancestors', QVariant.String)]]  # list of QGgsfield objects
        self.unlinks = {}
        self.spIndex = QgsSpatialIndex()

    def addedges(self, layer):

        new_key_count = 0
        f_count = 1

        for f in layer.getFeatures():

            self.progress.emit(30 * f_count / self.feat_count)
            f_count += 1

            if self.killed is True:
                break

            f_geom = f.geometry()

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
                        new_geom = QgsGeometry.fromPolyline([QgsPoint(polyline[i], segm)])
                        feat = feat_from_geom_id(new_geom, new_key_count)
                        self.spIndex.insertFeature(feat)
                        expl_sedge = sEdge(new_key_count, new_geom, f.attributes(), f.id())
                        startnd = expl_sedge.get_startnode().asPoint()
                        try:
                            self.sNodesMemory[startnd] += 1
                        except KeyError:
                            self.sNodesMemory[startnd] = 1
                        endnd = expl_sedge.get_endnode().asPoint()
                        try:
                            self.sNodesMemory[endnd] += 1
                        except KeyError:
                            self.sNodesMemory[endnd] = 1
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
                polyline = geom_type.asPolyline()
                for i, segm in enumerate(polyline[1:]):
                    new_geom = QgsGeometry.fromPolyline([QgsPoint(polyline[i], segm)])
                    feat = feat_from_geom_id(new_geom, new_key_count)
                    self.spIndex.insertFeature(feat)
                    self.sEdges[new_key_count] = sEdge(new_key_count, new_geom, f.attributes(), f.id())
        return

    def prepare_unlinks(self, unlinks_layer, buffer_threshold):
        for unlink in unlinks_layer.getFeatures():
            # find two intersecting lines
            unlink_geom = unlink.geometry()
            if buffer:
                unlink_geom = unlink_geom.buffer(buffer_threshold)
            inter_lines = self.spIndex.intersects(unlink_geom.boundingBox())
            if unlinks_layer.wkbType() == 1:
                inter_lines = [x for x in inter_lines if unlink_geom.intersection(self.sEdges[x]).wkbType() == 1]
            elif unlink_geom.wkbType() == 3:
                inter_lines = [x for x in inter_lines if unlink_geom.intersection(self.sEdges[x]).wkbType() == 2]
            if len(inter_lines) == 2: # excluding invalid unlinks
                try:
                    self.unlinks[inter_lines[0]] .append(inter_lines[1])
                except KeyError:
                    self.unlinks[inter_lines[0]] = [inter_lines[1]]
        return

    def break_features(self, stub_ratio):

        f_count = 1
        segm_id = 0

        segments = []
        breakPoints = []

        # TODO: if self.breakPoints:
        for sedge in self.sEdges.values():

            if self.killed is True:
                break

            f_geom = sedge.getgeom()

            # intersecting lines
            gids = self.spIndex.intersects(f_geom.boundingBox())

            # crossing lines
            # exclude unlinks
            gids = [gid for gid in gids if f_geom.crosses(self.sEdges[gid]) and gid not in self.unlinks[sedge.e_fid] ]
            crossing_points = []
            for gid in gids:
                point = f_geom.intersection(self.sEdges[gid])
                if point.wkbType() == 4:
                    for p in point.asGeometryCollection():
                        crossing_points.append((p, p.distance(sedge.startnode.getgeom())))
                elif point.wkbType() == 1:
                    crossing_points.append((point, point.distance(sedge.startnode.getgeom())))

            self.progress.emit((60 * f_count / self.feat_count) + 30)
            f_count += 1

            if len(crossing_points) == 0:
                # new_feat
                segm_id += 1
                # add new segment id
                sedge.e_fid = segm_id
                segments.append(sedge)
            else:
                crossing_points_ordered = [sorted(v, key=lambda tup: tup[1]) for v in crossing_points]
                crossing_points_ordered = [i[0] for i in crossing_points_ordered]
                if self.breakPoints:
                    # not duplicates TODO?
                    # TODO: only geom, or plus line 1 & line 2
                    breakPoints += crossing_points_ordered
                crossing_points_ordered = [sedge.get_startnode()] + crossing_points_ordered + [sedge.get_endnode()]
                for i, cross_point in crossing_points_ordered[1:]:
                    include = True
                    new_geom = QgsGeometry.fromPolyline([QgsPoint(crossing_points_ordered[i], cross_point)])
                    if stub_ratio:
                        if i == 0:
                            startnode = sedge.get_startnode()
                            # find if sharing vertex with intersecting lines
                            if self.sNodesMemory[startnode.asPoint()] == 1:
                                if new_geom.length() <= stub_ratio * sedge.geom.length()/100:
                                    include = False
                        elif i == len(crossing_points_ordered) - 1:
                            endnode = sedge.get_endnode()
                            # find if sharing vertex with intersecting lines
                            if self.sNodesMemory[endnode.asPoint()] == 1:
                                if new_geom.length() <= stub_ratio * sedge.geom.length() / 100:
                                    include = False
                    if include:
                        # new_feat
                        segm_id += 1
                        segments.append(sEdge(segm_id, new_geom, sedge.attrs, sedge.original_id))

        return segments, breakPoints

    def kill(self):
        self.br_killed = True