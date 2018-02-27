execfile(u'C:/Users/I.Kolovou/Documents/GitHub/NetworkSegmenter/segment_tools.py'.encode('mbcs'))
execfile(u'C:/Users/I.Kolovou/Documents/GitHub/NetworkSegmenter/utilityFunctions.py'.encode('mbcs'))
layer_name = 'axial_map_m25'
import time
start = time.time()
segment_dict = {}
segment_index = QgsSpatialIndex()
# Loop through network features
index = 1
layer = getLayerByName(layer_name)

for f in layer.getFeatures():
    geom = f.geometry()
    segments = list(segm_from_pl_iter(geom))
    # Write segments to index and dictionary
    for segment in segments:
        f = QgsFeature()
        f.setFeatureId(index)
        f.setGeometry(segment)
        segment_index.insertFeature(f)
        segment_dict[index] = {'geom': segment}
        index += 1



end = time.time()
print 'time:', (end - start)


############################
start = time.time()
for f in layer.getFeatures():
    #f_geom = f.geometry()
    f_attrs = f.attributes()
    #pass

end = time.time()
print 'time:', (end - start)






##############################
import timeit

# Test 1
test = """
my_list = []
for i in xrange(50):
    my_list.append(0)
"""
timeit(test)


# Test 2
test = """
my_list = []
for i in xrange(50):
    my_list += [0]
"""

timeit(test)