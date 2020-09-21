#Final_FeatureClass tool
# This tool joins data from a text file to a fishnet grid feature class

###Define variables######
##biweek = "mar14b2"
biweek = "Feb20B"
table = "C:\\Users\\tim.gowan\\Desktop\\predict.txt" #.txt file containing predicted whale abundance data
#table = "C:\\Users\\katie.jackson\\KAJ_Files\\Hab_Model_PredTool\\1920\\2019_Dec_31-Jan_1\\predict.txt" #.txt file containing predicted whale abundance data
fishnet = "R:\\Projects\\Habitat\\PredictiveTool\\PredictiveTool.gdb\\HabModelPredictions"  #fishnet feature class to which data will be joined
########################


temp = 'R:\\Projects\\Habitat\\PredictiveTool\\PredictiveTool.gdb\\copy_predict' #temporary table to be created
# Import system modules
import sys, string, os, win32com.client, os.path, getopt, arcgisscripting
import re
import arcpy
arcpy.env.overwriteOutput = 1

#Copy table into file geodatabase
arcpy.CopyRows_management(table, temp, '#')

#Join data to fishnet
arcpy.JoinField_management(fishnet, 'FishnetID', temp, 'FishnetID', 'pres;abund')

#Rename fields with biweek ID
arcpy.AddField_management(fishnet, biweek+'Pres', 'FLOAT', '#', '#', '#', '#', 'NULLABLE', 'NON_REQUIRED', '#')
arcpy.AddField_management(fishnet, biweek+'Abund', 'FLOAT', '#', '#', '#', '#', 'NULLABLE', 'NON_REQUIRED', '#')
arcpy.CalculateField_management(fishnet, biweek+'Pres', '[pres]', 'VB', '#')
arcpy.CalculateField_management(fishnet, biweek+'Abund', '[abund]', 'VB', '#')
arcpy.DeleteField_management(fishnet, 'pres')
arcpy.DeleteField_management(fishnet, 'abund')
#Delete temp table
arcpy.Delete_management(temp)                           


print "Done!!"
