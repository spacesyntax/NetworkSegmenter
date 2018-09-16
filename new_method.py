import itertools
from PyQt4.QtCore import QObject, pyqtSignal, QVariant
from itertools import groupby
from operator import itemgetter
import math

# read graph - as feat
class segmentor(QObject):

    finished = pyqtSignal(object)
    error = pyqtSignal(Exception, basestring)
    progress = pyqtSignal(float)
    warning = pyqtSignal(str)
    killed = pyqtSignal(bool)

    def __init__(self, layer, unlinks, stub_ratio, buffer):
        QObject.__init__(self)
        self.layer, self.unlinks, self.stub_ratio, self.buffer = layer, unlinks, stub_ratio, buffer

        # internal
        self.spIndex = QgsSpatialIndex()
        self.con1 = {}
        self.feats = {}
        self.break_points = {}
        self.pairs_crossing = {}

        self.id = 0
        self.step = 1/self.layer.featureCount()

        # load graph
        res = map(lambda feat: self.spIndex.insertFeature(feat), self.feat_iter(layer))
        self.step = 1/len(res)

        # feats need to be created - after iter
        self.unlink_points = {ml_id: [] for ml_id in self.feats.keys()}
        self.stubs_points = []

        # unlink validity
        if self.unlinks:
            res = map(lambda unlink: self.load_unlink(unlink), unlinks.getFeatures())
            res = map(lambda (k, v): self.load_valid_unlink(k, v), self.pairs_crossing.items())

        del res

    def load_valid_unlink(self, k, v):
        self.unlink_points[k] = v
        return True

    def load_unlink(self, unlink): # TODO self.buffer can be 0,  buffer not allowed in polygons
        unlink_geom = unlink.geometry()
        unlink_geom_buffer = unlink_geom.buffer(self.buffer, 36)
        lines = filter(lambda i: unlink_geom_buffer.intersects(self.feats[i].geometry()),
                       self.spIndex.intersects(unlink_geom_buffer.boundingBox()))
        if unlink_geom.wkbType() == 3:
            unlink_geom = self.feats[lines[0]].geometry().intersection(self.feats[lines[1]].geometry())

        if len(lines) == 2:
            for i in lines:
                try:
                    self.pairs_crossing[i] += [unlink_geom.asPoint()]
                except KeyError:
                    self.pairs_crossing[i] = [unlink_geom.asPoint()]
        else:
            self.invalid_unlinks.append(unlink_geom)
        return True

    # every line explode and find crossings
    def break_segm(self, ml_id, ml_feat):

        self.progress.emit(self.step)

        ml_geom = ml_feat.geometry()
        interlines = filter(lambda i:  ml_geom.intersects(self.feats[i].geometry()), self.spIndex.intersects(ml_geom.boundingBox()))
        cross_p = list(itertools.chain.from_iterable(map(lambda i: load_points(ml_geom.intersection(self.feats[i].geometry())),
                                               interlines)))  # same id intersection is line
        order = map(lambda p: ml_geom.lineLocatePoint(QgsGeometry.fromPoint(p)), cross_p)
        cross_p = [x for _, x in sorted(zip(order, cross_p))]
        expl_p = ml_geom.asPolyline()

        if self.stub_ratio:
            for i in (((0, 0), (-2, -1))):
                end = QgsGeometry.fromPoint(ml_geom.vertexAt(i[1]))
                if len(filter(lambda j: end.intersects(self.feats[j].geometry()), self.spIndex.intersects(end.boundingBox()))) == 1:
                    end_segm = QgsGeometry.fromPolyline([ml_geom.vertexAt(i[0]), ml_geom.vertexAt(i[0]+1)])
                    end_stub = QgsGeometry.fromPolyline([ml_geom.vertexAt(i[0]), cross_p[i[0]]])
                    if end_stub.geometry().length() < 0.4 * end_segm.geometry().length():
                        self.stubs_points.append(ml_geom.vertexAt(i[1]))
                        expl_p.remove(expl_p[i[1]])

        self.break_points[ml_id] = set(cross_p + expl_p).difference(set(self.unlink_points[ml_id]))
        order = map(lambda p: ml_geom.lineLocatePoint(QgsGeometry.fromPoint(p)), self.break_points[ml_id])
        ordered_points = [x for _, x in sorted(zip(order, self.break_points[ml_id]))]
        return map(lambda pair: self.copy_feat(ml_feat, QgsGeometry.fromPolyline(list(pair))), zip(ordered_points[:-1], ordered_points[1:]))

    def segment(self):

        # TODO: if postgis - run function
        # progress emitted by break_segm
        break_features = list(itertools.chain.from_iterable(map(lambda (ml_id, ml_feat): self.break_segm(ml_id, ml_feat), self.feats.items())))

        return break_features, self.break_points, self.invalid_unlinks, self.stubs_points

    def copy_feat(self,f, geom):
        copy_feat = QgsFeature(f)
        copy_feat.setGeometry(geom)
        copy_feat.setFeatureId(self.id)
        # TODO: add ml_id attr
        self.id += 1
        return copy_feat

    # only 1 time execution permitted
    def feat_iter(self, layer):
        id = 0
        for f in layer.getFeatures():
            self.progress.emit(self.step)
            f_geom = f.geometry()
            if self.killed is True:
                break
            elif f_geom.wkbType() == 2:
                f.setFeatureId(id)
                self.feats[id] = f
                id += 1
                yield f
            elif f_geom.wkbType() == 5:
                ml_segms = f_geom.asMultiPolyline()
                for ml in ml_segms:
                    ml_feat = QgsFeature(f)
                    ml_geom = QgsGeometry(ml)
                    ml_feat.setGeometry(ml_geom)
                    ml_feat.setFeatureId(id)
                    self.feats[id] = ml_feat
                    id += 1
                    yield ml_feat