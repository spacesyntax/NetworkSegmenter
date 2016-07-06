# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NetworkSegmenter
                                 A QGIS plugin
 Breaking a network into segments while removing stubbs and reading unlinks
                             -------------------
        begin                : 2016-07-06
        copyright            : (C) 2016 by Laurens Versluis
        email                : l.versluis@spacesyntax.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load NetworkSegmenter class from file NetworkSegmenter.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .network_segmenter import NetworkSegmenter
    return NetworkSegmenter(iface)
