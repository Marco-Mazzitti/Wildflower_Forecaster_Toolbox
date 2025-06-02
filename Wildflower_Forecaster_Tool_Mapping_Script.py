import arcpy
import os

# Add 'suitability' field as the average of 'obs_count' and 'species_ri'
def calculate_suitability(input_fc):
    print("🧮 Calculating suitability index...")
    if arcpy.Exists(input_fc):
        fields = [f.name for f in arcpy.ListFields(input_fc)]
        if "suitability" not in fields:
            arcpy.management.AddField(input_fc, "suitability", "DOUBLE")
        with arcpy.da.UpdateCursor(input_fc, ["obs_count", "species_ri", "suitability"]) as cursor:
            for row in cursor:
                obs = row[0] or 0
                rich = row[1] or 0
                row[2] = (obs + rich) / 2
                cursor.updateRow(row)
        print("✅ Suitability field added.")
    else:
        print("❌ Input feature class not found.")

# Generate a map layout using the specified field for symbology
def auto_map(input_fc, sym_field, output_folder, map_title=""):
    arcpy.env.overwriteOutput = True

    # Define friendly labels for layout and filenames
    field_labels = {
        "species_ri": "Species Richness",
        "obs_count": "Observation Count",
        "suitability": "Suitability Index",
        "NDVI_MEAN": "Mean NDVI",
        "DEM_MEAN": "Mean Elevation"
    }
    pretty_field_name = field_labels.get(sym_field, sym_field)

    # Set layout title text
    if not map_title or map_title.strip() == "":
        map_title = pretty_field_name

    # Open current ArcGIS Pro project and layout
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map_obj = aprx.listMaps()[0]
    layout = aprx.listLayouts()[0]

    # Remove old layer named 'Forecast' from map
    for lyr in map_obj.listLayers():
        if lyr.name == "Forecast":
            map_obj.removeLayer(lyr)

    # Add new data layer to the map
    print(f"➕ Adding input feature class: {input_fc}")
    new_layer = map_obj.addDataFromPath(input_fc)
    new_layer.name = "Forecast"

    # Apply graduated symbology using the target field
    sym = new_layer.symbology
    fields = [f.name for f in arcpy.ListFields(new_layer)]
    if sym_field not in fields:
        raise ValueError(f"❌ Field '{sym_field}' not found in layer. Available fields: {fields}")

    if hasattr(sym, "renderer") and sym.renderer.type != "GraduatedColorsRenderer":
        sym.updateRenderer("GraduatedColorsRenderer")

    sym.renderer.classificationField = sym_field
    sym.renderer.breakCount = 5
    sym.renderer.colorRamp = aprx.listColorRamps("Yellow to Red")[0]
    new_layer.symbology = sym
    print(f"🎨 Applied graduated symbology to '{sym_field}'")

    # Add the new layer to the layout legend
    legend_elements = [e for e in layout.listElements("LEGEND_ELEMENT") if "legend" in e.name.lower()]
    if legend_elements:
        legend = legend_elements[0]
        legend.autoAdd = True
        legend.addItem(new_layer)
        print("✅ New layer added to legend.")
    else:
        print("⚠️ No legend element found in layout.")

    # Update layout title using a text element named "Map Title"
    title_elements = [e for e in layout.listElements("TEXT_ELEMENT") if e.name.lower() == "map title"]
    if title_elements:
        title_element = title_elements[0]
        print(f"📝 Updating layout title text to: {pretty_field_name}")
        title_element.text = pretty_field_name
        aprx.save()  # Save to commit title update
    else:
        print("⚠️ No text element named 'Map Title' found.")

    # Build safe filenames for exported maps
    safe_label = pretty_field_name.replace(" ", "_")
    pdf_out = os.path.join(output_folder, f"{safe_label}_Forecast_Map.pdf")
    png_out = os.path.join(output_folder, f"{safe_label}_Forecast_Map.png")

    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Export layout to PDF and PNG
    try:
        layout.exportToPDF(pdf_out)
        layout.exportToPNG(png_out)
        print(f"\n✅ Map exported successfully:")
        print(f"📄 PDF: {pdf_out}")
        print(f"🖼 PNG: {png_out}")
    except Exception as e:
        print(f"❌ Export failed: {e}")

# Main execution block
if __name__ == "__main__":
    # Define input feature class and export folder
    input_fc = r"C:\Users\Marcu\OneDrive\Documents\ArcGIS\Projects\Wildflower_Forecaster_Toolbox\Wildflower_Forecaster_Toolbox.gdb\wildflower_grid_enriched_shapefile"
    output_folder = r"C:\Users\Marcu\OneDrive\Desktop\GEOG 181C\Wildflower_Forecaster_Toolbox\Script4\output"

    # Add suitability index before mapping
    calculate_suitability(input_fc)

    # Define which fields to map
    fields_to_map = ["species_ri", "obs_count", "suitability"]

    # Generate one map per field
    for field in fields_to_map:
        print(f"\n--- Generating map for: {field} ---")
        auto_map(
            input_fc=input_fc,
            sym_field=field,
            output_folder=output_folder,
            map_title=""
        )