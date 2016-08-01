from utility_functions import *
from qgis.core import *
from processing.algs.qgis.Explode import *


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


def prepareNetwork(network_vector):
    segment_index = QgsSpatialIndex()
    segment_dict = {}
    # Loop through network features
    index = 1
    for polyline in network_vector.getFeatures():
        geom = polyline.geometry()
        segments = extractSinglePolyline(geom)
        # Write segments to index and dictionary
        for segment in segments:
            f = QgsFeature()
            f.setGeometry(segment)
            segment_index.insertFeature(f)
            segment_dict[index] = {'geom': segment}
            index += 1

    return segment_index, segment_dict


def indexUnlinks(unlink_vector, unlink_buffer):
    unlink_index = QgsSpatialIndex()
    unlink_geom_type = unlink_vector.geometryType()
    for unlink in unlink_vector.getFeatures():
        # Create unlink buffer areas when unlinks are points
        if unlink_geom_type == 'point':
            unlink_geom = unlink.geometry().buffer(unlink_buffer, 5)
            unlink_area = QgsFeature()
            unlink_area.setGeometry(unlink_geom)
        # Create unlink area when unlinks are polygons or lines
        else:
            unlink_area = unlink
        # Add unlink to index and to dictionary
        unlink_index.insertFeature(unlink_area)

    return unlink_index


def breakPoints(index, segment_index, segment_dict, unlink_index):
    geom = segment_dict[index]['geom']
    break_points = []
    intersecting_segments_ids = segment_index.intersects(geom.boundingBox())
    print intersecting_segments_ids
    for id in intersecting_segments_ids:
        if id != index: # Skip if segment is itself
            # Get geometry of intersecting segment
            int_seg_geom = segment_dict[id]['geom']
            # Identify the construction point of the new segment
            if geom.crosses(int_seg_geom) or geom.touches(int_seg_geom):
                point_geom = geom.intersection(int_seg_geom)
                point_buffer_geom = point_geom.buffer(1, 1).boundingBox()
                # Add break point if cross point is an unlink
                if unlink_index:
                    if not unlink_index.intersects(point_buffer_geom):
                        break_points.append(point_geom.asPoint())
                else:
                    break_points.append(point_geom.asPoint())
    # Getting a set of unique points
    break_points = list(set(break_points))

    return break_points


def segmentNetwork(segment_dict, segment_index, unlink_index, stub_ratio, output_network):

    # Break each segment based on intersecting lines and unlinks
    id = 0
    for index in segment_dict:
        # Get geometry
        segment_geom = segment_dict[index]['geom']
        max_stub = segment_geom.length() * stub_ratio
        seg_start_point = segment_geom.asPolyline()[0]
        seg_end_point = segment_geom.asPolyline()[-1]
        break_points = breakPoints(index, segment_index, segment_dict, unlink_index)
        # If segment is a dead end write it straight away
        if len(break_points) == 1:
            insertTempFeatures(output_network, segment_geom, [id, ])
        else:
            # Sort break_points according to distance to start point
            break_points.sort(key=lambda x: QgsDistanceArea().measureLine(seg_start_point, x))
            # Create segments using break points
            for i in range(0, len(break_points) - 1):
                start_geom = QgsPoint(break_points[i])
                end_geom = QgsPoint(break_points[i + 1])
                line_geom = QgsGeometry.fromPolyline([start_geom, end_geom])
                insertTempFeatures(output_network, line_geom, [index, ])
            # Check if first segment is a potential stub
            for point in break_points:
                if point != seg_start_point:
                    # Calculate distance between point and start point
                    distance_nearest_break = QgsDistanceArea().measureLine(seg_start_point, break_points[0])
                    # Only add first segment if it is a dead end
                    if distance_nearest_break > max_stub:

                        # Create new geometry and cost and write to network
                        line_geom = QgsGeometry.fromPolyline([seg_start_point, break_points[0]])
                        insertTempFeatures(output_network, line_geom, [id, ])

                # Check if last segment is a potential stub
                elif point != seg_end_point:

                    # Calculate distance between point and end point
                    distance_nearest_break = QgsDistanceArea().measureLine(seg_end_point, break_points[-1])

                    # Only add last segment if it is a dead end
                    if distance_nearest_break > max_stub:

                        # Create new geometry and cost and write to network
                        line_geom = QgsGeometry.fromPolyline([seg_end_point, break_points[-1]])

                        insertTempFeatures(output_network, line_geom, [id, ])
        id += 1
    return output_network


def renderNetwork(output_network):
    # add network to the canvas
    QgsMapLayerRegistry.instance().addMapLayer(output_network)