
execfile(u'/Users/joe/NetworkSegmenter/sGraph/segment_tools.py'.encode('utf-8'))
execfile(u'/Users/joe/NetworkSegmenter/sGraph/utilityFunctions.py'.encode('utf-8'))

# _________________________ TRANSFORMATIONS ______________________________


layer_name = 'invalid'
unlinks_layer_name = 'p'
# cleaning settings
path = None

# project settings
layer = getLayerByName(layer_name)
crs = layer.dataProvider().crs()
encoding = layer.dataProvider().encoding()
geom_type = layer.dataProvider().geometryType()

unlinks_layer = getLayerByName(unlinks_layer_name)
flds = getQFields(layer)
explodedGraph = segmentTool(flds)
explodedGraph.addedges(layer)

#explodedGraph.prepare_unlinks(unlinks_layer, 0) #todo buffer_threshold

segments, breakages = explodedGraph.break_features(40, True)

segmented = to_shp(path, [segm.qgsFeat() for segm in segments], explodedGraph.sEdgesFields, crs, 'segmented', encoding, geom_type)
QgsMapLayerRegistry.instance().addMapLayer(segmented)


# TODO: fix stubs, fix unlinks





to_dblayer('geodb', 'postgres', '192.168.1.10', '5432', 'spaces2017', 'gbr_exeter', 'cleaned',  br.layer_fields, result, crs)

final = to_shp(path, result, fields, crs, 'f', encoding, geom_type )
QgsMapLayerRegistry.instance().addMapLayer(final)


layer = iface.mapCanvas().currentLayer()
qgs_flds = [QgsField(i.name(), i.type()) for i in layer.dataProvider().fields()]
postgis_flds = qgs_to_postgis_fields(qgs_flds, arrays = False)



