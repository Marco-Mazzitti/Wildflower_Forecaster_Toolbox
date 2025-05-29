# TOOL 2: Spatial Gridding and Co-Occurance tool

import arcpy
import os

def main(input_occurrence, cell_size, output_grid_fc):
    arcpy.env.overwriteOutput = True

    # If input is CSV, convert to feature class
    if input_occurrence.lower().endswith(".csv"):
        xy_layer = "gbif_points"
        arcpy.management.MakeXYEventLayer(
            input_occurrence,  # table
            "lon",  # X field
            "lat",  # Y field
            xy_layer,  # output layer name
            arcpy.SpatialReference(4326)  # WGS84
        )
        input_fc = os.path.join("in_memory", "gbif_fc")
        arcpy.management.CopyFeatures(xy_layer, input_fc)
    else:
        input_fc = input_occurrence

    # Project to a coordinate system with meter-based units (CA Albers)
    projected_fc = os.path.join("in_memory", "gbif_projected")
    arcpy.management.Project(
        in_dataset=input_fc,
        out_dataset=projected_fc,
        out_coor_system=arcpy.SpatialReference(3310)  # NAD83 / California Albers
    )

    # Define extent and create fishnet grid using projected features
    extent = arcpy.Describe(projected_fc).extent
    origin = f"{extent.XMin} {extent.YMin}"
    y_axis = f"{extent.XMin} {extent.YMin + 10}"
    width = height = cell_size  # in meters

    temp_grid = os.path.join("in_memory", "grid")

    arcpy.management.CreateFishnet(
        out_feature_class=temp_grid,
        origin_coord=origin,
        y_axis_coord=y_axis,
        cell_width=width,
        cell_height=height,
        number_rows="0",
        number_columns="0",
        labels="NO_LABELS",
        template=projected_fc,
        geometry_type="POLYGON"
    )

    # Spatial join to count observations per cell
    join_output = os.path.join("in_memory", "joined")
    arcpy.analysis.SpatialJoin(
        target_features=temp_grid,
        join_features=projected_fc,
        out_feature_class=join_output,
        join_operation="JOIN_ONE_TO_MANY",
        join_type="KEEP_COMMON",
        match_option="INTERSECT"
    )
    fields = [f.name for f in arcpy.ListFields(join_output)]
    print("Fields in joined output:", fields)

    # Calculate total observations and species richness
    summary_table = os.path.join("in_memory", "summary")
    arcpy.analysis.Statistics(
        in_table=join_output,
        out_table=summary_table,
        statistics_fields=[["species", "COUNT"]],
        case_field="TARGET_FID"
    )

    species_table = os.path.join("in_memory", "species_summary")
    arcpy.analysis.Statistics(
        in_table=join_output,
        out_table=species_table,
        statistics_fields=[["species", "UNIQUE"]],
        case_field="TARGET_FID"
    )

    # Join stats back to grid
    arcpy.management.JoinField(
        in_data=temp_grid,
        in_field="OID",
        join_table=summary_table,
        join_field="TARGET_FID",
        fields=["COUNT_species"]
    )

    arcpy.management.JoinField(
        in_data=temp_grid,
        in_field="OID",
        join_table=species_table,
        join_field="TARGET_FID",
        fields=["UNIQUE_species"]
    )

    # Rename fields
    arcpy.management.AlterField(
        in_table=temp_grid,
        field="COUNT_species",
        new_field_name="obs_count",
        new_field_alias="Observation Count"
    )

    arcpy.management.AlterField(
        in_table=temp_grid,
        field="UNIQUE_species",
        new_field_name="species_richness",
        new_field_alias="Species Richness"
    )

    # Export to shapefile
    arcpy.management.CopyFeatures(temp_grid, output_grid_fc)

    if arcpy.Exists(output_grid_fc):
        print(f"Shapefile exported to: {output_grid_fc}")
    else:
        print("Export failed. Double-check path and locks.")

if __name__ == "__main__":
    input_occurrence = r"C:\Documents\Geog181C\FinalProj\gilia_capitata_occurrences.csv"
    cell_size = 10000  # 10km grid
    output_grid_fc = r"C:\Documents\Geog181C\FinalProj\wildflower_grid.shp"

    print("Running Wildflower Gridding Tool...")
    try:
        main(input_occurrence, cell_size, output_grid_fc)
    except Exception as e:
        print("Script failed with error:")
        print(e)
