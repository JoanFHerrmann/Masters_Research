# Created by Joanie Herrmann

from arcpy import env
import arcpy
import sys
import time
import math 
import numpy as np


# Set the workspace
arcpy.env.workspace = r"I:\NASA\Florida_SDB\Florida_SDB.gdb"


def calculate_RMSE(raster_1, raster_2, AOI, tag):

    # Create domain for raster_1
    domain_1 = "Domain1" + "_" + str(tag)
    if arcpy.Exists(domain_1) == 1: 
        arcpy.Delete_management(domain_1)
    arcpy.ddd.RasterDomain(raster_1, domain_1, "POLYGON") 

    # Create domain for raster_2
    domain_2 = "Domain2" + "_" + str(tag)
    if arcpy.Exists(domain_2) == 1: 
        arcpy.Delete_management(domain_2)
    arcpy.ddd.RasterDomain(raster_2, domain_2, "POLYGON")

    # Intersect between two extents 
    intersect = "intersect" + "_" + str(tag) 
    if arcpy.Exists(intersect) == 1: 
        arcpy.Delete_management(intersect)
    arcpy.analysis.Intersect(str(domain_1) + " #;" + str(domain_2) + " #", intersect, "ALL", None, "INPUT")

    # Extract by intersect for raster_1 
    extract_1 = "extract_1" + "_" + str(tag)
    if arcpy.Exists(extract_1) == 1: 
        arcpy.Delete_management(extract_1)
    out_raster_CNES = arcpy.sa.ExtractByMask(raster_1, intersect)
    out_raster_CNES.save(extract_1)

    # Extract by intersect for raster_2 
    extract_2 = "extract_2" + "_" + str(tag)
    if arcpy.Exists(extract_2) == 1: 
        arcpy.Delete_management(extract_2)
    out_raster_CNES = arcpy.sa.ExtractByMask(raster_2, intersect)
    out_raster_CNES.save(extract_2)

    # start calculation for RMSE

    # Difference between two rasters
    difference = "difference" + "_" + str(tag)
    if arcpy.Exists(difference) == 1: 
        arcpy.Delete_management(difference)
    arcpy.ddd.Minus(extract_1, extract_2, difference)

    # Calculate the number of cells in the minus DEM 
    difference_table = "difference_table" + str(tag) 
    if arcpy.Exists(difference_table) == 1: 
        arcpy.Delete_management(difference_table)
    arcpy.sa.ZonalStatisticsAsTable(AOI, "OBJECTID", difference, difference_table, "DATA", "ALL", "CURRENT_SLICE")

    # Print the bias (mean difference) 
    get_bias = arcpy.SearchCursor(difference_table)
    bias_num = []
    field_name = "MEAN"
    for area in get_bias:
        bias_num.append(area.getValue(field_name))
    bias_num = np.sum(bias_num)
    print("The bias for " + str(tag) + " is " + str(round(bias_num,3))+ " meters.")

    # Print the standard (mean difference) 
    get_std = arcpy.SearchCursor(difference_table)
    std_num = []
    field_name = "STD"
    for area in get_std:
        std_num.append(area.getValue(field_name))
    std_num = np.sum(std_num)
    print("The standard deviation for " + str(tag) + " is " + str(round(std_num,3))+ " meters.")

    check = np.sqrt(std_num**2 + bias_num**2)
    print("The square root of the square standard deviation plus the square mean for " + str(tag) + " is " + str(round(check,3))+ " meters.")

    # Square each value of the difference raster 
    square_raster = "square_raster" + str(tag) 
    if arcpy.Exists(square_raster) == 1: 
        arcpy.Delete_management(square_raster)
    out_raster = arcpy.ia.Square(difference); 
    out_raster.save(square_raster)

    # Calculate the number of cells in the minus DEM 
    square_table = "square_table" + str(tag) 
    if arcpy.Exists(square_table) == 1: 
        arcpy.Delete_management(square_table)
    arcpy.sa.ZonalStatisticsAsTable(AOI, "OBJECTID", square_raster, square_table, "DATA", "ALL", "CURRENT_SLICE")

    # Get the number of cells
    get_count = arcpy.SearchCursor(square_table)
    count_num = []
    field_name = "COUNT"
    for area in get_count:
        count_num.append(area.getValue(field_name))
        
    count_num = np.sum(count_num)

    get_sum = arcpy.SearchCursor(square_table)
    sum_num = []
    field_name = "SUM"
    for area in get_sum:
        sum_num.append(area.getValue(field_name))

    sum_num = np.sum(sum_num)

    RMSE = math.sqrt(int(sum_num)/int(count_num))

    print("The RMSE for " + str(tag) + " is " + str(round(RMSE,3))+ " meters.")

    test_2 = np.abs(RMSE-check)
    if test_2 < 0.01: 
        print("All good! RMSE minus square root of square mean plus square standard deviation is " + str(round(test_2,3)) + " m.")
    else: 
        print("No good! RMSE minus square root of square mean plus square standard deviation is " + str(round(test_2,3)) + " m.")
        
    arcpy.management.Delete(domain_1)
    arcpy.management.Delete(domain_2)
    arcpy.management.Delete(intersect)
    arcpy.management.Delete(extract_1)
    arcpy.management.Delete(extract_2)
    # arcpy.management.Delete(difference)
    arcpy.management.Delete(difference_table)
    arcpy.management.Delete(square_raster)
    arcpy.management.Delete(square_table)

calculate_RMSE(r"I:\NASA\Florida_SDB\sm_AOI_truth.tif", r"I:\NASA\Florida_SDB\sm_AOI_difference.tif", "AOI_btw_tracklines", "cut_extent")