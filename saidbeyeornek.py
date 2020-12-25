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
import os
from arcpy import env
from io import open

report_choice_list = ['Rapor 1', 'Rapor 2', 'Rapor 3', 'Rapor 4', 'Rapor 5', ]
# https://bootswatch.com/4/superhero/bootstrap.css

base_html_head = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Said Bey {report_title} </title>

    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootswatch/4.5.2/cerulean/bootstrap.min.css">

    <style>      
      th {
        background-color: #ea6053;
        color: white;
        font-size: 15px;
        text-align: center;
      }

      .umut-table-style {
          width: 600px;
          text-anchor: middle;
          column-width: 600px;
          font-size: 15px;
          float: left;
      }

      .parcel-detail-table-style {
          width: 800px;
          text-anchor: middle;
          column-width: 600px;
          font-size: 15px;
          float: left;
      }

      .parcel-mini-table-style {
          margin-left: 2px;
          font-size: 15px;
      }

      .parcel-aratable-style{
          float: left;
      }

      .mini-table-style {
          padding-left: 5em;
          font-size: 15px;
          float: left;
          margin-top: -50px;
          margin-left: 10px;
      }

      .yapi-icmal-style {
          width: 600px;
          text-anchor: middle;
          column-width: 600px;
          font-size: 15px;
      }

      .peml-table-style {
          margin-top: 10px;
          width: 600px;
          text-anchor: middle;
          column-width: 600px;
          font-size: 15px;
      }

    </style>
</head>
"""
pd.options.display.float_format = '{:,.3f}'.format
pd.set_option('display.width', 100)


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "SaidBeyToolbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [SaidBeyToolbox]


class SaidBeyToolbox(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "SaidBeyToolbox"
        self.description = "Sececeginiz rapor HTML olarak hazirlanir."
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
        report_type = arcpy.Parameter(
            displayName="Rapor Seciniz",
            name="report_type",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )

        out_html = arcpy.Parameter(
            displayName="Output HTML",
            name="out_html",
            datatype="DEFile",
            parameterType="Derived",
            direction="Output"
        )

        report_type.filter.list = report_choice_list
        params = [report_type, out_html]
        return params

    def table_to_data_frame(self, in_table, input_fields=None, where_clause=None, **kwargs):
        """
        Veriler da.SearchCursor kulanilarak DB'den alinip pandas dataframe yapilir.

        :param in_table:
        :param input_fields:
        :param where_clause:
        :param kwargs: ek parametreler sonradan fonksiyona eklenebilir
        :return:
        """
        try:
            OIDFieldName = arcpy.Describe(in_table).OIDFieldName
            if input_fields:
                final_fields = [OIDFieldName] + input_fields
            else:
                final_fields = [field.aliasName for field in arcpy.ListFields(in_table)]

            try:
                data = [row for row in arcpy.da.SearchCursor(in_table, final_fields, where_clause=where_clause)]

            except RuntimeError:
                final_fields = [f.name for f in arcpy.ListFields(in_table)]
                data = [row for row in arcpy.da.SearchCursor(in_table, final_fields, where_clause=where_clause)]

            fc_dataframe = pd.DataFrame(data, columns=final_fields)
            fc_dataframe = fc_dataframe.set_index(OIDFieldName, drop=True)

            return fc_dataframe
        except OSError as err:
            arcpy.AddError("Veritabaninda {0} view'i bulunamadigi icin rapor uretilemedi. \n".format(in_table))
            arcpy.AddError("Hata : {0}".format(err))

            sys.exit(0)

    def execute(self, parameters, messages):
        workspace = r""  # todo: SAID BEY BURAYA SDE CONNECTION ADRESI VERILIR
        env.workspace = workspace
        report_type = parameters[0].valueAsText

        arcpy.AddMessage("pandas version : {0}".format(pd.__version__))

        if report_type == report_choice_list[0]:
            # Rapor 1
            arcpy.AddMessage("Rapor 1 secildi")
            rapor_html = base_html_head.replace("{report_title}", "Rapor 1 ")
            name = "rapor1.html"

            added_first_text = f"<h2 style='color:black;'>Rapor 1</h2>" \
                               f"<hr>"
            rapor_html += added_first_text

            df_detail = self.table_to_data_frame('DBADI.SDE.TABLOADI',
                                                 donotdelete=['ykibedinimyontemi'])
            df_detail = df_detail.fillna('Kayit Yok')
            df_detail.drop(['Yapi_ID'], inplace=True, errors='ignore')

            # datetime formatting
            df_detail['TARIHSUTUNUORNEK'] = pd.to_datetime(df_detail['TARIHSUTUNUORNEK'],
                                                           errors='coerce').dt.strftime('%d-%m-%Y')

            # formatting nulls
            df_detail.loc[df_detail['GuncelDurum'].isnull(), 'GuncelDurum'] = 'YKIB_KAYITYOK'

            # Column formatting
            df_detail.rename(columns={'x_durumu': 'X Durumu', 'XGuncelDurum': 'X Guncel Durum',
                                      'YDurum': 'Y Durum', 'Yyontemi': 'Y Yöntemi',
                                      'Yapi_ID': 'Yapı ID'},
                             inplace=True)

            # Step 1
            # Özet rapor hazirlamak
            df_summary = df_detail.copy()
            df_detail = df_detail.replace('Kayit Yok', np.nan)

            # Pivot table
            df_sum_pivot = pd.crosstab(df_summary['Malik'], columns=[df_summary['X Durumu'],
                                                                     df_summary['x Guncel Durum'],
                                                                     df_summary['Y Durum'],
                                                                     df_summary['Y Yöntemi']], dropna=False)

            df_sum_pivot.rename(columns={'rowid': 'INDEX', 'disinda': 'Dışında', 'icinde': 'İçinde'}, inplace=True)
            # ordering OEB Durumu
            df_sum_pivot = df_sum_pivot.reindex(columns=['İçinde', 'Dışında'], level=0)

            arcpy.AddMessage("Pivot dataframe was created")

            # Genel toplam row added
            df_sum_pivot_columns = list(df_sum_pivot.columns)
            df_sum_pivot[df_sum_pivot_columns] = df_sum_pivot[df_sum_pivot_columns].apply(pd.to_numeric, errors='raise',
                                                                                          axis=1)

            df_sum_pivot.loc['Dikey Toplam'] = df_sum_pivot.sum(axis=0)
            df_sum_pivot.loc[:, 'Yatay Toplam'] = df_sum_pivot.sum(axis=1)

            # dataframe html style ayarlari
            df_sum_pivot_html_style = df_sum_pivot.style
            df_sum_pivot_html_style.set_properties(**{'width': '600px', 'text-align': 'center'})
            df_sum_pivot_html_style = df_sum_pivot_html_style.set_table_attributes(
                'border="1" class=dataframe table table-hover table-bordered')
            df_sum_pivot_html_style_rendered = df_sum_pivot_html_style.render().replace('YKIB', 'YKİB')

            # index to column
            df_detail.reset_index(inplace=True)
            df_detail.rename(columns={'index': 'Sıra No'}, inplace=True)

            # son yazilar
            added_text = f"<h2 style='color: blue;'>Rapor 1 Öznitelik Tablo Listesi</h2>" \
                         f"Toplam Kayıt Sayısı : {len(df_detail)}"
            arcpy.AddMessage("Columns renaming completed")

            # formatting records
            df_detail['ORNEKSUTUN'] = df_detail['ORNEKSUTUN'].replace('None', "Kayıt Yok")

            # sorting formatting
            df_detail.sort_values(['SIRALAMAKISTEDIGIMSUTUN'], inplace=True)
            # index ekle
            df_detail['Sıra No'] = np.arange(start=1, stop=len(df_detail) + 1)

            # export html
            df_detail_style = df_detail.style
            df_detail_style.set_properties(**{'width': '600px', 'text-align': 'center'})
            df_detail_style = df_detail_style.set_table_attributes(
                'border="1" class=dataframe table table-hover table-bordered')

            df_detail_html = df_detail_style.hide_index().render(). \
                replace('NaT', '').replace('None', '').replace('nan', '').replace('YKIB', 'YKİB')
            arcpy.AddMessage("Detail dataframe was created")

            result_html = rapor_html + "<br>" + df_sum_pivot_html_style_rendered + 2 * "<br>" + added_text + df_detail_html
            result_html = result_html.replace('icinde', 'İçinde').replace('disinda', 'Dışında')

        elif report_type == report_choice_list[1]:
            # todo: kendi raporum 2 gelir.
            arcpy.AddMessage("Rapor 2 secildi")
            rapor_html = base_html_head.replace("{report_title}", "Rapor 2 ")
            name = "rapor1.html"

            df_detail_html = pd.DataFrame().to_html()
            added_text = ""

            # HTML Convert
            added_first_text = f"<h2 style='color:black;'>Rapor 2</h2>" \
                               f"<hr>"
            rapor_html += added_first_text
            result_html = rapor_html + "<br>" + 2 * "<br>" + added_text + df_detail_html
            result_html = result_html.replace('icinde', 'İçinde').replace('disinda', 'Dışında')

        elif report_type == report_choice_list[2]:
            arcpy.AddMessage("Rapor 3 secildi")
            rapor_html = base_html_head.replace("{report_title}", "Rapor 3 ")
            name = "rapor1.html"

            df_detail_html = pd.DataFrame().to_html()
            added_text = ""

            # HTML Convert
            added_first_text = f"<h2 style='color:black;'>Rapor 2</h2>" \
                               f"<hr>"
            rapor_html += added_first_text
            result_html = rapor_html + "<br>" + 2 * "<br>" + added_text + df_detail_html
            result_html = result_html.replace('icinde', 'İçinde').replace('disinda', 'Dışında')

        elif report_type == report_choice_list[3]:
            arcpy.AddMessage("Rapor 4 secildi")
            rapor_html = base_html_head.replace("{report_title}", "Rapor 4 ")
            name = "rapor1.html"

            df_detail_html = pd.DataFrame().to_html()
            added_text = ""

            # HTML Convert
            added_first_text = f"<h2 style='color:black;'>Rapor 2</h2>" \
                               f"<hr>"
            rapor_html += added_first_text
            result_html = rapor_html + "<br>" + 2 * "<br>" + added_text + df_detail_html
            result_html = result_html.replace('icinde', 'İçinde').replace('disinda', 'Dışında')

        elif report_type == report_choice_list[4]:
            arcpy.AddMessage("Rapor 5 secildi")
            rapor_html = base_html_head.replace("{report_title}", "Rapor 5 ")
            name = "rapor1.html"

            df_detail_html = pd.DataFrame().to_html()
            added_text = ""

            # HTML Convert
            added_first_text = f"<h2 style='color:black;'>Rapor 2</h2>" \
                               f"<hr>"
            rapor_html += added_first_text
            result_html = rapor_html + "<br>" + 2 * "<br>" + added_text + df_detail_html
            result_html = result_html.replace('icinde', 'İçinde').replace('disinda', 'Dışında')

        else:
            msg = "Seceneklerde olmayan bir rapor secildi. Lutfen dokumandan yardim aliniz."
            result_html = pd.DataFrame({'error': msg}).to_html(index=False, justify='center',
                                                               classes='umut-table-style')
            name = "error.html"
            arcpy.AddError(msg)

        output_folder = arcpy.env.scratchWorkspace
        if output_folder.endswith('.gdb'):
            output_folder = arcpy.env.scratchFolder

        out_job_path = os.path.join(output_folder, name)
        arcpy.AddMessage("html output path : {0}".format(out_job_path))

        with open(out_job_path, 'w', encoding='utf-8') as writer:
            writer.write(result_html)

        writer.close()

        arcpy.AddMessage("HTML Output was created : {0}".format(out_job_path))

        arcpy.AddMessage("Before setting parameter")
        arcpy.SetParameter(1, out_job_path)
        return
