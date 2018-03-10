
import time

layer = iface.mapCanvas().currentLayer()

############################
start = time.time()
for f in layer.getFeatures():
    pass

end = time.time()
print 'TEST 1 time:', (end - start)


############################
start = time.time()
for f in layer.getFeatures():
    f_geom = f.geometry()

end = time.time()
print 'TEST 2 time:', (end - start)

############################
start = time.time()
for f in layer.getFeatures():
    f_attrs = f.attributes()

end = time.time()
print 'TEST 3 time:', (end - start)

############################
start = time.time()
for f in layer.getFeatures():
    f_geom = f.geometry()
    f_attrs = f.attributes()

end = time.time()
print 'TEST 4 time:', (end - start)

############################
feats = []
start = time.time()

for f in layer.getFeatures():
    new_feat = QgsFeature()
    new_feat.setGeometry(f.geometry())
    new_feat.setAttributes(f.attributes())
    feats.append(new_feat)


end = time.time()
print 'TEST 5 time:', (end - start)


############################
feats = []
start = time.time()

for f in layer.getFeatures():
    new_feat = QgsFeature(f)
    new_feat.setGeometry(f.geometry())
    feats.append(new_feat)

end = time.time()
print 'TEST 6 time:', (end - start)

############################
dict_feat = {}
start = time.time()

for f in layer.getFeatures():
    dict_feat[f.id()] = {'attrs': f.attributes(), 'geom': f.geometry()}

end = time.time()
print 'TEST 7 time:', (end - start)

############################
dict_feat = {}
from PyQt4.QtCore import QObject

class sEdge(QObject):
    def __init__(self, id, geom, attrs):
        QObject.__init__(self)
        self.id = id
        self.geom = geom
        self.attrs = attrs

start = time.time()

for f in layer.getFeatures():
    f_id = f.id()
    dict_feat[f.id()] = sEdge(f_id, f.geometry(), f.attributes())

end = time.time()
print 'TEST 8 time:', (end - start)

############################

start = time.time()

feats = map(lambda x: (x.geometry(), x.attributes()), layer.getFeatures())
end = time.time()
print 'TEST 9 time:', (end - start)

############################

start = time.time()

def copy_feat(f):
    new_feat = QgsFeature(f)
    new_feat.setGeometry(f.geometry())
    return new_feat


feats = map(lambda x: copy_feat(x), layer.getFeatures())
end = time.time()
print 'TEST 10 time:', (end - start)

############################

start = time.time()
dict_feat = {}
def add_feat(f):
    dict_feat[f.id()] = {'attrs': f.attributes(), 'geom':f.geometry()}
    return

res = map(lambda x: copy_feat(x), layer.getFeatures())
end = time.time()
print 'TEST 11 time:', (end - start)


############################


class sEdge(QObject):
    def __init__(self, id, geom, attrs):
        QObject.__init__(self)
        self.id = id
        self.geom = geom
        self.attrs = attrs


start = time.time()
def sedge_from_feat(f):
    return sEdge(f.id(), f.geometry(), f.attributes())

sedges = map(lambda x: copy_feat(x), layer.getFeatures())

dict_feat = dict(zip([e.id for e in sedges], sedges))
end = time.time()
print 'TEST 12 time:', (end - start)


############################
#TEST 1 time: 0.891966819763
#TEST 2 time: 0.91631603241
#TEST 3 time: 2.08853697777
#TEST 4 time: 2.27606415749

# storing feats
#TEST 5 time: 3.82744908333
#TEST 6 time: 1.59538292885
#TEST 7 time: 2.58583498001
#TEST 8 time: 3.13741397858
#TEST 9 time: 2.70247602463
#TEST 10 time: 1.32574510574 XXXX
#TEST 11 time: 1.50159096718
#TEST 12 time: 1.77451610565

# for storing attribute test 7 -> store in dict format so that you do not need to retrieve again
