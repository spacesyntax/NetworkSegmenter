# Network Segmenter
### Breaking a network into segments and removing stubs while reading unlinks

## About
This tool takes a line-based network. It explodes polylines in the network and breaks them based on their intersection with other lines. Lines that cross other lines can be an unwanted stub. These stubs are removed based on a specified ratio. Optionally, a point or polygon based unlink layer can be specified which highlight crossing lines which should not break. The search area around the unlink features is specified by the unlink buffer variable. This plugin was developed by Space Syntax Open Digital Works © 2016 Space Syntax Ltd.

## Installation
Currently the plugin is not available through the QGIS plugins repository. To install you need to download the latest Plugin.zip file from the Clone or download button on the top right corner of this page. Unzip and copy the entire folder into the QGIS plugins directory. This directory can be found here:

- MS Windows: C:\Users(your user name).qgis2\python\plugins\
- Mac OSX: Users/(your user name)/.qgis2/python/plugins/
- Linux: home/(your user name)/.qgis2/python/plugins/

This directory is usually hidden and you must make hidden files visible. Under Mac OSX you can open the folder in Finder by selecting 'Go > Go To Folder...' and typing '~/.qgis2/python/plugins/'. If you haven’t installed any QGIS plugins so far, you need to create the ‘plugins’ directory in the ‘.qgis2/python/’ directory. After copying the plugin, it will be available in the plugin manager window once you (re)start QGIS. Check the box next to the plugin to load it.

## How to
**Network layer**
Choose the line-based vector layer from the drop-down menu that you want segment.

**Unlink layer**
Choose the point-based vector layer containing the unlink points or polygons that define lines that should not be broken.

**Unlink buffer**
Define the search distance around the unlink features that capture the unconnected lines.

**Stub ratio**
This percentage defines the minimum proportion of the line length that signifies an unwanted stub.

**Output network**
This tool provides a segmented network as temporary layer or as a shapefile if its path is set.

**Run**
Pressing the run button will activate the analysis for all the current settings.

**Cancel**
Pressing cancel will close and terminate the Network Segmenter.

## Software Requirements
QGIS (2.0 or above) - http://www.qgis.org/en/site/
