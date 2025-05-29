import arcpy
import os
from arcpy.sa import ZonalStatisticsAsTable

def integrate_env_covariates(grid_fc, raster_list, output_fc):
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("Spatial")

    # Step 1: Copy the grid to a working output
    arcpy.management.CopyFeatures(grid_fc, output_fc)

    # Step 2: Determine zone field name (OBJECTID or FID)
    fields = [f.name for f in arcpy.ListFields(output_fc)]
    zone_field = "OBJECTID" if "OBJECTID" in fields else "FID"

    print(f"Using zone field: {zone_field}")

    # Step 3: Loop through each raster and process
    for raster in raster_list:
        print(f"Processing raster: {raster}")
        base_name = arcpy.Describe(raster).baseName
        stats_table = os.path.join("in_memory", f"{base_name}_stats")

        # Run Zonal Statistics as Table
        ZonalStatisticsAsTable(
            in_zone_data=output_fc,
            zone_field=zone_field,
            in_value_raster=raster,
            out_table=stats_table,
            ignore_nodata="DATA",
            statistics_type="MEAN"
        )

        # Join the table back to the feature class
        arcpy.management.JoinField(
            in_data=output_fc,
            in_field=zone_field,
            join_table=stats_table,
            join_field=zone_field,
            fields=["MEAN"]
        )

        # Note: We skip renaming the field for compatibility with shapefiles

    print(f"\n✅ Enriched grid exported to: {output_fc}")

# Example usage
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
