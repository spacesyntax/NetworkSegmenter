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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant, QThread
from PyQt4.QtGui import QAction, QIcon
# Initialize Qt resources from file resources.py
import resources

# Import QGIS classes
from qgis.core import *
from qgis.utils import *

# Import the code for the dialog
from network_segmenter_dialog import NetworkSegmenterDialog
import os.path

# Import tool classes
import network_segmenter_tool

# Import utility tools
import utility_functions as uf

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
        # Initialize analysis
        # self.networkSegmenter = network_segmenter_tool.networkSegmenter(self.iface)
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
        self.menu = self.tr(u'&Space Syntax Toolkit')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.pluginToolBar()


        # Setup GUI signals
        self.dlg.analysisButton.clicked.connect(self.runAnalysis)


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
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/NetworkSegmenter/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Network Segmenter'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.menu,
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        # del self.toolbar


    def updateLayers(self):
        self.updateNetwork()
        self.updateUnlinks()


    def updateNetwork(self):
        network_layers = uf.getLegendLayersNames(self.iface, geom=[1, ], provider='all')
        self.dlg.setNetworkLayers(network_layers)


    def updateUnlinks(self):
        unlink_layers = uf.getLegendLayersNames(self.iface, geom=[0, 2, ], provider='all')
        unlink_layers.append('-----')
        self.dlg.setUnlinkLayers(unlink_layers)


    def getNetwork(self):
        return uf.getLegendLayerByName(self.iface, self.dlg.getNetwork())


    def getUnlinks(self):
        return uf.getLegendLayerByName(self.iface, self.dlg.getUnlinks())


    def tempNetwork(self, epsg):
        output_network = uf.createTempLayer(
            'segment_network',
            'LINESTRING',
            str(epsg),
            ['id', ],
            [QVariant.Int, ]
        )
        return output_network


    def getStubRatio(self):
        return self.dlg.getStubRatio()

    def getUnlinkBuffer(self):
        return self.dlg.getUnlinkBuffer()

    def giveWarningMessage(self, message):
        # Gives warning according to message
        self.iface.messageBar().pushMessage(
            "Network Segmenter: ",
            "%s" % (message),
            level=QgsMessageBar.WARNING,
            duration=5)

    def getSettings(self):
        # Creating a combined settings dictionary
        settings = {}

        # Give warnings
        if not self.getNetwork():
            self.giveWarningMessage("No network selected!")
        else:
            # Get settings from the dialog
            settings['network'] = self.getNetwork()
            settings['unlinks'] = self.getUnlinks()
            settings['stub ratio'] = self.getStubRatio()
            settings['unlink buffer'] = self.getUnlinkBuffer()
            settings['epsg'] = self.getNetwork().crs().authid()[5:]
            settings['crs'] = self.getNetwork().crs()
            settings['temp network'] = self.tempNetwork(settings['epsg'])
            settings['output network'] = self.dlg.getNetworkOutput()

            return settings

    def runAnalysis(self):
        self.dlg.analysisProgress.reset()
        # Create an analysis instance
        settings = self.getSettings()
        analysis = network_segmenter_tool.networkSegmenter(self.iface, settings)
        # Create new thread and move the analysis class to it
        analysis_thread = QThread()
        analysis.moveToThread(analysis_thread)
        # Setup signals
        self.dlg.cancelButton.clicked.connect(self.killAnalysis)
        analysis.finished.connect(self.finishAnalysis)
        analysis.error.connect(self.analysisError)
        analysis.warning.connect(self.giveWarningMessage)
        analysis.progress.connect(self.dlg.analysisProgress.setValue)
        # Start analysis
        analysis_thread.started.connect(analysis.analysis)
        analysis_thread.start()
        self.analysis_thread = analysis_thread
        self.analysis = analysis

    def finishAnalysis(self, output):
        # Clean up thread and analysis
        self.analysis_thread.quit()
        self.analysis_thread.wait()
        self.analysis_thread.deleteLater()
        self.analysis.deleteLater()
        # Render output
        if output:
            self.renderNetwork(output)
        else:
            self.giveWarningMessage('Something went wrong')
        # Closing the dialog
        self.dlg.closeDialog()

    def analysisError(self, e, exception_string):
        QgsMessageLog.logMessage(
            'Catchment Analyser raised an exception: %s' % exception_string,
            level=QgsMessageLog.CRITICAL)
        # Closing the dialog
        self.dlg.closeDialog()

    def killAnalysis(self):
        # Clean up thread and analysis
        self.analysis.kill()
        self.analysis_thread.quit()
        self.analysis_thread.wait()
        self.analysis_thread.deleteLater()
        self.analysis.deleteLater()
        # Closing the dialog
        self.dlg.closeDialog()

    def renderNetwork(self, output_network):
        # Add network to the canvas
        QgsMapLayerRegistry.instance().addMapLayer(output_network)


    def run(self):
        # show the dialog
        self.dlg.show()
        # Update layers
        self.updateLayers()