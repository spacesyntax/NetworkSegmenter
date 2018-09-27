# general imports
from qgis.core import QgsMapLayerRegistry, QgsVectorFileWriter, QgsVectorLayer, QgsFeature, QgsGeometry,QgsFields, QgsDataSourceURI, QgsField
import psycopg2
from psycopg2.extensions import AsIs

# source: ess utility functions

# -------------------------- LAYER HANDLING


def getLayerByName(name):
    layer = None
    for i in QgsMapLayerRegistry.instance().mapLayers().values():
        if i.name() == name:
            layer = i
    return layer

# -------------------------- GEOMETRY HANDLING

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
    if layer_type == 'memory':
        geom_types = { 1: 'Point', 2: 'Line', 3:'Polygon'}
        layer = QgsVectorLayer(geom_types[geom_type] + '?crs=' + crs.toWkt(), name, "memory")
        pr = layer.dataProvider()
        pr.addAttributes(fields)
        layer.startEditing()
        pr.addFeatures(features)
        layer.commitChanges()

    elif layer_type == 'shapefile':
        file_writer = QgsVectorFileWriter(path, encoding, fields, geom_type, crs, "ESRI Shapefile")
        print path, encoding, fields, geom_type, crs
        if file_writer.hasError() != QgsVectorFileWriter.NoError:
            print "Error when creating shapefile: ", file_writer.errorMessage()
        del file_writer
        layer = QgsVectorLayer(path, name, "ogr")
        pr = layer.dataProvider()
        layer.startEditing()
        pr.addFeatures(features)
        layer.commitChanges()

    elif layer_type == 'postgis':
        crs_id = str(crs.postgisSrid())
        # TODO: or service
        connstring = "dbname=%s user=%s host=%s port=%s password=%s" % (dbname, user, host, port, password)
        try:
            uri = "dbname='test' host=localhost port=5432 user='user' password='password' key=gid type=POINT table=\"public\".\"test\" (geom) sql="
            crs_id = 4326
            crs = QgsCoordinateReferenceSystem(crs_id, QgsCoordinateReferenceSystem.EpsgCrsId)
            # layer - QGIS vector layer
            error = QgsVectorLayerImport.importLayer(layer, uri, "postgres", crs, False, False)
            if error[0] != 0:
                iface.messageBar().pushMessage(u'Error', error[1], QgsMessageBar.CRITICAL, 5)

        except psycopg2.DatabaseError, e:
            return e

    else:
        print "file type not supported"
    return layer





