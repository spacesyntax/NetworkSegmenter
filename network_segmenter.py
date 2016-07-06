# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NetworkSegmenter
                                 A QGIS plugin
 Breaking a network into segments while removing stubbs and reading unlinks
                              -------------------
        begin                : 2016-07-06
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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from network_segmenter_dialog import NetworkSegmenterDialog
import os.path


class NetworkSegmenter:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'NetworkSegmenter_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = NetworkSegmenterDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Network Segmenter')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'NetworkSegmenter')
        self.toolbar.setObjectName(u'NetworkSegmenter')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('NetworkSegmenter', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/NetworkSegmenter/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Network segmenter'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Network Segmenter'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
def network_preparation(self, network_vector, network_cost_field, unlink_vector, topology_bool, stub_ratio):

        # Settings
        unlink_buffer = 5

        # Variables
        network_crs = network_vector.crs()
        network_epsg = network_crs.authid()
        segment_index = QgsSpatialIndex()
        segment_dict = {}
        unlink_index = QgsSpatialIndex()

        # Output network
        network = uf.createTempLayer('network','LINESTRING', network_crs,['cost',],[QVariant.Int,])

        if not network_vector:
            uf.giveWarningMessage("No network layer selected!")

        else:

            # Check network layer validity
            if not network_vector.isValid():
                uf.giveWarningMessage("Invalid network layer!")

            # Check if network layer contains lines
            elif not (network_vector.wkbType() == 2 or network_vector.wkbType() == 5):
                uf.giveWarningMessage("Network layer contains no lines!")

        # Check unlink layer geometry type
        if unlink_vector:

            origin_type = uf.getGeomType(unlink_vector)

        # If network is not topological start segmentation
        if topology_bool == False:

            # Insert segments of network to the spatial index and dictionary
            for segment in network_vector.getFeatures():

                # Add segment to spatial index
                segment_index.insertFeature(segment)

                # Create
                segment_dict[segment.id()] = {'geom' : segment.geometryAndOwnership(), 'cost' : None}

                # If exist append custom cost to segment dictionary
                if network_cost_field:
                    segment_dict[segment.id()]['cost'] = segment[network_cost_field]

            # Create index of unlinks
            if unlink_vector:
                for unlink in unlink_vector.getFeatures():

                    # Create unlink area when unlinks are points
                    if origin_type == 'point':

                        # Create unlink area 5m around the point
                        unlink_geom = unlink.geometry().buffer(unlink_buffer, 5)
                        unlink_area = QgsFeature()
                        unlink_area.setGeometry(unlink_geom)

                    # Create unlink area when unlinks are polygons or lines
                    else:
                        unlink_area = unlink

                    # Add unlink to index and to dictionary
                    unlink_index.insertFeature(unlink_area)

            # Break each segment based on intersecting lines and unlinks
            for segment_id, att in segment_dict.items():

                # Get geometry, length, cost from segment
                segment_geom = att['geom']
                segment_length = segment_geom.length()

                if network_cost_field:
                    segment_cost = att['cost']

                    # Calculate cost ratio
                    cost_ratio = segment_length/segment_cost

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
                    if id == segment_id:
                        continue

                    # Break segment according to remaining intersecting segment
                    else:

                        # Get geometry of intersecting segment
                        int_seg_geom = segment_dict[id]

                        # Identify the construction point of the new segment
                        if segment_geom.crosses(int_seg_geom) or segment_geom.touches(int_seg_geom):

                            # Create point where lines cross
                            point_geom = segment_geom.intersection(int_seg_geom)

                            # Create polygon of inters
                            point_buffer_geom = point_geom.buffer(1, 1).boundingBox()

                            # Check if cross point is an unlink
                            if not unlink_index.intersects(point_buffer_geom):
                                # Break points of intersecting lines
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
                    if network_cost_field:
                        line_cost = line_geom.length() * cost_ratio
                    else:
                        line_cost = ''
                    uf.insertTempFeatures(network,line_geom,line_cost)

                # Check if first segment is a potential stub
                for point in break_points:

                    if point != seg_start_point:

                        # Calculate distance between point and start point
                        distance_nearest_break = QgsDistanceArea().measureLine(seg_start_point, break_points[0])

                        # Only add first segment if it is a dead end
                        if distance_nearest_break > (stub_ratio * segment_length):

                            # Create new geometry and cost and write to network
                            line_geom = QgsGeometry.fromPolyline([seg_start_point, break_points[0]])
                            if network_cost_field:
                                line_cost = line_geom.length() * cost_ratio
                            else:
                                line_cost = ''
                            uf.insertTempFeatures(network, line_geom, line_cost)

                    # Check if last segment is a potential stub
                    elif point != seg_end_point:

                        # Calculate distance between point and end point
                        distance_nearest_break = QgsDistanceArea().measureLine(seg_end_point, break_points[-1])

                        # Only add last segment if it is a dead end
                        if distance_nearest_break > (stub_ratio * segment_length):

                            # Create new geometry and cost and write to network
                            line_geom = QgsGeometry.fromPolyline([seg_end_point, break_points[-1]])
                            if network_cost_field:
                                line_cost = line_geom.length() * cost_ratio
                            else:
                                line_cost = ''

                            uf.insertTempFeatures(network, line_geom, line_cost)

        # If topological network add all segments of the network layer straight away
        else:

            # Loop through features and add them to network
            for segment in network_vector.getFeatures():

                # Create new geometry and cost and write to network
                line_geom = segment.geometryAndOwnership()
                if network_cost_field:
                    line_cost = line_geom.length() * cost_ratio
                else:
                    line_cost = ''
                uf.insertTempFeatures(network, line_geom, line_cost)

        return network