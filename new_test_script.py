execfile(u'C:/Users/I.Kolovou/Documents/GitHub/NetworkSegmenter/new_method.py'.encode('utf-8'))
execfile(u'C:/Users/I.Kolovou/Documents/GitHub/NetworkSegmenter/utilityFunctions.py'.encode('utf-8'))

import time
execfile(u'/Users/joe/NetworkSegmenter/new_method.py'.encode('utf-8'))
execfile(u'/Users/joe/NetworkSegmenter/utilityFunctions.py'.encode('utf-8'))

start_time = time.time()
layer = getLayerByName('axial_map_m25')
unlinks = getLayerByName('axial_map_m25_u')
stub_ratio = 0.4
buffer = 0
# my_segmentor = segmentor(layer, None, stub_ratio, None)
my_segmentor = segmentor(layer, unlinks, stub_ratio, buffer)

br, cross_p, invalid_unlinks, stubs  = my_segmentor.segment()
print 'process time', time.time() - start_time

segmented = to_layer(br, layer.crs(), layer.dataProvider().encoding(), layer.dataProvider().geometryType(), "shapefile", '/Users/joe/segmented.shp', 'segmented')
QgsMapLayerRegistry.instance().addMapLayer(segmented)
print 'process time', time.time() - start_time



# old : 1 m 30 s
# now: 1 m 05 s
# PST: 0 m 12 s


