import itertools
from PyQt4.QtCore import QObject, pyqtSignal, QVariant
from qgis.core import QgsSpatialIndex, QgsGeometry, QgsDistanceArea, QgsFeature, QgsField, QgsFields
import traceback

# read graph - as feat
class segmentor(QObject):

    finished = pyqtSignal(object)
    error = pyqtSignal(Exception, basestring)
    progress = pyqtSignal(float)
    warning = pyqtSignal(str)
    killed = pyqtSignal(bool)

    def __init__(self, layer, unlinks, stub_ratio, buffer, errors):
        QObject.__init__(self)
        self.layer, self.unlinks, self.stub_ratio, self.buffer, self.errors = layer, unlinks, stub_ratio, buffer, errors

        # internal
        self.spIndex = QgsSpatialIndex()
        self.feats = {}
        self.stubs = []
        self.cross_points = []
        self.connectivity = {}
        self.invalid_unlinks = []
        self.stubs_points = []

        self.id = -1

    def load_graph(self):

        # load graph
        res = map(lambda feat: self.spIndex.insertFeature(feat), self.feat_iter(self.layer))
        self.step = 70/float(len(res))

        # feats need to be created - after iter
        self.unlinks_points = {ml_id: [] for ml_id in self.feats.keys()}

        # unlink validity
        if self.unlinks:
            res = map(lambda unlink: self.load_unlink(unlink), self.unlinks.getFeatures())
        del res
        return

    def load_unlink(self, unlink): # TODO buffer not allowed in polygons

        unlink_geom = unlink.geometry()
        if self.buffer:
            unlink_geom = unlink_geom.buffer(self.buffer, 36)
        lines = filter(lambda i: unlink_geom.intersects(self.feats[i].geometry()),
                       self.spIndex.intersects(unlink_geom.boundingBox()))
        if unlink_geom.wkbType() == 3:
            unlink_geom = self.feats[lines[0]].geometry().intersection(self.feats[lines[1]].geometry())
        if len(lines) == 2:
            self.unlinks_points[lines[0]].append(lines[1]) #TODO: what if line unlinked by one line in two points?
            self.unlinks_points[lines[1]].append(lines[0])
        else:
            self.invalid_unlinks.append(unlink_geom.asPoint())
        return True

    # for every line explode and crossings
    def point_iter(self, interlines, ml_geom):
        for line in interlines:
            inter = ml_geom.intersection(self.feats[line].geometry())
            if inter.wkbType() == 1:
                yield ml_geom.lineLocatePoint(inter), inter.asPoint()
            elif inter.wkbType() == 4:
                for i in inter.geometry().asMultiPoint():
                    yield ml_geom.lineLocatePoint(QgsGeometry.fromPoint(i)), i
        for p in ml_geom.asPolyline():
            yield ml_geom.lineLocatePoint(QgsGeometry.fromPoint(p)), p

    def break_segm(self, feat):

        f_geom = feat.geometry()
        inter_lines = filter(lambda line: feat.geometry().distance(self.feats[line].geometry()) <= 0,
                             self.spIndex.intersects(f_geom.boundingBox()))
        inter_lines = (set(inter_lines) - set(self.unlinks_points[feat.id()]))
        cross_p = [p for (factor, p) in sorted(set(self.point_iter(inter_lines, f_geom)))]

        if self.stub_ratio:
            cross_p = map(lambda p: p, self.stubs_clean_iter(cross_p, f_geom.asPolyline()))

        return cross_p

    def break_feats_iter(self, cross_p_list):
        self.total_progress = 80
        for idx, cross_p in enumerate(cross_p_list):
            if self.killed is True:
                break
            self.total_progress += self.step
            self.progress.emit(self.total_progress)

            for pair in zip(cross_p[:-1], cross_p[1:]):
                feat = self.feats[idx]
                self.id += 1
                yield feat, QgsGeometry.fromPolyline(list(pair)), self.id

    def list_iter(self, any_list):
        self.total_progress = 10
        for item in any_list:
            if self.killed is True:
                break
            self.total_progress += self.step
            self.progress.emit(self.total_progress)

            yield item

    def segment(self):

        break_point_feats, invalid_unlink_point_feats, stubs_point_feats, segmented_feats = [], [], [], []

        try:
            # TODO: if postgis - run function
            self.step = 10 / float(self.layer.featureCount())
            self.load_graph()
            # progress emitted by break_segm & break_feats_iter
            cross_p_list = map(lambda feat: self.break_segm(feat), self.list_iter(self.feats.values()))
            self.step = 20/float(len(cross_p_list))
            segmented_feats = map(lambda (feat, geom, fid): self.copy_feat(feat, geom, fid), self.break_feats_iter(cross_p_list))

            if self.errors:
                break_f = QgsFeature()
                fields = QgsFields()
                fields.append(QgsField('type', QVariant.String))
                break_f.initAttributes(1)
                break_f.setFields(fields)
                break_f.setAttributes(['break point'])
                break_f.setGeometry(QgsGeometry())

                invalid_unlink_f = QgsFeature()
                invalid_unlink_f.initAttributes(1)
                invalid_unlink_f.setFields(fields)
                invalid_unlink_f.setAttributes(['invalid unlink'])
                invalid_unlink_f.setGeometry(QgsGeometry())

                stub_f = QgsFeature()
                stub_f.initAttributes(1)
                stub_f.setFields(fields)
                stub_f.setAttributes(['stub'])
                stub_f.setGeometry(QgsGeometry())

                cross_p_list = set(list(itertools.chain.from_iterable(cross_p_list)))

                ids1 = [i for i in range(0, len(cross_p_list))]
                break_point_feats = map(lambda (p, fid) : self.copy_feat(break_f, QgsGeometry.fromPoint(p), fid), (zip(cross_p_list, ids1)))
                ids2 = [i for i in range(max(ids1) + 1, max(ids1) + 1 + len(self.invalid_unlinks))]
                invalid_unlink_point_feats = map(lambda (p, fid) : self.copy_feat(invalid_unlink_f, QgsGeometry.fromPoint(p), fid), (zip(self.invalid_unlinks, ids2)))
                ids = [i for i in range(max(ids1 + ids2) + 1, max(ids1 + ids2) + 1 + len(self.stubs))]
                stubs_point_feats = map(lambda (p, fid): self.copy_feat(stub_f, QgsGeometry.fromPoint(p), fid), (zip(self.stubs, ids)))

        except Exception, exc:
            print exc, traceback.format_exc()

        return segmented_feats, break_point_feats + invalid_unlink_point_feats + stubs_point_feats

    def stubs_clean_iter(self, cross_p, f_pl):
        for pnt in cross_p[:1]:
            if QgsDistanceArea().measureLine(pnt, cross_p[1])/ QgsDistanceArea().measureLine(pnt, f_pl[1]) > 0.4:
                yield pnt
            elif self.connectivity[(pnt.x(), pnt.y())] == 1:
                pass
            else:
                yield pnt
        for pnt in cross_p[1:-1]:
            yield pnt
        for pnt in cross_p[-1:]:
            if QgsDistanceArea().measureLine(pnt, cross_p[-2])/ QgsDistanceArea().measureLine(pnt, f_pl[-2]) > 0.4:
                yield pnt
            elif self.connectivity[(pnt.x(), pnt.y())] == 1:
                pass
            else:
                yield pnt

    def copy_feat(self,f, geom, id):
        copy_feat = QgsFeature(f)
        copy_feat.setGeometry(geom)
        copy_feat.setFeatureId(id)
        return copy_feat

    # only 1 time execution permitted
    def feat_iter(self, layer):
        id = 0
        self.total_progress = 0

        for f in layer.getFeatures():

            self.total_progress += self.step
            self.progress.emit(self.total_progress)

            f_geom = f.geometry()
            if self.killed is True:
                break
            elif f_geom.length() == 0:
                pass
            elif f_geom.wkbType() == 2:
                f.setFeatureId(id)
                self.feats[id] = f
                id += 1
                f_pl = f_geom.asPolyline()
                try:
                    self.connectivity[(f_pl[0].x(), f_pl[0].y())] += 1
                except KeyError:
                    self.connectivity[(f_pl[0].x(), f_pl[0].y())] = 1
                try:
                    self.connectivity[(f_pl[-1].x(), f_pl[-1].y())] += 1
                except KeyError:
                    self.connectivity[(f_pl[-1].x(), f_pl[-1].y())] = 1
                yield f
            elif f_geom.wkbType() == 5:
                ml_segms = f_geom.asMultiPolyline()
                for ml in ml_segms:
                    ml_geom = QgsGeometry(ml)
                    ml_feat = self.copy_feat(f, ml_geom, id)
                    self.feats[id] = ml_feat
                    id += 1
                    f_pl = ml_feat.asPolyline()
                    try:
                        self.connectivity[(f_pl[0].x(), f_pl[0].y())] += 1
                    except KeyError:
                        self.connectivity[(f_pl[0].x(), f_pl[0].y())] = 1
                    try:
                        self.connectivity[(f_pl[-1].x(), f_pl[-1].y())] += 1
                    except KeyError:
                        self.connectivity[(f_pl[-1].x(), f_pl[-1].y())] = 1
                    yield ml_feat

    def kill(self):
        self.killed = True