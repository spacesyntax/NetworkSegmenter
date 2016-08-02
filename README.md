# Network Segmenter
### Breaking a network into segments and removing stubs while reading unlinks

## About
This tool takes a line-based network. It explodes polylines in the network and breaks them based on their intersection with other lines. Lines that cross other lines can be an unwanted stub. These stubs are removed based on a specified ratio. Optionally, a point or polygon based unlink layer can be specified which highlight crossing lines which should not break. The search area around the unlink features is specified by the unlink buffer variable.This plugin was developed by Space Syntax Open Digital Works © 2016 Space Syntax Ltd.

## Installation
The plug-in can be installed from the QGIS Plugins Manager, and updates become automatically available once submitted to the QGIS plugins repository.

## How to
**Network layer**
Choose the line-based vector layer from the drop-down menu that you want segment. 

**Unlink layer** 
Choose the point-based vector layer containing the unlink points or polygons that define lines that should not be broken. 

**Unlink buffer**
Define the search distance around the unlink features that capture the unconnected lines.

**Stub ratio**:  
This percentage defines the minimum proportion of the line length that signifies an unwanted stub.

**Output network**: 
This tool provides a segmented network as temporary layer or as a shapefile if its path is set. 

**Run**: 
Pressing the run button will activate the analysis for all the current settings.

**Cancel**: 
Pressing cancel will close and terminate the Network Segmenter.

## Software Requirements
QGIS (2.0 or above) - http://www.qgis.org/en/site/

