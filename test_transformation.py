import arcpy
from pyproj import CRS
from pyproj import Transformer
import os

# environment settings
env_path = r"C:\Users\sozeren.mapit\Desktop\UMUT\onyapitest\tumdata_1.gdb"
arcpy.env.workspace = env_path

# transformation settings
src_wkt = """PROJCS["ED_1950_Turkey_12",GEOGCS["GCS_European_1950",DATUM["D_European_1950",SPHEROID["International_1924",6378388.0,297.0]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",12500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",36.0],PARAMETER["Scale_Factor",1.0],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]"""
target_wkt = """PROJCS["ED_1950_TM36",GEOGCS["GCS_European_1950",DATUM["D_European_1950",SPHEROID["International_1924",6378388.0,297.0]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Gauss_Kruger"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",36.0],PARAMETER["Scale_Factor",1.0],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0],AUTHORITY["EPSG",2322]]"""

# initial variables
src_crs = CRS.from_wkt(src_wkt)
target_crs = CRS.from_wkt(target_wkt)
transformer = Transformer.from_crs(src_crs, target_crs)

# mxd setting
# tüm katmanlar aprx'e aktarılır
# aprx = arcpy.mp.ArcGISProject("CURRENT")
# map = aprx.listMaps("*")[0]  # one map
# arcpy.AddMessage(f"Map was selected : {map.name}")
# layers = map.listLayers()

# editing session
edit = arcpy.da.Editor(env_path)
edit.startEditing(True, False)
# edit.startOperation()

# sample_x, sample_y = 12519133.878038634, 4066382.0430306355
for fc in arcpy.ListFeatureClasses("*"):
    fc = os.path.join(env_path, fc)

    try:
        arcpy.AddMessage("{0} fc icin basliyoruz ..".format(fc))
        with arcpy.da.UpdateCursor(fc, ['OID@', 'SHAPE@XY']) as ucursor:
            for row in ucursor:
                old_x, old_y = row[1][0], row[1][1]
                new_x, new_y = transformer.transform(old_x, old_y)

                row[1] = new_x, new_y

                ucursor.updateRow(row)

        arcpy.DefineProjection_management(env_path, target_wkt)

    except Exception as err:
        arcpy.AddMessage("{0} feature classinda hata aldik : {1}".format(fc, str(err)))

# edit.stopOperation()
edit.stopEditing(True)
