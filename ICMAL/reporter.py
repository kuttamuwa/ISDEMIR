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
        icmal_type = arcpy.Parameter(
            displayName="Icmal Seciniz",
            name="icmal_type",
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

        icmal_type.filter.list = report_choice_list
        params = [icmal_type, out_html]
        return params

    @staticmethod
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
                    self.column_cleaner(fc_dataframe, **kwargs)

                else:
                    self.column_cleaner(fc_dataframe)

            return fc_dataframe
        except OSError as err:
            arcpy.AddError("Veritabaninda {0} view'i bulunamadigi icin rapor uretilemedi. \n".format(in_table))
            arcpy.AddError("Hata : {0}".format(err))

            sys.exit(0)

    @staticmethod
    def find_genel_toplam_indexes(df):
        r_c = df.loc[df['KULLANIM AMACI'] == 'Genel Toplam']['KULLANIM AMACI'].index.tolist()
        return r_c

    @staticmethod
    def find_malik_indexes(df, maliks):
        r_c = []
        for index, row in df.iterrows():
            arcpy.AddMessage(row['KULLANIM AMACI'])
            if row['KULLANIM AMACI'] in maliks:
                r_c.append(index)

        # r_c = df.loc[df['KULLANIM AMACI'] in maliks]['KULLANIM AMACI'].index.tolist()
        return r_c

    def execute(self, parameters, messages):
        workspace = r"C:\YAYIN\cbsarcgisew.sde"
        env.workspace = workspace
        icmal_type = parameters[0].valueAsText

        arcpy.AddMessage("pandas version : {0}".format(pd.__version__))

        if icmal_type == report_choice_list[0]:
            # Yapi Icmali: Yapi_Geo_Icmal_Sorgusu (Detay) - Summary
            arcpy.AddMessage("Yapi Icmali secildi")
            icmal_html = base_html_head.replace("{report_title}", "Yerlesim Alani Genel Arazi Icmali (Yapi) ")
            name = "yapi_icmali.html"

            added_first_text = f"<h2 style='color:black;'>ISDEMIR YERLEŞİM ALANI GENEL ARAZİ İCMALİ</h2>" \
                               f"<hr>"
            icmal_html += added_first_text

            df_detail = self.table_to_data_frame('ISD_NEW.dbo.Yapi_Geo_Icmal_Sorgusu',
                                                 donotdelete=['ykibedinimyontemi'])
            df_detail.drop(['Yapi_ID'], inplace=True, errors='ignore')

            # datetime formatting
            df_detail['Ykib_Tarihi'] = pd.to_datetime(df_detail['Ykib_Tarihi'], errors='coerce')
            df_detail['RuhsatAlinmaTarihi'] = pd.to_datetime(df_detail['RuhsatAlinmaTarihi'], errors='coerce')

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
            df_sum = df_detail.copy()

            # imar barışı tricking
            df_sum.loc[df_sum['YKIB Edinim Yöntemi'] == 'İmar Barışı', 'YKIB Durum'] = 'İmar Barışı'
            df_sum_pivot = pd.crosstab(df_sum['Malik'], columns=[df_sum['OEB Durumu'],
                                                                 df_sum['Ruhsat Durum'], df_sum['YKIB Durum']])

            # df_sum_pivot_with_imar_barisi.rename(columns={'disinda': 'Dışında', 'icinde': 'İçinde'})

            df_sum_pivot.rename(columns={'rowid': 'INDEX', 'disinda': 'Dışında', 'icinde': 'İçinde',
                                         'YKIB_ALINDI': 'YKIB ALINDI', 'YKIB_KAYITYOK': 'YKIB KAYDI YOK',
                                         'RUHSAT_ALINMADI': 'RUHSAT ALINMADI', 'RUHSAT_ALINDI': 'RUHSAT ALINDI',
                                         'RUHSAT_KAYITYOK': 'RUHSAT KAYDI YOK', 'YKIB_ALINMADI': 'YKIB ALINMADI'
                                         }, inplace=True)

            arcpy.AddMessage("Pivot dataframe was created")

            # Genel toplam row added
            df_sum_pivot_columns = list(df_sum_pivot.columns)
            df_sum_pivot[df_sum_pivot_columns] = df_sum_pivot[df_sum_pivot_columns].apply(pd.to_numeric, errors='raise',
                                                                                          axis=1)

            df_sum_pivot.loc['Dikey Toplam'] = df_sum_pivot.sum(axis=0)
            df_sum_pivot.loc[:, 'Yatay Toplam'] = df_sum_pivot.sum(axis=1)

            df_sum_pivot_html_style = df_sum_pivot.style
            df_sum_pivot_html_style.set_properties(**{'width': '600px', 'text-align': 'center'})
            df_sum_pivot_html_style = df_sum_pivot_html_style.set_table_attributes(
                'border="1" class=dataframe table table-hover table-bordered')

            # Last step
            df_detail.rename(columns={'YapiAdi': 'Yapı Adı', 'Yapi_No': 'Yapı No',
                                      'AdaNo': 'Ada No', 'ParselNo': 'Parsel No', 'KullanimSekli': 'Kullanım Şekli',
                                      'InsaatTuru': 'İnşaat Türü', 'YapiSinifi': 'Yapı Sınıfı',
                                      'ToplamInsaatAlani': 'Toplam İnşaat Alanı', 'ILCE_ADI': 'İlçe Adı',
                                      'Ykib_BelgeTuru': 'YKIB Belge Türü',
                                      'Ykib_Tarihi': 'YKIB Tarihi', 'YkibNo': 'YKIB No',
                                      'RuhsatBelgeTuru': 'Ruhsat Belge Türü',
                                      'RuhsatAlinmaTarihi': 'Ruhsat Alınma Tarihi', 'RuhsatNo': 'Ruhsat No',
                                      'ykibedinimyontemi': 'YKIB Edinim Yöntemi', 'oeb_durumu': 'OEB Durumu',
                                      'rowid': 'INDEX'}, inplace=True, errors='ignore')

            # number formatting
            df_detail['Ada No'] = df_detail['Ada No'].astype(str) \
                .apply(lambda x: x.split(".")[0] if x.count(".") else 'Kayıt Yok')
            df_detail['Ruhsat No'] = df_detail['Ruhsat No'].astype(str) \
                .apply(lambda x: x.split(".")[0] if x.count(".") else 'Kayıt Yok')
            df_detail['Toplam İnşaat Alanı'] = df_detail['Toplam İnşaat Alanı'].astype(str) \
                .apply(lambda x: x.split(".")[0] if x.count(".") else 'Kayıt Yok')
            arcpy.AddMessage("Number formatting completed")

            # index to column
            df_detail.reset_index(inplace=True)
            df_detail.rename(columns={'rowid': 'INDEX'}, inplace=True)
            added_text = f"<h2 style='color: blue;'>İSDEMİR YAPI LİSTESİ</h2>" \
                         f"Detay tablosu sayısı : {df_detail.count()['Ada No']}"
            arcpy.AddMessage("Columns renaming completed")

            # formatting records
            df_detail['İnşaat Türü'] = df_detail['İnşaat Türü'].replace('None', "Kayıt Yok")
            df_detail['YKIB Tarihi'] = df_detail['YKIB Tarihi'].astype(str).replace({"NaT": "Kayıt Yok"})
            arcpy.AddMessage("filling null values completed")

            # export html
            df_detail_style = df_detail.style
            df_detail_style.set_properties(**{'width': '600px', 'text-align': 'center'})
            df_detail_style = df_detail_style.set_table_attributes(
                'border="1" class=dataframe table table-hover table-bordered')

            df_detail_html = df_detail_style.hide_index().render()
            arcpy.AddMessage("Detail dataframe was created")

            result_html = icmal_html + "<br>" + df_sum_pivot_html_style.render() + 2 * "<br>" + added_text + df_detail_html

        elif icmal_type == report_choice_list[1]:
            # Yapi Emlak Vergisi Icmali : YAPI_EML_ICMAL_VW
            arcpy.AddMessage("Yapi Emlak Icmali secildi.")
            icmal_html = base_html_head.replace("{report_title}", "Yapı Emlak Vergisi Icmali")
            name = "bina_emlak_icmali.html"

            added_first_text = f"<h1 style='color:black;'>Yapı Emlak Vergisi İcmali</h1>" \
                               f"<hr>"
            icmal_html += added_first_text

            df_detail = self.table_to_data_frame("ISD_NEW.dbo.Yapi_Geo_Eml_Od_Icmal_Sorgu")
            df_sum = self.table_to_data_frame("ISD_NEW.dbo.YAPI_EML_ICMAL_VW")

            # formatting for values
            df_detail = df_detail.replace(np.nan, 'Kayıt Yok', regex=True)
            df_sum = df_sum.replace(np.nan, 'Kayıt Yok', regex=True)

            df_sum.loc['Genel Toplam'] = df_sum.sum(numeric_only=True, axis=0)
            df_sum.index.names = ['INDEX']

            # formatting for columns
            df_sum.rename(columns={'Emlakvergisi_durumu': 'Emlak Vergisi Durumu', 'TOPLAM': 'ADET SAYISI',
                                   'TOPLAM_INSAAT_ALAN': 'TOPLAM (m²)'}, inplace=True)
            df_sum = df_sum.replace(np.nan, 'Genel Toplam', regex=True)

            df_detail.rename(columns={'yapi_no': 'Yapı No', 'YapiAdi': 'Yapı Adı', 'AdaNo': 'Ada No',
                                      'ParselNo': 'Parsel No', 'katsayisi': 'Kat Sayısı', 'yapimtarihi': 'Yapım Tarihi',
                                      'asansor': 'Asansör', 'kalorifer': 'Kalorifer', 'KullanimSekli': 'Kullanım Şekli',
                                      'yapimulkiyeti': 'Yapı Mülkiyeti', 'InsaatTuru': 'İnşaat Türü',
                                      'ToplamInsaatAlani': 'Toplam İnşaat Alanı', 'ILCE_ADI': 'İlçe Adı',
                                      'Emlakvergisi_durumu': 'Emlak Vergisi Durumu',
                                      'EmlakInsaatSinifi': 'Emlak İnşaat Sınıfı',
                                      }, inplace=True)

            # datetime formatting
            df_detail['Yapım Tarihi'] = pd.to_datetime(df_detail['Yapım Tarihi'], errors='coerce')

            # number formatting
            df_detail['Ada No'] = df_detail['Ada No'].astype(str) \
                .apply(lambda x: x.split(".")[0] if x.count(".") else 'Kayıt Yok')
            df_detail['Toplam İnşaat Alanı'] = df_detail['Toplam İnşaat Alanı'].astype(str) \
                .apply(lambda x: x.split(".")[0] if x.count(".") else 'Kayıt Yok')
            df_detail['Kat Sayısı'] = df_detail['Kat Sayısı'].astype(str) \
                .apply(lambda x: x.split(".")[0] if x.count(".") else 'Kayıt Yok')
            df_detail['Emlak İnşaat Sınıfı'] = df_detail['Emlak İnşaat Sınıfı'].astype(str) \
                .apply(lambda x: x.split(".")[0] if x.count(".") else 'Kayıt Yok')

            pd.options.display.float_format = '{:,.0f}'.format

            # record formatting
            df_detail['Yapım Tarihi'] = df_detail['Yapım Tarihi'].astype(str)
            df_detail['Yapım Tarihi'] = df_detail['Yapım Tarihi'].apply(lambda x: "Kayıt Yok" if x == "NaT" else x)

            # delete index row
            df_detail.index.name = None

            # delete Malik
            df_detail.drop(columns=['Malik'], inplace=True)

            # export html
            df_detail_style = df_detail.style
            df_detail_style = df_detail_style.set_properties(**{'width': '600px', 'text-align': 'center'})
            df_detail_style = df_detail_style.set_table_attributes(
                'border="1" class=dataframe table table-hover table-bordered')
            df_detail_style = df_detail_style.set_table_styles(
                [{
                    'selector': 'th',
                    'props': [
                        ('background-color', '#2880b8'),
                        ('color', 'white')]
                }]
            )

            # delete index row
            df_sum.index.name = None

            df_sum['ADET SAYISI'] = df_sum['ADET SAYISI'].astype(str) \
                .apply(lambda x: x.split(".")[0] if x.count(".") else 'Kayıt Yok')
            df_sum['TOPLAM (m²)'] = df_sum['TOPLAM (m²)'].astype(str) \
                .apply(lambda x: x.split(".")[0] if x.count(".") else 'Kayıt Yok')

            # delete Kayıt Yok rows
            df_sum = df_sum[df_sum['Emlak Vergisi Durumu'] != "Kayıt Yok"]

            # Toplam column formatting
            df_sum['TOPLAM (m²)'] = df_sum['TOPLAM (m²)'].astype(float).map('{:,.2f}'.format)

            df_sum_html = df_sum.style
            df_sum_html = df_sum_html.set_table_styles(
                [{
                    'selector': 'th',
                    'props': [
                        ('background-color', '#2880b8'),
                        ('color', 'white')]
                }]
            )
            df_sum_html = df_sum_html.set_properties(**{'width': '300px', 'text-align': 'center'})
            df_sum_html = df_sum_html.set_table_attributes(
                'border="1" class=dataframe table table-hover table-bordered')

            df_sum_html = df_sum_html.apply(
                lambda x: ['background: #ea6053' if x['Emlak Vergisi Durumu'] == 'Genel Toplam'
                           else '' for i in x], axis=1)

            # df_sum_html = df_sum.to_html(index=False, justify='center', classes='umut-table-style')
            last_added_text = f"<h1 style='color:black;'>Yapı Emlak Vergi Listesi</h1>" \
                              f"<hr>"
            last_added_text += f"Detay tablosu sayısı : {df_detail.count()['Ada No']}"

            result_html = icmal_html + 2 * "<br>" + df_sum_html.hide_index().render() + 4 * "<br>" \
                          + last_added_text + df_detail_style.render()

        elif icmal_type == report_choice_list[2]:
            # Parsel Icmali
            pd.options.display.float_format = '{:,.3f}'.format

            arcpy.AddMessage("Parsel Icmali secildi")
            icmal_html = base_html_head.replace("{report_title}", "Parsel Icmali ")
            name = "parsel_icmal_report.html"

            added_first_text = f"<h2 style='color:black;'>ISDEMIR YERLEŞİM ALANI GENEL ARAZİ İCMALİ</h2>" \
                               f"<hr>"
            icmal_html += added_first_text

            clean_fields = ["OBJECTID", "Aciklama", "PaftaNo", "ParselUavt_Kodu", "Mahalle_Koy",
                            "HisseOrani", "oeb_durumu", "rowid", "SHAPE.STArea()", "SHAPE.STLength()"]

            df_detail = self.table_to_data_frame("ISD_NEW.dbo.Parsel_Geo_Icmal_Sorgu")
            df_sum = self.table_to_data_frame("ISD_NEW.dbo.PARSEL", input_fields=['AlanBuyuklugu', 'Eski_Parsel_ID',
                                                                                  'rapor_malik', 'rapor_kullanimi'])
            arcpy.AddMessage("Summary and Detail Dataframe were created")

            df_sum.rename(columns={'Eski_Parsel_ID': 'parselid'}, inplace=True)
            # rapor malik ve rapor kullanim sutunlarinin Parselden detaya aktarilmasi
            df_detail = df_detail.join(df_sum, lsuffix='_caller', rsuffix='_other')
            df_detail.drop(columns=[i for i in list(df_detail.columns) if i.count('caller') or i.count('other')],
                           inplace=True)
            arcpy.AddMessage("Detay icmaline rapor_malik ve rapor_kullanim sütunları aktarıldı ")

            df_detail = df_detail[[i for i in df_detail.columns if i not in clean_fields]]

            df_sums_html = []
            maliks = df_sum['rapor_malik'].unique()
            maliks_toplam = 0

            df_groups = []
            cnt = 0

            for m in list(maliks):
                df_sum_malik = df_sum[df_sum['rapor_malik'] == m]

                if m is not None:
                    grouped = df_sum_malik.groupby('rapor_kullanimi')
                    df_grouped = pd.DataFrame({'PARSEL SAYISI': grouped.count()['AlanBuyuklugu'],
                                               'ALAN TOPLAMI': grouped.sum()['AlanBuyuklugu']})

                    df_grouped.index.names = [m]

                    # Genel toplam row added
                    toplam = df_grouped.sum(numeric_only=True, axis=0)['ALAN TOPLAMI']

                    df_grouped.loc['Genel Toplam'] = df_grouped.sum(numeric_only=True, axis=0)

                    df_grouped['PARSEL SAYISI'] = df_grouped['PARSEL SAYISI'].astype(int)
                    df_grouped['ALAN TOPLAMI'] = df_grouped['ALAN TOPLAMI'].astype(int)

                    df_grouped['PARSEL SAYISI'] = df_grouped['PARSEL SAYISI'].round(3)
                    df_grouped['ALAN TOPLAMI'] = df_grouped['ALAN TOPLAMI'].round(3)
                    df_grouped['ALAN TOPLAMI'] = df_grouped['ALAN TOPLAMI'].astype(float).map('{:,.2f}'.format)
                    df_grouped['ALAN TOPLAMI'] = df_grouped['ALAN TOPLAMI'].astype(str) \
                        .apply(lambda x: x.split(".")[0] if x.count(".") else 'Kayıt Yok')

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

            all_in_one = pd.concat(df_groups, join='inner', axis=0)

            # colorizing
            # all_in_one['KULLANIM AMACI'] = all_in_one.index
            all_in_one.index.names = ['INDEX']

            # sorting
            all_in_one = all_in_one[['KULLANIM AMACI', 'PARSEL SAYISI', 'ALAN TOPLAMI']]

            all_in_one.reset_index(drop=True, inplace=True)

            indexes = self.find_genel_toplam_indexes(all_in_one)
            malik_indexes = self.find_malik_indexes(all_in_one, maliks)
            arcpy.AddMessage("Indexes has been found !")

            # rendered_text = all_in_one.style.apply(self.pandas_colorizing, args=(indexes,), axis=None).render()
            all_in_one_rendered = all_in_one.style.apply(lambda x: ['background: #ea6053' if x.name in indexes
                                                                    else '' for i in x], axis=1)
            all_in_one_rendered.apply(
                lambda x: ['colspan: 3' if x.name in malik_indexes else '' for i in x], axis=1)

            all_in_one_rendered = all_in_one_rendered.apply(
                lambda x: ['background: #ea6053' if x['KULLANIM AMACI'] == 'İSDEMİR YERLEŞİM ALANI GENEL TOPLAM'
                           else '' for i in x], axis=1)

            all_in_one_rendered = all_in_one_rendered.set_table_styles(
                [{
                    'selector': 'th',
                    'props': [
                        ('background-color', '#2880b8'),
                        ('color', 'white')]
                }]
            )
            all_in_one_rendered = all_in_one_rendered.set_properties(**{'width': '300px', 'height': '20px',
                                                                        'text-align': 'left'})
            all_in_one_rendered = all_in_one_rendered.apply(
                lambda x: ['color: white' if x['KULLANIM AMACI'] == 'Genel Toplam' else '' for i in x], axis=1)

            all_in_one_rendered = all_in_one_rendered.set_table_attributes(
                'border="1" class=parcel-aratable-style')
            all_in_one_rendered_html = all_in_one_rendered.hide_index().render()

            all_in_one_rendered_html = all_in_one_rendered_html.replace('None', '')

            # beatifulsoup
            # soup = bs4.BeautifulSoup(all_in_one_rendered_html, 'lxml')
            # tables = soup.findAll('table')
            # aratable = [i for i in tables if i.get('class')[0] == 'parcel-aratable-style'][0]
            # for td in aratable.find_all('td'):
            #     if td.text == '':
            #         td.decompose()
            #
            #     if td.text.count('.)'):
            #         td.attrs['colspan'] = 3

            df_sums_html.append(all_in_one_rendered_html)

            # for none rapor malik
            try:
                # todo: debugging
                none_malik_df = df_sum[df_sum['rapor_malik'].isnull()]
                # none_grouped = none_malik.groupby('rapor_kullanimi')
                none_df_grouped = pd.DataFrame({'PARSEL SAYISI': none_malik_df.count()['AlanBuyuklugu'],
                                                'ALAN TOPLAMI': none_malik_df.sum()['AlanBuyuklugu']})

                none_toplam = none_df_grouped.sum(numeric_only=True, axis=0)['ALAN TOPLAMI']

                none_malik_df.loc['Genel Toplam'] = none_df_grouped.sum(numeric_only=True, axis=0)
                maliks_toplam += none_toplam

                none_malik_df.index.names = ['RAPOR MALIK KAYDI YOK']
                df_sums_html.append(none_malik_df.to_html(index=True, justify='center', classes='umut-table-style'))

            except:
                arcpy.AddWarning("Rapor icin bos kayitli malikler cikarilamadi.")

            # formatting
            df_detail = df_detail.replace(np.nan, 'Kayit Yok', regex=True)
            df_detail.rename(columns={'parselid': 'Parsel ID', 'AdaNo': 'Ada No',
                                      'ParselNo': 'Parsel No', 'AlanBuyuklugu': 'Alan Büyüklüğü',
                                      'Kullanimsekli': 'Kullanım Şekli', 'ImarDurumu': 'İmar Durumu',
                                      'ParselMulkiyet': 'Parsel Mülkiyet', 'HisseAlani': 'Hisse Alanı',
                                      'rapor_malik': 'Rapor Malik', 'rapor_kullanimi': 'Rapor Kullanımı',
                                      'ILCE_ADI': 'İlçe Adı'}, inplace=True)

            # number formatting for df detail
            df_detail['Hisse Alanı'] = df_detail['Hisse Alanı'].astype(str) \
                .apply(lambda x: x.split(".")[0] if x.count(".") else 'Kayıt Yok')

            # export html
            df_detail_html = df_detail.style
            df_detail_html = df_detail_html.set_table_attributes(
                'border="1" class=umut-table-style')

            df_detail_html = df_detail_html.set_properties(**{'width': '600px', 'height': '20px',
                                                              'text-align': 'center'})

            # df_detail_html = df_detail.to_html(index=True, justify='center', classes='umut-table-style')
            arcpy.AddMessage("DF Detail html was created")

            result_html = icmal_html

            # mini table
            mini_df = self.table_to_data_frame('ISD_NEW.dbo.PARSEL_ICMAL_MINI_VW')
            mini_df.rename(columns={'rowid': 'INDEX', 'ParselNo': 'Veri Adı',
                                    }, inplace=True)

            genel_toplam = mini_df['TOPLAM_ALAN'].sum()

            # mini_df.loc['Kalan Genel Yerleşim Alanı Toplam']
            kalan_alan_gyt = float(maliks_toplam) - genel_toplam
            arcpy.AddMessage(f"Genel toplam : {genel_toplam} \n "
                             f"Kalan Alan Genel Yerleşim Alanı Toplamı : {kalan_alan_gyt}")

            # mini_df = mini_df.append({'Veri Adı': 'Genel Toplam', 'TOPLAM_ALAN': genel_toplam},
            #                          ignore_index=True)
            mini_df = mini_df.append(
                {'Veri Adı': 'ISDEMIR YERLEŞİM ALANI GENEL TOPLAM', 'TOPLAM_ALAN': kalan_alan_gyt},
                ignore_index=True)
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
                lambda x: ['background: #ea6053' if int(x['INDEX']) == 4 else '' for i in x], axis=1)
            mini_df_style.hide_columns(['INDEX'])

            mini_df_style = mini_df_style.set_table_attributes(
                'border="1" class=mini-table-style')

            mini_df_html = mini_df_style.hide_index().render()

            arcpy.AddMessage("Mini df was created")

            # parsel summary icmalleri
            for m_html in df_sums_html:
                result_html += m_html

            # mini dataframe
            result_html += 2 * "<br>" + mini_df_html + 2 * "<br>"

            # detay icmalleri
            # adding detay
            last_added_text = f"<h2 style='color:black; margin-top: 800px; '>İSDEMİR PARSEL DETAY LİSTESİ</h2>" \
                              f"<hr>"
            last_added_text += f"Detay tablosu sayısı : {df_detail.count()['Ada No']}"

            result_html += last_added_text
            result_html += df_detail_html.render()

            arcpy.AddMessage("result was created")

        elif icmal_type == report_choice_list[3]:
            # Parsel Emlak Vergisi Icmali
            # todo: Emlak vergisi durumuna göre ilçeye gruplayarak hem adet hem de toplam bulunacak
            # todo: crosstab(aggfunc='sum') and joined it with count one

            arcpy.AddMessage("Parsel Emlak Vergisi Icmali secildi")
            icmal_html = base_html_head.replace("{report_title}", "Parsel Emlak Vergisi Icmali")
            name = "parsel_emlak_vergisi_icmal_report.html"

            # table_name = "ISD_NEW.dbo.Parsel_Eml_Od_Icmal_Sorgusu"
            table_name = "ISD_NEW.DBO.ParselEmlakOdemelerIcmal_VW2"

            clean_fields = ["OBJECTID", "Eski_Parsel_ID", "Aciklama", "AlanBuyuklugu", "KullanimSekli", "ImarDurumu",
                            "ParselMulkiyet", "PaftaNo", "ParselUavt_Kodu", "HisseOrani", "VRHTip",
                            "VRHAlt_Tip", "VRH_Kurum", "Odemetipi", "Kurulus", "OdemeTarihi", "OdemeYili",
                            "OdemeTutari", "OdemeTutarBirimi", "odemeaciklama", "rowid", "SHAPE.STArea()",
                            "SHAPE.STLength()", "AlanBuyuklugu", "Hisse"]

            df_detail = self.table_to_data_frame(table_name)
            df_detail = df_detail[[i for i in df_detail.columns if i not in clean_fields]]

            # formatting
            df_detail = df_detail.replace(np.nan, 'Kayit Yok', regex=True)

            df_detail.rename(columns={'AdaNo': 'Ada No', 'ParselNo': 'Parsel No',
                                      'KullanimSekli': 'Kullanım Şekli', 'ILCE_ADI': 'İlçe Adı',
                                      'EmlakVergisiDurumu': 'Emlak Vergisi Durumu',
                                      'Vergiye_esas_mahalle': 'Vergiye Esas Mahalle',
                                      'Vergiye_esas_cad_sokak': 'Vergiye Esas Cadde Sokak',
                                      'Emlak_Vergisi_Tarihi': 'Emlak Vergisi Tarihi',
                                      'Arsa_birim_bedeli': 'Arsa Birim Bedeli',
                                      'parselemlakaciklama': 'Parsel Emlak Açıklama',
                                      'ParselNitelik': 'Parsel Nitelik', 'Kullanimsekli': 'Kullanım Şekli',
                                      'Arsa_birim_bedeli_nereden_alind': 'Arsa Birim Bedeli Nereden Alındı',
                                      'YapiDurumu': 'YAPI DURUMU', 'HisseAlani': 'Hisse Alanı'},
                             inplace=True)

            # datetime formatting
            df_detail['Emlak Vergisi Tarihi'] = pd.to_datetime(df_detail['Emlak Vergisi Tarihi'], errors='coerce')

            df_detail['Hisse Alanı'] = df_detail['Hisse Alanı'].astype(str) \
                .apply(lambda x: x.split(".")[0] if x.count(".") else 'Kayıt Yok')
            df_detail['Arsa Birim Bedeli'] = df_detail['Arsa Birim Bedeli'].astype(str) \
                .apply(lambda x: x.split(".")[0] if x.count(".") else 'Kayıt Yok')
            df_detail['Ada No'] = df_detail['Hisse Alanı'].astype(str) \
                .apply(lambda x: x.split(".")[0] if x.count(".") else 'Kayıt Yok')

            df_sum = pd.crosstab(df_detail['İlçe Adı'], df_detail['Emlak Vergisi Durumu'])

            # df_cnt = pd.crosstab(df_detail['İlçe Adı'], df_detail['Emlak Vergisi Durumu'], aggfunc='count',
            #                      values=['Payas', 'İskenderun'])
            # df_sum2 = pd.crosstab(df_detail['İlçe Adı'], df_detail['Emlak Vergisi Durumu'], aggfunc='sum',
            #                       values=['Payas', 'İskenderun'])
            #
            # df_sum3 = df_sum2.join(df_cnt)

            df_sum = df_sum.T

            # for testing
            df_sum.loc['Genel Toplam'] = df_sum.sum(numeric_only=True, axis=0)
            df_sum.loc[:, 'Genel Toplam'] = df_sum.sum(numeric_only=True, axis=1)

            # formatting
            df_detail.index.names = ['INDEX']

            # delete index row
            df_detail.index.name = None

            # export html
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
                        'selector': 'th:nth-child(11)',
                        'props': [
                            ('min-width', '40%')
                        ]
                    }
                ]
            )

            df_sum_html = df_sum.style
            df_sum_html = df_sum_html.set_properties(**{'width': '300px', 'text-align': 'center'})
            df_sum_html = df_sum_html.set_table_attributes(
                'border="1" class=dataframe table table-hover table-bordered')

            added_text = f"<h2 style='color:black;'>ISDEMIR PARSEL EMLAK VERGİSİ LİSTESİ</h2>" \
                         f"<hr>"
            added_text += f"Detay tablosu sayısı : {df_detail.count()['Ada No']}"

            result_html = icmal_html + 2 * "<br>" + df_sum_html.render() + 4 * "<br>" + added_text + "<br>" + df_detail_style.render()

        elif icmal_type == report_choice_list[4]:
            # Yapi Dava Takip Raporu
            arcpy.AddMessage("Yapi Dava Takip Raporu secildi")
            icmal_html = base_html_head.replace("{report_title}", "Yapi Dava Takip Raporu ")
            name = "yapi_dava_takip_report.html"
            added_first_text = f"<h2 style='color:black;'>İSDEMIR YAPI DAVA TAKİP İCMALİ</h2>" \
                               f"<hr>"
            icmal_html += added_first_text

            clean_fields = ['yoid', 'yapi_id', 'YapiAdi', 'YapiMulkiyeti', 'KullanimSekli', 'Mahalle_Koy',
                            "Unite", "YapiSinifi", "Malik", "rowid", "DavaDegerBirimi", "SHAPE.STArea()",
                            "SHAPE.STLength()"]

            df_detail = self.table_to_data_frame('ISD_NEW.dbo.Yapi_Geo_HK_Icmal_Sorgu')
            df_detail = df_detail[[i for i in df_detail.columns if i not in clean_fields]]
            arcpy.AddMessage("Detail dataframe was created")

            # formatting
            df_detail = df_detail.replace(np.nan, 'Kayit Yok', regex=True)
            df_detail.rename(columns={'yapi_no': 'Yapı No', 'AdaNo': 'Ada No', 'ParselNo': 'Parsel No',
                                      'DavaKonusu': 'Dava Konusu', 'DavaAcilisTarihi': 'Dava Açılış Tarihi',
                                      'KararTarihi': 'Karar Tarihi', 'KararNo': 'Karar No',
                                      'EsasNo': 'Esas No', 'DavaSonucu': 'Dava Sonucu', 'DavaDurumu': 'Dava Durumu',
                                      'DavaDegeri': 'Dava Değeri', 'ILCE_ADI': 'İlçe Adı', 'Aciklama': 'Açıklama',
                                      'Davaci': 'Davacı', 'Davali': 'Davalı',
                                      'adliye': 'Adliye', 'merci': 'Merci'},
                             inplace=True)

            df_detail.index.names = ['index']
            arcpy.AddMessage("Detail was formatted as column")

            # date formatting
            df_detail['Dava Açılış Tarihi'] = pd.to_datetime(df_detail['Dava Açılış Tarihi'], errors='coerce')
            df_detail['Dava Açılış Tarihi'] = df_detail['Dava Açılış Tarihi'].astype(str)
            df_detail['Dava Açılış Tarihi'] = df_detail['Dava Açılış Tarihi'].apply(
                lambda x: 'Kayıt Yok' if x == 'NaT' else x)
            # df_detail['Ada No'] = df_detail['Ada No'].astype(int, errors='ignore')
            arcpy.AddMessage("Detail was formatted as date")

            # index to column
            df_detail.reset_index(inplace=True)
            df_detail.rename(columns={'index': 'INDEX'}, inplace=True)
            arcpy.AddMessage("Detail was formatted as index")

            # number formatting
            df_detail['Dava Değeri'] = df_detail['Dava Değeri'].astype(str)
            df_detail['Dava Değeri'] = df_detail['Dava Değeri'].apply(lambda x: 'Kayıt Yok' if x == "None" else x)
            df_detail['Ada No'] = df_detail['Ada No'].astype(str) \
                .apply(lambda x: x.split(".")[0] if x.count(".") else 'Kayıt Yok')
            arcpy.AddMessage("Dava degeri and Ada No was formatted")

            # export html
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
                            ('width', '40%')
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

            arcpy.AddMessage("Detail dataframe was styled")

            added_text = f"Detay tablosu sayısı : {df_detail.count()['Ada No']}"
            arcpy.AddMessage("Detail row count was added")

            result_html = icmal_html + 2 * "<br>" + added_text + "<br>" + df_detail_style.hide_index().render()
            arcpy.AddMessage("added to result html")

        elif icmal_type == report_choice_list[5]:
            # Parsel Dava Takip Raporu
            arcpy.AddMessage("Parsel Dava Takip Raporu secildi.")
            icmal_html = base_html_head.replace("{report_title}", "Parsel Dava Takip Raporu ")
            name = "parsel_dava_takip_report.html"

            clean_fields = ["p_oid", "parselid", "AlanBuyuklugu", "ParselNitelik", "KullanimSekli", "ImarDurumu",
                            "ParselMulkiyet", "Malik", "parselaciklama", "davadegeribirimi", "rowid",
                            "shape.STArea()", "shape.STLength()"]

            df_detail = self.table_to_data_frame("ISD_NEW.dbo.Parsel_Geo_HK_Icmal_Sorgusu")
            df_detail = df_detail[[i for i in df_detail.columns if i not in clean_fields]]

            # formatting
            df_detail = df_detail.replace(np.nan, 'Kayıt Yok', regex=True)
            df_detail = df_detail.drop(labels=['p_oid'], errors='ignore')

            # specific column formatting
            df_detail.rename(columns={'ILCE_ADI': 'İlçe Adı', 'adano': 'Ada No', 'ParselNo': 'Parsel No',
                                      'KullanimSekli': 'Kullanım Şekli', 'davaacilistarihi': 'Dava Açılış Tarihi',
                                      'esasno': 'Esas No', 'kararno': 'Karar No', 'karartarihi': 'Karar Tarihi',
                                      'davadurumu': 'Dava Durumu', 'davasonucu': 'Dava Sonucu',
                                      'davadegeri': 'Dava Degeri', 'davaci': 'Davacı', 'davali': 'Davalı',
                                      'hukukaciklama': 'Hukuki Açıklama'}, inplace=True)
            arcpy.AddMessage("DF Detail is ready")

            # index to olumn
            df_detail.reset_index(inplace=True)
            df_detail.rename(columns={'index': 'INDEX'}, inplace=True)

            # export html
            # df_detail.index.names = ['INDEX']

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

            added_text = f"<h2 style='color:black;'>PARSEL DAVA TAKİP RAPORU</h2>" \
                         f"<hr>"
            added_text += f"Detay tablosu sayısı : {df_detail.count()['Ada No']}"

            result_html = icmal_html + 2 * "<br>" + added_text + "<br>" + df_detail_style.hide_index().render()

        elif icmal_type == report_choice_list[6]:
            # Kiralama Icmali
            arcpy.AddMessage("Kiralama Icmali secildi.")
            icmal_html = base_html_head.replace("{report_title}", "ISDEMIR Kiralama Icmali")
            name = "kiralama_report.html"

            added_first_text = f"<h2 style='color:black;'>ISDEMIR KİRALAMALAR İCMALİ</h2>" \
                               f"<hr>"
            icmal_html += added_first_text

            clean_fields = ["kht_tip", "SozlesmeYapilanKurulus", "Yillik_OdenecekMiktar", "OdemeFormulu",
                            "BirimBedeli", "ParaBirimi", "malik",
                            "KONUSU", "ACIKLAMA", "GUNCELDURUM", "AdaNo", "PARSELNO",
                            "KIRA_BASLANGIC_TARIHI", "KIRA_BITIS_TARIHI", "KHTNO", "ALAN_BUYUKLUGU"]

            table_name = "ISD_NEW.dbo.KHT_SORGU_VW"

            df_detail = self.table_to_data_frame(table_name)
            df_detail = df_detail[[i for i in df_detail.columns if i in clean_fields]]

            # formatting
            df_detail = df_detail.replace(np.nan, 'Kayit Yok', regex=True)
            df_detail.rename(columns={'kht_tip': 'Kira İzin Durumu', 'PARSELNO': 'Parsel No', 'AdaNo': 'Ada No',
                                      'KHTNO': 'KHT No', 'KHTID': 'KHT ID', 'GUNCELDURUM': 'Güncel Durum',
                                      'KIRA_BASLANGIC_TARIHI': 'Kira Başlangıç Tarihi',
                                      'KIRA_BITIS_TARIHI': 'Kira Bitiş Tarihi',
                                      'Yillik_OdenecekMiktar': 'Yıllık Ödenecek Miktar (TL/YIL)',
                                      'SozlesmeYapilanKurulus': 'Sözleşme Yapılan Kuruluş',
                                      'OdemeFormulu': 'Ödeme Formülü',
                                      'BirimBedeli': 'Birim Bedeli', 'ParaBirimi': 'Para Birimi',
                                      'ALAN_BUYUKLUGU': 'İzin Yüzölçümü (m²)'},
                             inplace=True)

            # date formatting due to arcpy
            df_detail['Kira Başlangıç Tarihi'] = pd.to_datetime(df_detail['Kira Başlangıç Tarihi'], errors='coerce')
            df_detail['Kira Bitiş Tarihi'] = pd.to_datetime(df_detail['Kira Bitiş Tarihi'], errors='coerce')
            # df_detail['Sözleşme Başlangıç Tarihi'] = pd.to_datetime(df_detail['Sözleşme Başlangıç Tarihi'],
            #                                                         errors='coerce')
            # df_detail['Sözleşme Bitiş Tarihi'] = pd.to_datetime(df_detail['Sözleşme Bitiş Tarihi'], errors='coerce')

            # removing NaT values
            df_detail['Kira Başlangıç Tarihi'] = df_detail['Kira Başlangıç Tarihi'].astype(str).replace(
                {"NaT": "Kayıt Yok"})
            df_detail['Kira Bitiş Tarihi'] = df_detail['Kira Bitiş Tarihi'].astype(str).replace({"NaT": "Kayıt Yok"})
            # df_detail['Sözleşme Başlangıç Tarihi'] = df_detail['Sözleşme Başlangıç Tarihi'].astype(str).replace(
            #     {"NaT": "Kayıt Yok"})
            # df_detail['Sözleşme Bitiş Tarihi'] = df_detail['Sözleşme Bitiş Tarihi'].astype(str).replace(
            #     {"NaT": "Kayıt Yok"})

            # number formatting
            df_detail['Ada No'] = df_detail['Ada No'].astype(str) \
                .apply(lambda x: x.split(".")[0] if x.count(".") else 'Kayıt Yok')
            df_detail['Yıllık Ödenecek Miktar (TL/YIL)'] = df_detail['Yıllık Ödenecek Miktar (TL/YIL)'].astype(str) \
                .apply(lambda x: x.split(".")[0] if x.count(".") else 'Kayıt Yok')
            df_detail['Birim Bedeli'] = df_detail['Birim Bedeli'].astype(str) \
                .apply(lambda x: x.split(".")[0] if x.count(".") else 'Kayıt Yok')
            df_detail['İzin Yüzölçümü (m²)'] = df_detail['İzin Yüzölçümü (m²)'].astype(str) \
                .apply(lambda x: x.split(".")[0] if x.count(".") else 'Kayıt Yok')

            df_detail.index.names = ['INDEX']

            # delete index row
            df_detail.index.name = None

            # export html
            df_detail_html = df_detail.style
            df_detail_html = df_detail_html.set_properties(**{'width': '600px', 'text-align': 'left'})
            df_detail_html = df_detail_html.set_table_attributes(
                'border="1" class=dataframe table table-hover table-bordered')
            df_detail_html = df_detail_html.set_table_styles(
                [{
                    'selector': 'th',
                    'props': [
                        ('background-color', '#2880b8'),
                        ('color', 'white')]
                }]
            )

            df_detail_html = df_detail_html.render()

            # df_detail_html = df_detail.to_html(index=True, justify='center', classes='umut-table-style')
            added_text = f"Detay tablosu sayısı : {df_detail.count()['Ada No']}"

            result_html = icmal_html + 2 * "<br>" + added_text + "<br>" + df_detail_html

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
