# coding=utf-8
# Esri start of added imports
from subprocess import call

import arcpy
import os
# import bs4
# import lxml

# Esri end of added imports
import pandas as pd
import numpy as np
import re
import sys
import warnings
from datetime import datetime as py_datetime
import string

# disable warnings
pd.options.mode.chained_assignment = None

# Esri start of added variables
import pip

g_ESRI_variable_1 = os.path.join(arcpy.env.packageWorkspace, u'html')
# Esri end of added variables

# !/usr/bin/env python
# -*- #################
# Author : Umut Ucok, MAPIT

# Prepared in Python3 - ArcGIS Pro

import arcpy


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "ISDEMIRToolbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [IcmalReportGenerator]


class IcmalReportGenerator(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "IcmalReportGenerator"
        self.description = "Sececeginiz icmalin raporu HTML olarak hazirlanir."
        self.canRunInBackground = False

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def getParameterInfo(self):
        """Define parameter definitions"""
        feature_set = arcpy.Parameter(
            displayName="Feature set giriniz",
            name="icmal_type",
            datatype="GPFeatureRecordSetLayer",
            parameterType="Required",
            direction="Input",
            symbology=r"Database Connections\Connection to localhost.sde\testsde.sde.AKARSU"
        )
        in_type = arcpy.Parameter(
            displayName="Feature tip giriniz",
            name="icmal_type",
            datatype="GPFeatureRecordSetLayer",
            parameterType="Required",
            direction="Input",
            symbology=r"Database Connections\Connection to localhost.sde\testsde.sde.AKARSU"
        )

        params = [feature_set]
        return params

    def execute(self, parameters, messages):
        pass
