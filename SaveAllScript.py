import os
import os.path
import processing
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import QIcon
from qgis.gui import QgsMessageBar
from PyQt5.QtWidgets import *
from qgis.utils import *


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
    selected_folder = QFileDialog.getExistingDirectory(None, "Select parent folder (Project folder will be saved here):", "")

    if selected_folder:
        # Ask the user to enter a folder name
        folder_name, ok = QInputDialog.getText(None, "Folder Name", "Enter desired folder name. Use same name (case sensitive) to overwrite previous save:")

        if ok and folder_name:
            # Create the full path for the new folder
            new_folder_path = os.path.join(selected_folder, folder_name)

            # Check if the folder already exists, else create the new folder
            if os.path.exists(new_folder_path):
                pass
            else:
                os.makedirs(new_folder_path)

            # Save each layer in the project
            for layer in project.mapLayers().values():
                layer_name = sanitize(layer.name())
                layer_file_path = os.path.join(new_folder_path, layer_name)

                # Save vector layers
                if layer.type() == QgsMapLayerType.VectorLayer:
                    layerProvider = layer.dataProvider()
                    layerStorage = layerProvider.storageType()

                    # Save CSV layers as CSV files
                    if layerStorage == "CSV":
                        output_file = os.path.join(new_folder_path, layer_name + ".csv")

                        # CSV file does not exist in the folder, write it for the first time
                        if not os.path.exists(output_file):
                            error, error_string = QgsVectorFileWriter.writeAsVectorFormat(layer, output_file, "utf-8", layer.crs(), "CSV")
                            if error != QgsVectorFileWriter.NoError:
                                # Failure message
                                iface.messageBar().pushMessage("Failed: ", "Layer '{}' was not saved. Error: {}".format(layer.name(), error_string), level=2)
                        else:
                            # CSV file already exists in the folder, perform a normal save
                            layer.startEditing()
                            if layer.commitChanges():
                                pass
                            else:
                                # Failure message
                                iface.messageBar().pushMessage("Failed: ", "Layer '{}' was not saved. Error: Failed to save changes.".format(layer.name()), level=2)

                    # Save no geometry layers as CSV files
                    elif layer.wkbType() == 100:
                        output_file = os.path.join(new_folder_path, layer_name + ".csv")
                        error, error_string = QgsVectorFileWriter.writeAsVectorFormat(layer, output_file, "utf-8", layer.crs(), "CSV")
                        if error != QgsVectorFileWriter.NoError:
                            # Failure message
                            iface.messageBar().pushMessage("Failed: ", "Layer '{}' was not saved. Error: {}".format(layer.name(), error_string), level=2)

                    # Save KML or KMZ layers as KML files
                    elif layerStorage == "LIBKML":
                        output_file = os.path.join(new_folder_path, layer_name + ".kml")

                        # KML file does not exist in the folder, write it for the first time
                        if not os.path.exists(output_file):
                            error, error_string = QgsVectorFileWriter.writeAsVectorFormat(layer, output_file, "utf-8", layer.crs(), "LIBKML")
                            if error != QgsVectorFileWriter.NoError:
                                # Failure message
                                iface.messageBar().pushMessage("Failed: ", "Layer '{}' was not saved. Error: {}".format(layer.name(), error_string), level=2)
                        else:
                            # KML file already exists in the folder, perform a normal save
                            layer.startEditing()
                            if layer.commitChanges():
                                pass
                            else:
                                # Failure message
                                iface.messageBar().pushMessage("Failed: ", "Layer '{}' was not saved. Error: Failed to save changes.".format(layer.name()), level=2)

                    # Save SHP layers as SHP files
                    elif layerStorage == "ESRI Shapefile":
                        output_file = os.path.join(new_folder_path, layer_name + ".shp")

                        # SHP file does not exist in the folder, write it for the first time
                        if not os.path.exists(output_file):
                            error, error_string = QgsVectorFileWriter.writeAsVectorFormat(layer, output_file, "utf-8", layer.crs(), "ESRI Shapefile", onlySelected=False, symbologyExport=True)
                            if error != QgsVectorFileWriter.NoError:
                                # Failure message
                                iface.messageBar().pushMessage("Failed: ", "Layer '{}' was not saved. Error: {}".format(layer.name(), error_string), level=2)
                        else:
                            # SHP file already exists in the folder, perform a normal save
                            layer.startEditing()
                            if layer.commitChanges():
                                pass
                            else:
                                # Failure message
                                iface.messageBar().pushMessage("Failed: ", "Layer '{}' was not saved. Error: Failed to save changes.".format(layer.name()), level=2)

                    # Save all other vector layers as GPKG files
                    else:
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
                                    pass
                                else:
                                    iface.messageBar().pushMessage("Failed: ", "Layer '{}' was not saved.".format(layer.name()), level=2)
                            except QgsProcessingException as e:
                                iface.messageBar().pushMessage("Error: ", "An error occurred while packaging layer '{}': '{}'".format(layer.name(), str(e)), level=2)

                    # Sets the layer's data source to the newly created path, replaces temp layers with their permanent ones
                    layer.setDataSource(output_file, layer.name(), "ogr")

                # Save raster layers
                elif layer.type() == QgsMapLayerType.RasterLayer:
                    output_file = os.path.join(new_folder_path, layer_name + ".tif")

                    # Remove the old version
                    if os.path.exists(layer_file_path):
                        os.remove(output_file)

                    file_writer = QgsRasterFileWriter(output_file)
                    pipe = QgsRasterPipe()
                    provider = layer.dataProvider()

                    if not pipe.set(provider.clone()):
                        iface.messageBar().pushMessage("Failed: ", "Cannot set pipe provider for layer '{}'.".format(layer.name()), level=2)

                    file_writer.writeRaster(
                        pipe,
                        provider.xSize(),
                        provider.ySize(),
                        provider.extent(),
                        provider.crs()
                    )

            iface.messageBar().pushMessage("Success: ", "All layers saved.", level=3, duration=1)

            # Set the QGIS project file name and the project path and get the project instance
            project_file_name = folder_name + ".qgs"
            project_file_path = os.path.join(new_folder_path, project_file_name)

            # Save the project if already in folder, else save the QGIS project file into the folder for the first time
            if os.path.exists(project_file_path):
                iface.mainWindow().findChild(QAction, 'mActionSaveProject').trigger()
                iface.messageBar().pushMessage("Success: ", "QGIS project file saved successfully.", level=3)
            else:
                project.write(project_file_path)
                iface.messageBar().pushMessage("Success: ", "QGIS project file saved successfully for the first time.", level=3)

        else:
            iface.messageBar().pushMessage("No folder name entered. Please try again.", level=1)

    else:
        iface.messageBar().pushMessage("No folder selected. Please try again.", level=1)

else:
    iface.messageBar().pushMessage("Warning: ", "Not all layer names are unique. Make sure all layers have different names and try again.", level=1)
