# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NetworkSegmenter
                                 Network Segmenter
 Breaking a network into segments and removing stubs while reading unlinks
                              -------------------
        begin                : 2016-07-06
        author               : Laurens Versluis
        copyright            : (C) 2016 by Space Syntax Limited
        email                : l.versluis@spacesyntax.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
from qgis.utils import *
from processing.algs.qgis.Explode import *
import utility_functions as uf

class networkSegmenter(QObject):

    # Setup signals
    finished = pyqtSignal(object)
    error = pyqtSignal(Exception, basestring)
    progress = pyqtSignal(float)
    warning = pyqtSignal(str)

    def __init__(self, iface, settings):
        QObject.__init__(self)
        self.iface = iface
        self.settings = settings
        self.killed = False

    def explodePolyline(self, polyline):
        segments = []
        for i in range(len(polyline) - 1):
            ptA = polyline[i]
            ptB = polyline[i + 1]
            segment = QgsGeometry.fromPolyline([ptA, ptB])
            segments.append(segment)
        return segments


    def extractSinglePolyline(self, geom):
        segments = []
        if geom.isMultipart():
            multi = geom.asMultiPolyline()
            for polyline in multi:
                segments.extend(self.explodePolyline(polyline))
        else:
            segments.extend(self.explodePolyline(geom.asPolyline()))
        return segments


    def prepareNetwork(self, network_vector):
        segment_index = QgsSpatialIndex()
        segment_dict = {}
        # Loop through network features
        index = 1
        for polyline in network_vector.getFeatures():
            geom = polyline.geometry()
            segments = self.extractSinglePolyline(geom)
            # Write segments to index and dictionary
            for segment in segments:
                f = QgsFeature()
                f.setFeatureId(index)
                f.setGeometry(segment)
                segment_index.insertFeature(f)
                segment_dict[index] = {'geom': segment}
                index += 1

        return segment_index, segment_dict


    def indexUnlinks(self, unlink_vector, unlink_buffer):
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


    def breakPoints(self, index, segment_index, segment_dict, unlink_index):
        geom = segment_dict[index]['geom']
        break_points = []
        intersecting_segments_ids = segment_index.intersects(geom.boundingBox())
        for id in intersecting_segments_ids:
            if self.killed == True: return
            if id != index: # Skip if segment is itself
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


    def segmentNetwork(self, segment_dict, segment_index, unlink_index, stub_ratio, output_network):

        # Break each segment based on intersecting lines and unlinks
        tot = len(segment_dict)
        id = 0
        for index in segment_dict:
            if self.killed == True: return
            self.progress.emit(20+int(80*(id+1)/tot))
            # Get geometry
            segment_geom = segment_dict[index]['geom']
            max_stub = segment_geom.length() * stub_ratio
            seg_start_point = segment_geom.asPolyline()[0]
            seg_end_point = segment_geom.asPolyline()[-1]
            break_points = self.breakPoints(index, segment_index, segment_dict, unlink_index)
            # If segment is a dead end write it straight away
            if len(break_points) == 1:
                uf.insertTempFeatures(output_network, segment_geom, [id, ])
            elif len(break_points) > 1:
                # Sort break_points according to distance to start point
                break_points.sort(key=lambda x: QgsDistanceArea().measureLine(seg_start_point, x))
                # Create segments using break points
                for i in range(0, len(break_points) - 1):
                    start_geom = QgsPoint(break_points[i])
                    end_geom = QgsPoint(break_points[i + 1])
                    line_geom = QgsGeometry.fromPolyline([start_geom, end_geom])
                    uf.insertTempFeatures(output_network, line_geom, [index, ])
                # Check if first segment is a potential stub
                # for point in break_points:
                if self.killed == True: return
                if break_points[0] != seg_start_point:
                    # Calculate distance between point and start point
                    distance_nearest_break = abs(QgsDistanceArea().measureLine(seg_start_point, break_points[0]))
                    # Only add first segment if it is a dead end
                    if distance_nearest_break > max_stub:
                        line_geom = QgsGeometry.fromPolyline([seg_start_point, break_points[0]])
                        uf.insertTempFeatures(output_network, line_geom, [id, ])
                # Check if last segment is a potential stub
                if break_points[-1] != seg_end_point:
                    # Calculate distance between point and end point
                    distance_nearest_break = abs(QgsDistanceArea().measureLine(seg_end_point, break_points[-1]))
                    # Only add last segment if it is a dead end
                    if distance_nearest_break > max_stub:
                        line_geom = QgsGeometry.fromPolyline([seg_end_point, break_points[-1]])
                        uf.insertTempFeatures(output_network, line_geom, [id, ])
            id += 1

        return output_network


    def analysis(self):
        if self.settings:
            try:
                # Preparing the network
                segment_index, segment_dict = self.prepareNetwork(self.settings['network'])
                if self.killed == True: return
                self.progress.emit(10)
                # Preparing the unlinks
                if self.settings['unlinks'] and self.settings['unlinks'] != '-----':
                    unlink_index = self.indexUnlinks(self.settings['unlinks'], self.settings['unlink buffer'])
                else:
                    unlink_index = ''
                if self.killed == True: return
                self.progress.emit(20)
                # Performing the segmentation of the network
                output_network = self.segmentNetwork(
                    segment_dict,
                    segment_index,
                    unlink_index,
                    self.settings['stub ratio'],
                    self.settings['temp network'])
                # Depending on user input create temporary output layer or shapefile
                if self.settings['output network']:
                    uf.createShapeFile(output_network, self.settings['output network'], self.settings['crs'])
                    output_network = QgsVectorLayer(self.settings['output network'], 'segmented network', 'ogr')
                # Emit output when everything went fine
                if self.killed == False:
                    self.progress.emit(100)
                    self.finished.emit(output_network)
            except Exception, e:
                self.error.emit(e, traceback.format_exc())

    def kill(self):
        self.killed = True

