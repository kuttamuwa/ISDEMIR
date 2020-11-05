# This script takes the state of a web map in a web application 
# (for example, included services, layer visibility settings, and client-side graphics) 
# and returns a printable page layout or basic map of the specified area of interest
# in vector (such as pdf, svg etc.) or image (e.g. png, jpeg etc.)
#


# Import required modules
#
import sys
import os
import arcpy
import uuid
import json
import requests

# constants
#
SERVER_PROD_NAME = 'Server'
PRO_PROD_NAME = 'ArcGISPro'
PAGX_FILE_EXT = "pagx"
RPTX_FILE_EXT = "rptx"
MAP_ONLY = 'map_only'

# default location and current product name
#
_defTmpltFolder = os.path.join(arcpy.GetInstallInfo()['InstallDir'],
                               r"Resources\ArcToolBox\Templates\ExportWebMapTemplates")
_prodName = arcpy.GetInstallInfo()['ProductName']
_isMapOnly = False

lgr = open(r"C:\YAYIN\projealan\projealan\lgr.txt", 'w')


# export only map without any layout elements
#
def exportMap(result, outfile, outFormat):
    mapView = result.ArcGISProject.listMaps()[0].defaultView

    w = result.outputSizeWidth
    h = result.outputSizeHeight
    dpi = int(result.DPI)  # a workaround for now for a bug

    try:
        if outFormat == "png8" or outFormat == "png32":
            if (outFormat == "png8"):
                colorMode = "8-BIT_ADAPTIVE_PALETTE"
            else:
                colorMode = "32-BIT_WITH_ALPHA"
            mapView.exportToPNG(outfile, w, h, dpi, None, colorMode)
        elif outFormat == "pdf":
            mapView.exportToPDF(outfile, w, h, dpi)
        elif outFormat == "jpg":
            mapView.exportToJPEG(outfile, w, h, dpi, None, '24-BIT_TRUE_COLOR', 100)
        elif outFormat == "gif":
            mapView.exportToGIF(outfile, w, h, dpi)
        elif outFormat == "eps":
            mapView.exportToEPS(outfile, w, h, dpi)
        elif outFormat == "svg":
            mapView.exportToSVG(outfile, w, h, dpi, False)
        elif outFormat == "svgz":
            mapView.exportToSVG(outfile, w, h, dpi, True)
    except Exception as err:
        arcpy.AddError("error raised..." + str(err))
        raise


# export layout
#
def exportLayout(result, outfile, outFormat):
    layout = result.ArcGISProject.listLayouts()[0]

    dpi = result.DPI

    try:
        if outFormat == "png8" or outFormat == "png32":
            if (outFormat == "png8"):
                colorMode = "8-BIT_ADAPTIVE_PALETTE"
            else:
                colorMode = "32-BIT_WITH_ALPHA"
            layout.exportToPNG(outfile, dpi, colorMode)
        elif outFormat == "pdf":
            layout.exportToPDF(outfile, dpi)
            lgr.write("export to pdf run in export layout function \n")
        elif outFormat == "jpg":
            layout.exportToJPEG(outfile, dpi)
        elif outFormat == "gif":
            layout.exportToGIF(outfile, dpi)
        elif outFormat == "eps":
            layout.exportToEPS(outfile, dpi)
        elif outFormat == "svg":
            layout.exportToSVG(outfile, dpi, False)
        elif outFormat == "svgz":
            layout.exportToSVG(outfile, dpi, True)
    except Exception as err:
        arcpy.AddError("error raised..." + str(err))
        raise


# export report
# **Note**: report file (.rptx) must be in the same location where layout template files (.pagx) are stored
def exportReport(p, reportfn, outfile):
    m = p.listMaps()[0]
    lyrs = m.listLayers("*Proje*")  # Change wildcard here to find your layer
    if (len(lyrs) == 0):
        return

    l = lyrs[0]
    lgr.write("Layer bulundu : {0} \n".format(l))
    lgr.write('outFile : {0}\n'.format(outfile))

    p.importDocument(reportfn)
    r = p.listReports()[0]
    r.setReferenceDataSource(l)

    lgr.write("report was found : {0} \n".format(r))

    outReportFileName = generateUniqueFileName('pdf')
    outReportFileName = r"C:\YAYIN\projealan\projealan\report.pdf"

    lgr.write("out report file name : {0} \n".format(outReportFileName))

    lgr.write('export to pdf baslayacak \n')
    lgr.write('report : {0}'.format(r.name))

    try:
        r.exportToPDF(outReportFileName)
        lgr.write("exporttopdf run ! \n")
    except Exception as err:
        try:
            lgr.write('Export to pdf calismadi kendimiz deneyek : {0} \n'.format(str(err)))
            arcpy.ExportReportToPDF_management(r, r"C:\YAYIN\projealan\projealan\report.pdf")
        except Exception as err:
            lgr.write('Hata : {0}\n'.format(str(err)))

    pdf = arcpy.mp.PDFDocumentOpen(outfile)
    lgr.write("PDF document opened \n")
    pdf.appendPages(outReportFileName)
    lgr.write("pdf appended \n")
    pdf.saveAndClose()
    lgr.write("pdf saved and closed \n")
    os.remove(outReportFileName)
    lgr.write("os removed \n")


# generating a unique name for each output file
def generateUniqueFileName(outFormat):
    guid = str(uuid.uuid1())
    fileName = ""

    if outFormat == "png8" or outFormat == "png32":
        fileName = '{}.{}'.format(guid, "png")
    else:
        fileName = '{}.{}'.format(guid, outFormat)

    fullFileName = os.path.join(arcpy.env.scratchFolder, fileName)
    return fullFileName


# Main module
#
def main():
    # Get the value of the input parameter
    #
    lgr.write("Arac calismaya basladi \n")
    WebMap_as_JSON = arcpy.GetParameterAsText(0)
    outfilename = arcpy.GetParameterAsText(1)
    format = arcpy.GetParameterAsText(2).lower()
    layoutTemplatesFolder = arcpy.GetParameterAsText(3).strip()
    layoutTemplate = arcpy.GetParameterAsText(4).lower()
    report = arcpy.GetParameterAsText(5).lower()

    lgr.write("report : {0} \n".format(report))
    lgr.write("layout : {0} \n".format(layoutTemplate))

    if (layoutTemplate.lower() == MAP_ONLY):
        _isMapOnly = True
        layoutTemplate = None
    else:
        _isMapOnly = False

    # Special logic while being executed in ArcGIS Pro 
    # - so that a Geoprocessing result can be acquired without needing any json to begin to feed in
    # - this is to make the publishing experience easier
    if (WebMap_as_JSON == '#'):
        if (_prodName == PRO_PROD_NAME):
            return
        elif (_prodName == SERVER_PROD_NAME):
            arcpy.AddIDMessage('ERROR', 590, 'WebMap_as_JSON')
        else:
            arcpy.AddIDMessage('ERROR', 120004, _prodName)

    # generate a new output filename when the output_filename parameter is empty or the script is running on server
    if outfilename.isspace() or _prodName == SERVER_PROD_NAME:
        outfilename = generateUniqueFileName(format)
        lgr.write("outfile name : {0} \n".format(outfilename))

    # constructing the full path for the layout file (.pagx)
    if not _isMapOnly:
        # use the default location when Layout_Templates_Folder parameter is not set
        tmpltFolder = _defTmpltFolder if not layoutTemplatesFolder else layoutTemplatesFolder
        layoutTemplate = os.path.join(tmpltFolder, '{}.{}'.format(layoutTemplate, PAGX_FILE_EXT))
        reportFilePath = os.path.join(tmpltFolder, '{}.{}'.format(report, RPTX_FILE_EXT))

        lgr.write("layoutTemplate : {0} \n".format(layoutTemplate))
        lgr.write("reportFilePath : {0} \n".format(reportFilePath))

    # Convert the webmap to a map document
    try:
        result = arcpy.mp.ConvertWebMapToArcGISProject(WebMap_as_JSON, layoutTemplate)
        lgr.write("result was generated \n")
        lgr.write('WMASJSON : {0}\n'.format(WebMap_as_JSON))

        # Export...
        if (_isMapOnly):
            lgr.write("Map only was selected ?? \n")
            if (result.outputSizeWidth == 0) or (result.outputSizeHeight == 0):
                arcpy.AddIDMessage('ERROR', 1305)
            exportMap(result, outfilename, format)
        else:
            exportLayout(result, outfilename, format)
            lgr.write("export layout run? \n")
            if format == "pdf":
                lgr.write("pdf was selected \n")
                exportReport(result.ArcGISProject, reportFilePath, outfilename)
            else:
                arcpy.AddWarning("Can't generate when output format is anything but pdf.")

    except Exception as err:
        arcpy.AddError(str(err))
        lgr.write(str(err))
        lgr.close()

    # Set output parameter
    #
    arcpy.SetParameterAsText(1, outfilename)


if __name__ == "__main__":
    main()


