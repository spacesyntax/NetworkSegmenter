execfile(u'C:/Users/I.Kolovou/Documents/GitHub/NetworkSegmenter/segment_tools.py'.encode('utf-8'))
execfile(u'C:/Users/I.Kolovou/Documents/GitHub/NetworkSegmenter/utilityFunctions.py'.encode('utf-8'))

import time
execfile(u'/Users/joe/NetworkSegmenter/segment_tools.py'.encode('utf-8'))
execfile(u'/Users/joe/NetworkSegmenter/utilityFunctions.py'.encode('utf-8'))

start_time = time.time()
layer = getLayerByName('axial_map_m25')
unlinks = getLayerByName('axial_map_m25_u')
#layer = getLayerByName('merged_mixed_model1')
#unlinks = None
stub_ratio = 0.4
buffer = 0
errors = True
# my_segmentor = segmentor(layer, None, stub_ratio, None)
my_segmentor = segmentor(layer, unlinks, stub_ratio, buffer, errors)

my_segmentor.step = 10 / float(my_segmentor.layer.featureCount())
my_segmentor.load_graph()

break_lines, break_points = my_segmentor.segment()


for f in my_segmentor.list_iter(my_segmentor.feats.values()):
    cross_p = my_segmentor.break_segm(f)

print 'process time', time.time() - start_time
print 'finished'

segmented = to_layer(break_lines, layer.crs(), layer.dataProvider().encoding(), layer.dataProvider().geometryType(), "shapefile", '/Users/joe/segmented.shp', 'segmented')
QgsMapLayerRegistry.instance().addMapLayer(segmented)
errors = to_layer(break_points, layer.crs(), layer.dataProvider().encoding(), 1, "shapefile", '/Users/joe/errors.shp', 'segmented points')
QgsMapLayerRegistry.instance().addMapLayer(errors)

print 'process time', time.time() - start_time


# old : 1 m 54 s = 114
# now: 1 m 29 s = 89 -20%
# PST: 0 m 12 s


