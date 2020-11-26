import arcpy
import pandas as pd

fclasses = arcpy.ListFeatureClasses("*")


# only for feature classes
domain_dict = []

for fc in fclasses:
    fields = arcpy.ListFields(fc, "*")

    for f in fields:
        if f.domain != '':
            domain_dict.append((fc, f.name, f.domain))
            print("domains : {0}".format(domain_dict))

df = pd.DataFrame(domain_dict)


# fc classes imported
tables = arcpy.ListTables("*")
domain_dict = []

for t in tables:
    fields = arcpy.ListFields(t, "*")

    for f in fields:
        if f.domain != '':
            domain_dict.append((t, f.name, f.domain))
            print("domains : {0}".format(domain_dict))

df = pd.DataFrame(domain_dict)