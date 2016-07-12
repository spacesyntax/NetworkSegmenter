from utility_functions import *

class NetworkSegmenter():

    def indexNetwork(self, network_vector):
        segment_index = QgsSpatialIndex()
        segment_dict = {}
        for segment in network_vector.getFeatures():
            segment_index.insertFeature(segment)
            segment_dict[segment.id()] = {'geom' : segment.geometryAndOwnership()}

        return segment_index, segment_dict


    def indexUnlinks(self, unlink_vector, unlink_buffer):
        unlink_index = QgsSpatialIndex()
        for unlink in unlink_vector.getFeatures():

            # Create unlink buffer areas when unlinks are points
            if unlink.geometryType() == 'point':
                unlink_geom = unlink.geometry().buffer(unlink_buffer, 5)
                unlink_area = QgsFeature()
                unlink_area.setGeometry(unlink_geom)

            # Create unlink area when unlinks are polygons or lines
            else:
                unlink_area = unlink

            # Add unlink to index and to dictionary
            unlink_index.insertFeature(unlink_area)

        return unlink_index

    def breakPoints(self, segment_dict, segment_index, unlink_index, stub_ratio, output_network):

        # Break each segment based on intersecting lines and unlinks
        for segment_id, att in segment_dict.items():

            # Get geometry, length, cost from segment
            segment_geom = att['geom']
            segment_length = segment_geom.length()

            # Get points from original segment
            seg_start_point = segment_geom.asPolyline()[0]
            seg_end_point = segment_geom.asPolyline()[-1]

            # List of break points for the new segments
            break_points = []

            # Identify intersecting segments
            intersecting_segments_ids = segment_index.intersects(segment_geom.boundingBox())

            # Loop for intersecting segments excluding itself
            for id in intersecting_segments_ids:

                # Skip if segment is itself
                if id != segment_id:
                    # Get geometry of intersecting segment
                    int_seg_geom = segment_dict[id]

                    # Identify the construction point of the new segment
                    if segment_geom.crosses(int_seg_geom) or segment_geom.touches(int_seg_geom):
                        point_geom = segment_geom.intersection(int_seg_geom)
                        point_buffer_geom = point_geom.buffer(1, 1).boundingBox()

                        # Add break point if cross point is an unlink
                        if not unlink_index.intersects(point_buffer_geom):
                            break_points.append(point_geom.asPoint())

            # Sort break_points according to distance to start point
            break_points.sort(key=lambda x: QgsDistanceArea().measureLine(seg_start_point, x))

            # Create segments using break points
            for i in range(0, len(break_points) - 1):
                # Set end points
                start_geom = QgsPoint(break_points[i])
                end_geom = QgsPoint(break_points[i + 1])

                # Create new geometry and cost and write to network
                line_geom = QgsGeometry.fromPolyline([start_geom, end_geom])
                insertTempFeatures(output_network, line_geom)

                # Check if first segment is a potential stub
                for point in break_points:

                    if point != seg_start_point:

                        # Calculate distance between point and start point
                        distance_nearest_break = QgsDistanceArea().measureLine(seg_start_point, break_points[0])

                        # Only add first segment if it is a dead end
                        if distance_nearest_break > (stub_ratio * segment_length):

                            # Create new geometry and cost and write to network
                            line_geom = QgsGeometry.fromPolyline([seg_start_point, break_points[0]])
                            insertTempFeatures(output_network, line_geom)

                    # Check if last segment is a potential stub
                    elif point != seg_end_point:

                        # Calculate distance between point and end point
                        distance_nearest_break = QgsDistanceArea().measureLine(seg_end_point, break_points[-1])

                        # Only add last segment if it is a dead end
                        if distance_nearest_break > (stub_ratio * segment_length):

                            # Create new geometry and cost and write to network
                            line_geom = QgsGeometry.fromPolyline([seg_end_point, break_points[-1]])

                            insertTempFeatures(output_network, line_geom)

        return output_network