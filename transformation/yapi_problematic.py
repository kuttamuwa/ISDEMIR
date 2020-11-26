import arcpy

oids = []
with arcpy.da.SearchCursor('ISD_DEV.DBO.YAPI_MP', ['OBJECTID', 'SHAPE@']) as scursor:
    for row in scursor:
        if row[1].partCount > 1:
            oids.append(row[0])


cpp = {}
with arcpy.da.SearchCursor('ISD_NEW.DBO.YAPI_FROM_BACKUP', ["GLOBALIDBACKUP", "SHAPE@"]) as sCursor:
    for row in sCursor:
        cpp[row[0]] = row[1]


with arcpy.da.SearchCursor('ISD_NEW.DBO.YAPI_FROM_BACKUP', ['GLOBALIDBACKUP', 'SHAPE@']) as scursor:
    for row in scursor:
        guid = row[0]
        shape = row[1]
        with arcpy.da.UpdateCursor('YAPI', ['GLOBALIDBACKUP', 'SHAPE@'],
                                   where_clause="""GLOBALIDBACKUP = {0}""".format(guid)) as ucursor:
            for urow in scursor:
                urow[1] = shape

                ucursor.updateRow(urow)


with arcpy.da.UpdateCursor('YAPI', ['GlobalID', "SHAPE@"]) as uCursor:
    for row in uCursor:
            # Update the geometry if it's in cpp.
            recordId = row[0]
            if recordId in cpp:
                row[1] = cpp[recordId]
                uCursor.updateRow(row)