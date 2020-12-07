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

report_choice_list = ['Yerlesim Alani Genel Arazi Icmali (Yapi)',
                      'Yapi Emlak Vergisi Icmali',
                      'Yerlesim Alani Genel Arazi Icmali (Parsel)',
                      'Parsel Emlak Vergisi Icmali',
                      'Yapi Dava Takip Raporu',
                      'Parsel Dava Takip Raporu',
                      'Kiralama Raporu']
# https://bootswatch.com/4/superhero/bootstrap.css

base_html_head = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>ISDEMIR {report_title} </title>

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


@staticmethod
def column_cleaner(df, *additional_fields, **kwargs):
    static_fields = ["yapi_oid", "OBJECTID", "shape", "SHAPE", "SHAPE.STArea()", "SHAPE.STLength()", "rowid",
                     "shape.STArea()", "shape.STLength()",

                     "TabanAlani", "Mahalle_Koy", "YapiMulkiyeti", "Unite", "yapidurum", "Kalorifer", "KatSayisi",
                     "YapimTarihi", "yapiaciklama", "YapiRiskDurumu", "YikimTarihi", "YikimTarihi",
                     "ykibedinimyontemi", "edinimyontemiaciklama", "ykibaciklama", "YapiRuhsatBasvuruTarihi",
                     "yapi_durum", "ruhsat_aciklama", "yapi_ruhsat_kapsami", "yapi_id", "mahalle_koy",
                     "yapi_mulkiyeti", "malik", "tip", "alttip", "VRH_Kurum", "Yapi_Durumu", "odemetipi", "Kurulus",
                     "OdemeTarihi", "OdemeYili", "OdemeTutari", "OdemeTutarBirimi", "odemeaciklama", "created_user",
                     "created_date", "last_edited_user", "last_edited_date", "SDE_STATE_ID"]

    if kwargs.get('donotdelete'):
        static_fields = [i for i in static_fields if i not in kwargs['donotdelete']]

    if not additional_fields:
        for f in additional_fields:
            static_fields.append(f)
    try:
        df.drop(columns=static_fields, errors="ignore", inplace=True)

    except:
        df = df[[i for i in df.columns if i not in static_fields]]

    return df


def table_to_data_frame(self, in_table, fix_fields=True, input_fields=None, where_clause=None, **kwargs):
    """Function will convert an arcgis table into a pandas dataframe with an object ID index, and the selected
    input fields using an arcpy.da.SearchCursor."""
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

        if fix_fields:
            if kwargs.get('donotdelete'):
                column_cleaner(fc_dataframe, **kwargs)

            else:
                column_cleaner(fc_dataframe)

        return fc_dataframe
    except OSError as err:
        arcpy.AddError("Veritabaninda {0} view'i bulunamadigi icin rapor uretilemedi. \n".format(in_table))
        arcpy.AddError("Hata : {0}".format(err))

        sys.exit(0)


def find_genel_toplam_indexes(df, text='Genel Toplam'):
    r_c = df.loc[df['KULLANIM AMACI'] == text]['KULLANIM AMACI'].index.tolist()
    return r_c


def find_malik_indexes(df, maliks):
    r_c = []
    for index, row in df.iterrows():
        arcpy.AddMessage(row['KULLANIM AMACI'])
        if row['KULLANIM AMACI'] in maliks:
            r_c.append(index)

    return r_c


def ada_parsel_merger(df, adafield='Ada No', parselfield='Parsel No', mergerfield='Ada Parsel', sep='/'):
    df[mergerfield] = df[[adafield, parselfield]].apply(lambda row: sep.join(row.values.astype(str)), axis=1)
    return df


def make_column_nth_order(df, column_name, order):
    df_columns = list(df.columns)
    df_columns.remove(column_name)
    df_columns.insert(order, column_name)
    df = df[[i for i in df_columns]]

    return df


# Parsel Dava Takip Raporu
arcpy.AddMessage("Parsel Dava Takip Raporu secildi.")
icmal_html = base_html_head.replace("{report_title}", "İsdemir Parsel Dava Takip Raporu ")
name = "parsel_dava_takip_report.html"

clean_fields = ["p_oid", "parselid", "AlanBuyuklugu", "ParselNitelik", "ImarDurumu",
                "ParselMulkiyet", "Malik", "parselaciklama", "davadegeribirimi", "rowid",
                "shape.STArea()", "shape.STLength()"]

df_detail = table_to_data_frame("ISD_NEW.dbo.Parsel_Geo_HK_Icmal_Sorgusu")
df_detail = df_detail[[i for i in df_detail.columns if i not in clean_fields]]

# formatting
df_detail = df_detail.drop(labels=['p_oid'], errors='ignore')

# specific column formatting
df_detail.rename(columns={'ILCE_ADI': 'İlçe Adı', 'adano': 'Ada No', 'ParselNo': 'Parsel No',
                          'Kullanimsekli': 'Kullanım Şekli', 'davaacilistarihi': 'Dava Açılış Tarihi',
                          'esasno': 'Esas No', 'kararno': 'Karar No', 'karartarihi': 'Karar Tarihi',
                          'davadurumu': 'Dava Durumu', 'davasonucu': 'Dava Sonucu',
                          'davadegeri': 'Dava Degeri', 'davaci': 'Davacı', 'davali': 'Davalı',
                          'hukukaciklama': 'Hukuki Açıklama', 'rowid': 'Sıra No', 'adliye': 'Adliye',
                          'merci': 'Merci', 'davano': 'Dava No', 'davakonusu': 'Dava Konusu'},
                 inplace=True)
arcpy.AddMessage("DF Detail is ready")

# delete index row
df_detail.reset_index(inplace=True)
df_detail.rename(columns={'rowid': 'Sıra No'}, inplace=True)

# formatting
df_detail.index.names = ['Sıra No']

# formatting values
df_detail['Dava Açılış Tarihi'] = df_detail['Dava Açılış Tarihi'].dt.strftime('%d-%m-%Y')

# Ada Parsel
df_detail['Ada No'] = df_detail['Ada No'].astype(float).map('{:.0f}'.format)
# NOT : Parsel no coalesce

df_detail = ada_parsel_merger(df_detail)
df_detail.drop(columns=['Ada No', 'Parsel No'], inplace=True)

# Ada Parsel to leftest
df_detail = make_column_nth_order(df_detail, 'Ada Parsel', order=1)

df_detail_style = df_detail.style
df_detail_style = df_detail_style.set_properties(**{'width': '600px', 'text-align': 'left'})
df_detail_style = df_detail_style.set_table_attributes(
    'border="1" class=dataframe table table-hover table-bordered')

df_detail_style = df_detail_style.set_table_styles(
    [{
        'selector': 'td',
        'props': [
            ('vertical-align', 'top'),
            ('text-align', 'left')]
    },
        {
            'selector': 'th:nth-child(19)',
            'props': [
                ('width', '50%')
            ]
        },
        {
            'selector': 'th',
            'props': [
                ('background-color', '#2880b8'),
                ('color', 'white')]
        }
    ]
)
df_detail_style_html = df_detail_style.hide_index().render().replace('nan', '').replace('None', '')

added_text = f"<h2 style='color:black;'>PARSEL DAVA TAKİP RAPORU</h2>" \
             f"<hr>"
added_text += f"Toplam Kayıt Sayısı : {len(df_detail)}"

result_html = icmal_html + 2 * "<br>" + added_text + "<br>" + df_detail_style_html
