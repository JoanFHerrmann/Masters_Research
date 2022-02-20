# Created by Joanie Herrmann
# This code was developed to aid in vertical datum transformation needs through NOAA's VDatum project by creating offshore mean sea surface (MSS) and topographic sea surface (TSS) grids. 
# Offshore areas are defined are those greater than 9 m offshore. For inshore TSS and MSS grid generation, another method is used, outside the scope of this code. 
# For MSS grid generation, four inputs are required and for TSS grid generation, six inputs are needed. 
# For MSS:  (1) Global MSS grid: For this project, CNES's (France's Space Agency) product is used. This represents mean sea profile above a reference ellipsoid 
#               (T/P or WSG84) and its resolution is 1/60°x1/60°, 1 minute. This grid was chosen because it contains another grid that provides the estimation of error fields 
#               which represent the MSS accuracy estimated through the inverse technique. This was crucial for determining the exact value defining offshore/inshore extents. 
#           (2): Grid that accounts for the vertical conversion from topex poseidon to WGS 84 (both are ellipsoids). Ellipsoid heights is the difference between the ellisoid 
#               a point on earth's surface. This was accomplished through a custom MATLAB script. 
#           (3): Grid that accounts for mean tide to tide free. Because geodetic parameters are affected by tidal variations, observable gravitational potential contains time
#               independent (permanent) and time dependent (periodic) parts. Mean tide refers to positions where time dependence of tidal contributrions is removed. For tide 
#               free, the total tidal effects have been removed within a model. 
#           (4): Land polygon: A polygon shapefile that captures land. This is the area that will be removed from the final product because we're only interested in areas of earth
#               covered in water, not land. 
# For TSS:  (1) Global MSS grid (see above for detail)
#           (2) Geoid product: A geoid is an imaginary sea level surface that undulates (wavy surface) across earth's surface (including over land) under the influence of gravity
#               This project uses xGeoid 20 which is an experimental geoid through the National Geodetic Survey (NGS) containing gravity data from a number of satellite gravity models
#               including airborne graviety from GRAV-D.  
#           (3) Grid that accounts for vertical coversion from the topex poseidon ellipsoid to the WGS 84 ellipsoid (see above for detail )
#           (4) Grid that accounts for mean tide to tide free (see above for detail)
#           (5) Land polygon (see above for detail)
#           (6) Intersect is an polygon shapefile that is the intersection between the MSS product (CNES) and the Geoid product (xGeoid20). Previously this was done within the code, however 
#               there was an error with automating it so this single step was performed manually in ArcGIS Pro. 
# Both products are generated with simple equations. For MSS grid generation, the equation is CNES MSS + conversion from topex poseidon + conversion from mean tide to tide free. Because
# the two conversion grids can be generated to any extent, the MSS grid extent is limited to areas covered by CNES' MSS product. Because CNES' MSS grid covers the entire world, the final 
# MSS grid presented also covers the entire world. For TSS grid generation, the equation is xGeoid20 - CNES' MSS - conversion from topex poseidon - conversion from mean tide to tide free.
# Similarly, the conversion grids can be generated for any extent, therefore the limiting factors for extent are xGeoid 20 and CNES' MSS coverage. As mentioned previously, CNES' MSS grid 
# covers the entire world, however xGeoid20 covers from 0 to 82 degrees north and 180 to 10 degrees west. Therefore this is also the extent of the TSS grid. 


from arcpy import env
import arcpy
# import sys
# import time
import math 
import numpy as np


# Set the workspace to the ArcGIS Pro project geodatabase
arcpy.env.workspace = r"C:\Users\herrmanj\Desktop\NOAA\TSS_final\TSS_final.gdb"


def MSS_generation(CNES, TP_WGS, MT_FT, land_polygon, tag): # this code generates MSS grids based on the extents provided by the inputs 
                                                            # (CNES' MSS grid, conversion grid from topex poseidon to WGS 84, conversion grid from mean tide to tide free, a land polygon 
                                                            # covering area NOT of interest, tag (string of characters) to be added to outputs to distinguish)

    # Create polygon shapefile covering the extent of CNES' MSS 
    CNES_domain = "CNES_domain" + "_" + str(tag) # create name for shapefile
    if arcpy.Exists(CNES_domain) == 1: # see if shapefile already exists
        arcpy.Delete_management(CNES_domain) # if so, delete old shapefile
    arcpy.ddd.RasterDomain(CNES, CNES_domain, "POLYGON") # "POLYGON": The output will be a z-enabled polygon feature class.

    # Create polygon shapefile covering the extent of the matlab inputs 
    matlab_domain = "matlab_domain" + "_" + str(tag) # create name for shapefile
    if arcpy.Exists(matlab_domain) == 1: # see if shapefile already exists
        arcpy.Delete_management(matlab_domain) # if so, delete old shapefile
    arcpy.ddd.RasterDomain(MT_FT, matlab_domain, "POLYGON") # "POLYGON": The output will be a z-enabled polygon feature class.
                                                            # note that either TP_WGS or MT_FT can be used

    #Find intersect between extent of CNES' MSS and the matlab inputs 
    intersect = "intersect" + "_" + str(tag) # create name for shapefile
    if arcpy.Exists(intersect) == 1: # see if shapefile already exists
        arcpy.Delete_management(intersect) # if so, delete old shapefile
    arcpy.analysis.Intersect(CNES_domain + " #;" + matlab_domain + " #", intersect, "ALL", None, "INPUT")   # creates polygon shapefile covering the intersection of the two input shapefiles. 
                                                                                                            # "ALL": All the attributes from the input features are transferred to the output feature class.
                                                                                                            # "None": The minimum distance separating all feature coordinates (nodes and vertices) as well as the distance a coordinate can move in x or y (or both).
                                                                                                            # "INPUT": Output type is the same as the input type (polygon shapefile)


    # Create buffer around land shapefile to delineate between onshore and offshore extents 
    buffer = "buffer" + "_" + str(tag) # create name for shapefile
    if arcpy.Exists(buffer) == 1: # see if shapefile already exists
        arcpy.Delete_management(buffer)# if so, delete old shapefile
    arcpy.analysis.Buffer(land_polygon, buffer, "9000 Meters", "FULL", "ROUND", "ALL", None, "PLANAR") # "Buffer" creates buffer around a shapefile for a designated distance 
                                                                                                        #'9000 Meters': (or 9 km) The distance around the input features that will be buffered. Using CNES' MSS product, this was determined as the offshore extent where uncertainty meaningfully increases. 
                                                                                                        #"FULL":  For polygon input features, buffers will be generated around the polygon and will contain and overlap the area of the input features. 
                                                                                                        #"ROUND": The ends of the buffer will be round, in the shape of a half circle. 
                                                                                                        # "ALL": Dissolve all output features into a single feature — All buffers will be dissolved together into a single feature, removing any overlap.
                                                                                                        # "NONE": The list of fields from the input features on which the output buffers will be dissolved. 
                                                                                                        #"PLANAR": If the input features are in a geographic coordinate system and the buffer distance is in linear units (meters, feet, and so forth, as opposed to angular units such as degrees), geodesic buffers will be created. 


    # Create final extent by removing areas not of interest (e.g. land and nearshore extents)
    final_mask = "final_mask" + "_" + str(tag) # create name for shapefile
    if arcpy.Exists(final_mask) == 1: # see if shapefile already exists
        arcpy.Delete_management(final_mask) # if so, delete old shapefile
    arcpy.analysis.Erase(intersect, buffer, final_mask, None)   # Erase land polygon plus buffer from final extent 
                                                                # "None": The minimum distance separating all feature coordinates (nodes and vertices) as well as the distance a coordinate can move in X or Y (or both). 


    # Crop CNES to the final mask extent 
    final_CNES = "final_CNES" + "_" + str(tag) # create name for raster
    if arcpy.Exists(final_CNES) == 1: # see if raster already exists
        arcpy.Delete_management(final_CNES) # if so, delete old raster
    out_raster_CNES = arcpy.sa.ExtractByMask(CNES, final_mask) # Crop CNES' MSS to the extent of final mask
    out_raster_CNES.save(final_CNES) # save the output from tool above

    # Crop conversion grid from topex poseidon to WGS84 to final mask extent
    final_TP_WGS = "final_TP_WGS" + "_" + str(tag) # create name for raster
    if arcpy.Exists(final_TP_WGS) == 1: # see if raster already exists
        arcpy.Delete_management(final_TP_WGS) # if so, delete old raster
    out_raster_TP_WGS = arcpy.sa.ExtractByMask(TP_WGS, final_mask) # Crop conversion grid to the extent of final mask
    out_raster_TP_WGS.save(final_TP_WGS) # save the output from tool above
        
    # Crop conversion grid from mean tide to tide free to final mask extent
    final_MT_FT = "final_MT_FT" + "_" + str(tag) # create name for raster
    if arcpy.Exists(final_MT_FT) == 1: # see if raster already exists
        arcpy.Delete_management(final_MT_FT) # if so, delete old raster
    out_raster_MT_FT = arcpy.sa.ExtractByMask(MT_FT, final_mask) # Crop conversion grid to the extent of final mask
    out_raster_MT_FT.save(final_MT_FT) # save the output from tool above

    # Use raster calculator to generate the final TSS grid
    raster = "raster" + "_" + str(tag) # create name for raster
    if arcpy.Exists(raster) == 1: # see if raster already exists
        arcpy.Delete_management(raster) # if so, delete old raster
    output_raster = arcpy.ia.RasterCalculator([final_CNES, final_TP_WGS, final_MT_FT], ["a", "b", "c"], "a+b+c")    # the equation is CNES MSS + conversion from topex poseidon to WGS 84 + conversion from mean tide to tide free 
                                                                                                                    # Note all inputs are cut to the same extent due to the three previous steps 
    output_raster.save(raster) # save output 

    # Take out the trash 
    arcpy.management.Delete(CNES_domain)
    arcpy.management.Delete(matlab_domain)
    arcpy.management.Delete(buffer)
    arcpy.management.Delete(final_mask)
    arcpy.management.Delete(final_CNES)
    arcpy.management.Delete(final_TP_WGS)
    arcpy.management.Delete(final_MT_FT)

# MSS_generation(r"C:\Users\herrmanj\Desktop\NOAA\TSS_final\Raw_Data\MSS.tif", r"C:\Users\herrmanj\Desktop\NOAA\TSS_final\tp_wgs_xGeoid20_2.tif", r"C:\Users\herrmanj\Desktop\NOAA\TSS_final\mt_tf_xGeoid20.tif", "aggregate_land", "MSS_extentxGeoid20") # this line of code will run the "MSS_generation" function. 

# The "TSS_generation" function creates TSS grids based on the extents provided by the inputs. 
def TSS_generation(CNES, Geoid, TP_WGS, MT_FT, land_polygon, tag, intersect): # (CNES' MSS raster, xGeoid20 raster, conversion grid from topex poseidon to WGS 84,
#                                                                             # conversion grid from mean tide to tide free, a poylgon shapefile covering land not to be included
#                                                                             # tag (string of characters) to be added to ouputs for organization, polygon shapefile covering intersection of CNES' MSS and xGeoid20)

    # Create polygon shapefile for buffer around land shapefile 
    buffer = "buffer" + "_" + str(tag) # create name for shapefile
    if arcpy.Exists(buffer) == 1: # check to see if it already exists
        arcpy.Delete_management(buffer) # if so, delete old shapefile 
    arcpy.analysis.Buffer(land_polygon, buffer, "9000 Meters", "FULL", "ROUND", "ALL", None, "PLANAR") # "Buffer" creates buffer around a shapefile for a designated distance 
                                                                                                        #'9000 Meters': (or 9 km) The distance around the input features that will be buffered. Using CNES' MSS product, this was determined as the offshore extent where uncertainty meaningfully increases. 
                                                                                                        #"FULL":  For polygon input features, buffers will be generated around the polygon and will contain and overlap the area of the input features. 
                                                                                                        #"ROUND": The ends of the buffer will be round, in the shape of a half circle. 
                                                                                                        # "ALL": Dissolve all output features into a single feature — All buffers will be dissolved together into a single feature, removing any overlap.
                                                                                                        # "NONE": The list of fields from the input features on which the output buffers will be dissolved. 
                                                                                                        #"PLANAR": If the input features are in a geographic coordinate system and the buffer distance is in linear units (meters, feet, and so forth, as opposed to angular units such as degrees), geodesic buffers will be created. 


    # Create final mask that reflects area not of interest (e.g. buffer around land shapefile) from extent 
    final_mask = "final_mask" + "_" + str(tag) # create name for shapefile
    if arcpy.Exists(final_mask) == 1: # check to see if it already exists
        arcpy.Delete_management(final_mask) # if so, delete old shapefile 
    arcpy.analysis.Erase(intersect, buffer, final_mask, None) # Erase land polygon plus buffer from final extent 
                                                              # "None": The minimum distance separating all feature coordinates (nodes and vertices) as well as the distance a coordinate can move in X or Y (or both). 


    # Create raster that crops CNES' MSS grid to the final mask extent 
    final_CNES = "final_CNES" + "_" + str(tag) # create name for raster
    if arcpy.Exists(final_CNES) == 1: # check to see if it already exists
        arcpy.Delete_management(final_CNES) # if so, delete old raster 
    out_raster_CNES = arcpy.sa.ExtractByMask(CNES, final_mask) # Crop CNES' MSS raster to final extent 
    out_raster_CNES.save(final_CNES) #save output
    
    # Create raster that crops the Geoid grid to the final mask extent 
    final_Geoid = "final_Geoid" + "_" + str(tag) # create name for raster
    if arcpy.Exists(final_Geoid) == 1: # check to see if it already exists
        arcpy.Delete_management(final_Geoid) # if so, delete old raster 
    out_raster_Geoid = arcpy.sa.ExtractByMask(Geoid, final_mask) # Crop Geoid raster to final extent 
    out_raster_Geoid.save(final_Geoid) # save output

    # Create raster that crops the conversion from topex poseidon to WGS84 grid to the final mask extent 
    final_TP_WGS = "final_TP_WGS" + "_" + str(tag) # create name for raster
    if arcpy.Exists(final_TP_WGS) == 1: # check to see if it already exists
        arcpy.Delete_management(final_TP_WGS) # if so, delete old raster 
    out_raster_TP_WGS = arcpy.sa.ExtractByMask(TP_WGS, final_mask) # Crop conversion from topex poseidon to WGS84 raster to final extent 
    out_raster_TP_WGS.save(final_TP_WGS) # save output
        
    # Create raster that crops the conversion from mean tide to tide free to the final mask extent 
    final_MT_FT = "final_MT_FT" + "_" + str(tag) # create name for raster
    if arcpy.Exists(final_MT_FT) == 1: # check to see if it already exists
        arcpy.Delete_management(final_MT_FT) # if so, delete old raster 
    out_raster_MT_FT = arcpy.sa.ExtractByMask(MT_FT, final_mask) # Crop conversion from mean tide to tide free raster to final extent
    out_raster_MT_FT.save(final_MT_FT) # save output

    # Use raster calculator to generate TSS grid
    raster = "raster" + "_" + str(tag) # create name for raster
    if arcpy.Exists(raster) == 1: # check to see if it already exists
        arcpy.Delete_management(raster) # if so, delete old raster 
    output_raster = arcpy.ia.RasterCalculator([final_Geoid, final_CNES, final_TP_WGS, final_MT_FT], ["a", "b", "c", "d"], "a-b-c-d") # the equation is CNES MSS - xGeoid20 - conversion from topex poseidon to WGS 84 - conversion from mean tide to tide free 
                                                                                                                                     # Note all inputs are cut to the same extent due to the three previous steps 
    output_raster.save(raster) # save output from raster calculator 

    # Take out the trash 
    arcpy.management.Delete(buffer)
    arcpy.management.Delete(final_mask)
    arcpy.management.Delete(final_CNES)
    arcpy.management.Delete(final_Geoid)
    arcpy.management.Delete(final_TP_WGS)
    arcpy.management.Delete(final_MT_FT)

# TSS_generation(r"C:\Users\herrmanj\Desktop\NOAA\TSS_final\Raw_Data\MSS.tif", r"C:\Users\herrmanj\Desktop\NOAA\TSS_final\Raw_Data\xGeoid20.tif", r"C:\Users\herrmanj\Desktop\NOAA\TSS_final\tp_wgs_xGeoid20_2.tif", r"C:\Users\herrmanj\Desktop\NOAA\TSS_final\mt_tf_xGeoid20.tif", "aggregate_land", "xGeoid20_agg", "xGeoid20_RD") # this line of code will run the "TSS_generation" function.