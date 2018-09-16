
execfile(u'/Users/joe/NetworkSegmenter/new_method.py'.encode('utf-8'))
execfile(u'/Users/joe/NetworkSegmenter/utilityFunctions.py'.encode('utf-8'))

layer = getLayerByName('axial_map_m25')
unlinks = getLayerByName('axial_map_m25_u')
stub_ratio = 0.4
buffer = 0
# my_segmentor = segmentor(layer, None, stub_ratio, None)
my_segmentor = segmentor(layer, unlinks, stub_ratio, buffer)

my_segmentor.unlink_points.items()[0:10]

maxlen = 0
for k, v in my_segmentor.unlink_points.items():
    if len(v) > maxlen:
        maxlen = len(v)


maxlen





br = my_segmentor.segment()

# old : 1 m 30 s
# now: 1 m 05 s

for ml_id, ml_feat in my_segmentor.feats.items():
    break


ml_geom = ml_feat.geometry()
interlines = filter(lambda i:  ml_geom.intersects(my_segmentor.feats[i].geometry()), my_segmentor.spIndex.intersects(ml_geom.boundingBox()))
cross_p = list(itertools.chain.from_iterable(map(lambda i: load_points(ml_geom.intersection(my_segmentor.feats[i].geometry())),
                                       interlines)))  # same id intersection is line
expl_p = ml_geom.asPolyline()

if my_segmentor.stub_ratio:

for i in (((0, 0), (-2, -1))):
    end = QgsGeometry.fromPoint(ml_geom.vertexAt(i[1]))
    if len(filter(lambda j: end.intersects(my_segmentor.feats[j].geometry()), my_segmentor.spIndex.intersects(end.boundingBox()))) == 1:
        end_segm = QgsGeometry.fromPolyline([ml_geom.vertexAt(i[0]), ml_geom.vertexAt(i[0] + 1)])
        end_stub = QgsGeometry.fromPolyline([ml_geom.vertexAt(i[0]), ml_geom.vertexAt(i[0] + 1)])
        if end_stub.geometry().length() < 0.4 * end_segm.geometry().length():
            print 'a'


                my_segmentor.stubs_points.append(ml_geom.vertexAt(i[1]))
                expl_p.remove(expl_p[i[1]])

self.break_points[ml_id] = set(cross_p + expl_p).difference(set(self.unlink_points[ml_id]))
order = map(lambda p: ml_geom.lineLocatePoint(QgsGeometry.fromPoint(p)), self.break_points[ml_id])
ordered_points = [x for _, x in sorted(zip(order, self.break_points[ml_id]))]
map(lambda pair: self.copy_feat(ml_feat, QgsGeometry.fromPolyline(list(pair))), zip(ordered_points[:-1], ordered_points[1:]))