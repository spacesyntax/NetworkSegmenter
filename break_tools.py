import itertools
from PyQt4.QtCore import QObject, pyqtSignal, QVariant
from qgis.core import QgsSpatialIndex, QgsGeometry, QgsDistanceArea, QgsFeature, QgsField, QgsFields

# read graph - as feat
class break_tools(QObject):

    finished = pyqtSignal(object)
    error = pyqtSignal(Exception, basestring)
    progress = pyqtSignal(float)
    warning = pyqtSignal(str)
    killed = pyqtSignal(bool)

    def __init__(self, layer, snap_threshold, _break,  _merge, angle_threshold, _orphans, unlinks, errors):
        QObject.__init__(self)
        self.layer = layer
        self.snap_threshold = snap_threshold
        self.angle_threshold = angle_threshold
        self._break = _break
        self._merge = _merge
        self._orphans = _orphans
        self.errors = errors
        self.unlinks = unlinks

        # internal
        self.edgSpIndex = QgsSpatialIndex()
        self.ndSpIndex = QgsSpatialIndex()
        self.edges = {}
        self.nodes = {}
        self.nodes_visited = {}
        self.topology = {}

        self.id = -1
        self.node_id = 0
        self.step = self.layer.featureCount()

        # errors (points and lines)
        self.empty_geometries = []
        self.points = [] #
        self.invalids = []
        self.mlparts = []
        self.orphans = []
        self.duplicates = []
        self.overlaps = []
        self.snaps = [] #
        self.self_intersections = [] #
        self.closed_polylines = []
        self.breaks = [] #
        self.merges = [] #
        self.collinear = [] #

        # unlinks feats
        self.unlinks = {}

        self.node_prototype = QgsFeature()
        node_fields = QgsFields()
        node_fields.append(QgsField('id', QVariant.Int))
        self.node_prototype.setFields(node_fields)
        self.node_prototype.setAttributes([0])
        self.node_prototype.setGeometry(QgsGeometry())

        self.step = 20 / float(len(self.layer.featureCount()))

    def load_graph(self):

        # load graph
        res = map(lambda feat: self.edgSpIndex.insertFeature(feat), self.feat_iter(self.layer))
        self.step = 35 / float(len(res))

        return

    def snap_endpoints(self):
        # group points by distance
        self.combined = []
        res = map(lambda i: self.con_comp(i), self.nodes_closest_iter())

        # merge snapped endpoints

        # delete duplicates


        return

    def nodes_closest_iter(self):
            for nd_id, nd_feat in self.nodes.items():
                nd_geom = nd_feat.geometry()
                nd_buffer = nd_geom.buffer(self.snap_threshold, 29)
                closest_nodes = self.ndSpIndex.intersects(nd_buffer.boundingBox())
                closest_nodes = set(filter(lambda id: nd_geom.distance(self.nodes[id].geometry()) <= self.snap_threshold , closest_nodes))
                yield closest_nodes

    def con_comp(self, subset):
        for candidate in self.combined:
            if not candidate.isdisjoint(subset):
                candidate.update(subset)
                break
        else:
            self.combined.append(subset)
        return True

    def copy_feat(self, f, geom, id):
        copy_feat = QgsFeature(f)
        copy_feat.setGeometry(geom)
        copy_feat.setFeatureId(id)
        return copy_feat

    # only 1 time execution permitted
    def feat_iter(self, layer):
        id = 0
        for f in layer.getFeatures():

            #self.progress.emit(self.step)
            if self.killed is True:
                break

            f_geom = f.geometry()
            # NULL, points, invalids, mlparts

            if f_geom is NULL:
                self.empty_geometries.append(f.id())
            elif not f_geom.isGeosValid():
                self.invalids.append(f.id())
            else:
                f_geom_length = f_geom.length()
                if f_geom_length == 0:
                    self.points.append(f.id())
                elif 0 < f_geom_length < self.snap_threshold:
                    pass # do not add to the graph - as it will be removed later
                else:
                    if f_geom.wkbType() == 2:
                        f.setFeatureId(id)
                        self.feats[id] = f
                        pl = f_geom.asPolyline()
                        for i in (0, -1):
                            try:
                                nd_id = self.nodes_visited[(pl[i].x(), pl[i].y())]
                                self.topology[nd_id].append(id)
                            except KeyError:
                                # TODO: find if within distance x from point
                                self.nodes_visited[(pl[i].x(), pl[i].y())] = self.node_id
                                node_feat = self.copy_feat(self.node_prototype, QgsGeometry.fromPoint(pl[i]), self.node_id)
                                self.nodes[self.node_id] = node_feat
                                self.ndSpIndex.insertFeature(node_feat)
                                self.topology[self.node_id] = [id]
                                self.node_id += 1
                        id += 1
                        yield f
                    elif f_geom.wkbType() == 5:
                        ml_segms = f_geom.asMultiPolyline()
                        for ml in ml_segms:
                            ml_geom = QgsGeometry(ml)
                            ml_feat = self.copy_feat(f, ml_geom, id)
                            self.feats[id] = ml_feat
                            pl = ml_geom.asPolyline()
                            for i in (0, -1):
                                try:
                                    nd_id = self.nodes_visited[(pl[i].x(), pl[i].y())]
                                except KeyError:
                                    self.nodes_visited[(pl[i].x(), pl[i].y())] = self.node_id
                                    node_feat = self.copy_feat(self.node_prototype, QgsGeometry.fromPoint(pl[i]), self.node_id)
                                    self.nodes[self.node_id] = node_feat
                                    self.ndSpIndex.insertFeature(node_feat)
                                    self.node_id += 1
                            id += 1
                            yield ml_feat

    def kill(self):
        self.killed = True