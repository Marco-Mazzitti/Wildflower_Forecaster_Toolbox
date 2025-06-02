import arcpy
import os
from arcpy.sa import ZonalStatisticsAsTable, Raster

def integrate_env_covariates(grid_fc, raster_list, output_fc):
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("Spatial")

    #Step 1: Copying the grid to a working output (now a .gdb feature class)
    arcpy.management.CopyFeatures(grid_fc, output_fc)

    #Step 2: Determining zone field name
    fields = [f.name for f in arcpy.ListFields(output_fc)]
    zone_field = "OBJECTID" if "OBJECTID" in fields else "FID"
    print(f"Using zone field: {zone_field}")

    #Step 3: Looping through rasters and process each one
    for raster_path in raster_list:
        raster_name = os.path.basename(raster_path)
        print(f"\n Processing raster: {raster_name}")

        #Checking for NDVI and apply scaling if needed
        if "ndvi" in raster_name.lower():
            print("  → Rescaling NDVI values by dividing by 10000.0")
            raster_obj = Raster(raster_path)
            rescaled_raster = raster_obj / 10000.0
        else:
            rescaled_raster = Raster(raster_path)

        #Getting the base name for field naming
        base_name = arcpy.Describe(raster_path).baseName
        stats_table = os.path.join("in_memory", f"{base_name}_stats")
        
        #Running Zonal Statistics
        ZonalStatisticsAsTable(
            in_zone_data=output_fc,
            zone_field=zone_field,
            in_value_raster=rescaled_raster,
            out_table=stats_table,
            ignore_nodata="DATA",
            statistics_type="MEAN"
        )

        #Joining the mean field back and get actual field name used
        arcpy.management.JoinField(
            in_data=output_fc,
            in_field=zone_field,
            join_table=stats_table,
            join_field=zone_field,
            fields=["MEAN"]
        )

        #Determining actual field name (MEAN, MEAN_1, etc.)
        current_fields = [f.name for f in arcpy.ListFields(output_fc)]
        mean_fields = [f for f in current_fields if f.startswith("MEAN")]
        latest_mean_field = max(mean_fields, key=lambda x: (len(x), x))  #This gets the most recently added one

        #Adding and calculating renamed field
        new_field = f"{base_name}_MEAN"
        if new_field not in current_fields:
            arcpy.management.AddField(output_fc, new_field, "DOUBLE")
            arcpy.management.CalculateField(
                in_table=output_fc,
                field=new_field,
                expression=f"!{latest_mean_field}!",
                expression_type="PYTHON3"
        )
        try:
            arcpy.management.DeleteField(output_fc, latest_mean_field)
        except Exception as e:
            print(f"Warning: Could not delete temp field {latest_mean_field}: {e}")         
    print(f"\n Enriched grid exported to: {output_fc}")

if __name__ == "__main__":
    grid_fc = r"C:\Users\KHendri\Desktop\Geog181C\Final_Project\wildflower_grid.shp"

    raster_list = [
        r"C:\Users\KHendri\Desktop\Geog181C\Final_Project\NDVI.tif",
        r"C:\Users\KHendri\Desktop\Geog181C\Final_Project\DEM.tif"
    ]

    output_fc = r"C:\Users\KHendri\Desktop\Geog181C\Final_Project\wildflower_grid_enriched.shp"

    print("Running Environmental Covariate Integration Tool...")
    try:
        integrate_env_covariates(grid_fc, raster_list, output_fc)
    except Exception as e:
        print("Script failed with error:")
        print(e)
