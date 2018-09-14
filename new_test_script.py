
layer = iface.mapCanvas().currentLayer()

unlinks = iface.mapCanvas().currentLayer()

execfile(u'/Users/joe/NetworkSegmenter/new_method.py'.encode('utf-8'))

stub_ratio = 0.4
# my_segmentor = segmentor(layer, None, stub_ratio, None)
my_segmentor = segmentor(layer, unlinks, stub_ratio, None)

br = my_segmentor.segment()

for id, ml_feat in my_segmentor.feats.items():
    break


ml_geom = ml_feat.geometry()
