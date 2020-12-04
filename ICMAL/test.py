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


def column_cleaner(df, *additional_fields, **kwargs):
    static_fields = ["yapi_oid", "OBJECTID", "shape", "SHAPE", "SHAPE.STArea()", "SHAPE.STLength()", "rowid",
                     "shape.STArea()", "shape.STLength()",

                     "TabanAlani", "Mahalle_Koy", "YapiMulkiyeti", "Unite", "yapidurum", "Kalorifer", "KatSayisi",
                     "YapimTarihi", "yapiaciklama", "YapiRiskDurumu", "YikimTarihi", "YikimTarihi",
                     "ykibedinimyontemi", "edinimyontemiaciklama", "ykibaciklama", "YapiRuhsatBasvuruTarihi",
                     "yapi_durum", "ruhsat_aciklama", "yapi_ruhsat_kapsami", "yapi_id", "mahalle_koy",
                     "yapi_mulkiyeti", "malik", "tip", "alttip", "VRH_Kurum", "Yapi_Durumu", "odemetipi", "Kurulus",
                     "OdemeTarihi", "OdemeYili", "OdemeTutari", "OdemeTutarBirimi", "odemeaciklama"]

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


def table_to_data_frame(in_table, fix_fields=True, input_fields=None, where_clause=None, **kwargs):
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


workspace = r"C:\YAYIN\cbsarcgisew.sde"
env.workspace = workspace

# Yapi Icmali: Yapi_Geo_Icmal_Sorgusu (Detay) - Summary
# Sıra noyu tepeye almayı burada başardık

arcpy.AddMessage("Yapi Icmali secildi")
icmal_html = base_html_head.replace("{report_title}", "Yerlesim Alani Genel Arazi Icmali (Yapi) ")
name = "yapi_icmali.html"

added_first_text = f"<h2 style='color:black;'>İsdemir Yerleşim Alanı Genel Arazi İcmali</h2>" \
                   f"<hr>"
icmal_html += added_first_text

df_detail = table_to_data_frame('ISD_NEW.dbo.Yapi_Geo_Icmal_Sorgusu',
                                     donotdelete=['ykibedinimyontemi'])
df_detail.drop(['Yapi_ID'], inplace=True, errors='ignore')

# datetime formatting
df_detail['Ykib_Tarihi'] = pd.to_datetime(df_detail['Ykib_Tarihi'],
                                          errors='coerce').dt.strftime('%d-%m-%Y')
df_detail['RuhsatAlinmaTarihi'] = pd.to_datetime(df_detail['RuhsatAlinmaTarihi'],
                                                 errors='coerce').dt.strftime('%d-%m-%Y')

# formatting nulls
df_detail.loc[df_detail['GuncelDurum'].isnull(), 'GuncelDurum'] = 'YKIB_KAYITYOK'
df_detail.loc[df_detail['RuhsatGuncelDurum'].isnull(), 'RuhsatGuncelDurum'] = 'RUHSAT_KAYITYOK'

# formatting ALINMADI
df_detail['GuncelDurum'] = df_detail['GuncelDurum'].replace(['Alındı'], 'YKIB_ALINDI')
df_detail['GuncelDurum'] = df_detail['GuncelDurum'].replace(['Alınmadı'], 'YKIB_ALINMADI')

df_detail['RuhsatGuncelDurum'] = df_detail['RuhsatGuncelDurum'].replace(['Alındı'], 'RUHSAT_ALINDI')
df_detail['RuhsatGuncelDurum'] = df_detail['RuhsatGuncelDurum'].replace(['Alınmadı'], 'RUHSAT_ALINMADI')

df_detail.rename(columns={'oeb_durumu': 'OEB Durumu', 'RuhsatGuncelDurum': 'Ruhsat Durum',
                          'GuncelDurum': 'YKIB Durum', 'ykibedinimyontemi': 'YKIB Edinim Yöntemi',
                          'Yapi_ID': 'Yapı ID'},
                 inplace=True)

# Step 1
# oeb icindekiler alinir, gereksiz sutunlar silinir
df_summary = df_detail.copy()

# imar barışı tricking
# df_summary.loc[df_summary['YKIB Edinim Yöntemi'] == 'İmar Barışı', 'YKIB Durum'] = 'İmar Barışı'
df_sum_pivot = pd.crosstab(df_summary['Malik'], columns=[df_summary['OEB Durumu'],
                                                         df_summary['Ruhsat Durum'],
                                                         df_summary['YKIB Durum'],
                                                         df_summary['YKIB Edinim Yöntemi']], dropna=False)

df_sum_pivot.rename(columns={'rowid': 'INDEX', 'disinda': 'Dışında', 'icinde': 'İçinde',
                             'YKIB_ALINDI': 'YKIB ALINDI', 'YKIB_KAYITYOK': 'YKIB KAYDI YOK',
                             'RUHSAT_ALINMADI': 'RUHSAT ALINMADI', 'RUHSAT_ALINDI': 'RUHSAT ALINDI',
                             'RUHSAT_KAYITYOK': 'RUHSAT KAYDI YOK', 'YKIB_ALINMADI': 'YKIB ALINMADI'
                             }, inplace=True)
# ordering OEB Durumu
df_sum_pivot = df_sum_pivot.reindex(columns=['İçinde', 'Dışında'], level=0)

arcpy.AddMessage("Pivot dataframe was created")

# Genel toplam row added
df_sum_pivot_columns = list(df_sum_pivot.columns)
df_sum_pivot[df_sum_pivot_columns] = df_sum_pivot[df_sum_pivot_columns].apply(pd.to_numeric, errors='raise',
                                                                              axis=1)

df_sum_pivot.loc['Dikey Toplam'] = df_sum_pivot.sum(axis=0)
df_sum_pivot.loc[:, 'Yatay Toplam'] = df_sum_pivot.sum(axis=1)

# İsdemir malik en tepeye alinacak.. reindexing
df_sum_pivot_indexes = df_sum_pivot.index.to_list()
df_sum_pivot_indexes.remove('İsdemir')
df_sum_pivot_indexes.insert(0, 'İsdemir')
df_sum_pivot = df_sum_pivot.reindex(df_sum_pivot_indexes)

df_sum_pivot_html_style = df_sum_pivot.style
df_sum_pivot_html_style.set_properties(**{'width': '600px', 'text-align': 'center'})
df_sum_pivot_html_style = df_sum_pivot_html_style.set_table_attributes(
    'border="1" class=dataframe table table-hover table-bordered')
df_sum_pivot_html_style_rendered = df_sum_pivot_html_style.render().replace('YKIB', 'YKİB')

# Last step
df_detail.rename(columns={'YapiAdi': 'Yapı Adı', 'Yapi_No': 'Yapı No',
                          'AdaNo': 'Ada No', 'ParselNo': 'Parsel No', 'KullanimSekli': 'Kullanım Şekli',
                          'InsaatTuru': 'İnşaat Türü', 'YapiSinifi': 'Yapı Sınıfı',
                          'ToplamInsaatAlani': 'Toplam İnşaat Alanı (m²)', 'ILCE_ADI': 'İlçe Adı',
                          'Ykib_BelgeTuru': 'YKIB Belge Türü',
                          'Ykib_Tarihi': 'YKIB Tarihi', 'YkibNo': 'YKIB No',
                          'RuhsatBelgeTuru': 'Ruhsat Belge Türü',
                          'RuhsatAlinmaTarihi': 'Ruhsat Alınma Tarihi', 'RuhsatNo': 'Ruhsat No',
                          'ykibedinimyontemi': 'YKIB Edinim Yöntemi', 'oeb_durumu': 'OEB Durumu',
                          'rowid': 'Sıra No'}, inplace=True, errors='ignore')

# index to column
df_detail.reset_index(inplace=True)
df_detail.rename(columns={'rowid': 'Sıra No'}, inplace=True)

# son yazilar
added_text = f"<h2 style='color: blue;'>İSDEMİR YAPI LİSTESİ</h2>" \
             f"Toplam Kayıt Sayısı : {df_detail.count()['Ada No']}"
arcpy.AddMessage("Columns renaming completed")

# formatting records
df_detail['İnşaat Türü'] = df_detail['İnşaat Türü'].replace('None', "Kayıt Yok")
df_detail['YKIB Tarihi'] = df_detail['YKIB Tarihi'].astype(str).replace({"NaT": "Kayıt Yok"})
arcpy.AddMessage("filling null values completed")

# Ada Parsel issue
df_detail['Ada No'] = df_detail['Ada No'].astype(float).map('{:,.0f}'.format)
df_detail['Ruhsat No'] = df_detail['Ruhsat No'].astype(float).map('{:,.0f}'.format)
df_detail['Yapı ID'] = df_detail['Yapı ID'].astype(float).map('{:,.0f}'.format)
df_detail['Toplam İnşaat Alanı (m²)'] = df_detail['Toplam İnşaat Alanı (m²)'].astype(float).map(
    '{:,.2f}'.format)

df_detail = ada_parsel_merger(df_detail)
df_detail.sort_values(['Yapı No'], inplace=True)
df_detail.drop(columns=['Ada No', 'Parsel No'], inplace=True)

# Ada Parsel to leftest
df_detail = make_column_nth_order(df_detail, 'Ada Parsel', order=4)

# export html
df_detail_style = df_detail.style
df_detail_style.set_properties(**{'width': '600px', 'text-align': 'center'})
df_detail_style = df_detail_style.set_table_attributes(
    'border="1" class=dataframe table table-hover table-bordered')

df_detail_html = df_detail_style.hide_index().render(). \
    replace('NaT', '').replace('None', '').replace('nan', '').replace('YKIB', 'YKİB')
arcpy.AddMessage("Detail dataframe was created")

result_html = icmal_html + "<br>" + df_sum_pivot_html_style_rendered + 2 * "<br>" + added_text + df_detail_html
result_html = result_html.replace('icinde', 'İçinde').replace('disinda', 'Dışında')