#This tool summarizes a pre-existing average SST raster and adds SST values to a fishnet polygon.

### Define Variables #########
biweek = "Feb20A"
##biweek = "mar15B2"
wdir = "R:\\Data\\SST\\CoastWatch_CaribNode\\cw1920\\Biweeks\\FebA\\Pred_Model\\2020_Jan28-Feb3" #folder containing avg SST raster
fishnet = "R:\\Projects\\Habitat\\PredictiveTool\\PredictiveTool.gdb\\HabModelEnviro" #fishnet polygon
#####################


# Import system modules
import sys, string, os, win32com.client, os.path, getopt, arcgisscripting
import re
import arcpy
from arcpy.sa import *
arcpy.env.overwriteOutput = 1
arcpy.CheckOutExtension('Spatial')

arcpy.env.workspace = wdir


######Summarize avg SST into fishnet###############
#Calculate zonal statistics within fishnet polygon
outZsat = ZonalStatisticsAsTable(fishnet, 'OBJECTID', 'sstavg', 'R:\\Projects\\Habitat\\PredictiveTool\\sst_tables\\'+biweek, 'DATA', 'ALL')

#Join mean from zonal statistics table to fishnet polygon
arcpy.JoinField_management(fishnet, 'OBJECTID', 'R:\\Projects\\Habitat\\PredictiveTool\\sst_tables\\'+biweek, 'OBJECTID', 'MEAN')

#Rename field with biweek ID
arcpy.AddField_management(fishnet, 'mean_' +biweek, 'FLOAT', '#', '#', '#', '#', 'NULLABLE', 'NON_REQUIRED', '#')
arcpy.CalculateField_management(fishnet, 'mean_' +biweek, '[MEAN]', 'VB', '#')
arcpy.DeleteField_management(fishnet, 'MEAN')

print "Done!!"