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

    def __init__(self, layer, snap_threshold, angle_threshold, break_com_vertices, merge_method, collinear_threshold, remove_orphans, remove_islands, create_unlinks, create_errors):
        QObject.__init__(self)
        self.layer = layer
        self.snap_threshold = snap_threshold
        self.angle_threshold = angle_threshold
        self.break_com_vertices = break_com_vertices
        self.merge_method = merge_method
        self.collinear_threshold = collinear_threshold
        self.remove_orphans = remove_orphans
        self.remove_islands = remove_islands
        self.create_errors = create_errors
        self.create_unlinks = create_unlinks

        # internal
        self.spIndex = QgsSpatialIndex()
        self.ndSpIndex = QgsSpatialIndex()
        self.feats = {}
        self.topology = {}
        self.nodes_coords = {}

        self.id = 0
        self.node_id = 0
        self.step = self.layer.featureCount()

        # errors (points and lines)
        self.empty_geometries = []
        self.points = [] #
        self.invalids = []
        self.mlparts = []
        self.orphans = []
        self.islands = []
        self.duplicates = []
        self.overlaps = [] # TODO if overlap not matching vertices of polyline
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


    def nodes_closest_iter(self):
        for k, v in self.nodes_coords.items():
            nd_geom = QgsGeometry.fromPoint(k)
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

    def clean(self):
        self.load_features()
        if self.snap_threshold:
            # use feat iter to create self.feats and coords
            # create nodes with spIndex
            indexed_nodes = {}
            self.nodes_id = 0
            self.nodes_coords = dict(map(lambda f:self.load_node_coord(f), self.load_features_iter()))

            # group based on distance
            self.combined = []
            res = map(lambda i: self.con_comp(i), self.nodes_closest_iter())
            self.combined = dict(zip(range(self.nodes_id, len(self.combined) + self.nodes_id), self.combined))
            # merge
            res =
            # update self.nodes_coords
            # update feats
            # feats to edges
        else:
            # use feat iter to create self.edges (from f , node otf)
            # feats to edges, nodes

        if self.remove_orphans:
            # remove where both endpoints connectivity = 1
        if self.remove_islands:

        if self.break_com_vertices:

        if self.merge_btw_intersections:

        elif self.merge_collinear:

    def load_node_coord(self, f):
        self.feats[f.id()] = f
        f_pl = f.geometry().asPolyline()
        for endp in (0,-1):
            try:
                visited_id = self.nodes_coords[f_pl[endp]]
            except KeyError:
                nd_feat = QgsFeature()
                nd_feat.setGeometry(QgsGeometry.fromPoint(f_pl[endp]))
                nd_feat.setFeatureId(self.node_id)
                nd_feat.setAttributes([self.node_id])
                self.ndSpIndex.insertFeature(nd_feat)
                self.node_id += 1
                yield self.nodes_id -1, f_pl[endp]

    def create_topology(self):

    # only 1 time execution permitted
    def load_features_iter(self):
        id = 0
        for f in self.layer.getFeatures():

            #self.progress.emit(self.step)
            if self.killed is True:
                break

            f_geom = f.geometry()
            # NULL, points, invalids, mlparts

            # TODO: add dropZValue()

            f_geom_length = f_geom.length()

            if f_geom is NULL:
                self.empty_geometries.append(f.id())
            elif not f_geom.isGeosValid():
                self.invalids.append(f.id())
            elif f_geom_length == 0:
                self.points.append(f.id())
            elif 0 < f_geom_length < self.snap_threshold:
                pass # do not add to the graph - as it will be removed later
            elif f_geom.wkbType() == 2:
                f.setFeatureId(id)
                id += 1
                f_pl = f_geom.asPolyline()
                for pnt in f_pl[0, -1]:
                    try:
                        ex_id = self.nodes_coords[pnt]

                    except KeyError:



            elif f_geom.wkbType() == 5:
                ml_segms = f_geom.asMultiPolyline()
                for ml in ml_segms:
                    ml_geom = QgsGeometry(ml)
                    ml_feat = self.copy_feat(f, ml_geom, id)
                    id += 1
                    yield ml_feat
        self.id = id

    def kill(self):
        self.killed = True