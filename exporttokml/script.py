# -*- coding: utf-8 -*-
#

# Esri start of added imports
import sys, os, arcpy

# Esri end of added imports

# Esri start of added variables
from shutil import copyfile

g_ESRI_variable_2 = 'C:\\YAYIN\\outputkmls'
lgr = open('C:\\YAYIN\\outputkmls\\lgr.txt', 'w')

# Esri end of added variables

import os
import zipfile

import arcpy
from sys import argv

input_feature = arcpy.GetParameterAsText(0)
out_feature = arcpy.GetParameterAsText(1)

# describes
feature_name = arcpy.Describe(input_feature).name
feature_pure_name = feature_name
lgr.write("Feature pure name : {0} \n".format(feature_pure_name))

if feature_name.count("."):
    feature_pure_name = feature_name.split(".")[-1]
    feature_name = feature_name.split(".")[-1] + '.kmz'
else:
    feature_name = feature_name + '.kmz'

lgr.write("Feature pure, layer name : {0} \n".format(feature_pure_name))

output_kml = os.path.join(g_ESRI_variable_2, feature_name)
lgr.write("Output KML name : {0} \n".format(output_kml))

jobsDir = g_ESRI_variable_2

lyr = arcpy.MakeFeatureLayer_management(input_feature, feature_name)
arcpy.LayerToKML_conversion(lyr, output_kml)
arcpy.LayerToKML_conversion(input_feature, output_kml)

if arcpy.Exists(output_kml):
    lgr.write("KML was exported \n")

else:
    lgr.write("Export KML DID NOT WORK \n")

lgr.write("Layer to kml completed \n")

outputZip = jobsDir + "\\" + feature_pure_name + ".zip"
lgr.write("Output ZIP : {0} \n".format(outputZip))

zip = zipfile.ZipFile(outputZip, 'w', zipfile.ZIP_DEFLATED)
lgr.write("files : {0} \n".format(os.listdir(jobsDir)))

for file in os.listdir(jobsDir):
    if file.endswith('.kmz'):
        if not file.endswith(".zip"):
            print(os.path.join(jobsDir, file))
            zip.write(os.path.join(jobsDir, file))

zip.close()

lgr.write("Zip file created. \n")
lgr.write('scrachtworkspace : {0} \n'.format(arcpy.env.scratchWorkspace))

output_folder = arcpy.env.scratchWorkspace
if output_folder.endswith('.gdb'):
    output_folder = arcpy.env.scratchFolder

lgr.write('output folder : {0}'.format(output_folder))
out_job_path = os.path.join(output_folder, outputZip)
lgr.write("KML output path : {0}".format(out_job_path))
copyfile(output_kml, out_job_path)

arcpy.SetParameter(1, out_job_path)


