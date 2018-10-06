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
stub_ratio = None
buffer = 0
errors = True
# my_segmentor = segmentor(layer, None, stub_ratio, None)
my_segmentor = segmentor(layer, unlinks, stub_ratio, buffer, errors)

my_segmentor.step = 10 / float(my_segmentor.layer.featureCount())
my_segmentor.load_graph()

break_lines, break_points = my_segmentor.segment()
print 'process time', time.time() - start_time
print 'finished'

segmented = to_layer(break_lines, layer.crs(), layer.dataProvider().encoding(), layer.dataProvider().geometryType(), "shapefile", '/Users/joe/segmented.shp', 'segmented')
QgsMapLayerRegistry.instance().addMapLayer(segmented)
errors = to_layer(break_points, layer.crs(), layer.dataProvider().encoding(), 1, "shapefile", '/Users/joe/errors.shp', 'segmented points')
QgsMapLayerRegistry.instance().addMapLayer(errors)

print 'process time', time.time() - start_time

con_settings = []
settings = QSettings()
settings.beginGroup('/PostgreSQL/connections')
for item in settings.childGroups():
    con = dict()
    con['name'] = unicode(item)
    con['host'] = unicode(settings.value(u'%s/host' % unicode(item)))
    if con['host'] == 'NULL':
        del con['host']
        con['service'] = unicode(settings.value(u'%s/service' % unicode(item)))
    else:
        con['port'] = unicode(settings.value(u'%s/port' % unicode(item)))
        con['database'] = unicode(settings.value(u'%s/database' % unicode(item)))
        con['username'] = unicode(settings.value(u'%s/username' % unicode(item)))
        if con['username'] == 'NULL':
            del con['username']
        con['password'] = unicode(settings.value(u'%s/password' % unicode(item)))
        if con['password'] == 'NULL':
            del con['password']
        con_settings.append(con)



settings.endGroup()
dbs = {}
if len(con_settings) > 0:
    for conn in con_settings:
        dbs[conn['name']] = conn





settings.endGroup()
dbs = {}
if len(con_settings) > 0:
    for conn in con_settings:
        dbs[conn['name']]= conn
return dbs








# old : 1 m 30 s
# now: 1 m 05 s
# PST: 0 m 12 s


