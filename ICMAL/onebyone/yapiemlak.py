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


# Yapi Emlak Vergisi Icmali
# todo: Sıra no 1'den baslayacak
arcpy.AddMessage("Yapi Emlak Icmali secildi.")
icmal_html = base_html_head.replace("{report_title}", "Yapı Emlak Vergisi Icmali")
name = "bina_emlak_icmali.html"

added_first_text = f"<h1 style='color:black;'>İsdemir Yapı Emlak Vergisi İcmali</h1>" \
                   f"<hr>"
icmal_html += added_first_text

df_detail = table_to_data_frame("ISD_NEW.dbo.YAPI_EMLAK_ICMAL_VW")
df_summary = table_to_data_frame("ISD_NEW.dbo.YAPI_EML_ICMAL_VW")

df_summary.loc['Genel Toplam'] = df_summary.sum(numeric_only=True, axis=0)
df_summary = df_summary.replace(np.nan, 'Genel Toplam', regex=True)
df_summary = df_summary.replace('Iliskisiz', 'İlişkisiz', regex=True)
df_summary.index.names = ['INDEX']

# formatting for columns
df_summary.rename(columns={'Emlakvergisi_durumu': 'Emlak Vergisi Durumu', 'TOPLAM': 'Adet Sayısı',
                           'TOPLAM_INSAAT_ALAN': 'Toplam (m²)'}, inplace=True)

df_detail.rename(columns={'YapiAdi': 'Yapı Adı', 'yapi_no': 'Yapı No', 'AdaNo': 'Ada No',
                          'ParselNo': 'Parsel No', 'katsayisi': 'Kat Sayısı', 'yapimtarihi': 'Yapım Tarihi',
                          'asansor': 'Asansör', 'kalorifer': 'Kalorifer', 'KullanimSekli': 'Kullanım Şekli',
                          'yapimulkiyeti': 'Yapı Mülkiyeti', 'InsaatTuru': 'İnşaat Türü',
                          'ToplamInsaatAlani': 'Toplam İnşaat Alanı (m²)', 'ILCE_ADI': 'İlçe Adı',
                          'Emlakvergisi_durumu': 'Emlak Vergisi Durumu',
                          'EmlakInsaatSinifi': 'Emlak İnşaat Sınıfı',
                          }, inplace=True)

df_detail['Ada No'] = df_detail['Ada No'].astype(float).map('{:,.0f}'.format)
df_detail['Kat Sayısı'] = df_detail['Kat Sayısı'].astype(float).map('{:,.0f}'.format)
df_detail['Toplam İnşaat Alanı (m²)'] = df_detail['Toplam İnşaat Alanı (m²)'].astype(float).map(
    '{:,.2f}'.format)
df_detail['Emlak İnşaat Sınıfı'] = df_detail['Emlak İnşaat Sınıfı'].astype(float).map('{:,.0f}'.format)

# datetime formatting
df_detail['Yapım Tarihi'] = pd.to_datetime(df_detail['Yapım Tarihi'], errors='coerce')

# sorting
df_detail.sort_values('Yapı No', inplace=True)

# record formatting
df_detail['Yapım Tarihi'] = pd.to_numeric(df_detail['Yapım Tarihi'].dt.year,
                                          errors='coerce').astype(float).map('{:.0f}'.format)
df_detail = ada_parsel_merger(df_detail)

# delete index row
df_detail.reset_index(inplace=True)
df_detail.rename(columns={'rowid': 'Sıra No'}, inplace=True)

# delete Malik
df_detail.drop(columns=['Malik', 'Ada No', 'Parsel No'], inplace=True)

df_detail = df_detail.replace('nan', '', regex=True)
df_summary = df_summary.replace('nan', '', regex=True)

# sorting columns
new_sorted_columns = list(df_detail.columns)
new_sorted_columns.remove('Yapı Adı')
new_sorted_columns.insert(1, 'Yapı Adı')

df_detail = df_detail.reindex(new_sorted_columns, axis=1)

# resetting index
df_detail['Sıra No'] = np.arange(df_detail.shape[0])

# Ada Parsel to leftest
df_detail = make_column_nth_order(df_detail, 'Ada Parsel', 3)

# export html
df_detail_style = df_detail.style
df_detail_style = df_detail_style.set_properties(**{'width': '600px', 'text-align': 'center'})
df_detail_style = df_detail_style.set_properties(subset=['Yapı Adı'], **{'text-align': 'left'})

df_detail_style = df_detail_style.set_table_attributes(
    'border="1" class=dataframe table table-hover table-bordered')
df_detail_style = df_detail_style.set_table_styles(
    [
        {
            'selector': 'th',
            'props': [
                ('background-color', '#2880b8'),
                ('color', 'white')]
        },
        {
            'selector': 'th:nth-child(0)',
            'props': [
                ('text-align', 'left')
            ]
        }
    ]
)
df_detail_style_html = df_detail_style.hide_index().render().replace('None', '')

df_summary['Adet Sayısı'] = df_summary['Adet Sayısı'].astype(float).map('{:,.0f}'.format)
df_summary['Toplam (m²)'] = df_summary['Toplam (m²)'].astype(float).map('{:,.2f}'.format)

# Emlak Vergisi Index sorting
custom_evd_sort = ['Verilen', 'Verilecek', 'İnşaatı Devam Ediyor', 'Muaf', 'İlişkisiz', 'Genel Toplam']

# make evd as index and sort and make column again
df_summary = df_summary.set_index(['Emlak Vergisi Durumu']).reindex(custom_evd_sort).reset_index()

# styling
df_sum_html = df_summary.style
df_sum_html = df_sum_html.set_table_styles(
    [{
        'selector': 'th',
        'props': [
            ('background-color', '#2880b8'),
            ('color', 'white')]
    }]
)
df_sum_html = df_sum_html.set_properties(**{'width': '150px', 'text-align': 'center'})
df_sum_html = df_sum_html.set_table_attributes(
    'border="1" class=dataframe table table-hover table-bordered')

df_sum_html = df_sum_html.apply(
    lambda x: ['background: #ea6053; font-weight: bold' if x['Emlak Vergisi Durumu'] == 'Genel Toplam'
               else '' for i in x], axis=1)

last_added_text = f"<h1 style='color:black;'>Yapı Emlak Vergi Listesi</h1>" \
                  f"<hr>"
last_added_text += f"Toplam Kayıt Sayısı : {len(df_detail)}"
df_sum_html = df_sum_html.hide_index().render()
df_sum_html = df_sum_html.replace('nan', 'Kayıt Yok')

result_html = icmal_html + 2 * "<br>" + df_sum_html + 4 * "<br>" \
              + last_added_text + df_detail_style_html