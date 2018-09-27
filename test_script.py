execfile(u'C:/Users/I.Kolovou/Documents/GitHub/NetworkSegmenter/segment_tools.py'.encode('utf-8'))
execfile(u'C:/Users/I.Kolovou/Documents/GitHub/NetworkSegmenter/utilityFunctions.py'.encode('utf-8'))

import time
execfile(u'/Users/joe/NetworkSegmenter/segment_tools.py'.encode('utf-8'))
execfile(u'/Users/joe/NetworkSegmenter/utilityFunctions.py'.encode('utf-8'))

start_time = time.time()
layer = getLayerByName('axial_map_m25')
unlinks = getLayerByName('axial_map_m25_u')
stub_ratio = 0.4
buffer = 0
errors = True
# my_segmentor = segmentor(layer, None, stub_ratio, None)
my_segmentor = segmentor(layer, unlinks, stub_ratio, buffer, errors)
my_segmentor.load_graph()

start_time = time.time()
break_lines, break_points = my_segmentor.segment()
print 'process time', time.time() - start_time

segmented = to_layer(break_lines, layer.crs(), layer.dataProvider().encoding(), layer.dataProvider().geometryType(), "shapefile", '/Users/joe/merged_mixed_model1_seg.shp', 'merged_mixed_model1_seg')
QgsMapLayerRegistry.instance().addMapLayer(segmented)
errors = to_layer(break_points, layer.crs(), layer.dataProvider().encoding(), 1, "shapefile", '/Users/joe/merged_mixed_model1_seg_errors.shp', 'merged_mixed_model1_seg_errors')
QgsMapLayerRegistry.instance().addMapLayer(errors)

print 'process time', time.time() - start_time



for layer in QgsMapLayerRegistry.instance().mapLayers().values():
    layer.loadNamedStyle('path/to/qml/file')




# old : 1 m 30 s
# now: 1 m 05 s
# PST: 0 m 12 s


