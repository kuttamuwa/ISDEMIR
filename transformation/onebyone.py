import arcpy
from pyproj import CRS
from pyproj import Transformer
import os

# environment settings
env_path = r"C:\Users\sozeren.mapit\Documents\ArcGIS\Projects\KoordinatSistemiTest\cbsarcgisew.sde"
arcpy.env.workspace = env_path

# transformation settings
src_wkt = """PROJCS["ED_1950_Turkey_12",GEOGCS["GCS_European_1950",DATUM["D_European_1950",SPHEROID["International_1924",6378388.0,297.0]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",12500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",36.0],PARAMETER["Scale_Factor",1.0],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]"""
target_wkt = """PROJCS["ED_1950_TM36",GEOGCS["GCS_European_1950",DATUM["D_European_1950",SPHEROID["International_1924",6378388.0,297.0]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Gauss_Kruger"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",36.0],PARAMETER["Scale_Factor",1.0],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0],AUTHORITY["EPSG",2322]]"""

# initial variables
src_crs = CRS.from_wkt(src_wkt)
target_crs = CRS.from_wkt(target_wkt)
transformer = Transformer.from_crs(src_crs, target_crs)


try:
    with arcpy.da.UpdateCursor("Numarataj", ['OID@', 'SHAPE@XY']) as ucursor:
        for row in ucursor:
            old_x, old_y = row[1][0], row[1][1]
            new_x, new_y = transformer.transform(old_x, old_y)

            row[1] = new_x, new_y

            ucursor.updateRow(row)

    arcpy.DefineProjection_management("Numarataj", target_wkt)

except Exception as err:
    print("hata aldik : {0}".format(str(err)))


# point
def XYsetVALUE(shape):
    from pyproj import CRS
    from pyproj import Transformer
    src_wkt = """PROJCS["ED_1950_Turkey_12",GEOGCS["GCS_European_1950",DATUM["D_European_1950",SPHEROID["International_1924",6378388.0,297.0]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",12500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",36.0],PARAMETER["Scale_Factor",1.0],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]"""
    target_wkt = """PROJCS["ED_1950_TM36",GEOGCS["GCS_European_1950",DATUM["D_European_1950",SPHEROID["International_1924",6378388.0,297.0]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Gauss_Kruger"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",36.0],PARAMETER["Scale_Factor",1.0],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0],AUTHORITY["EPSG",2322]]"""

    src_crs = CRS.from_wkt(src_wkt)
    target_crs = CRS.from_wkt(target_wkt)
    transformer = Transformer.from_crs(src_crs, target_crs)
    point = shape.getPart(0)
    new_x, new_y = transformer.transform(point.X, point.Y)
    point.X = new_x
    point.Y = new_y
    return point

# polygon
ucursor = arcpy.UpdateCursor('OEBSDE', ["OID@", "SHAPE@XY"])
for row in ucursor:
    old_pnts = row.getValue('SHAPE').getPart(0)
    new_pnts = []
    for old_pnt in old_pnts:
        new_x, new_y = transformer.transform(old_pnt.X, old_pnt.Y)
        new_pnt = arcpy.Point(new_x, new_y)

        old_pnt.X, old_pnt.Y = new_pnt.X, new_pnt.Y
        # row.setValue('SHAPE', new_pnt)
        ucursor.updateRow(row)

        new_pnts.append(new_pnt)

    new_polygon = arcpy.Polygon(arcpy.Array([i for i in new_pnts]))
    row.setValue('SHAPE', new_polygon)
    ucursor.updateRow(row)

arcpy.DefineProjection_management("OEBSDE", target_wkt)


# polygon calculate field
def XYsetVALUE(shape):
    from pyproj import CRS
    from pyproj import Transformer
    src_wkt = """PROJCS["ED_1950_Turkey_12",GEOGCS["GCS_European_1950",DATUM["D_European_1950",SPHEROID["International_1924",6378388.0,297.0]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",12500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",36.0],PARAMETER["Scale_Factor",1.0],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]"""
    target_wkt = """PROJCS["ED_1950_TM36",GEOGCS["GCS_European_1950",DATUM["D_European_1950",SPHEROID["International_1924",6378388.0,297.0]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Gauss_Kruger"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",36.0],PARAMETER["Scale_Factor",1.0],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0],AUTHORITY["EPSG",2322]]"""

    src_crs = CRS.from_wkt(src_wkt)
    target_crs = CRS.from_wkt(target_wkt)
    transformer = Transformer.from_crs(src_crs, target_crs)

    new_pnts = []

    old_pnts = shape.getPart(0)
    for old_pnt in old_pnts:
        new_x, new_y = transformer.transform(old_pnt.X, old_pnt.Y)
        new_pnt = arcpy.Point(new_x, new_y, ID=old_pnt.ID)

        new_pnts.append(new_pnt)

    new_polygon = arcpy.Polygon(arcpy.Array([i for i in new_pnts]))
    return new_polygon




# polygon python
cpp = {}
with arcpy.da.SearchCursor('OGA_PROJECTED', ["OBJECTID", "SHAPE@"]) as sCursor:
    for row in sCursor:
        cpp[row[0]] = row[1]


uCursor = arcpy.da.UpdateCursor('OGA_OLD', ["OBJECTID", "SHAPE@"])
for row in uCursor:
    # Update the geometry if it's in cpp.
    recordId = row.getValue('OBJECTID')
    if recordId in cpp:
        row.setValue('SHAPE', cpp[recordId])
        row[1] = cpp[recordId]
        uCursor.updateRow(row)

# polygon python field calculator
def XYsetVALUE(shape, globalidfield):
    cpp = {}
    with arcpy.da.SearchCursor('YAPI_PROJECTED', ["GlobalID", "SHAPE@"]) as sCursor:
        for row in sCursor:
            if row[0] in cpp:
                cpp[row[0]] = row[1]

    return cpp[globalidfield]

# tamamlananlar
# numarataj
# oeb
# oga

# 2409 field is null hatasi verdi ilk ama..