

def createSpIndex(layer):
    spIndex = QgsSpatialIndex()
    for f in layer.getFeatures():
        spIndex.insertFeature(f)
    return spIndex

def explodePolyline(polyline):
    segments = []
    for i in range(len(polyline) - 1):
        ptA = polyline[i]
        ptB = polyline[i + 1]
        segment = QgsGeometry.fromPolyline([ptA, ptB])
        segments.append(segment)
    return segments

def extractSinglePolyline(geom):
    segments = []
    if geom.isMultipart():
        multi = geom.asMultiPolyline()
        for polyline in multi:
            segments.extend(explodePolyline(polyline))
    else:
        segments.extend(explodePolyline(geom.asPolyline()))
    return segments