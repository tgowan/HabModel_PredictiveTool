#Isotherm_fishnet tool
# This tool creates a 22°C isotherm from a SST raster, then calculates the distance between the isotherm and the midpoint of a fishnet grid cell.


###Define variables######
biweek = "Feb20A"
##biweek = "mar15B2"
sst = "R:\\Data\\SST\\CoastWatch_CaribNode\\cw1920\\Biweeks\\FebA\\Pred_Model\\2020_Jan28-Feb3\\sstavg" #raster with average SST values

####Static variables#######################
workspace = "R:\\Projects\\Habitat\\PredictiveTool\\PredictiveTool.gdb"
centroids = "centroids" #point feature class of fishnet grid centroids (exists in workspace)
front_fishnet = "front_fishnetC" #existing 4.2 km fishnet to resample SST image (exists in workspace)
habmodel = "HabModelEnviro" #Habitat Model fishnet

######## Temporary files########
outRaster = "Ras"+biweek #output Converted Raster to be created
contours = "contour"+biweek #Contour feature class to be created`
contour22 = "contour22"+biweek #Contour feature class to be created
centroidsJoin = biweek #Spatially joined centroids feature class to be created
########################


# Import system modules
import sys, string, os, win32com.client, os.path, time, arcgisscripting
import re
import arcpy
from arcpy.sa import *
arcpy.CheckOutExtension('Spatial')
arcpy.env.overwriteOutput = 1

#Set the workspace
arcpy.env.workspace = workspace
CPU_timeStart = time.time()  # Start the processing timer clock

#Calculate zonal statistics within fishnet polygon
outZsat = ZonalStatisticsAsTable(front_fishnet, 'ID', sst, biweek+'Table', 'DATA', 'MEAN')
#Join table to fishnet polygon
arcpy.JoinField_management(front_fishnet, 'ID', biweek+'Table', 'ID', 'MEAN')
#Convert polygon to raster
#PolygonToRaster_conversion(in_features, value_field, out_rasterdataset, {cell_assignment}, {priority_field}, {cellsize})
arcpy.PolygonToRaster_conversion(front_fishnet, 'MEAN', outRaster, 'MAXIMUM_AREA', 'NONE', '4200')

#Create 1°C isotherm contours using new raster
Contour(outRaster, contours, 1, 0)
#Select out 22 degree contour
arcpy.Select_analysis(contours, contour22, '"Contour" = 22')
#Calculate distance from 22 isotherm to centroids of grid cells
arcpy.Near_analysis(centroids, contour22)

#Spatial Join Mean SST values to centroids, retaining FishnetID and 'distance_to_isotherm' fields
arcpy.SpatialJoin_analysis(centroids, front_fishnet, centroidsJoin, 'JOIN_ONE_TO_ONE', 'KEEP_ALL', r'FishnetID "FishnetID" true true false 8 Double 0 0 ,First,#,'+centroids+',FishnetID,-1,-1;NEAR_DIST "NEAR_DIST" true true false 8 Double 0 0 ,First,#,'+centroids+',NEAR_DIST,-1,-1;MEAN "MEAN" true true false 4 Float 0 0 ,First,#,'+front_fishnet+',MEAN,-1,-1', 'INTERSECT', '#', '#')

#Update 'distance_to_22isotherm' field (change to negative value if mean >=22 degrees)
expression = "getNewVal(!NEAR_DIST!,!MEAN!)"
codeblock = """def getNewVal(dist,mean):
    if mean >= 22:
        return dist*-1
    else:
        return dist""" 
arcpy.CalculateField_management(centroidsJoin, "NEAR_DIST", expression, "PYTHON", codeblock)

#Rename 'distance_to_22isotherm' field
arcpy.AddField_management(centroidsJoin, 'Iso22' +biweek, 'FLOAT', '#', '#', '#', '#', 'NULLABLE', 'NON_REQUIRED', '#')
arcpy.CalculateField_management(centroidsJoin, 'Iso22' +biweek, '[NEAR_DIST]', 'VB', '#')
arcpy.DeleteField_management(centroidsJoin, 'NEAR_DIST')

#Join results to Habitat Model fishnet
arcpy.JoinField_management(habmodel, 'FishnetID', centroidsJoin, 'FishnetID', 'Iso22' +biweek)


#Delete temporary files and fields
arcpy.Delete_management(biweek+'Table')
arcpy.Delete_management(outRaster)
arcpy.Delete_management(contour22)
arcpy.DeleteField_management(centroids, ["NEAR_FID","NEAR_DIST"])
arcpy.DeleteField_management(front_fishnet, ["MEAN"])



CPU_timeEnd = time.time() #end the processing timer clock
CPU_timeElapsed = (CPU_timeEnd - CPU_timeStart)/60 #in minutes
print "Total processing time elapsed: %5.2f minutes" % CPU_timeElapsed