"""
Location Picker Tool for QGIS
Allows users to click on the map to select a location.
"""

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QCursor, QPixmap
from qgis.core import QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from qgis.gui import QgsMapToolEmitPoint


class LocationPickerTool(QgsMapToolEmitPoint):
    """Map tool for picking locations by clicking on the map."""
    
    locationPicked = pyqtSignal(float, float)  # lon, lat in EPSG:4326
    
    def __init__(self, canvas):
        """Initialize the location picker tool.
        
        Args:
            canvas: QgsMapCanvas instance
        """
        super().__init__(canvas)
        self.canvas = canvas
        self.cursor = QCursor(Qt.CrossCursor)
        
    def canvasPressEvent(self, event):
        """Handle mouse press event on the map canvas.
        
        Args:
            event: QgsMapMouseEvent
        """
        # Get the clicked point in map coordinates
        point = self.toMapCoordinates(event.pos())
        
        # Transform to EPSG:4326 (WGS84) for geocoding
        transform = QgsCoordinateTransform(
            self.canvas.mapSettings().destinationCrs(),
            QgsCoordinateReferenceSystem('EPSG:4326'),
            QgsProject.instance()
        )
        
        try:
            point_4326 = transform.transform(point)
            # Emit signal with longitude, latitude
            self.locationPicked.emit(point_4326.x(), point_4326.y())
        except Exception as e:
            print(f"Error transforming coordinates: {e}")
    
    def activate(self):
        """Activate the tool."""
        super().activate()
        self.canvas.setCursor(self.cursor)
    
    def deactivate(self):
        """Deactivate the tool."""
        super().deactivate()
