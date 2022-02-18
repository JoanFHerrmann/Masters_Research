# Created by Joanie Herrmann
# This code compares two raster grids with a range of statistical measures: bias, standard deviation and root mean square error (RMSE). 
# Its original intention is to compare a bathymetric grid generated from satellite data to a grid from aerial LiDAR.  
# This code utilizes ArcPy, ArcGIS Pro's proprietary coding language, therefore requires a license and project. 
# Last updated 2/4/2022

from arcpy import env
import arcpy
# import sys 
# import time
import math 
import numpy as np 


# Set the workspace to the ArcGIS Pro datbase for the project
arcpy.env.workspace = r"I:\NASA\Florida_SDB\Florida_SDB.gdb"

def calculate_RMSE(raster_1, raster_2, AOI, tag): # (raster to compare other raster to, raster that other raster will be compared to, shapefile of the area of interest, string that will be added to outputs to distinguish)

    # Capture extent for raster_1
    domain_1 = "Domain1" + "_" + str(tag) # name of raster extent shapefile using the tag 
    if arcpy.Exists(domain_1) == 1: # checks to see if name already exists
        arcpy.Delete_management(domain_1) # deletes shapefile if it already exists
    arcpy.ddd.RasterDomain(raster_1, domain_1, "POLYGON") # creates polygon shapefile covering the extent of the first raster 

    # Capture extent for raster_2
    domain_2 = "Domain2" + "_" + str(tag) # name of raster extent shapefile using the tag 
    if arcpy.Exists(domain_2) == 1: # checks to see if name already exists
        arcpy.Delete_management(domain_2) # deletes shapefile if it already exists
    arcpy.ddd.RasterDomain(raster_2, domain_2, "POLYGON") # creates polygon shapefile covering the extent of the first raster 

    # Intersect between two extents 
    intersect = "intersect" + "_" + str(tag) # name of overlapping extents shapefile using the tag 
    if arcpy.Exists(intersect) == 1: # checks to see if name already exists
        arcpy.Delete_management(intersect) # deletes shapefile if it already exists
    arcpy.analysis.Intersect(str(domain_1) + " #;" + str(domain_2) + " #", intersect, "ALL", None, "INPUT") # creates polygon shapefile covering the intersection of the two rasters. 
                                                                                                            # "ALL": All the attributes from the input features are transferred to the output feature class.
                                                                                                            # "None": The minimum distance separating all feature coordinates (nodes and vertices) as well as the distance a coordinate can move in x or y (or both).
                                                                                                            #"INPUT": Output type is the same as the input type (polygon shapefile)

    # Crop first raster to the intersecting extent 
    extract_1 = "extract_1" + "_" + str(tag) # name of cropped raster 1 using the tag
    if arcpy.Exists(extract_1) == 1: # checks to see if name already exists
        arcpy.Delete_management(extract_1) # deletes raster if it already exists
    out_raster_CNES = arcpy.sa.ExtractByMask(raster_1, intersect) # Crops raster according to intersection "mask" shapefile
    out_raster_CNES.save(extract_1) # saves the cropped raster

    # Extract by intersect for raster_2 
    extract_2 = "extract_2" + "_" + str(tag) # name of cropped raster 2 using the tag
    if arcpy.Exists(extract_2) == 1: # checks to see if name already exists
        arcpy.Delete_management(extract_2) # deletes raster if it already exists
    out_raster_CNES = arcpy.sa.ExtractByMask(raster_2, intersect) # Crops raster according to intersection "mask" shapefile
    out_raster_CNES.save(extract_2) # saves the cropped raster

    # Now that both rasters are cropped to the same extent, start calculation for RMSE

    # Difference between two rasters
    difference = "difference" + "_" + str(tag) # name of the difference DEM using the tag 
    if arcpy.Exists(difference) == 1: # checks to see if name already exists
        arcpy.Delete_management(difference) # deletes raster if it already exists
    arcpy.ddd.Minus(extract_1, extract_2, difference) # takes the difference between the two DEMS

    # Generate statistics of the difference DEM 
    difference_table = "difference_table" + str(tag) # name of the statistics table using the tag 
    if arcpy.Exists(difference_table) == 1: # checks to see if name already exists
        arcpy.Delete_management(difference_table) # deletes raster if it already exists
    arcpy.sa.ZonalStatisticsAsTable(AOI, "OBJECTID", difference, difference_table, "DATA", "ALL", "CURRENT_SLICE")  # "AOI": dataset that defines the zone 
                                                                                                                    # "OBJECTID": The field that contains the values that define each zone.
                                                                                                                    # "DATA": Within any particular zone, only cells that have a value in the input value raster will be used in determining the output value for that zone. NoData cells in the value raster will be ignored in the statistic calculation
                                                                                                                    # "ALL":  All of the statistics will be calculated
                                                                                                                    # "CURRENT_SLICE": Statistics will be calculated from the current slice of the input multidimensional dataset.

    # Capture bias (mean difference) of difference DEM
    get_bias = arcpy.SearchCursor(difference_table) #Create cursor to access zonal statistics table 
    bias_num = [] #Create empty list for values to be added to
    field_name = "MEAN" # define we're looking for MEAN
    for area in get_bias: # search through cursor 
        bias_num.append(area.getValue(field_name)) # once desired field name matches field name in zonal table, add (append) that value to the empty list
    bias_num = np.sum(bias_num) # sum all MEAN values 
    print("The bias for " + str(tag) + " is " + str(round(bias_num,3))+ " meters.") # print the mean difference to three decimal places 

    # Capture standard deviation (STD) of difference DEM  
    get_std = arcpy.SearchCursor(difference_table) #Create cursor to access zonal statistics table 
    std_num = [] #Create empty list for values to be added to
    field_name = "STD" # define we're looking for STD 
    for area in get_std: # search through cursor
        std_num.append(area.getValue(field_name)) # once desired field name matches field name in zonal table, add (append) that value to the empty list
    std_num = np.sum(std_num) # sum all STF values 
    print("The standard deviation for " + str(tag) + " is " + str(round(std_num,3))+ " meters.") # print the standard deviation to three decimal places 

    # Create check that the RMSE will be compared to as "gut check"
    check = np.sqrt(std_num**2 + bias_num**2) #square root of the square standard deviation plus the square mean
    print("The square root of the square standard deviation plus the square mean for " + str(tag) + " is " + str(round(check,3))+ " meters.") # print the result to three decimal places 

    # Square each value of the difference raster  
    square_raster = "square_raster" + str(tag) # name of the square DEM using the tag 
    if arcpy.Exists(square_raster) == 1: # checks to see if name already exists
        arcpy.Delete_management(square_raster) # deletes raster if it already exists
    out_raster = arcpy.ia.Square(difference); # Squares every value within the difference DEM
    out_raster.save(square_raster) # Saves the square DEM 

    # Generate statistics table for the square 
    square_table = "square_table" + str(tag) # name of the square DEM using the tag
    if arcpy.Exists(square_table) == 1: # checks to see if name already exists
        arcpy.Delete_management(square_table) # deletes raster if it already exists
    arcpy.sa.ZonalStatisticsAsTable(AOI, "OBJECTID", square_raster, square_table, "DATA", "ALL", "CURRENT_SLICE")   # "AOI": dataset that defines the zone 
                                                                                                                    # "OBJECTID": The field that contains the values that define each zone.
                                                                                                                    # "DATA": Within any particular zone, only cells that have a value in the input value raster will be used in determining the output value for that zone. NoData cells in the value raster will be ignored in the statistic calculation
                                                                                                                    # "ALL":  All of the statistics will be calculated
                                                                                                                    # "CURRENT_SLICE": Statistics will be calculated from the current slice of the input multidimensional dataset.

    # Capture the number of cells in square DEM
    get_count = arcpy.SearchCursor(square_table) # Create cursor to access zonal statistics table 
    count_num = [] #Create empty list for values to be added to
    field_name = "COUNT" # define we're looking for COUNT 
    for area in get_count: #search through cursor 
        count_num.append(area.getValue(field_name)) # once desired field name matches field name in zonal table, add (append) that value to the empty list
        
    count_num = np.sum(count_num) #sum all count values 

    # Capture sum of square DEM
    get_sum = arcpy.SearchCursor(square_table) # Create cursor to access zonal statistics table 
    sum_num = [] #Create empty list for values to be added to
    field_name = "SUM" # define we're looking for SUM 
    for area in get_sum: #search through cursor 
        sum_num.append(area.getValue(field_name)) # once desired field name matches field name in zonal table, add (append) that value to the empty list

    sum_num = np.sum(sum_num) # sum all sum values 

    RMSE = math.sqrt(int(sum_num)/int(count_num)) # calculate root mean square error

    print("The RMSE for " + str(tag) + " is " + str(round(RMSE,3))+ " meters.") # Print the RMSE for the user to three decimal places

    # Test to make sure RMSE is reasonable 
    test_2 = np.abs(RMSE-check)
    if test_2 < 0.01: # if its not within 1 cm, then its no good 
        print("All good! RMSE minus square root of square mean plus square standard deviation is " + str(round(test_2,3)) + " m.") # Tell the user RMSE passed the check 
    else: 
        print("No good! RMSE minus square root of square mean plus square standard deviation is " + str(round(test_2,3)) + " m.") # Tell the user RMSE did not pass the check 
        
    # Take out the trash     
    arcpy.management.Delete(domain_1)
    arcpy.management.Delete(domain_2)
    arcpy.management.Delete(intersect)
    arcpy.management.Delete(extract_1)
    arcpy.management.Delete(extract_2)
    # arcpy.management.Delete(difference) commented out to produce visual of areas of highest and lowest agreement
    arcpy.management.Delete(difference_table)
    arcpy.management.Delete(square_raster)
    arcpy.management.Delete(square_table)

calculate_RMSE(r"I:\NASA\Florida_SDB\sm_AOI_truth.tif", r"I:\NASA\Florida_SDB\sm_AOI_difference.tif", "AOI_btw_tracklines", "cut_extent") # this line runs the code and is change for new datasets