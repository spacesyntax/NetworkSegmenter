execfile(u'/Users/joe/NetworkSegmenter/segment_tools_ss.py'.encode('utf-8'))
execfile(u'/Users/joe/NetworkSegmenter/utilityFunctions.py'.encode('utf-8'))
execfile(u'/Users/joe/NetworkSegmenter/sEdge.py'.encode('utf-8'))
#execfile(u'C:/Users/I.Kolovou/Documents/GitHub/NetworkSegmenter/segment_tools_ss.py'.encode('mbcs'))
#execfile(u'C:/Users/I.Kolovou/Documents/GitHub/NetworkSegmenter/utilityFunctions.py'.encode('mbcs'))
layer_name = 'axial_map_m25'

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

explGraph = sGraph(flds)

start = time.time()
explGraph.addexpledges(explGraph.iter_from_layer(layer), layer.featureCount())
end = time.time()
print 'Graph build', end - start

len(explGraph.sEdges)

exploded_layer = to_shp(path, map(lambda sedge: sedge.qgsFeat(), explGraph.sEdges.values()), explGraph.sEdgesFields, crs, 'exploded layer', encoding, geom_type)
QgsMapLayerRegistry.instance().addMapLayer(exploded_layer)

explGraph.getBreakPoints = True
explGraph.stub_ratio = 40
explGraph.hasunlinks = True

#for i in explGraph.sEdges.values():
#    break

# explGraph.generatesegments(i)

start = time.time()
segments, breakages = explGraph.segmentedges(unlinks_layer, None) #todo test buffer_threshold
end = time.time()
print 'Graph explode', end - start

import itertools
segmented = to_layer(path, list(itertools.chain.from_iterable(segments)), explGraph.sEdgesFields, crs, 'segmented', encoding, geom_type)
QgsMapLayerRegistry.instance().addMapLayer(segmented)

























to_dblayer('geodb', 'postgres', '192.168.1.10', '5432', 'spaces2017', 'gbr_exeter', 'cleaned',  br.layer_fields, result, crs)

final = to_shp(path, result, fields, crs, 'f', encoding, geom_type )
QgsMapLayerRegistry.instance().addMapLayer(final)


layer = iface.mapCanvas().currentLayer()
qgs_flds = [QgsField(i.name(), i.type()) for i in layer.dataProvider().fields()]
postgis_flds = qgs_to_postgis_fields(qgs_flds, arrays = False)



