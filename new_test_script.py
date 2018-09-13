import itertools

spIndex = QgsSpatialIndex()
stub_ratio = 0.4
layer = iface.mapCanvas().currentLayer()
feats = {}
id = 0

def feat_iter(layer):
    id = 0
    for f in layer.getFeatures():
        f_geom = f.geometry()
        if f_geom.wkbType() == 2:
            f.setFeatureId(id)
            feats[id] = f
            id += 1
            yield f
        elif f_geom.wkbType() == 5:
            ml_segms = f_geom.asMultiPolyline()
            for ml in ml_segms:
                ml_feat = QgsFeature(f)
                ml_geom = QgsGeometry(ml)
                ml_feat.setGeometry(ml_geom)
                ml_feat.setFeatureId(id)
                feats[id] = ml_feat
                id += 1
                yield ml_feat


res = map(lambda feat: spIndex.insertFeature(feat), feat_iter(layer))


for ml_feat in feat_iter(layer):
    break


ml_geom = ml_feat.geometry()

expl_points = ml_geom.asPolyline()
segms_geoms = [QgsGeometry.fromPolyline([i[0], i[1]]) for i in zip(expl_points[:-1], expl_points[1:])]  # start and end added

[i for i in spIndex.intersects(ml_geom.boundingBox()) if i!= ml_feat.id()]

[ feats[i].attributes()[0] for i in [i for i in spIndex.intersects(ml_geom.boundingBox()) if i!= ml_feat.id()] and ml_geom.intersects(feats[i].geometry())]

for i in spIndex.intersects(ml_geom.boundingBox()):
    ml_geom.intersects(feats[i].geometry())

crossing_points = filter(lambda inter: inter.wkbType() in [1, 3], [ml_geom.intersection(feats[i].geometry()) for i in spIndex.intersects(ml_geom.boundingBox()) if i!= ml_feat.id() and ml_geom.intersects(feats[i].geometry())])


def copy_feat(f, geom):
    copy_feat = QgsFeature(f)
    copy_feat.setGeometry(geom)
    copy_feat.setFeatureId(id)
    id += 1
    return copy_feat

# TODO: multipoint? - with iter before
# index based on segm
break_points = list(set(crossing_points + [QgsGeometry.fromPoint(p) for p in expl_points]))
# TODO: if len(crossing_points) == 2: copy
order = [ml_geom.lineLocatePoint(p) for p in break_points]
break_points = [x for _,x in sorted(zip(order,break_points))]
break_points = zip(break_points[:-1],break_points[1:])
broken_feats = map(lambda pair: copy_feat(ml_feat, QgsGeometry.fromPolyline([i.asPoint() for i in pair])), break_points)

stubs = [[0, broken_feats[0]], [-1, broken_feats[-1]]]
stubs = filter(lambda stub: stub[1].geometry().length < (stub_ratio * segms_geoms[stub[0]].length()), stubs)
# touches
end_points = [QgsGeometry.fromPoint(expl_points[0]), QgsGeometry.fromPoint(expl_points[-1])]
stubs = filter(lambda stub : len(filter(lambda i: end_points[stub[0]].intersects(i) and i!= ml_feat.id() , spIndex.intersects(stub[1].geometry()))) > 0 , stubs)
broken_feats -= stubs