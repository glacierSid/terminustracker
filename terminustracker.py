import arcpy
from arcpy import env
from arcpy.sa import *
import numpy as np
import arcpy.da

'''
Author: Siddharth Shankar
Purpose: Glacier Terminus Tracking Tool - Final Project GEOG-560
Year: Spring 2016

Input 1 : Raster image of Rink Isbrae showing the terminus of the glacier for particular month/year.
Input 2: Second raster image of Rink Isbrae from a different month/year.
Input 3: Terminus Width - Reference line shapefile.

These two inputs will provide two timeline scales against which the change in terminus of the glacier will be calculated.

Algorithm:
1) Input the raster image.
2) Reclassify it based on DN values of the input raster. Ice = 1 , Water/Land = 0
3) Find contours. Contours with maximum length will be the terminus.
4) Convert the contour to a point shapefile.
5) Input a reference line shapefile called Terminus Width. This will help in determining the endpoints of the glacier terminus.
6) Find the two end-points of the glacier for different months.
7) Repeat this for second image as well.
7) Convert the end-points of glacier terminus from different months into two line features.
8) Find the center-point of the early month line feature and calculate the shortest distance to each of the terminus positions.
9) Find the difference between the two distances which will be the change in glacier terminus position.

This will determine the terminus of one image.

Output: The output will be the distance retreated by the glacier.
'''

arcpy.CheckOutExtension("Spatial")
env.overwriteOutput=True
#Month of Oct, Month 2

def rasterLateImage(in_Raster):

    in_Raster = "path\to\project\location\Oct6.tif"
    maxVal = int(arcpy.GetRasterProperties_management(in_Raster,"MAXIMUM").getOutput(0))
    minVal = int(arcpy.GetRasterProperties_management(in_Raster,"MINIMUM").getOutput(0))
    print "Water = ", range(minVal,int(0.25*maxVal))," = 0"
    print "Ice = ", range(int(0.25*maxVal),maxVal)," = 1"
    remapRange = RemapRange([[minVal,int(0.25*maxVal),0],[int(0.25*maxVal),maxVal,1]])
    reclass = Reclassify(in_Raster,"VALUE",remapRange)
    reclass.save("path\to\project\location\classPrg")

    # Creating contour shapefile from the reclassified raster image
    contourInterval = 1
    baseContour = 0
    zFactor = 1
    outContour = "path\to\project\location\eclass-contour.shp"
    contour = Contour(reclass,outContour,contourInterval,baseContour,zFactor)

    lengthField = "Length"
    fieldPrecision = 15
    fieldScale = 15
    arcpy.AddField_management(contour,lengthField,"DOUBLE",fieldPrecision,fieldScale)
    arcpy.CalculateField_management(contour,lengthField,"!SHAPE.LENGTH!","PYTHON_9.3")

    in_table = "path\to\project\location\eclass-contour.dbf"

    # Selecting the contour with maximum length and writing it to a raster
    inputShape = "path\to\project\location\e-contourSelect.shp"
    outputRaster = "path\to\project\location\prgSelect"
    cell_size = 15
    outputRas = arcpy.FeatureToRaster_conversion(inputShape,"ID",outputRaster,cell_size)

    # Converting the raster to the point shapefile of the selected feature
    outputPoint = "path\to\project\location\sras2point.shp"
    opPoint = arcpy.RasterToPoint_conversion(outputRas,outputPoint,"VALUE")

    # Input terminus width which will be used as a reference line in the shapefile
    lineShape = "path\to\project\location\TerminusWidth.shp"
    startPointShp = "path\to\project\location\startPoint.shp"
    endPointShp = "path\to\project\location\endPoint.shp"
    start = arcpy.FeatureVerticesToPoints_management(lineShape,startPointShp,"START")
    end = arcpy.FeatureVerticesToPoints_management(lineShape,endPointShp,"END")

    outSTable = "path\to\project\location\start2Points"
    arcpy.GenerateNearTable_analysis(opPoint,start,outSTable,'','LOCATION','NO_ANGLE','',0,"PLANAR")

    outETable = "path\to\project\location\end2Points"
    arcpy.GenerateNearTable_analysis(opPoint,end,outETable,'','LOCATION','NO_ANGLE','',0,"PLANAR")

    # Coordinates for the furthest point from start point of terminus width shapefile
    myField = "NEAR_DIST"
    fX = "FROM_X"
    fY = "FROM_Y"
    sortDesc = arcpy.SearchCursor(outSTable,"","","",myField+" D")

    row = sortDesc.next()
    distance = row.NEAR_DIST
    fromX = row.FROM_X
    fromY = row.FROM_Y

    print distance, fromX, fromY


    # Coordinates for furthest point from end point of terminus width shapefile
    sortDescEnd = arcpy.SearchCursor(outETable,"","","",myField+" D")
    rowE = sortDescEnd.next()
    distanceE = rowE.NEAR_DIST
    fromX2 = rowE.FROM_X
    fromY2 = rowE.FROM_Y

    print distanceE, fromX2 , fromY2

    #Creating point shapefile from the coordinates generated in the previous step
    fc = "point1.shp"
    nfc = arcpy.CreateFeatureclass_management("path\to\project\location",fc,"POINT")
    arcpy.AddField_management(nfc,"X","FLOAT",field_length=50)
    arcpy.AddField_management(nfc,"Y","FLOAT",field_length=50)
    sRef = arcpy.SpatialReference("WGS 1984 Complex UTM Zone 22N")
    arcpy.DefineProjection_management(nfc,sRef)

    cursor = arcpy.da.InsertCursor(nfc,["X","Y","SHAPE@XY"])
    newRow = float(fromX),float(fromY),(fromX,fromY)
    cursor.insertRow(newRow)

    fc2 = "point2.shp"
    nfc2 = arcpy.CreateFeatureclass_management("path/to\project\location",fc2,"POINT")
    arcpy.AddField_management(nfc2,"X","FLOAT",field_length=50)
    arcpy.AddField_management(nfc2,"Y","FLOAT",field_length=50)
    sRef2 = arcpy.SpatialReference("WGS 1984 Complex UTM Zone 22N")
    arcpy.DefineProjection_management(nfc2,sRef2)

    #Convert the 2 sets of coordinates from previous step into a line shapefile
    cursor = arcpy.da.InsertCursor(nfc,["X","Y","SHAPE@XY"])
    newRow = float(fromX2),float(fromY2),(fromX2,fromY2)
    cursor.insertRow(newRow)

    line1 = arcpy.PointsToLine_management(nfc,"path/to\project\location\sline1.shp")

# Month of July, Month 1
def rasterEarlyImage(in_Raster):

    #Input Raster
    in_Raster = "path/to\project\location\clipnew.tif"

    maxVal = int(arcpy.GetRasterProperties_management(in_Raster,"MAXIMUM").getOutput(0))
    minVal = int(arcpy.GetRasterProperties_management(in_Raster,"MINIMUM").getOutput(0))

    #Reclassify the raster into 0 and 1. Land/Water = 0, Ice = 1
    remapRange = RemapRange([[minVal,int(0.25*maxVal),0],[int(0.25*maxVal),maxVal,1]])
    reclass = Reclassify(in_Raster,"VALUE",remapRange)
    reclass.save("path\to\project\location\classPrg1")

    # Creating the contour shapefile from the reclassified raster
    contourInterval = 1
    baseContour = 0
    zFactor = 1
    outContour = "path\to\project\location\eclass-contour1.shp"
    contour = Contour(reclass,outContour,contourInterval,baseContour,zFactor)

    lengthField = "Length"
    fieldPrecision = 15
    fieldScale = 15
    arcpy.AddField_management(contour,lengthField,"DOUBLE",fieldPrecision,fieldScale)
    arcpy.CalculateField_management(contour,lengthField,"!SHAPE.LENGTH!","PYTHON_9.3")

    in_table = "path\to\project\location\eclass-contour1.dbf"

    # Selected contour with maximum length
    inputShape = "path\to\project\location\e-contourSelect1.shp " # Creating selected shapefile above line
    outputRaster = "path\to\project\location\prgSelect1"
    cell_size = 15

    # Convert the contour into Raster shapefile
    outputRas = arcpy.FeatureToRaster_conversion(inputShape,"ID",outputRaster,cell_size)

    outputPoint1 = "path\to\project\location\sras2point1.shp"
    opPoint = arcpy.RasterToPoint_conversion(outputRas,outputPoint1,"VALUE")

    # Input the terminus reference line shapefile
    lineShape = "path\to\project\location\TerminusWidth.shp"

    startPointShp = "path\to\project\location\startPoint.shp"
    endPointShp = "path\to\project\location\endPoint.shp"

    #Convert the vertices into start and end point shapefile
    start = arcpy.FeatureVerticesToPoints_management(lineShape,startPointShp,"START")
    end = arcpy.FeatureVerticesToPoints_management(lineShape,endPointShp,"END")

    outSTable = "path\to\project\location\start2Points1"
    arcpy.GenerateNearTable_analysis(opPoint,start,outSTable,'','LOCATION','NO_ANGLE','',0,"PLANAR")

    outETable = "path\to\project\location\end2Points1"
    arcpy.GenerateNearTable_analysis(opPoint,end,outETable,'','LOCATION','NO_ANGLE','',0,"PLANAR")

    # Coordinates for the furthest point from start point of terminus width shapefile
    myField = "NEAR_DIST"
    fX = "FROM_X"
    fY = "FROM_Y"
    sortDesc = arcpy.SearchCursor(outSTable,"","","",myField+" D")

    row = sortDesc.next()
    distance = row.NEAR_DIST
    fromX = row.FROM_X
    fromY = row.FROM_Y

    print distance, fromX, fromY

    # Coordinates for furthest point from end point of terminus width shapefile
    sortDescEnd = arcpy.SearchCursor(outETable,"","","",myField+" D")
    rowE = sortDescEnd.next()
    distanceE = rowE.NEAR_DIST
    fromX2 = rowE.FROM_X
    fromY2 = rowE.FROM_Y

    print distanceE, fromX2 , fromY2

    fc = "point3.shp"
    nfc = arcpy.CreateFeatureclass_management("path\to\project\location",fc,"POINT")
    arcpy.AddField_management(nfc,"X","FLOAT",field_length=50)
    arcpy.AddField_management(nfc,"Y","FLOAT",field_length=50)
    sRef = arcpy.SpatialReference("WGS 1984 Complex UTM Zone 22N")
    arcpy.DefineProjection_management(nfc,sRef)

    cursor = arcpy.da.InsertCursor(nfc,["X","Y","SHAPE@XY"])
    newRow = float(fromX),float(fromY),(fromX,fromY)
    cursor.insertRow(newRow)

    fc2 = "point4.shp"
    nfc2 = arcpy.CreateFeatureclass_management("path\to\project\location",fc2,"POINT")
    arcpy.AddField_management(nfc2,"X","FLOAT",field_length=50)
    arcpy.AddField_management(nfc2,"Y","FLOAT",field_length=50)
    sRef2 = arcpy.SpatialReference("WGS 1984 Complex UTM Zone 22N")
    arcpy.DefineProjection_management(nfc2,sRef2)

    #Converting the points to line shapefile
    cursor = arcpy.da.InsertCursor(nfc,["X","Y","SHAPE@XY"])
    newRow = float(fromX2),float(fromY2),(fromX2,fromY2)
    cursor.insertRow(newRow)

    line2 = arcpy.PointsToLine_management(nfc,"path\to\project\location\/sline2.shp")
    line2Point = "path\to\project\location\/line2Point.shp"
    point = arcpy.FeatureToPoint_management(line2,line2Point)


    near1 = arcpy.Near_analysis(point,outputPoint1,'','LOCATION','NO_ANGLE',"PLANAR")

    #Calculate distance to terminus 1
    near_cursor = arcpy.SearchCursor(near1)
    for row in near_cursor:
        dist1 =  row.getValue("NEAR_DIST")
    print dist1

    #Calculate distance to terminus 2
    outputPoint = "path\to\project\location\sras2point.shp"
    near2 = arcpy.Near_analysis(point,outputPoint,'','LOCATION','NO_ANGLE',"PLANAR")

    # Distance the glacier has receded between these two points
    near_cursor2 = arcpy.SearchCursor(near2)
    for row in near_cursor2:
        dist2 =  row.getValue("NEAR_DIST")
    print dist2
    distToTerm =  float(dist2 - dist1)
    return arcpy.AddMessage("Distance glacier has retreated = " + str(distToTerm)+" meters")


# ArcGIS user input
inputRas1 = arcpy.GetParameterAsText(0)
inputRas2 = arcpy.GetParameterAsText(1)
Terminus = arcpy.GetParameterAsText(2)

rasterLateImage(inputRas1)
rasterEarlyImage(inputRas2)

arcpy.CheckInExtension("Spatial")
print "Completed"



