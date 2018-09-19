import itertools
from PyQt4.QtCore import QObject, pyqtSignal, QVariant

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

        self.id = 0
        self.step = 1/self.layer.featureCount()

        # load graph
        res = map(lambda feat: self.spIndex.insertFeature(feat), self.feat_iter(layer))
        self.step = 1/len(res)

        # feats need to be created - after iter
        self.unlinks_points = {ml_id: [] for ml_id in self.feats.keys()}
        self.invalid_unlinks = []
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
            self.unlinks_points[lines[0]].append(lines[1])
            self.unlinks_points[lines[1]].append(lines[0])
        else:
            self.invalid_unlinks.append(unlink_geom)
        return True

    # for every line explode and crossings
    def point_iter(self, interlines, ml_geom):
        for line in interlines:
            inter = ml_geom.intersection(self.feats[line].geometry())
            if inter.wkbType() == 1:
                yield  ml_geom.lineLocatePoint(inter), inter.asPoint()
            elif inter.wkbType() == 4:
                for i in inter.geometry().asMultiPoint():
                    yield i.lineLocatePoint(inter), i
        for p in ml_geom.asPolyline():
            yield ml_geom.lineLocatePoint(QgsGeometry.fromPoint(p)), p

    def segment(self):

        # TODO: if postgis - run function
        # progress emitted by break_segm ??

        interlines_list = map(lambda feat: (feat, self.spIndex.intersects(feat.geometry().boundingBox())), self.feats.values())
        interlines_list = map(lambda (feat, interlines): (feat, filter(lambda line: feat.geometry().distance(self.feats[line].geometry()) <= 0, interlines)),
                              interlines_list)
        interlines_list = map(lambda (feat, interlines): (feat, (set(interlines) - set(self.unlinks_points[feat.id()]))), interlines_list)
        cross_p_list = map(lambda (feat, interlines): (feat, [p for (factor, p) in sorted(set(self.point_iter(interlines, feat.geometry())))]), interlines_list)

        # exclude stubs
        self.stubs = []
        if self.stub_ratio:
            cross_p_list =  map(lambda (start, end, cross_p, feat): (feat, cross_p[start:end]), self.stubs_iter(cross_p_list))

        break_feats = map(lambda (feat, cross_p): [self.copy_feat(feat, QgsGeometry.fromPolyline(list(pair))) for pair in zip(cross_p[:-1], cross_p[1:])], cross_p_list)

        return list(itertools.chain.from_iterable(break_feats)), list(itertools.chain.from_iterable(cross_p_list)), self.invalid_unlinks, self.stubs

    def stubs_iter(self, cross_p_list):
        for feat, cross_p in cross_p_list:
            f_geom = feat.geometry()
            start, end = 0, len(cross_p)
            start_p, end_p = f_geom.asPolyline()[0], f_geom.asPolyline()[-1]
            start_geom, end_geom = QgsGeometry.fromPoint(start_p), QgsGeometry.fromPoint(end_p)
            if QgsDistanceArea().measureLine(start_p, cross_p[1])/ QgsDistanceArea().measureLine(start_p, f_geom.asPolyline()[1]) <= 0.4 \
                    and len(filter(lambda line: self.feats[line].geometry().distance(start_geom) <= 0 , self.spIndex.intersects(start_geom.boundingBox()))) == 1:
                start += 1
                self.stubs.append(cross_p[0])
            if QgsDistanceArea().measureLine(end_p, cross_p[-2])/ QgsDistanceArea().measureLine(f_geom.asPolyline()[-2], end_p) <= 0.4 \
                    and len(filter(lambda line: self.feats[line].geometry().distance(end_geom) <= 0 , self.spIndex.intersects(end_geom.boundingBox()))) == 1:
                end += (-1)
                self.stubs.append(cross_p[-1])
            yield start, end, cross_p, feat

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
    def kill(self):
        self.killed = True