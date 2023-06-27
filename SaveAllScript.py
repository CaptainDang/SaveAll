import os
import processing
from qgis.core import *
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QAction


# Function to sanitize layer name by replacing special characters with an underscore
def sanitize(layer_name):
    forbidden_chars = r'<>:"/\|?*'
    return ''.join(c if c not in forbidden_chars else '_' for c in layer_name)


project = QgsProject.instance()
layers = project.mapLayers().values()

# Check to make sure all layers have different names
unique_names = set()
non_unique_names = []

for layer in project.mapLayers().values():
    name = layer.name()
    if name in unique_names:
        # Layer name is not unique, so add it to the list
        non_unique_names.append(name)

    else:
        # Add the layer name to the set
        unique_names.add(name)

# Check if non-unique layer names were found
if len(non_unique_names) > 0:
    # Display a pop-up message with the non-unique layer names
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setWindowTitle("Layer Name Conflict")
    msg_box.setText("Two or more layers have the same name, which will lead to unintended effects. "
    "Please make sure that all layers have different names and try again.\n"
    "Non-unique layer names: {}".format(", ".join(non_unique_names)))
    msg_box.exec_()

# Check if all layer names are unique
if len(unique_names) == len(layers):
    # Open a dialog to select the folder
    selected_folder = QFileDialog.getExistingDirectory(None, "Select Folder", "")

    if selected_folder:
        # Ask the user to enter a folder name
        folder_name, ok = QInputDialog.getText(None, "Folder Name", "Enter the folder name:")

        if ok and folder_name:
            # Create the full path for the new folder
            new_folder_path = os.path.join(selected_folder, folder_name)

            # Check if the folder already exists, else create the new folder
            if os.path.exists(new_folder_path):
                pass
            else:
                os.makedirs(new_folder_path)

            # Save each layer in the project (raster as .tif and vector as .gpkg)
            for layer in project.mapLayers().values():
                layer_name = sanitize(layer.name())
                layer_file_path = os.path.join(new_folder_path, layer_name)

                if layer.type() == QgsMapLayerType.VectorLayer:
                    # Setting up the processing run
                    output_file = os.path.join(new_folder_path, layer_name + ".gpkg")
                    if not os.path.exists(output_file):
                        parameters = {
                            'LAYERS': [layer],
                            'OUTPUT': layer_file_path + ".gpkg",  # Specify the output file with .gpkg extension
                            'OVERWRITE': True,
                            'SAVE_STYLES': True,
                            'SAVE_METADATA': True,
                            'SELECTED_FEATURES_ONLY': False,
                            'EXPORT_RELATED_LAYERS': False}

                        feedback = QgsProcessingFeedback()

                        # Execute the package algorithm
                        try:
                            result = processing.run("native:package", parameters, feedback=feedback)
                            if result['OUTPUT']:
                                print("Layer '{}' saved successfully.".format(layer.name()))
                            else:
                                print("Failed to save layer '{}'.".format(layer.name()))
                        except QgsProcessingException as e:
                            print("An error occurred while packaging layer '{}': '{}'".format(layer.name(), str(e)))

                    # Sets the layer's data source to the newly created path, replaces temp layers with their permanent ones
                    layer.setDataSource(output_file, layer.name(), "ogr")

                elif layer.type() == QgsMapLayerType.RasterLayer:
                    output_file = os.path.join(new_folder_path, layer_name + ".tif")

                    # Remove the old version
                    if os.path.exists(layer_file_path):
                        os.remove(output_file)

                    file_writer = QgsRasterFileWriter(output_file)
                    pipe = QgsRasterPipe()
                    provider = layer.dataProvider()

                    if not pipe.set(provider.clone()):
                        print("Cannot set pipe provider")

                    file_writer.writeRaster(
                        pipe,
                        provider.xSize(),
                        provider.ySize(),
                        provider.extent(),
                        provider.crs()
                    )

            print("Vector, raster, and scratch layer save complete.")

            # Set the QGIS project file name and the project path and get the project instance
            project_file_name = folder_name + ".qgs"
            project_file_path = os.path.join(new_folder_path, project_file_name)

            # Save the project if already in folder, else save the QGIS project file into the folder for the first time
            if os.path.exists(project_file_path):
                iface.mainWindow().findChild(QAction, 'mActionSaveProject').trigger()
                print("QGIS project file saved successfully.")
            else:
                project.write(project_file_path)
                print("QGIS project file saved successfully for the first time.")

    else:
        print("No folder name entered. Please try again.")

else:
    print("Not all layer names are unique. Make sure all layers have different names and try again.")

