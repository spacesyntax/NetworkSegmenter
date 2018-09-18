execfile(u'C:/Users/I.Kolovou/Documents/GitHub/NetworkSegmenter/new_method.py'.encode('utf-8'))
execfile(u'C:/Users/I.Kolovou/Documents/GitHub/NetworkSegmenter/utilityFunctions.py'.encode('utf-8'))


execfile(u'/Users/joe/NetworkSegmenter/new_method.py'.encode('utf-8'))
execfile(u'/Users/joe/NetworkSegmenter/utilityFunctions.py'.encode('utf-8'))

layer = getLayerByName('axial_map_m25')
unlinks = getLayerByName('axial_map_m25_u')
stub_ratio = 0.4
buffer = 0
# my_segmentor = segmentor(layer, None, stub_ratio, None)
my_segmentor = segmentor(layer, unlinks, None, buffer)

my_segmentor.unlink_points.items()[0:10]

maxlen = 0
for k, v in my_segmentor.unlink_points.items():
    if len(v) > maxlen:
        v
        maxlen = len(v)


maxlen


connstring = "service=%s" % ('uk')



br = my_segmentor.segment()
to_layer(br, layer.crs(), layer.dataProvider().encoding(), layer.dataProvider().geometryType(), "shapefile", '/Users/joe/segmented.shp', 'segmented')

# old : 1 m 30 s
# now: 1 m 05 s

for ml_id, ml_feat in my_segmentor.feats.items():
    break

my_segmentor.break_segm(ml_id, ml_feat)
