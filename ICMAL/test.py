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

# Parsel Icmali
workspace = r"C:\YAYIN\cbsarcgisew.sde"
env.workspace = workspace
arcpy.AddMessage("Parsel Icmali secildi")
icmal_html = base_html_head.replace("{report_title}", "Parsel Icmali ")
name = "parsel_icmal_report.html"

added_first_text = f"<h2 style='color:black;'>İsdemir Yerleşim Alanı Genel Arazi İcmali</h2>" \
                   f"<hr>"
icmal_html += added_first_text

clean_fields = ["OBJECTID", "Aciklama", "PaftaNo", "ParselUavt_Kodu", "Mahalle_Koy",
                "HisseOrani", "oeb_durumu", "SHAPE.STArea()", "SHAPE.STLength()"]

df_summary = table_to_data_frame("ISD_NEW.dbo.PARSEL_ICMALI_VW")
df_detail = df_summary.copy()
arcpy.AddMessage("Summary and Detail Dataframe were created")

df_summary.rename(columns={'Eski_Parsel_ID': 'parselid'}, inplace=True)

df_detail = df_detail[[i for i in df_detail.columns if i not in clean_fields]]

df_sums_html = []
maliks = df_summary['rapor_malik'].unique()

maliks_toplam = 0

df_groups = []
cnt = 0

for m in list(maliks):
    df_sum_malik = df_summary[df_summary['rapor_malik'] == m]

    if m is not None:
        grouped = df_sum_malik.groupby('rapor_kullanimi')
        if m == 'ISDEMIR_PARSELLERI':
            df_grouped = pd.DataFrame({'PARSEL SAYISI': grouped.count()['AlanBuyuklugu'],
                                       'ALAN TOPLAMI': grouped.sum()['HisseAlani']})
        else:
            df_grouped = pd.DataFrame({'PARSEL SAYISI': grouped.count()['AlanBuyuklugu'],
                                       'ALAN TOPLAMI': grouped.sum()['AlanBuyuklugu']})

        df_grouped.index.names = [m]

        # Genel toplam row added
        toplam = df_grouped.sum(numeric_only=True, axis=0)['ALAN TOPLAMI']

        df_grouped.loc['Genel Toplam'] = df_grouped.sum(numeric_only=True, axis=0)

        df_grouped['PARSEL SAYISI'] = df_grouped['PARSEL SAYISI'].astype(int)
        df_grouped['ALAN TOPLAMI'] = df_grouped['ALAN TOPLAMI'].astype(float).map('{:,.2f}'.format)

        df_grouped['KULLANIM AMACI'] = df_grouped.index

        # malik row to top
        letters = string.ascii_uppercase
        malik_row = pd.DataFrame({'KULLANIM AMACI': f'<b>{letters[cnt]}.) ' + m + '</b>',
                                  'PARSEL SAYISI': None, 'ALAN TOPLAMI': None}, index=[0])
        df_grouped = pd.concat([malik_row, df_grouped])

        # Genel toplamlar birlestirilir. minidf'de kullanilacak.
        maliks_toplam += toplam
        df_groups.append(df_grouped)

        cnt += 1

    else:
        grouped = df_sum_malik.groupby('rapor_kullanimi')
        df_grouped = pd.DataFrame({'PARSEL SAYISI': grouped.count()['AlanBuyuklugu'],
                                   'ALAN TOPLAMI': grouped.sum()['HisseAlani']})
        print(df_grouped)

all_in_one = pd.concat(df_groups, join='inner', axis=0)

# colorizing
all_in_one.index.names = ['INDEX']

# sorting
all_in_one = all_in_one[['KULLANIM AMACI', 'PARSEL SAYISI', 'ALAN TOPLAMI']]
all_in_one.rename(columns={'ALAN TOPLAMI': 'ALAN TOPLAMI (m²)'}, inplace=True)

all_in_one.reset_index(drop=True, inplace=True)

indexes = find_genel_toplam_indexes(all_in_one)
malik_indexes = find_malik_indexes(all_in_one, maliks)
arcpy.AddMessage("Indexes has been found !")

# adding one general last summary for all df in all in one
genel_toplam_df = all_in_one.iloc[indexes]
genel_toplam_df['ALAN TOPLAMI (m²)'] = genel_toplam_df['ALAN TOPLAMI (m²)'].str.replace(',', '').astype(
    float)

genel_toplam_df = genel_toplam_df.groupby(['KULLANIM AMACI']).agg(
    {'ALAN TOPLAMI (m²)': 'sum', 'PARSEL SAYISI': 'sum'})
genel_toplam_df['ALAN TOPLAMI (m²)'] = genel_toplam_df['ALAN TOPLAMI (m²)'].astype(float).map(
    '{:,.2f}'.format)
genel_toplam_df.reset_index(drop=True, inplace=True)
genel_toplam_df['KULLANIM AMACI'] = ['ISDEMIR YERLEŞİM ALANI GENEL TOPLAM']

all_in_one = pd.concat([all_in_one, genel_toplam_df])
# reset index
all_in_one.reset_index(inplace=True, drop=True)

style_indexes = find_genel_toplam_indexes(all_in_one)
style_indexes2 = find_genel_toplam_indexes(all_in_one, text='ISDEMIR YERLEŞİM ALANI GENEL TOPLAM')[0]
style_indexes.append(style_indexes2)

# all in one - ara tablo - styling
all_in_one_rendered = all_in_one.style.apply(lambda x: ['background: #ea6053' if x.name in style_indexes
                                                        else '' for i in x], axis=1)
all_in_one_rendered.apply(
    lambda x: ['colspan: 3' if x.name in malik_indexes else '' for i in x], axis=1)

all_in_one_rendered = all_in_one_rendered.apply(
    lambda x: ['background: #ea6053' if x['KULLANIM AMACI'] == 'ISDEMIR YERLEŞİM ALANI GENEL TOPLAM'
               else '' for i in x], axis=1)

all_in_one_rendered = all_in_one_rendered.set_table_styles(
    [
        {
            'selector': 'th',
            'props': [
                ('background-color', '#2880b8'),
                ('color', 'white')]
        }
    ]
)
all_in_one_rendered = all_in_one_rendered.set_properties(**{'width': '300px', 'height': '20px',
                                                            'text-align': 'left'})
all_in_one_rendered = all_in_one_rendered.apply(
    lambda x: ['color: white' if x['KULLANIM AMACI'] == 'Genel Toplam' else '' for i in x], axis=1)
all_in_one_rendered = all_in_one_rendered.apply(
    lambda x: ['color: white' if x['KULLANIM AMACI'] == 'ISDEMIR YERLEŞİM ALANI GENEL TOPLAM' else
               '' for i in x], axis=1)

all_in_one_rendered = all_in_one_rendered.set_table_attributes(
    'border="1" class=parcel-aratable-style')
all_in_one_rendered_html = all_in_one_rendered.hide_index().render()

all_in_one_rendered_html = all_in_one_rendered_html.replace('None', '')

df_sums_html.append(all_in_one_rendered_html)

# formatting
df_detail = df_detail.loc[:, ~df_detail.columns.duplicated()]
df_detail.drop(columns=[i for i in df_detail.columns if i.count('other') or i.count('caller')],
               inplace=True)

df_detail.rename(columns={'Eski_Parsel_ID': 'Parsel ID', 'AdaNo': 'Ada No',
                          'ParselNo': 'Parsel No', 'AlanBuyuklugu': 'Alan Büyüklüğü',
                          'Kullanimsekli': 'Kullanım Şekli', 'ImarDurumu': 'İmar Durumu',
                          'ParselMulkiyet': 'Parsel Mülkiyet',
                          'rapor_malik': 'Rapor Malik', 'rapor_kullanimi': 'Rapor Kullanımı',
                          'ILCE_ADI': 'İlçe Adı', 'ParselNitelik': 'Parsel Nitelik',
                          'HisseAlani': 'Hisse Alanı (m2)'}, inplace=True)
df_detail['Ada No'] = df_detail['Ada No'].astype(float).map('{:,.0f}'.format)
df_detail = ada_parsel_merger(df_detail)

# Ada Parsel to leftest
df_detail = make_column_nth_order(df_detail, 'Ada Parsel', order=3)

# number formatting for df detail
df_detail['Hisse Alanı (m2)'] = df_detail['Hisse Alanı (m2)'].astype(float).map('{:,.2f}'.format)
df_detail['Parsel ID'] = df_detail['Parsel ID'].astype(float).map('{:.0f}'.format)
df_detail['Alan Büyüklüğü'] = df_detail['Alan Büyüklüğü'].astype(float).map('{:,.2f}'.format)

# drop columns
df_detail_toplam_kayit = df_detail.count()['Ada No']
df_detail.drop(columns=['Ada No', 'Parsel No'], inplace=True)
df_detail = df_detail.replace('nan', '', regex=True)
df_detail = df_detail.replace('None', '', regex=True)
df_detail = df_detail.fillna('')

# delete index row
df_detail.reset_index(inplace=True)
df_detail.rename(columns={'rowid': 'Sıra No'}, inplace=True)

# export html
df_detail_html = df_detail.style
df_detail_html = df_detail_html.set_table_attributes(
    'border="1" class=parcel-detail-table-style')

df_detail_html = df_detail_html.set_properties(**{'width': '800px', 'height': '20px',
                                                  'text-align': 'center'})

arcpy.AddMessage("DF Detail html was created")

result_html = icmal_html

# mini table
mini_df = table_to_data_frame('ISD_NEW.dbo.PARSEL_ICMAL_MINI_VW')
mini_df.rename(columns={'rowid': 'INDEX', 'ParselNo': 'Veri Adı',
                        }, inplace=True)

genel_toplam = mini_df['TOPLAM_ALAN'].sum()

# mini_df.loc['Kalan Genel Yerleşim Alanı Toplam']
kalan_alan_gyt = float(maliks_toplam) - genel_toplam
arcpy.AddMessage(f"Genel toplam : {genel_toplam} \n "
                 f"Kalan Alan Genel Yerleşim Alanı Toplamı : {kalan_alan_gyt}")
mini_df = mini_df.append(
    {'Veri Adı': 'ISDEMIR YERLEŞİM ALANI GENEL TOPLAM', 'TOPLAM_ALAN': genel_toplam},
    ignore_index=True)

# Toplam column formatting
mini_df['TOPLAM_ALAN'] = mini_df['TOPLAM_ALAN'].astype(float).map('{:,.2f}'.format)
maliks_toplam = '{:,.2f}'.format(maliks_toplam)

# column renaming
mini_df.rename(columns={'Veri Adı': 'ISDEMIR YERLEŞİM ALANI GENEL TOPLAM', 'TOPLAM_ALAN': maliks_toplam},
               inplace=True)

# index populating -> will be removed later
mini_df['INDEX'] = mini_df.index

mini_df_style = mini_df.style
mini_df_style = mini_df_style.apply(
    lambda x: ['background: #ea6053' if int(x['INDEX']) == 3 else '' for i in x], axis=1)
mini_df_style.hide_columns(['INDEX'])

mini_df_style = mini_df_style.set_table_attributes(
    'border="1" class=mini-table-style')

mini_df_html = mini_df_style.hide_index().render()

arcpy.AddMessage("Mini df was created")

# parsel summary icmalleri
for m_html in df_sums_html:
    result_html += m_html

# mini dataframe
result_html += 2 * "<br>" + mini_df_html + 3 * "<br>"

# detay icmalleri
# adding detay
last_added_text = f"<h2 style='color:black; margin-top: 850px; '>İSDEMİR PARSEL DETAY LİSTESİ</h2>"

last_added_text += f"<h2>Toplam Kayıt Sayısı : {df_detail_toplam_kayit} </h2>"
last_added_text += "<hr>"

result_html += last_added_text
result_html += df_detail_html.hide_index().render()

arcpy.AddMessage("result was created")