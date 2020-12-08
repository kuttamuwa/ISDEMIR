# -*- coding: utf-8 -*-
#

# Esri start of added imports
import sys, os, arcpy

# Esri end of added imports

# Esri start of added variables
from shutil import copyfile

g_ESRI_variable_2 = 'C:\\YAYIN\\outputcads'
# Esri end of added variables


"""
Generated by ArcGIS ModelBuilder on : 2020-10-02 11:37:57
"""
import os
import zipfile

import arcpy
from sys import argv

arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(2322)

input_feature = arcpy.GetParameterAsText(0)
out_feature = arcpy.GetParameterAsText(1)
cad_type = arcpy.GetParameterAsText(2)

feature_name = arcpy.Describe(input_feature).name
feature_pure_name = feature_name
arcpy.AddMessage("CAD Type : {0}".format(cad_type))

if cad_type == 'DWG':
    cad_type = '.dwg'
    output_type = 'DWG_R2013'

elif cad_type == 'DGN':
    cad_type = '.dgn'
    output_type = 'DGN_V8'

elif cad_type == 'DXF':
    cad_type = '.dxf'
    output_type = 'DXF_R2013'

else:
    cad_type = '.dwg'
    output_type = 'DWG_R2013'

if feature_name.count("."):
    feature_pure_name = feature_name.split(".")[-1]
    feature_name = feature_name.split(".")[-1] + cad_type
else:
    feature_name = feature_name + cad_type

output_cad = os.path.join(g_ESRI_variable_2, feature_name)

jobsDir = g_ESRI_variable_2

arcpy.conversion.ExportCAD(in_features=input_feature, Output_Type=output_type,
                           Output_File=output_cad, Ignore_FileNames="Ignore_Filenames_in_Tables",
                           Append_To_Existing="Overwrite_Existing_Files", Seed_File="")

outputZip = jobsDir + "\\" + feature_pure_name + ".zip"

zip = zipfile.ZipFile(outputZip, 'w', zipfile.ZIP_DEFLATED)
for file in os.listdir(jobsDir):
    if file.endswith(cad_type):
        if not file.endswith(".zip"):
            print(os.path.join(jobsDir, file))
            zip.write(os.path.join(jobsDir, file))

zip.close()

arcpy.AddMessage("Zip file created.")

output_folder = arcpy.env.scratchWorkspace
if output_folder.endswith('.gdb'):
    output_folder = arcpy.env.scratchFolder

out_job_path = os.path.join(output_folder, feature_name)
copyfile(output_cad, out_job_path)
arcpy.AddMessage("CAD output path : {0}".format(out_job_path))

arcpy.SetParameter(1, out_job_path)




