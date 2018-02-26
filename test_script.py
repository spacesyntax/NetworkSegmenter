execfile(u'/Users/joe/NetworkSegmenter/sGraph/segment_tools.py'.encode('utf-8'))
execfile(u'/Users/joe/NetworkSegmenter/sGraph/utilityFunctions.py'.encode('utf-8'))

#execfile(u'C:/Users/I.Kolovou/Documents/GitHub/NetworkSegmenter/sGraph/segment_tools.py'.encode('mbcs'))
#execfile(u'C:/Users/I.Kolovou/Documents/GitHub/NetworkSegmenter/sGraph/utilityFunctions.py'.encode('mbcs'))
layer_name = 'axial_map_m25'

import datetime

layer_name = 'invalid'
unlinks_layer_name = 'unlinks'
path = None
layer = getLayerByName(layer_name)
crs = layer.dataProvider().crs()
encoding = layer.dataProvider().encoding()
geom_type = layer.dataProvider().geometryType()

unlinks_layer = getLayerByName(unlinks_layer_name)
flds = getQFields(layer)
explodedGraph = segmentTool(flds)
print datetime.datetime.now().time()
explodedGraph.addedges(layer)
print datetime.datetime.now().time()

print datetime.datetime.now().time()
segments, breakages = explodedGraph.break_features(40, True, unlinks_layer, None) #todo test buffer_threshold
print datetime.datetime.now().time()

expl = to_shp(path, [sedge.qgsFeat() for sedge in explodedGraph.sEdges.values()], explodedGraph.sEdgesFields, crs, 'expl', encoding, geom_type)
QgsMapLayerRegistry.instance().addMapLayer(expl)

segmented = to_shp(path, [segm.qgsFeat() for segm in segments], explodedGraph.sEdgesFields, crs, 'segmented', encoding, geom_type)
QgsMapLayerRegistry.instance().addMapLayer(segmented)

# TODO: fix stubs





to_dblayer('geodb', 'postgres', '192.168.1.10', '5432', 'spaces2017', 'gbr_exeter', 'cleaned',  br.layer_fields, result, crs)

final = to_shp(path, result, fields, crs, 'f', encoding, geom_type )
QgsMapLayerRegistry.instance().addMapLayer(final)


layer = iface.mapCanvas().currentLayer()
qgs_flds = [QgsField(i.name(), i.type()) for i in layer.dataProvider().fields()]
postgis_flds = qgs_to_postgis_fields(qgs_flds, arrays = False)



