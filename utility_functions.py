# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CatchmentAnalyser
                                 A QGIS plugin
 Network based catchment analysis
                              -------------------
        begin                : 2016-05-19
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Laurens Versluis
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

def getLegendLayers(iface, geom='all', provider='all'):
    """geometry types: 0 point; 1 line; 2 polygon; 3 multipoint; 4 multiline; 5 multipolygon"""
    layers_list = []
    for layer in iface.legendInterface().layers():
        add_layer = False
        if layer.isValid() and layer.type() == QgsMapLayer.VectorLayer:
            if layer.hasGeometryType() and (geom is 'all' or layer.geometryType() in geom):
                if provider is 'all' or layer.dataProvider().name() in provider:
                    add_layer = True
        if add_layer:
            layers_list.append(layer)
    return layers_list

def getLegendLayersNames(iface, geom='all', provider='all'):
    """geometry types: 0 point; 1 line; 2 polygon; 3 multipoint; 4 multiline; 5 multipolygon"""
    layers_list = []
    for layer in iface.legendInterface().layers():
        add_layer = False
        if layer.isValid() and layer.type() == QgsMapLayer.VectorLayer:
            if layer.hasGeometryType() and (geom is 'all' or layer.geometryType() in geom):
                if provider is 'all' or layer.dataProvider().name() in provider:
                    add_layer = True
        if add_layer:
            layers_list.append(layer.name())
    return layers_list


def getLegendLayerByName(iface, name):
    layer = None
    for i in iface.legendInterface().layers():
        if i.name() == name:
            layer = i
    return layer

def getNumericFieldNames(layer, type='all'):
    field_names = []
    if type == 'all':
        types = (QVariant.Int, QVariant.LongLong, QVariant.Double, QVariant.UInt, QVariant.ULongLong)
    else:
        types = [type]
    if layer and layer.dataProvider():
        for field in layer.dataProvider().fields():
            if field.type() in types:
                field_names.append(field.name())
    return field_names

def getFieldNames(layer):
    field_names = []
    if layer and layer.dataProvider():
        for field in layer.dataProvider().fields():
            field_names.append(field.name())
    return field_names


def giveWarningMessage(message):
    # Gives warning according to message
    self.iface.messageBar().pushMessage(
        "Catchment Analyser: ",
        "%s" % (message),
        level=QgsMessageBar.WARNING,
        duration=5)

def createTempLayer(name, geometry, srid, attributes, types):
    # Geometry can be 'POINT', 'LINESTRING' or 'POLYGON' or the 'MULTI' version of the previous
    vlayer = QgsVectorLayer('%s?crs=epsg:%s' % (geometry, srid), name, "memory")
    provider = vlayer.dataProvider()

    # Create the required fields
    if attributes:
        vlayer.startEditing()
        fields = []
        for i, att in enumerate(attributes):
            fields.append(QgsField(att, types[i]))

        # add the fields to the layer
        try:
            provider.addAttributes(fields)
        except:
            return None
        vlayer.commitChanges()

    return vlayer


def insertTempFeatures(layer, geometry, attributes):
    provider = layer.dataProvider()
    fet = QgsFeature()
    fet.setGeometry(geometry)
    if attributes:
        fet.setAttributes(attributes)
    provider.addFeatures([fet])
    provider.updateExtents()


def createShapeFile(layer, path, crs):
    shapefile = QgsVectorFileWriter.writeAsVectorFormat(
        layer,
        r"%s" % path,
        "utf-8",
        crs,
        "ESRI Shapefile"
    )
    return shapefile