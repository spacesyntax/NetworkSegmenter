# general imports
from qgis.core import QgsMapLayerRegistry, QgsVectorFileWriter, QgsVectorLayer, QgsFeature, QgsGeometry,QgsFields, QgsDataSourceURI, QgsField, QgsCoordinateReferenceSystem, QgsVectorLayerImport
import psycopg2
from psycopg2.extensions import AsIs
import ntpath

# source: ess utility functions

# -------------------------- LAYER HANDLING


def getLayerByName(name):
    layer = None
    for i in QgsMapLayerRegistry.instance().mapLayers().values():
        if i.name() == name:
            layer = i
    return layer

# -------------------------- GEOMETRY HANDLING


# -------------------------- FEATURE HANDLING

def prototype_feature(attrs, fields):
    feat = QgsFeature()
    feat.initAttributes(1)
    feat.setFields(fields)
    feat.setAttributes(attrs)
    feat.setGeometry(QgsGeometry())
    return feat

# -------------------------- POSTGIS INFO RETRIEVAL


# SOURCE: ESS TOOLKIT

def getPostgisSchemas(connstring, commit=False):
    """Execute query (string) with given parameters (tuple)
    (optionally perform commit to save Db)
    :return: result set [header,data] or [error] error
    """

    try:
        connection = psycopg2.connect(connstring)
    except psycopg2.Error, e:
        print e.pgerror
        connection = None

    schemas = []
    data = []
    if connection:
        query = unicode("""SELECT schema_name from information_schema.schemata;""")
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            if cursor.description is not None:
                data = cursor.fetchall()
            if commit:
                connection.commit()
        except psycopg2.Error, e:
            connection.rollback()
        cursor.close()

    # only extract user schemas
    for schema in data:
        if schema[0] not in ('topology', 'information_schema') and schema[0][:3] != 'pg_':
            schemas.append(schema[0])
    #return the result even if empty
    return sorted(schemas)


# -------------------------- LAYER BUILD

def to_layer(features, crs, encoding, geom_type, layer_type, path, name):

    first_feat = features[0]
    fields = first_feat.fields()
    layer = None
    if layer_type == 'memory':
        layer = QgsVectorLayer(geom_type + '?crs=' + crs.authid(), name, "memory")
        pr = layer.dataProvider()
        pr.addAttributes(fields.toList())
        layer.updateFields()
        layer.startEditing()
        pr.addFeatures(features)
        layer.commitChanges()

    elif layer_type == 'shapefile':

        wkbTypes = { 'Point': QGis.WKBPoint, 'Linestring': QGis.WKBLineString, 'Polygon': QGis.WKBPolygon }
        file_writer = QgsVectorFileWriter(path, encoding, fields, wkbTypes[geom_type], crs, "ESRI Shapefile")
        if file_writer.hasError() != QgsVectorFileWriter.NoError:
            print "Error when creating shapefile: ", file_writer.errorMessage()
        del file_writer
        layer = QgsVectorLayer(path, name, "ogr")
        pr = layer.dataProvider()
        layer.startEditing()
        pr.addFeatures(features)
        layer.commitChanges()

    elif layer_type == 'postgis':

        layer = QgsVectorLayer(geom_type + '?crs=' + crs.authid(), name, "memory")
        pr = layer.dataProvider()
        pr.addAttributes(fields.toList())
        layer.updateFields()
        layer.startEditing()
        pr.addFeatures(features)
        layer.commitChanges()
        uri = QgsDataSourceURI()
        # passwords, usernames need to be empty if not provided or else connection will fail
        if path['service']:
            uri.setConnection(path['service'], path['database'], '', '')
        elif path['password']:
            uri.setConnection(path['host'], path['port'], path['database'], path['user'], path['password'])
        else:
            uri.setConnection(path['host'], path['port'], path['database'], path['user'], '')
        #uri = "dbname='test' host=localhost port=5432 user='user' password='password' key=gid type=POINT table=\"public\".\"test\" (geom) sql="
        #crs = QgsCoordinateReferenceSystem(int(crs.postgisSrid()), QgsCoordinateReferenceSystem.EpsgCrsId)
        # layer - QGIS vector layer
        uri.setDataSource(path['schema'], path['table_name'], "geom")
        error = QgsVectorLayerImport.importLayer(layer, uri.uri(), "postgres", crs, False, False)
        if error[0] != 0:
            print "Error when creating postgis layer: ", error[1]

        print uri.uri()
        layer = QgsVectorLayer(uri.uri(), name, "postgres")

    return layer


def clean_nulls(attrs):
    cleaned_attrs = []
    for attr in attrs:
        if attr:
            cleaned_attrs.append(attr)
        else:
            cleaned_attrs.append(None)
    return cleaned_attrs

def rmv_parenthesis(my_string):
    idx = my_string.find(',ST_GeomFromText') - 1
    return  my_string[:idx] + my_string[(idx+1):]




