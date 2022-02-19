# Created by Joanie Herrmann
# This code was created to create the inputs needed for a physics based erosion model for sea cliffs on the Oregon Coast. Specifically, three inputs are needed: cross sections, cliff toe points 
# and cliff toe points. These products are automatically generated using CliffMetrics, a SAGA GUI developed by Payo et al. 2018. (https://gmd.copernicus.org/articles/11/4317/2018/). However, the 
# outputs from CliffMetrics pose three challenges; First, their density reflects a resolution more precise than the digital elevation model. Using the original density may lead to results that are
# overestimate accuracy. Next, the cross sections are not long enough for the erosion model. The cross sections need to extend several hundred meters to provide area for the model to predict erosion
# and originally, they are only ~100 m. Lastly, the erosion model needs X, Y and Z data for the cross sections. The coordinate system for this project is NAD 1983 Oregon Statewide Lambert (meters), 
# however any coordinate system can be used for this script.  
# Accordingly, this code contains three functions; (1) thin_it_out: thinning out CliffMetrics outputs including toe and top points as well as normals to reflect resolution 
#                                                  (2) extend_cross_sections: extending cross sections to capture entire sea cliff profile (e.g. area for model to project erosion)
#                                                  (3) get_the_good_stuff: Attach X, Y and Z data to the cross sections in meters 
# All functions are to aid in SPR 843 through Oregon Department of Transportation to forecast coastal cliff erosion. 
# This code relies on ArcPy, ArcGIS Pro's proprietary coding language. In the comment section, explanations, as well as justifications, for decisions is provided. 
# Last updated on 12/15/2021

from arcpy import env
import arcpy
# import sys
# import time

# Set the workplace to the ArcGIS Pro database 
arcpy.env.workspace = r"I:\Thesis\Thesis\Near_Brush_Creek.gdb"

# "Thin_it_out" function to create greater spacing in CliffMetrics outputs to increase processing speed of the erosion model 
def thin_it_out(normals, toe_pts, top_pts, tag): # (normals shapefile, toe points shapefile, top points shapefile, tag (string of characters) to be added to all outputs for organization)

    # Iterate through normals and keep one in every 15
    with arcpy.da.UpdateCursor(normals, "OBJECTID") as cursor: # Create cursor for OBJECTID because each OBJECTID is unique (no duplicates)
        for row in cursor: # Search through cursor 
            object_id = row[0] # We're interested in looking at the first row (i.e OBJECTID column)
            if object_id % 15 != 0: # Check to see whether that OBJECTID is divisible by 15
                cursor.deleteRow() # If there is a remainder, then delete
    
    # Iterate through toe points and keep one in every 15
    with arcpy.da.UpdateCursor(toe_pts, "OBJECTID") as cursor: # Create cursor for OBJECTID because each OBJECTID is unique (no duplicates)
        for row in cursor: # Search through cursor 
            object_id = row[0] # We're interested in looking at the first row (i.e OBJECTID column)
            if object_id % 15 != 0: # Check to see whether that OBJECTID is divisible by 15
                cursor.deleteRow() # If there is a remainder, then delete

    # Iterate through top points and keep one in every 15
    with arcpy.da.UpdateCursor(top_pts, "OBJECTID") as cursor: # Create cursor for OBJECTID because each OBJECTID is unique (no duplicates)
        for row in cursor: # Search through cursor 
            object_id = row[0] # We're interested in looking at the first row (i.e OBJECTID column)
            if object_id % 15 != 0: # Check to see whether that OBJECTID is divisible by 15
                cursor.deleteRow() # If there is a remainder, then delete
    
    # Copy normals to "reset" object ID numbers (previously 15, 30, 45 to 1, 2, 3)
    normals_thin = "normals_thin" + "_" + str(tag) # create shapefile name of new normals with tag
    if arcpy.Exists(normals_thin) == 1: # see if shapefile already exists
        arcpy.Delete_management(normals_thin) # delete if it already exists
    arcpy.management.CopyFeatures(normals, normals_thin, '', None, None, None)  #'': Geodatabase configuration keyword to be applied if the output is a geodatabase. (n/a)
                                                                                #: None: This parameter has been deprecated in ArcGIS Pro. Any value you enter is ignored.        
                                                                                #: None: This parameter has been deprecated in ArcGIS Pro. Any value you enter is ignored. 
                                                                                #: None: This parameter has been deprecated in ArcGIS Pro. Any value you enter is ignored. 

    # For the normals, delete unnecessary fields 
    arcpy.management.DeleteField(normals_thin, "ORIG_FID;Normal;StartCoast;EndCoast;HitLand;HitCoast;HitNormal;nCoast")

    # Copy toe points to "reset" object ID numbers (previously 15, 30, 45 to 1, 2, 3)
    toe_thin = "toe_thin" + "_" + str(tag) # create shapefile name of new points with tag
    if arcpy.Exists(toe_thin) == 1: # see if shapefile already exists
        arcpy.Delete_management(toe_thin) # delete if it already exists
    arcpy.management.CopyFeatures(toe_pts, toe_thin, '', None, None, None)  #'': Geodatabase configuration keyword to be applied if the output is a geodatabase. (n/a)
                                                                            #: None: This parameter has been deprecated in ArcGIS Pro. Any value you enter is ignored.        
                                                                            #: None: This parameter has been deprecated in ArcGIS Pro. Any value you enter is ignored. 
                                                                            #: None: This parameter has been deprecated in ArcGIS Pro. Any value you enter is ignored. 

    # For the toe points, delete stupid fields
    arcpy.management.DeleteField(toe_thin, "nCoast;nProf;bisOK;CoastEl;CliffToeEl")

    # Copy top points to "reset" object ID numbers (previously 15, 30, 45 to 1, 2, 3)
    top_thin = "top_thin" + "_" + str(tag) # create shapefile name of new points with tag
    if arcpy.Exists(top_thin) == 1: # see if shapefile already exists
        arcpy.Delete_management(top_thin) # delete if it already exists
    arcpy.management.CopyFeatures(top_pts, top_thin, '', None, None, None)  #'': Geodatabase configuration keyword to be applied if the output is a geodatabase. (n/a)
                                                                            #: None: This parameter has been deprecated in ArcGIS Pro. Any value you enter is ignored.        
                                                                            #: None: This parameter has been deprecated in ArcGIS Pro. Any value you enter is ignored. 
                                                                            #: None: This parameter has been deprecated in ArcGIS Pro. Any value you enter is ignored. 


    # For the top points, Delete stupid fields
    arcpy.management.DeleteField(top_thin, "nCoast;nProf;bisOK;CliffTopEl;Chainage")

# thin_it_out("normals", "cliff_toe", "cliff_top", "Ophir_Beach") # this line of code will run the function. All other lines of code to run functions must be commented out. 

# "Extend_cross_sections" function will extend cross sections 450 meters landward and 20 meters oceanward. 
def extend_cross_sections(normals, coast, tag): # (normals from previous function shapefile, coastline shapefile, tag (string of characters) to add to all outputs)
    
    # First, create land buffer that is 450 meters inland from the coastline shapefile
    land_buffer = "land_buffer" # Create name for land buffer polygon shapefile output
    if arcpy.Exists(land_buffer) == 1: # Check to see if name already exists
        arcpy.Delete_management(land_buffer) # If so, delete that shapefile 
    arcpy.analysis.Buffer(coast, land_buffer, "450 Meters", "RIGHT", "ROUND", "ALL", None, "Geodesic")  # "Buffer" creates buffer around a shapefile for a designated distance 
                                                                                                        #'450 Meters': The distance around the input features that will be buffered.
                                                                                                        #"RIGHT": For line input features, buffers will be generated on the topological right of the line.
                                                                                                        #"ROUND": The ends of the buffer will be round, in the shape of a half circle. 
                                                                                                        # "ALL": Dissolve all output features into a single feature — All buffers will be dissolved together into a single feature, removing any overlap.
                                                                                                        # "NONE": The list of fields from the input features on which the output buffers will be dissolved. 
                                                                                                        #"Geodesic": (shape preserving) — All buffers will be created using a shape-preserving geodesic buffer method, regardless of the input coordinate system. 

    #Next, turn land buffer polygon shapefile into line shapefile
    land_line = "land_line" # Create name for land buffer line shapefile output
    if arcpy.Exists(land_line) == 1: # Check to see if name already exists
        arcpy.Delete_management(land_line) # If so, delete that shapefile 
    arcpy.management.PolygonToLine(land_buffer, land_line, "IGNORE_NEIGHBORS") #"IGNORE_NEIGHBORS": doesnt identify and store neighbouring information 

    # Next, create beach buffer 
    beach_buffer = "beach_buffer" # Create name for beach buffer polygon shapefile output
    if arcpy.Exists(beach_buffer) == 1:  # Check to see if name already exists
        arcpy.Delete_management(beach_buffer) # If so, delete that shapefile
    arcpy.analysis.Buffer(coast, beach_buffer, "20 Meters", "LEFT", "ROUND", "ALL", None, "Geodesic")   # "Buffer" creates buffer around a shapefile for a designated distance 
                                                                                                        #'20 Meters': The distance around the input features that will be buffered.
                                                                                                        #"LEFT": For line input features, buffers will be generated on the topological left of the line.
                                                                                                        #"ROUND": The ends of the buffer will be round, in the shape of a half circle. 
                                                                                                        # "ALL": Dissolve all output features into a single feature — All buffers will be dissolved together into a single feature, removing any overlap.
                                                                                                        # "NONE": The list of fields from the input features on which the output buffers will be dissolved. 
                                                                                                        #"Geodesic": (shape preserving) — All buffers will be created using a shape-preserving geodesic buffer method, regardless of the input coordinate system. 


    #Next, turn beach buffer into line 
    beach_line = "beach_line" # Create name for beach buffer line shapefile output
    if arcpy.Exists(beach_line) == 1: # Check to see if name already exists
        arcpy.Delete_management(beach_line) # If so, delete that shapefile 
    arcpy.management.PolygonToLine(beach_buffer, beach_line, "IGNORE_NEIGHBORS") #"IGNORE_NEIGHBORS": doesnt identify and store neighbouring information 

    # Merge land and beach buffer line shapefiles 
    merge_buffer = "merge_buffer" # Create name for merged buffer lines shapefile output
    if arcpy.Exists(merge_buffer) == 1: # Check to see if name already exists
        arcpy.Delete_management(merge_buffer) # If so, delete that shapefile 
    arcpy.management.Merge(beach_line + ";" + land_line, merge_buffer) # Merge the land buffer line and beach buffer line into one shapefile

    # Delete middle line shared between both buffer line shapefiles 
    merged_buffer_erase = "merged_buffer_erase" # Create name for merged buffer lines shapefile output with middle line erased
    if arcpy.Exists(merged_buffer_erase) == 1:  # Check to see if name already exists
        arcpy.Delete_management(merged_buffer_erase) # If so, delete that shapefile 
    arcpy.analysis.Erase(merge_buffer, coast, merged_buffer_erase, None)    # Erase shared line between land and beach buffer line shapefile
                                                                            # "None": The minimum distance separating all feature coordinates (nodes and vertices) as well as the distance a coordinate can move in X or Y (or both). 

    # Create new feature class for final cross sections 
    final_CS = "final_CS" + "_" + str(tag) # Create name for final cross sections 
    if arcpy.Exists(final_CS) == 1: # Check to see if name already exists
        arcpy.Delete_management(final_CS) # If so, delete that shapefile 
    arcpy.management.CreateFeatureclass(arcpy.env.workspace, final_CS, "POLYLINE")  # Creates feature class in a geodatabase 
                                                                                    # "arcpy.env.workspace": chose the workspace for the featureclass to be saved 
                                                                                    # "POLYLINE": geometry type

    # Extend lines to extents of the buffers 
    with arcpy.da.UpdateCursor(normals, "OBJECTID") as cursor: # Create cursor for OBJECTID because each OBJECTID is unique (no duplicates)
        for line in cursor: # search in cursor  
            
            object_id = line[0] # "OBJECTID" is the first item in the list

            # Make layer with that normal 
            single_CS = "single_CS" # create new name for single CS layer
            if arcpy.Exists(single_CS) == 1: # check to see if name already exists
                arcpy.Delete_management(single_CS) # if so, delete it (after the first iteration, it will delete the previous iteration layer)
            arcpy.management.MakeFeatureLayer(normals, single_CS, "OBJECTID = " + str(object_id)) # Create layer by using query selecting the normal with the objectid of interest
        
            # Merged corrected buffer with normals 
            merge_CS_buffer= "merge_CS_buffer" # create name for shapefile that is product of merging of normals and buffer polylines
            if arcpy.Exists(merge_CS_buffer) == 1: # check to see if file exists
                arcpy.Delete_management(merge_CS_buffer) # if so, delete that file
            arcpy.management.Merge(str(single_CS)+";"+str(merged_buffer_erase) , merge_CS_buffer) # Merge buffer polylines with normals 
        
            arcpy.edit.ExtendLine(merge_CS_buffer, "10000 Meters", "EXTENSION") #"10000 Meters": choose a distance that's well beyond how far it will take for the normals to hit the buffer polyline 
            
            with arcpy.da.UpdateCursor(merge_CS_buffer, "OBJECTID") as cursor: # Create cursor for OBJECTID because each OBJECTID is unique (no duplicates)
                for parts in cursor: # search through cursor 
                    object_id = parts[0] # "OBJECTID" is the first item in the list
                    
                    if object_id != 1: # check to see if OBJECTID is equal to 1
                        cursor.deleteRow() # if not, delete
        
            arcpy.management.Append(merge_CS_buffer, final_CS, "NO_TEST") # Append cross section to final cross section feature class 

    # Copy lines to "reset" object ids
    extended_normals = "extended_normals" + str(tag) # create new name for extended normals
    if arcpy.Exists(extended_normals) == 1: # see if file already exists
        arcpy.Delete_management(extended_normals) # if so, delete old file 
    arcpy.management.CopyFeatures(final_CS, extended_normals, '', None, None, None) #'': Geodatabase configuration keyword to be applied if the output is a geodatabase. (n/a)
                                                                                    #: None: This parameter has been deprecated in ArcGIS Pro. Any value you enter is ignored.        
                                                                                    #: None: This parameter has been deprecated in ArcGIS Pro. Any value you enter is ignored. 
                                                                                    #: None: This parameter has been deprecated in ArcGIS Pro. Any value you enter is ignored. 
    # Take out the trash 
    arcpy.management.Delete(beach_buffer)
    arcpy.management.Delete(beach_line)
    arcpy.management.Delete(land_buffer)
    arcpy.management.Delete(land_line)
    arcpy.management.Delete(merge_buffer)
    arcpy.management.Delete(merged_buffer_erase)    

#extend_cross_sections("normals", "coast_Clip", "Near_Brush_Creek") #This line of code will run the "extend_cross_sections" function, make sure all other lines of code running other functions are commented out

#This function "gets the good stuff" (aka the final cross sections for the physics based model)
def get_the_good_stuff(normals, DEM, tag): # normals from the "extend_cross_sections" function 

    with arcpy.da.SearchCursor(normals, "OBJECTID") as cursor: # Create cursor for OBJECTID because each OBJECTID is unique (no duplicates)
        
        for row in cursor: #search through cursor
            
            row_ID = row[0] # first item in the list is the OBJECTID
            cross_section = "cross_section" #name of the cross section layer
            if arcpy.Exists(cross_section) == 1: # check to see if file already exists
                arcpy.Delete_management(cross_section) #if so, delete the file 
            arcpy.management.MakeFeatureLayer(normals, cross_section, "OBJECTID = " + str(row_ID)) # make a layer (or individual shapefile) by querying for that OBJECTID number
            
            points = "points" # name of the points file
            if arcpy.Exists(points) == 1: # check to see if file already exists
                arcpy.Delete_management(points) # if so, delete old file
            arcpy.management.GeneratePointsAlongLines(cross_section, points, "DISTANCE", "1 Meters", None, "END_POINTS")    # "DISTANCE": The Distance parameter value will be used to place points at fixed distances along the features
                                                                                                                            # "1 Meters": The interval from the beginning of the feature at which points will be placed. This distance chosen because DEM is 0.91 m spacing. 
                                                                                                                            # "None": The percentage from the beginning of the feature at which points will be placed. For example, if a percentage of 40 is used, points will be placed at 40 percent and 80 percent of the feature's distance.
                                                                                                                            # "END_POINTS": Additional points will be included at the start point and end point of the feature.                      
            
            arcpy.management.AddXY(points) # Adds X and Y data based on the coordinate system of the inputs 

            arcpy.ddd.AddSurfaceInformation(points, DEM, "Z", "BILINEAR", None, 1, 0, '')   # AddSurfaceInformation tool adds elevation data to shapefiles (e.g. points)
                                                                                            # "Z": The surface z-values interpolated for the x,y-location of each single-point feature will be added.
                                                                                            # "BILINEAR": An interpolation method exclusive to the raster surface which determines cell values from the four nearest cells will be used. This is the only option available for a raster surface.
                                                                                            # "NONE": The spacing at which z-values will be interpolated. 
                                                                                            # "1": The factor by which z-values will be multiplied. This is typically used to convert z linear units to match x,y linear units.
                                                                                            # "0": The z-tolerance or window-size resolution of the terrain pyramid level that will be used. 0 is full resolution 
                                                                                            # '': Noise filtering, Specifies whether portions of the surface that are potentially characterized by anomalous measurements will be excluded from contributing to slope calculations.

            excel = str(tag) + "_CSV" + str(row_ID-1) # create name for final CSV of X,Y and Z data for each cross section 
            if arcpy.Exists(excel) == 1: # check to see if file already exists
                arcpy.Delete_management(excel) # if so, delete the old file 
            arcpy.conversion.TableToExcel(points, excel, "NAME", "CODE")    # "NAME": Column headers will be set using the input's field names. 
                                                                            # "CODE": All field values will be used as they are stored in the table. 

# get_the_good_stuff("extended_normals_Near_Brush_Creek", "Near_Brush_Creek_full_m", "Near_Brush_Creek") # This line of code runs the "get_the_good_stuff" function