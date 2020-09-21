#PROCCESS SST tool
#Florida Fish and Wildlife Conservation Commission
#Fish and Wildlife Research Institute
# This tool is designed to take real time SST data downloaded from Coastwatch
#Caribbean node website http://cwcaribbean.aoml.noaa.gov/cwatch-web/cgi-bin/index.cgi

#working directory (where the current SST files are stored)
#NOTE: cloud mask files must be in a 'Cloud' directory within the SST directory (when
#downloaded from Coastwatch, they have the same name as the SST file)

wdir = "C:\\Users\\tim.gowan\\Documents\\Working\\SST\\PredictiveModel\\2020_Jan28-Feb3b"   # Update this Directory!! #!#!#!#!#!#!
wdirc = wdir + "\Cloud"
print "The working directory is " + wdir
print "The cloud directory is " + wdirc

# Import system modules
import sys, string, os, win32com.client, os.path, getopt, arcgisscripting

# Create the Geoprocessor object
gp = arcgisscripting.create()

# Set the necessary product code
gp.SetProduct("ArcInfo")

# Check out any necessary licenses
gp.CheckOutExtension("spatial")

# Set the Geoprocessing environment...
gp.outputCoordinateSystem = ""
gp.extent = "-9779081.500000 2564909.090000 -8103281.500000 4399469.090000"


import re
#Pull out the file names from the list of items in the
#working directory that end with .flt into SSTlist variable list
ALLlist = os.listdir(wdir)
SSTlist = [s for s in ALLlist if  string.find(s, ".flt") >0]
print SSTlist
NumItems = len (SSTlist)

#the list of cloud masks has the same names
SSTlistc = SSTlist

#list of names to be used for Grid name (remove the .flt from variable string)
NameList = [m.rstrip('.flt') for m in SSTlist]
NameListc = [n.rstrip('.flt') for n in SSTlistc]

# Process: convert .flt file to an ESRI grid for each item in SSTlist
# Note: FloatToRaster will not work with output file names beginning with numbers
# so the s was prepended to the file name (as c was already prepended in the cloud section
try:
    for x,y in zip(SSTlist, NameList):
        gp.FloatToRaster_conversion(wdir + "\\" + x, wdir + "\\s" + y)   
        print "!!Converting " + x + " to " + y + " grid!!"
except:
    print "exception:"
    print gp.GetMessages(2)
    
#and the same for the clouds
try:
    for a,b in zip(SSTlistc, NameListc):
        gp.FloatToRaster_conversion(wdirc + "\\" + a, wdirc + "\\c" + b)
        print "!!Converting " + a + " to " + b + " cloud grid!!"

except:
    print "exception:"
##    print gp.GetMessages(2)        

#Code NoData to 0 in Cloud Dir
gp.workspace = wdirc #use cloud work directory
rasters = gp.listrasters("*", "GRID")
rasters.reset
rasterc = rasters.next()

try:
    
    while rasterc:
 
        Output = wdirc + "\\z" + rasterc
        print Output
        InExpression = "Con(isnull(" + wdirc + "\\" + rasterc + "), 0, " + wdirc + "\\" + rasterc + ")"
        print InExpression
        gp.SingleOutputMapAlgebra_sa(InExpression, Output, rasterc)
        #delete the NoData rasters
        gp.Delete_management(rasterc)
        rasterc = rasters.next()
except:
    print "exception:"
    print gp.GetMessages(2)
    
#code cloud mask to 0 or 1 using greaterthan 0 (cloud mask=0, data=1)
rastersc = gp.listrasters("*", "GRID")
rastersc.reset
rasterc = rastersc.next()

try:
    
    while rasterc:
 
        Output = wdirc + "\\m" + rasterc
        print Output
        Input = wdirc + "\\" + rasterc
        gp.LessThan_sa(rasterc, .1, Output)    
        gp.Delete_management(rasterc)
        rasterc = rastersc.next()
        
except:
    print "exception:"
    print gp.GetMessages(2)

rastersc = gp.listrasters("*", "GRID")
rastersc.reset
rasterc = rastersc.next() #use this as the list of cloud mask rasters

gp.workspace = wdir

# Process: Define Projection...
for x in NameList:
    gp.DefineProjection_management(wdir + "\\s" + x, "PROJCS['WGS_1984_Mercator',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mercator'],PARAMETER['False_Easting',-1470.0],PARAMETER['False_Northing',1470.0],PARAMETER['Central_Meridian',0.0],PARAMETER['Standard_Parallel_1',0.0],UNIT['Meter',1.0]]")
    print "!!Defining projection for " + x + " grid!!"

#get a list of all rasters in the input workspace
rasters = gp.listrasters("*", "GRID")
rasters.reset #for each raster in the list
raster = rasters.next()

#create a new raster changing the NoData to 0 using Con statement, add C to this new raster name
try:
    
    while raster:
 
        Output = wdir + "\\N" + raster
        print Output
        InExpression = "Con(isnull(" + wdir + "\\" + raster + "), 0, " + wdir + "\\" + raster + ")"
        print InExpression
        gp.SingleOutputMapAlgebra_sa(InExpression, Output, raster)
        #delete the NoData rasters
        gp.Delete_management(raster)
        raster = rasters.next()
except:
    print "exception:"
    print gp.GetMessages(2)

#multiply SST image by cloud mask
gp.workspace = wdirc
rastersc = gp.listrasters("*", "GRID")
rastersc.reset
rasterc = rastersc.next()
gp.workspace = wdir
rasters = gp.listrasters("*", "GRID")
rasters.reset
raster = rasters.next()

try:
    while raster:
        Output = wdir + "\\x" + raster
        Input1 = raster
        Input2 = wdirc + "\\" + rasterc
        print Input1 + " * " + Input2
        gp.Times_sa(Input1, Input2, Output)
        gp.Delete_management(Input1)
        gp.Delete_management(Input2) #delete cloud mask
        raster = rasters.next()
        rasterc = rastersc.next()
        
except:
    print "exception:"
    print gp.GetMessages(2)


###  New   ###############
#Set invalid values (<5 degrees C) as null
rasters = gp.ListRasters("xns*", "GRID")
rasters.reset
raster = rasters.next()
while raster:
    #output = os.path.join(wdir,"\\final" + str(raster[3:11]))
    output = os.path.join(wdir + "\\final" + str(raster[3:11]))
    gp.SetNull_sa(raster, raster, output, "\"VALUE\" < 5")
    raster = rasters.next()

#Recode final rasters for use in the divider grid
rasters = gp.listrasters("final*", "GRID") #for each raster in the list
rasters.reset
raster = rasters.next()
while raster:
    #output = os.path.join(wdir,"\\div" + str(raster[5:13]))
    output = os.path.join(wdir + "\\div" + str(raster[5:13]))
    reclassRanges = "5 40 1; NoData NoData 0" #changes 5-40 to 1 and NoData to 0
    gp.Reclassify_sa(raster, "Value", reclassRanges, output)
    raster = rasters.next()

#Create SumSST grid (sum of all SST values at each pixel)
import arcpy
from arcpy.sa import *
sPath = sys.path[0]
arcpy.env.overwriteOutput = 1
arcpy.CheckOutExtension('Spatial')
arcpy.env.scratchWorkspace = wdir
arcpy.env.workspace = wdir
#create a list of rasters in the workspace
rasters = arcpy.ListRasters('final*','GRID')
i = 0
#loop through rasters in list
for raster in rasters:
    #convert nodata to zero
    out1 = Con(IsNull(raster), 0, raster)
    #sum rasters together
    if i == 0:
        out2 = out1
        i += 1
    else:
        out2 = out2 + out1
        i += 1
#save final output
out2.save(os.path.join(wdir,'SumSST'))

#Create DivSST grid (number of valid SST values at each pixel)
rasters = arcpy.ListRasters('div*','GRID')
i = 0
#loop through rasters in list
for raster in rasters:
    #convert nodata to zero
    out1 = Con(IsNull(raster), 0, raster)
    #sum rasters together
    if i == 0:
        out2 = out1
        i += 1
    else:
        out2 = out2 + out1
        i += 1
#save final output
out2.save(os.path.join(wdir,'DivSST'))

#Create SSTavg
expression = "sumsst / divsst"
#output = os.path.join(wdir,"\\SSTavg")
output = os.path.join(wdir + "\\SSTavg")
gp.SingleOutputMapAlgebra_sa(expression, output)

print "Done!! The SSTAvg ESRI grid is in " + wdir