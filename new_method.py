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
        self.break_feats = []
        self.unlinks_points = {}

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
        del res

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
                    self.unlinks_points[i[0]].append(i[1])
                except KeyError:
                    self.unlinks_points[i[0]] = [i[1]]
        else:
            self.invalid_unlinks.append(unlink_geom)
        return True

    # every line explode and find crossings
    def break_segm(self, ml_id, ml_feat):

        self.progress.emit(self.step)

        ml_geom = ml_feat.geometry()
        interlines = filter(lambda i:  ml_geom.intersects(self.feats[i].geometry()), self.spIndex.intersects(ml_geom.boundingBox()) - self.unlinks_points[ml_id])
        cross_p = sorted(map(lambda i: (ml_geom.lineLocatePoint(i), i.asPoint()), self.load_point_iter(interlines, ml_geom)))  # same id intersection is line
        cross_p = zip(*cross_p)[1]
        break_feats = map(lambda pair: self.copy_feat(ml_feat, QgsGeometry.fromPolyline(list(pair))), zip(cross_p[:-1], cross_p[1:]))
        end_segms = [QgsGeometry.fromPolyline([cross_p[0], ml_geom.vertexAt(1)]), QgsGeometry.fromPolyline([ml_geom.vertexAt(-2), cross_p[-1]])]
        return break_feats, cross_p, end_segms

    def load_point_iter(self, interlines, ml_geom):
        for line in interlines:
            inter = ml_geom.intersection(self.feats[line].geometry())
            if inter.wkbType() == 1:
                yield inter
            elif inter.wkbType() == 4:
                for i in inter.geometry().asMultiPoint():
                    yield i
        for p in ml_geom.asPolyline():
            yield p

    def segment(self):

        # TODO: if postgis - run function
        # progress emitted by break_segm
        res = map(lambda (ml_id, ml_feat): self.break_segm(ml_id, ml_feat), self.feats.items())

        # exclude stubs
        if self.stub_ratio:
            res = map(lambda (break_feats, cross_p, end_segms): clean_stubs(), res)
            # return break_feats, cross_p, stubs

        return res #, self.break_points, self.invalid_unlinks, self.stubs_points

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