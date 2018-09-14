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
        self.spIndex = QgsSpatialIndex()
        self.nodes = {}
        self.stub_ratio = stub_ratio
        self.buffer = buffer
        self.layer = layer
        self.unlinks = unlinks
        self.feats = {}
        self.id = 0

        # layer featureCount
        self.step = 1/self.layer.featureCount()
        res = map(lambda feat: self.spIndex.insertFeature(feat), self.feat_iter(layer))
        self.step = 1/len(res)
        del res

        # TODO add unlink buffer
        # TODO add if unlinks
        # unlink validity
        self.unlink_points = {i: None for i in self.feats.keys()}
        if self.unlinks:
            if self.buffer:
                res = map(lambda unlink: (unlink, [i for i in self.spIndex.intersects(unlink.geometry().boundingBox()) if unlink.geometry().buffer(self.buffer).intersects(self.feats[i].geometry())]), unlinks.getFeatures())
            else:
                res = map(lambda unlink: (unlink, [i for i in self.spIndex.intersects(unlink.geometry().boundingBox()) if unlink.geometry().intersects(self.feats[i].geometry())]), unlinks.getFeatures())
            all_combs = itertools.chain.from_iterable(map(lambda i: list(itertools.combinations(i, 2)), filter(lambda lines: len(lines) == 2, res)))
            all_combs_1, all_combs_2 = map(lambda i: i[0], all_combs), map(lambda i: i[1], all_combs)
            self.unlink_points.update(dict(zip(all_combs_1, all_combs_2)))
            self.unlink_points.update(dict(zip(all_combs_2, all_combs_1)))
            # TODO unlinks can be polygons
            self.invalid_unlinks = filter(lambda i: len(i[1]) != 2, res)
            del res, all_combs, all_combs_1, all_combs_2

    # every line explode and find crossings
    def expl_n_brk(self, ml_id, ml_feat):

        self.progress.emit(self.step)

        ml_geom = ml_feat.geometry()

        # expl_points
        crossing_points = ml_geom.asPolyline()
        interlines = filter(lambda i: i != ml_feat.id() and ml_geom.intersects(self.feats[i].geometry())
                                                         and i != self.unlink_points[ml_id],
                            self.spIndex.intersects(ml_geom.boundingBox()))
        crossing_points += list(itertools.chain.from_iterable(map(lambda i: load_points(ml_geom.intersection(self.feats[i].geometry())), interlines)))
        # index based on segm
        crossing_points = list(set(crossing_points))
        order = map(lambda p: ml_geom.lineLocatePoint(QgsGeometry.fromPoint(p)), crossing_points)
        crossing_points = [x for _,x in sorted(zip(order,crossing_points))]

        # save crossing points for errors
        broken_feats = map(lambda pair: self.copy_feat(ml_feat, QgsGeometry.fromPolyline(list(pair))),
                           zip(crossing_points[:-1],crossing_points[1:]))

        return broken_feats, crossing_points

    def segment(self):
        # progress emitted by expl_n_brk
        all_segms = map(lambda k: self.expl_n_brk(k[0], k[1]), self.feats.items())
        # filter stubs
        #if self.stub_ratio:
        #    all_broken_feats = map(lambda br_feats: self.check_for_stub(br_feats[0], br_feats[-1]), filter(lambda i: len(i) > 1, all_broken_feats))
        return list(itertools.chain.from_iterable(all_segms))

    def copy_feat(self,f, geom):
        copy_feat = QgsFeature(f)
        copy_feat.setGeometry(geom)
        copy_feat.setFeatureId(self.id)
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
                for i in [f_geom.asPolyline()[0], f_geom.asPolyline()[-1]]:
                    p = (i.x(), i.y())
                    try:
                        self.nodes[p] += 1
                    except KeyError:
                        self.nodes[p] = 1
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
                    for i in [f_geom.asPolyline()[0], f_geom.asPolyline()[-1]]:
                        p = (i.x(), i.y())
                        try:
                            self.nodes[p] += 1
                        except KeyError:
                            self.nodes[p] = 1
                    id += 1
                    yield ml_feat


def load_points(mlp):
    if mlp.wkbType() == 1:
        return [mlp.asPoint()]
    elif mlp.wkbType() == 3:
        return map(lambda m: m.asPoint(), mlp.geometry().asMultiPoint())
    else:
        return []