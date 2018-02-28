#execfile(u'/Users/joe/NetworkSegmenter/segment_tools.py'.encode('utf-8'))
#execfile(u'/Users/joe/NetworkSegmenter/utilityFunctions.py'.encode('utf-8'))

execfile(u'C:/Users/I.Kolovou/Documents/GitHub/NetworkSegmenter/segment_tools.py'.encode('mbcs'))
execfile(u'C:/Users/I.Kolovou/Documents/GitHub/NetworkSegmenter/utilityFunctions.py'.encode('mbcs'))
layer_name = 'axial_map_m25_small'

import time

#layer_name = 'invalid'
unlinks_layer_name = 'axial_map_m25_u'
path = None
layer = getLayerByName(layer_name)
crs = layer.dataProvider().crs()
encoding = layer.dataProvider().encoding()
geom_type = layer.dataProvider().geometryType()

unlinks_layer = getLayerByName(unlinks_layer_name)
flds = getQFields(layer)
explodedGraph = segmentTool(flds)

start = time.time()
explodedGraph.addedges(layer)

end = time.time()
print 'Graph build', end - start

start = time.time()
segments, breakages = explodedGraph.break_features(40, True, unlinks_layer, None) #todo test buffer_threshold
end = time.time()
print 'Graph explode', end - start

#expl = to_shp(path, [sedge.qgsFeat() for sedge in explodedGraph.sEdges.values()], explodedGraph.sEdgesFields, crs, 'expl', encoding, geom_type)
#QgsMapLayerRegistry.instance().addMapLayer(expl)

segmented = to_shp(path, segments, explodedGraph.sEdgesFields, crs, 'segmented', encoding, geom_type)
QgsMapLayerRegistry.instance().addMapLayer(segmented)

























to_dblayer('geodb', 'postgres', '192.168.1.10', '5432', 'spaces2017', 'gbr_exeter', 'cleaned',  br.layer_fields, result, crs)

final = to_shp(path, result, fields, crs, 'f', encoding, geom_type )
QgsMapLayerRegistry.instance().addMapLayer(final)


layer = iface.mapCanvas().currentLayer()
qgs_flds = [QgsField(i.name(), i.type()) for i in layer.dataProvider().fields()]
postgis_flds = qgs_to_postgis_fields(qgs_flds, arrays = False)



