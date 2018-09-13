# read graph - as feat
class segmentor(QObject):

    finished = pyqtSignal(object)
    error = pyqtSignal(Exception, basestring)
    progress = pyqtSignal(float)
    warning = pyqtSignal(str)
    killed = pyqtSignal(bool)

    def __init__(self, layer, stub_ratio):
        QObject.__init__(self)
        self.spIndex = QgsSpatialIndex()
        self.stub_ratio = stub_ratio
        self.layer = layer
        self.feats = {}
        self.id = 0
        res = map(lambda feat: self.spIndex.insertFeature(feat), self.feat_iter(layer))
        self.length = len(res)
        del res

    # every line explode and find crossings
    def expl_n_brk(self, ml_feat):

        self.progress.emit()
        ml_geom = ml_feat.geometry()

        expl_points = ml_geom.asPolyline()
        segms_geoms = [QgsGeometry.fromPolyline([i[0], i[1]]) for i in zip(expl_points[:-2], expl_points[1:])]  # start and end added
        interlines = [ml_geom.intersection(self.feats[i].geometry()) for i in self.spIndex.intersects(ml_geom.boundingBox()) if i!= ml_feat.id() and ml_geom.intersects(self.feats[i].geometry())]
        crossing_points = filter(lambda inter: inter.wkbType() in [1, 3], interlines)
        # index based on segm
        crossing_points = list(set(crossing_points + expl_points))
        order = [ml_geom.lineLocatePoint(p) for p in crossing_points]
        crossing_points = [x for _,x in sorted(zip(order,crossing_points))]
        crossing_points = zip(crossing_points[:-2],crossing_points[1:])
        broken_feats = map(lambda pair: self.copy_feat(ml_feat, QgsGeometry.fromPolyline(pair)), crossing_points)

        stubs = [[0, broken_feats[0]], [-1, broken_feats[-1]]]
        stubs = filter(lambda stub: stub[1].geometry().length < (self.stub_ratio * segms_geoms[stub[0]].length()), stubs)
        # touches/crosses?
        # stubs = filter(lambda stub: )
        broken_feats -= stubs
        return broken_feats

    def segment(self):
        res = map(lambda ml_feat: self.expl_n_brk(ml_feat), self.feat_iter(self.layer))
        return res

    def copy_feat(self,f, geom):
        copy_feat = QgsFeature(f)
        copy_feat.setGeometry(geom)
        copy_feat.setFeautreId(self.id)
        self.id += 1
        return copy_feat

    def feat_iter(self, layer):
        id = 0
        for f in layer.getFeatures():

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

