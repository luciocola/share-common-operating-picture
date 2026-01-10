"""
Share COP Dialog - Enhanced dialog with location naming, map navigation,
layer selection, and COP STAC package creation with signing.
"""

import os
import json
import hashlib
import zipfile
import urllib.request
import urllib.parse
import math
from datetime import datetime, timezone
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("ReportLab not available - PDF generation will be skipped")
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog, QMessageBox, QFileDialog, QListWidgetItem,
    QTextEdit, QVBoxLayout, QDialogButtonBox, QPushButton, QCheckBox
)
from qgis.core import (
    Qgis, QgsProject, QgsPointXY, QgsRectangle,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsDistanceArea,
    QgsVectorLayer, QgsRasterLayer, QgsFeature, QgsGeometry, QgsField, QgsMarkerSymbol,
    QgsSingleSymbolRenderer, QgsTextFormat, QgsTextBufferSettings,
    QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsFillSymbol,
    QgsWkbTypes
)
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor, QFont

from .location_picker import LocationPickerTool
from .stac_cop_exporter import STACCOPExporter
from .sealgeo_agent import SEALGeoAgent
from .ontology_parser import get_mission_concepts
from .chat_dialog import ChatDialog

# Load UI file
UI_FILE = os.path.join(os.path.dirname(__file__), 'ui', 'share_cop_dialog.ui')
FORM_CLASS, _ = uic.loadUiType(UI_FILE)


class ShareCOPDialog(QDialog, FORM_CLASS):
    """Dialog for creating and sharing Common Operating Picture packages."""
    
    def __init__(self, iface, parent=None):
        """Constructor.
        
        Args:
            iface: QGIS interface instance
            parent: Parent widget
        """
        super(ShareCOPDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.iface = iface
        self.canvas = iface.mapCanvas()
        
        # Set default zoom scale to 1:100,000 (Region level)
        self.cmbZoomLevel.setCurrentIndex(4)
        
        # Location picker tool
        self.location_tool = LocationPickerTool(self.canvas)
        self.location_tool.locationPicked.connect(self.on_location_picked)
        
        # Current location
        self.current_lon = None
        self.current_lat = None
        self.current_address = None
        self.current_zone_id = None
        self.current_aoi_bbox = None
        self.current_aoi_dggs_zones = None
        
        # SEAL Geo RAG agent and mission query results
        self.sealgeo_agent = SEALGeoAgent()
        self.mission_query_results = None
        self.mission_options = []
        
        # Ontology concept checkboxes
        self.ontology_checkboxes = []
        
        # Zoom scale mapping
        self.zoom_scales = {
            0: 1000,      # Building
            1: 5000,      # Block
            2: 10000,     # Neighborhood
            3: 50000,     # City
            4: 100000     # Region
        }
        
        # Connect signals
        self.btnPickLocation.clicked.connect(self.pick_location)
        self.btnGeocode.clicked.connect(self.geocode_location_name)
        self.btnZoom.clicked.connect(self.zoom_to_location)
        self.txtLongitude.textChanged.connect(self.on_coordinates_changed)
        self.txtLatitude.textChanged.connect(self.on_coordinates_changed)
        self.txtLocationName.textChanged.connect(self.on_location_name_changed)
        self.txtLocationName.returnPressed.connect(self.geocode_location_name)
        
        # DGGS conversion
        self.btnConvertDggs.clicked.connect(self.convert_to_dggs)
        self.btnSelectPolygonDggs.clicked.connect(self.select_polygon_for_dggs)
        self.btnCreateDggsGrid.clicked.connect(self.create_dggs_grid_from_extent)
        
        # Layer selection
        self.btnRefreshLayers.clicked.connect(self.populate_layers)
        self.btnSelectAll.clicked.connect(self.select_all_layers)
        self.btnSelectNone.clicked.connect(self.select_no_layers)
        self.lstLayers.itemSelectionChanged.connect(self.check_export_ready)
        
        # COP metadata
        self.txtMission.textChanged.connect(self.on_mission_changed)
        self.txtReleasability.textChanged.connect(self.check_export_ready)
        self.btnQueryChatbot.clicked.connect(self.query_chatbot_manual)
        self.grpOntologyConcepts.toggled.connect(self.on_ontology_group_toggled)
        
        # Export
        self.btnBrowse.clicked.connect(self.browse_output_dir)
        self.btnExport.clicked.connect(self.export_cop_package)
        
        # Initialize
        self.populate_layers()
        self.populate_ontology_concepts()
        self.check_export_ready()
        
        # Check and load OpenStreetMap basemap
        self.check_osm_basemap()
    
    def check_osm_basemap(self):
        """Check if OpenStreetMap basemap exists, prompt to load if not."""
        # Search for existing OpenStreetMap layer
        existing_osm = None
        for layer in QgsProject.instance().mapLayers().values():
            if 'OpenStreetMap' in layer.name() and isinstance(layer, QgsRasterLayer):
                existing_osm = layer
                break
        
        # If no OSM layer found, prompt user to load it
        if not existing_osm:
            reply = QMessageBox.question(
                self,
                'OpenStreetMap Basemap',
                'OpenStreetMap basemap is not loaded. Would you like to load it now?\n\n'
                'This provides a base map for geographic context.',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.load_osm_basemap()
    
    def load_osm_basemap(self):
        """Load OpenStreetMap XYZ tile layer as basemap."""
        try:
            # XYZ tile URL for OpenStreetMap
            osm_url = 'type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=0'
            osm_layer = QgsRasterLayer(osm_url, 'OpenStreetMap', 'wms')
            
            if osm_layer.isValid():
                # Add to project (at bottom of layer tree)
                QgsProject.instance().addMapLayer(osm_layer, False)
                root = QgsProject.instance().layerTreeRoot()
                root.insertLayer(len(root.children()), osm_layer)
                
                self.iface.messageBar().pushMessage(
                    'Success',
                    'OpenStreetMap basemap loaded successfully',
                    level=Qgis.Success,
                    duration=3
                )
            else:
                QMessageBox.warning(
                    self,
                    'OSM Load Error',
                    'Failed to load OpenStreetMap layer. Please check your internet connection.'
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                'OSM Load Error',
                f'Error loading OpenStreetMap: {str(e)}'
            )
    
    def populate_layers(self):
        """Populate layer list with project layers."""
        self.lstLayers.clear()
        project = QgsProject.instance()
        
        layer_count = 0
        for layer in project.mapLayers().values():
            item = QListWidgetItem(layer.name())
            item.setData(Qt.UserRole, layer.id())
            self.lstLayers.addItem(item)
            layer_count += 1
        
        # Show message about loaded layers
        if layer_count > 0:
            self.iface.messageBar().pushMessage(
                "Layers Loaded",
                f"Found {layer_count} layer(s) in the project",
                level=Qgis.Info,
                duration=2
            )
        else:
            self.iface.messageBar().pushMessage(
                "No Layers",
                "No layers found in the current project. Add layers to QGIS first.",
                level=Qgis.Warning,
                duration=3
            )
    
    def populate_ontology_concepts(self):
        """Populate checkboxes with Red River Flood ontology concepts."""
        try:
            # Get concepts from ontology
            concepts = get_mission_concepts()
            
            # Create a new widget for the scroll area
            from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QGridLayout
            
            scroll_widget = QWidget()
            layout = QGridLayout(scroll_widget)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(5)
            
            # Create checkboxes for each concept in 3 columns
            self.ontology_checkboxes = []
            num_columns = 3
            for i, concept in enumerate(concepts):
                checkbox = QCheckBox(concept)
                checkbox.stateChanged.connect(self.on_ontology_checkbox_changed)
                row = i // num_columns
                col = i % num_columns
                layout.addWidget(checkbox, row, col)
                self.ontology_checkboxes.append(checkbox)
            
            # Add stretch to push checkboxes to the top
            layout.setRowStretch(layout.rowCount(), 1)
            
            # Set the widget to the scroll area
            self.scrollAreaOntology.setWidget(scroll_widget)
            
        except Exception as e:
            print(f"Error populating ontology concepts: {e}")
            import traceback
            traceback.print_exc()
    
    def on_ontology_group_toggled(self, checked):
        """Handle ontology group box toggle."""
        if not checked:
            # Uncheck all ontology checkboxes when group is collapsed
            for checkbox in self.ontology_checkboxes:
                checkbox.setChecked(False)
    
    def on_ontology_checkbox_changed(self):
        """Handle ontology checkbox state changes."""
        # Collect all checked concepts
        checked_concepts = []
        for checkbox in self.ontology_checkboxes:
            if checkbox.isChecked():
                checked_concepts.append(checkbox.text())
        
        # Update mission text field
        if checked_concepts:
            mission_text = ", ".join(checked_concepts)
            self.txtMission.setText(mission_text)
        else:
            # Only clear if all ontology checkboxes are unchecked
            if self.grpOntologyConcepts.isChecked():
                self.txtMission.clear()
    
    def select_all_layers(self):
        """Select all layers in the list."""
        for i in range(self.lstLayers.count()):
            self.lstLayers.item(i).setSelected(True)
    
    def select_no_layers(self):
        """Deselect all layers."""
        self.lstLayers.clearSelection()
    
    def pick_location(self):
        """Activate the location picker tool."""
        self.canvas.setMapTool(self.location_tool)
        self.iface.messageBar().pushMessage(
            "Info",
            "Click on the map to select a location",
            level=Qgis.Info,
            duration=3
        )
    
    def on_location_picked(self, lon, lat):
        """Handle location picked from map.
        
        Args:
            lon: Longitude in EPSG:4326
            lat: Latitude in EPSG:4326
        """
        self.current_lon = lon
        self.current_lat = lat
        
        # Update UI
        self.txtLongitude.setText(f"{lon:.6f}")
        self.txtLatitude.setText(f"{lat:.6f}")
        
        # Enable zoom button
        self.btnZoom.setEnabled(True)
        self.btnConvertDggs.setEnabled(True)
        
        # Deactivate tool
        self.canvas.unsetMapTool(self.location_tool)
        
        # Auto-geocode
        self.reverse_geocode()
        
        # Show message
        self.iface.messageBar().pushMessage(
            "Success",
            f"Location selected: {lat:.6f}, {lon:.6f}",
            level=Qgis.Success,
            duration=3
        )
        
        self.check_export_ready()
    
    def on_location_name_changed(self):
        """Handle location name changes."""
        self.check_export_ready()
    
    def on_mission_changed(self):
        """Handle mission text changes."""
        # Just check if export is ready, don't auto-query
        self.check_export_ready()
    
    def query_chatbot_manual(self):
        """Open interactive chat window with SEAL Geo RAG Chatbot."""
        mission_text = self.txtMission.text().strip()
        
        # Open chat dialog with optional initial mission
        chat_dialog = ChatDialog(self.sealgeo_agent, initial_mission=mission_text, parent=self)
        result = chat_dialog.exec_()
        
        if result == QDialog.Accepted:
            # Get conversation history
            conversation = chat_dialog.get_conversation_history()
            
            if conversation:
                # Store conversation for export
                self.mission_query_results = {
                    'conversation': conversation,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                
                # Show success message
                msg_count = len([e for e in conversation if e['role'] in ['user', 'assistant']])
                self.iface.messageBar().pushMessage(
                    "Success",
                    f"Chat session completed with {msg_count} messages. Conversation will be included in COP export.",
                    level=Qgis.Success,
                    duration=5
                )
    
    def _format_chatbot_results(self, options):
        """Format RAG chatbot results for display.
        
        Args:
            options: List of option dictionaries
            
        Returns:
            Formatted string for display
        """
        lines = []
        lines.append("=" * 60)
        lines.append("SEAL GEO RAG CHATBOT RESULTS")
        lines.append("=" * 60)
        lines.append("")
        
        for idx, option in enumerate(options[:10], 1):  # Show top 10
            opt_type = option.get('type', 'unknown')
            title = option.get('title', 'No title')
            source = option.get('source', 'unknown')
            
            lines.append(f"{idx}. {title}")
            lines.append(f"   Type: {opt_type} | Source: {source}")
            lines.append(f"   {'-' * 55}")
            
            # Show full content for chatbot responses
            if option.get('content'):
                content = option['content']
                if opt_type == 'chatbot_response':
                    # Show full chatbot response
                    lines.append(f"   Response:")
                    for line in content.split('\n'):
                        lines.append(f"   {line}")
                else:
                    # Show first 200 chars for other types
                    if len(content) > 200:
                        lines.append(f"   {content[:200]}...")
                    else:
                        lines.append(f"   {content}")
            
            if option.get('description'):
                desc = option['description']
                if len(desc) > 200:
                    lines.append(f"   Description: {desc[:200]}...")
                else:
                    lines.append(f"   Description: {desc}")
            
            if option.get('mission'):
                lines.append(f"   Related Mission: {option['mission']}")
            
            if option.get('url'):
                lines.append(f"   URL: {option['url']}")
            
            if option.get('classification'):
                lines.append(f"   Classification: {option['classification']}")
            
            lines.append("")  # Blank line between results
        
        lines.append("=" * 60)
        lines.append(f"Total options: {len(options)}")
        lines.append("These options will be included in the exported COP package.")
        lines.append("=" * 60)
        
        return "\n".join(lines)
        return "\n".join(lines)
    
    def _show_results_dialog(self, title, text):
        """Show results in a scrollable dialog.
        
        Args:
            title: Dialog title
            text: Text content to display
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(700, 500)
        
        layout = QVBoxLayout()
        
        # Create text edit with monospace font
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(text)
        text_edit.setStyleSheet("font-family: monospace; font-size: 11pt;")
        layout.addWidget(text_edit)
        
        # Add buttons
        button_box = QDialogButtonBox()
        
        # Copy to clipboard button
        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(lambda: self._copy_to_clipboard(text))
        button_box.addButton(copy_button, QDialogButtonBox.ActionRole)
        
        # Close button
        close_button = button_box.addButton(QDialogButtonBox.Close)
        close_button.clicked.connect(dialog.accept)
        
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def _copy_to_clipboard(self, text):
        """Copy text to clipboard.
        
        Args:
            text: Text to copy
        """
        from qgis.PyQt.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        
        self.iface.messageBar().pushMessage(
            "Success",
            "Results copied to clipboard",
            level=Qgis.Success,
            duration=2
        )
    
    def generate_chatbot_pdf(self, assets_dir, mission, options):
        """Generate PDF report for chatbot results.
        
        Args:
            assets_dir: Directory to save the PDF
            mission: Mission text
            options: List of chatbot option dictionaries
            
        Returns:
            Path to generated PDF or None if failed
        """
        if not REPORTLAB_AVAILABLE:
            self.iface.messageBar().pushMessage(
                "Warning",
                "ReportLab not installed - cannot generate PDF. Install with: pip install reportlab",
                level=Qgis.Warning,
                duration=5
            )
            return None
        
        try:
            # Create PDF filename
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            pdf_filename = f"chatbot_mission_analysis_{timestamp}.pdf"
            pdf_path = os.path.join(assets_dir, pdf_filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                   rightMargin=0.75*inch, leftMargin=0.75*inch,
                                   topMargin=1*inch, bottomMargin=0.75*inch)
            
            # Container for PDF elements
            story = []
            
            # Define styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor='#003366',
                spaceAfter=30,
                alignment=TA_CENTER
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor='#003366',
                spaceAfter=12,
                spaceBefore=12
            )
            body_style = styles['BodyText']
            body_style.fontSize = 10
            body_style.leading = 14
            
            # Title
            story.append(Paragraph("SEAL Geo RAG Chatbot", title_style))
            story.append(Paragraph("Mission Analysis Report", title_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Mission Information
            story.append(Paragraph("Mission Query", heading_style))
            story.append(Paragraph(f"<b>Mission:</b> {mission}", body_style))
            story.append(Paragraph(f"<b>Generated:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", body_style))
            story.append(Paragraph(f"<b>Results Found:</b> {len(options)}", body_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Separator line
            story.append(Paragraph("<br/>" + "="*80 + "<br/>", body_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Results
            story.append(Paragraph("Analysis Results", heading_style))
            story.append(Spacer(1, 0.1*inch))
            
            for idx, option in enumerate(options, 1):
                opt_type = option.get('type', 'unknown')
                title = option.get('title', 'No title')
                source = option.get('source', 'unknown')
                
                # Result header
                story.append(Paragraph(f"<b>{idx}. {title}</b>", heading_style))
                story.append(Paragraph(f"<i>Type: {opt_type} | Source: {source}</i>", body_style))
                story.append(Spacer(1, 0.05*inch))
                
                # Content
                if option.get('content'):
                    content = option['content'].replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(f"<b>Response:</b>", body_style))
                    story.append(Paragraph(content, body_style))
                    story.append(Spacer(1, 0.1*inch))
                
                # Description
                if option.get('description'):
                    desc = option['description'].replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(f"<b>Description:</b> {desc}", body_style))
                    story.append(Spacer(1, 0.1*inch))
                
                # Related mission
                if option.get('mission'):
                    story.append(Paragraph(f"<b>Related Mission:</b> {option['mission']}", body_style))
                    story.append(Spacer(1, 0.1*inch))
                
                # URL
                if option.get('url'):
                    story.append(Paragraph(f"<b>URL:</b> <a href='{option['url']}'>{option['url']}</a>", body_style))
                    story.append(Spacer(1, 0.1*inch))
                
                # Classification
                if option.get('classification'):
                    story.append(Paragraph(f"<b>Classification:</b> {option['classification']}", body_style))
                    story.append(Spacer(1, 0.1*inch))
                
                # Separator between results
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph("-"*80, body_style))
                story.append(Spacer(1, 0.2*inch))
            
            # Footer
            story.append(PageBreak())
            story.append(Spacer(1, 0.5*inch))
            story.append(Paragraph("Report Information", heading_style))
            story.append(Paragraph(
                "This report was automatically generated by the QGIS Share Common Operating Picture plugin using the SEAL Geo RAG Chatbot service.",
                body_style
            ))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(
                f"<b>Service URL:</b> <a href='https://sealgeo.webgis1.com/demo/'>https://sealgeo.webgis1.com/demo/</a>",
                body_style
            ))
            story.append(Paragraph(
                f"<b>Plugin:</b> Share Common Operating Picture v1.0.0",
                body_style
            ))
            
            # Build PDF
            doc.build(story)
            
            self.iface.messageBar().pushMessage(
                "Success",
                f"Generated chatbot PDF report: {pdf_filename}",
                level=Qgis.Success,
                duration=3
            )
            
            return pdf_path
            
        except Exception as e:
            self.iface.messageBar().pushMessage(
                "Warning",
                f"Failed to generate PDF: {str(e)}",
                level=Qgis.Warning,
                duration=5
            )
            import traceback
            traceback.print_exc()
            return None
    
    def generate_conversation_pdf(self, assets_dir, mission, conversation):
        """Generate PDF report for chat conversation.
        
        Args:
            assets_dir: Directory to save the PDF
            mission: Mission text
            conversation: List of conversation entries (user/assistant messages)
            
        Returns:
            Path to generated PDF or None if failed
        """
        if not REPORTLAB_AVAILABLE:
            self.iface.messageBar().pushMessage(
                "Warning",
                "ReportLab not installed - cannot generate PDF. Install with: pip install reportlab",
                level=Qgis.Warning,
                duration=5
            )
            return None
        
        try:
            # Create PDF filename
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            pdf_filename = f"chatbot_conversation_{timestamp}.pdf"
            pdf_path = os.path.join(assets_dir, pdf_filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                   rightMargin=0.75*inch, leftMargin=0.75*inch,
                                   topMargin=1*inch, bottomMargin=0.75*inch)
            
            # Container for PDF elements
            story = []
            
            # Define styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor='#003366',
                spaceAfter=30,
                alignment=TA_CENTER
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor='#003366',
                spaceAfter=12,
                spaceBefore=12
            )
            user_style = ParagraphStyle(
                'UserMessage',
                parent=styles['BodyText'],
                fontSize=10,
                leading=14,
                textColor='#1976D2',
                leftIndent=20,
                spaceBefore=6,
                spaceAfter=6
            )
            bot_style = ParagraphStyle(
                'BotMessage',
                parent=styles['BodyText'],
                fontSize=10,
                leading=14,
                textColor='#558B2F',
                leftIndent=20,
                spaceBefore=6,
                spaceAfter=6
            )
            error_style = ParagraphStyle(
                'ErrorMessage',
                parent=styles['BodyText'],
                fontSize=10,
                leading=14,
                textColor='#C62828',
                leftIndent=20,
                spaceBefore=6,
                spaceAfter=6
            )
            body_style = styles['BodyText']
            body_style.fontSize = 10
            body_style.leading = 14
            
            # Title
            story.append(Paragraph("SEAL Geo RAG Chatbot", title_style))
            story.append(Paragraph("Interactive Conversation Transcript", title_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Session Information
            story.append(Paragraph("Session Information", heading_style))
            story.append(Paragraph(f"<b>Initial Mission:</b> {mission if mission else 'N/A'}", body_style))
            story.append(Paragraph(f"<b>Generated:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", body_style))
            
            # Count messages
            user_msgs = len([e for e in conversation if e['role'] == 'user'])
            bot_msgs = len([e for e in conversation if e['role'] == 'assistant'])
            story.append(Paragraph(f"<b>Messages:</b> {user_msgs} from user, {bot_msgs} from chatbot", body_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Separator line
            story.append(Paragraph("="*80, body_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Conversation
            story.append(Paragraph("Conversation", heading_style))
            story.append(Spacer(1, 0.1*inch))
            
            for entry in conversation:
                timestamp_dt = datetime.fromisoformat(entry['timestamp'])
                timestamp_str = timestamp_dt.strftime('%H:%M:%S')
                role = entry['role']
                content = entry['content'].replace('<', '&lt;').replace('>', '&gt;')
                
                if role == 'user':
                    story.append(Paragraph(f"<b>[{timestamp_str}] YOU:</b>", user_style))
                    story.append(Paragraph(content, user_style))
                    story.append(Spacer(1, 0.1*inch))
                
                elif role == 'assistant':
                    story.append(Paragraph(f"<b>[{timestamp_str}] 🤖 SEAL GEO RAG:</b>", bot_style))
                    story.append(Paragraph(content, bot_style))
                    story.append(Spacer(1, 0.1*inch))
                
                elif role == 'error':
                    story.append(Paragraph(f"<b>[{timestamp_str}] ❌ ERROR:</b>", error_style))
                    story.append(Paragraph(content, error_style))
                    story.append(Spacer(1, 0.1*inch))
                
                # Separator between messages
                story.append(Paragraph("-"*60, body_style))
                story.append(Spacer(1, 0.15*inch))
            
            # Footer
            story.append(PageBreak())
            story.append(Spacer(1, 0.5*inch))
            story.append(Paragraph("Report Information", heading_style))
            story.append(Paragraph(
                "This conversation transcript was automatically generated by the QGIS Share Common Operating Picture plugin using the SEAL Geo RAG Chatbot service.",
                body_style
            ))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(
                f"<b>Service URL:</b> <a href='https://sealgeo.servequake.com/api'>https://sealgeo.servequake.com/api</a>",
                body_style
            ))
            story.append(Paragraph(
                f"<b>Plugin:</b> Share Common Operating Picture v1.0.0",
                body_style
            ))
            
            # Build PDF
            doc.build(story)
            
            self.iface.messageBar().pushMessage(
                "Success",
                f"Generated conversation PDF: {pdf_filename}",
                level=Qgis.Success,
                duration=3
            )
            
            return pdf_path
            
        except Exception as e:
            self.iface.messageBar().pushMessage(
                "Warning",
                f"Failed to generate conversation PDF: {str(e)}",
                level=Qgis.Warning,
                duration=5
            )
            import traceback
            traceback.print_exc()
            return None
    
    def on_coordinates_changed(self):
        """Handle manual coordinate entry."""
        try:
            lon_text = self.txtLongitude.text().strip()
            lat_text = self.txtLatitude.text().strip()
            
            if lon_text and lat_text:
                lon = float(lon_text)
                lat = float(lat_text)
                self.current_lon = lon
                self.current_lat = lat
                self.btnZoom.setEnabled(True)
                self.btnConvertDggs.setEnabled(True)
                
                # Auto-reverse geocode if we don't have an address
                if not self.current_address:
                    self.reverse_geocode()
            else:
                self.btnZoom.setEnabled(False)
                self.btnConvertDggs.setEnabled(False)
                if not lon_text and not lat_text:
                    self.current_lon = None
                    self.current_lat = None
        except ValueError:
            self.btnZoom.setEnabled(False)
            self.btnConvertDggs.setEnabled(False)
            self.current_lon = None
            self.current_lat = None
        
        self.check_export_ready()
    
    def geocode_location_name(self):
        """Geocode location by name (forward geocoding)."""
        location_name = self.txtLocationName.text().strip()
        
        if not location_name:
            return
        
        try:
            # Nominatim forward geocoding API
            params = urllib.parse.urlencode({
                'q': location_name,
                'format': 'json',
                'limit': 1
            })
            url = f"https://nominatim.openstreetmap.org/search?{params}"
            
            # Set user agent (required by Nominatim)
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'QGIS ShareCOP Plugin/1.0'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
                if data and len(data) > 0:
                    result = data[0]
                    lat = float(result['lat'])
                    lon = float(result['lon'])
                    
                    # Update coordinates
                    self.current_lon = lon
                    self.current_lat = lat
                    self.txtLongitude.setText(f"{lon:.6f}")
                    self.txtLatitude.setText(f"{lat:.6f}")
                    
                    # Update address
                    self.current_address = result.get('display_name', '')
                    self.lblAddress.setText(f"Address: {self.current_address}")
                    
                    # Enable zoom and check export ready
                    self.btnZoom.setEnabled(True)
                    self.btnConvertDggs.setEnabled(True)
                    self.check_export_ready()
                    
                    # Auto-zoom to location
                    self.zoom_to_location()
                    
                    self.iface.messageBar().pushMessage(
                        "Success",
                        f"Found: {self.current_address[:80]}",
                        level=Qgis.Success,
                        duration=4
                    )
                else:
                    QMessageBox.warning(
                        self, 
                        "Not Found", 
                        f"Could not find location: '{location_name}'\n\nTry:\n"
                        "- City name (e.g., 'Berlin')\n"
                        "- Full address\n"
                        "- Landmark name\n"
                        "- Coordinates"
                    )
        
        except Exception as e:
            QMessageBox.warning(
                self, 
                "Error", 
                f"Geocoding failed: {str(e)}\n\nCheck your internet connection."
            )
        self.check_export_ready()
    
    def convert_to_dggs(self):
        """Convert location to DGGS zone ID using dggal."""
        if self.current_lon is None or self.current_lat is None:
            QMessageBox.warning(self, "Error", "No location selected")
            return
        
        try:
            # Import dggal
            try:
                import dggal
            except ImportError:
                QMessageBox.critical(
                    self,
                    "Error",
                    "dggal library not found. Please install it:\n\n"
                    "In QGIS Python Console:\n"
                    "import subprocess, sys\n"
                    "subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'dggal'])\n\n"
                    "Then restart QGIS."
                )
                return
            
            # Get DGGS parameters
            dggs_type = self.cmbDggsCrs.currentText()
            resolution = self.spinResolution.value()
            
            # Create DGGS grid based on type using GNOSISGlobalGrid
            try:
                if dggs_type == "H3":
                    # H3 uses a different approach - create a simple zone ID
                    zone_id = f"H3-R{resolution}-{self.current_lat:.4f}_{self.current_lon:.4f}"
                    self.current_zone_id = zone_id
                    self.lblZoneId.setText(f"Zone ID: {zone_id}")
                    self.iface.messageBar().pushMessage(
                        "Success",
                        f"Generated {dggs_type} zone ID",
                        level=Qgis.Success,
                        duration=3
                    )
                    # Create layer and continue
                    self.create_dggs_layer(dggs_type, resolution, zone_id)
                    return
                elif dggs_type == "S2":
                    # S2 uses a different approach - create a simple zone ID
                    zone_id = f"S2-R{resolution}-{self.current_lat:.4f}_{self.current_lon:.4f}"
                    self.current_zone_id = zone_id
                    self.lblZoneId.setText(f"Zone ID: {zone_id}")
                    self.iface.messageBar().pushMessage(
                        "Success",
                        f"Generated {dggs_type} zone ID",
                        level=Qgis.Success,
                        duration=3
                    )
                    # Create layer and continue
                    self.create_dggs_layer(dggs_type, resolution, zone_id)
                    return
                elif dggs_type == "rHEALPix":
                    projection = dggal.rHEALPix()
                    grid = dggal.GNOSISGlobalGrid(projection, resolution)
                    # For rHEALPix, create simplified zone ID
                    zone_id = f"{dggs_type}-R{resolution}-{self.current_lat:.4f}_{self.current_lon:.4f}"
                    self.current_zone_id = zone_id
                    self.lblZoneId.setText(f"Zone ID: {zone_id}")
                    self.iface.messageBar().pushMessage(
                        "Info",
                        f"Generated {dggs_type} zone ID (simplified format)",
                        level=Qgis.Info,
                        duration=3
                    )
                elif dggs_type == "ISEA3H":
                    projection = dggal.ISEA3H()
                    grid = dggal.GNOSISGlobalGrid(projection, resolution)
                    # For ISEA3H, create simplified zone ID
                    zone_id = f"{dggs_type}-R{resolution}-{self.current_lat:.4f}_{self.current_lon:.4f}"
                    self.current_zone_id = zone_id
                    self.lblZoneId.setText(f"Zone ID: {zone_id}")
                    self.iface.messageBar().pushMessage(
                        "Info",
                        f"Generated {dggs_type} zone ID (simplified format)",
                        level=Qgis.Info,
                        duration=3
                    )
                else:
                    QMessageBox.warning(self, "Error", f"Unsupported DGGS type: {dggs_type}")
                    return
                
            except Exception as e:
                # Fallback: generate a descriptive zone ID
                zone_id = f"{dggs_type}-R{resolution}-{self.current_lat:.4f}_{self.current_lon:.4f}"
                self.current_zone_id = zone_id
                self.lblZoneId.setText(f"Zone ID: {zone_id}")
                
                self.iface.messageBar().pushMessage(
                    "Warning",
                    f"Using simplified zone ID format (dggal API error: {str(e)[:50]})",
                    level=Qgis.Warning,
                    duration=5
                )
            
            # Create DGGS layer with the zone ID
            self.create_dggs_layer(dggs_type, resolution, zone_id)
        
        except Exception as e:
            self.lblZoneId.setText("Zone ID: (conversion failed)")
            QMessageBox.critical(self, "Error", f"DGGS conversion failed: {str(e)}")
    
    def select_polygon_for_dggs(self):
        """Allow user to select a polygon from existing layers and convert to DGGS zones."""
        # Get all polygon layers
        polygon_layers = []
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                if layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                    polygon_layers.append(layer)
        
        if not polygon_layers:
            QMessageBox.warning(
                self,
                "No Polygon Layers",
                "No polygon layers found in the project. Please add a polygon layer first."
            )
            return
        
        # Show layer selection dialog
        from qgis.PyQt.QtWidgets import QInputDialog
        layer_names = [layer.name() for layer in polygon_layers]
        layer_name, ok = QInputDialog.getItem(
            self,
            "Select Polygon Layer",
            "Choose a layer to convert to DGGS zones:",
            layer_names,
            0,
            False
        )
        
        if not ok:
            return
        
        # Find the selected layer
        selected_layer = None
        for layer in polygon_layers:
            if layer.name() == layer_name:
                selected_layer = layer
                break
        
        if not selected_layer:
            return
        
        # Get selected features or all features
        selected_features = selected_layer.selectedFeatures()
        if not selected_features:
            reply = QMessageBox.question(
                self,
                "No Selection",
                "No features are selected. Convert all features to DGGS zones?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                selected_features = list(selected_layer.getFeatures())
            else:
                return
        
        # Get DGGS parameters
        dggs_type = self.cmbDggsCrs.currentText()
        resolution = self.spinResolution.value()
        
        # Convert polygons to DGGS zones
        self.create_dggs_zones_from_polygons(selected_features, dggs_type, resolution)
    
    def create_dggs_grid_from_extent(self):
        """Create a DGGS grid covering the current map extent."""
        # Try to use AOI first if available
        if self.current_aoi_bbox:
            west, south, east, north = self.current_aoi_bbox
            extent_4326 = QgsRectangle(west, south, east, north)
        else:
            # Fall back to map extent
            extent = self.canvas.extent()
            if extent.isEmpty() or not extent.isFinite():
                QMessageBox.warning(
                    self,
                    "No Extent",
                    "Please zoom to an area or select a location to create DGGS grid."
                )
                return
            
            crs = self.canvas.mapSettings().destinationCrs()
            
            # Transform to EPSG:4326
            transform = QgsCoordinateTransform(
                crs,
                QgsCoordinateReferenceSystem('EPSG:4326'),
                QgsProject.instance()
            )
            extent_4326 = transform.transformBoundingBox(extent)
        
        # Get DGGS parameters
        dggs_type = self.cmbDggsCrs.currentText()
        resolution = self.spinResolution.value()
        
        # Create DGGS grid
        self.create_dggs_grid_layer(extent_4326, dggs_type, resolution)
    
    def create_dggs_zones_from_polygons(self, features, dggs_type, resolution):
        """Convert polygon features to DGGS zones.
        
        Args:
            features: List of QgsFeature with polygon geometry
            dggs_type: DGGS coordinate reference system type
            resolution: DGGS resolution level
        """
        try:
            print(f"[DGGS Polygons] Converting {len(features)} polygon(s) to DGGS zones")
            
            # Remove existing DGGS layer
            existing_layers = QgsProject.instance().mapLayersByName("DGGS Zones")
            for existing_layer in existing_layers:
                QgsProject.instance().removeMapLayer(existing_layer.id())
            
            # Create new polygon layer for DGGS zones
            layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "DGGS Zones", "memory")
            
            if not layer.isValid():
                raise Exception("Failed to create valid memory layer")
            
            provider = layer.dataProvider()
            layer.startEditing()
            
            # Add fields
            provider.addAttributes([
                QgsField("zone_id", QVariant.String),
                QgsField("dggs_type", QVariant.String),
                QgsField("resolution", QVariant.Int),
                QgsField("center_lat", QVariant.Double),
                QgsField("center_lon", QVariant.Double),
                QgsField("area_km2", QVariant.Double)
            ])
            layer.updateFields()
            
            dggs_features = []
            zone_count = 0
            
            for feature in features:
                geom = feature.geometry()
                if not geom or geom.isNull():
                    continue
                
                # Get centroid
                centroid = geom.centroid().asPoint()
                
                # Calculate zone ID for centroid
                zone_id = self.calculate_dggs_zone(
                    centroid.y(), centroid.x(), dggs_type, resolution
                )
                
                # Create approximate grid cell polygon around centroid
                # For simplicity, use a small box (this would ideally be the actual DGGS cell)
                cell_size = 0.01 * (15 - resolution)  # Smaller cells at higher resolution
                
                cell_polygon = QgsGeometry.fromPolygonXY([[
                    QgsPointXY(centroid.x() - cell_size, centroid.y() - cell_size),
                    QgsPointXY(centroid.x() + cell_size, centroid.y() - cell_size),
                    QgsPointXY(centroid.x() + cell_size, centroid.y() + cell_size),
                    QgsPointXY(centroid.x() - cell_size, centroid.y() + cell_size),
                    QgsPointXY(centroid.x() - cell_size, centroid.y() - cell_size)
                ]])
                
                # Calculate area in km²
                dist_calc = QgsDistanceArea()
                dist_calc.setEllipsoid('WGS84')
                area_m2 = dist_calc.measureArea(geom)
                area_km2 = area_m2 / 1000000.0
                
                dggs_feature = QgsFeature(layer.fields())
                dggs_feature.setGeometry(cell_polygon)
                dggs_feature.setAttributes([
                    zone_id,
                    dggs_type,
                    resolution,
                    centroid.y(),
                    centroid.x(),
                    round(area_km2, 2)
                ])
                dggs_features.append(dggs_feature)
                zone_count += 1
            
            # Add features
            provider.addFeatures(dggs_features)
            layer.commitChanges()
            layer.updateExtents()
            
            print(f"[DGGS Polygons] Created {zone_count} DGGS zone polygons")
            
            # Style the layer
            symbol = QgsFillSymbol.createSimple({
                'color': '255,107,107,100',  # Semi-transparent red
                'outline_color': '#C92A2A',
                'outline_width': '0.5'
            })
            renderer = QgsSingleSymbolRenderer(symbol)
            layer.setRenderer(renderer)
            
            # Add labels
            text_format = QgsTextFormat()
            text_format.setFont(QFont("Arial", 9, QFont.Bold))
            text_format.setSize(9)
            text_format.setColor(QColor(0, 0, 0))
            
            buffer_settings = QgsTextBufferSettings()
            buffer_settings.setEnabled(True)
            buffer_settings.setSize(1)
            buffer_settings.setColor(QColor(255, 255, 255))
            text_format.setBuffer(buffer_settings)
            
            label_settings = QgsPalLayerSettings()
            label_settings.setFormat(text_format)
            label_settings.fieldName = "zone_id"
            label_settings.enabled = True
            label_settings.dist = 2
            
            labeling = QgsVectorLayerSimpleLabeling(label_settings)
            layer.setLabeling(labeling)
            layer.setLabelsEnabled(True)
            
            # Add layer to project
            QgsProject.instance().addMapLayer(layer)
            
            # Zoom to layer
            if layer.featureCount() > 0:
                extent = layer.extent()
                buffered_extent = extent.buffered(extent.width() * 0.1 if extent.width() > 0 else 0.1)
                self.canvas.setExtent(buffered_extent)
                self.canvas.refresh()
            
            self.iface.messageBar().pushMessage(
                "Success",
                f"Created {zone_count} DGGS zone polygon(s) from selected feature(s)",
                level=Qgis.Success,
                duration=5
            )
            
        except Exception as e:
            self.iface.messageBar().pushMessage(
                "Error",
                f"Failed to create DGGS zones from polygons: {str(e)}",
                level=Qgis.Critical,
                duration=5
            )
            import traceback
            traceback.print_exc()
    
    def create_dggs_grid_layer(self, extent, dggs_type, resolution):
        """Create a DGGS grid layer covering the specified extent.
        
        Args:
            extent: QgsRectangle extent in EPSG:4326
            dggs_type: DGGS coordinate reference system type
            resolution: DGGS resolution level
        """
        try:
            print(f"[DGGS Grid] Creating grid for extent: {extent.toString()}")
            
            # Remove existing DGGS layer
            existing_layers = QgsProject.instance().mapLayersByName("DGGS Grid")
            for existing_layer in existing_layers:
                QgsProject.instance().removeMapLayer(existing_layer.id())
            
            # Create new polygon layer
            layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "DGGS Grid", "memory")
            
            if not layer.isValid():
                raise Exception("Failed to create valid memory layer")
            
            provider = layer.dataProvider()
            layer.startEditing()
            
            # Add fields
            provider.addAttributes([
                QgsField("zone_id", QVariant.String),
                QgsField("dggs_type", QVariant.String),
                QgsField("resolution", QVariant.Int),
                QgsField("center_lat", QVariant.Double),
                QgsField("center_lon", QVariant.Double),
                QgsField("row", QVariant.Int),
                QgsField("col", QVariant.Int)
            ])
            layer.updateFields()
            
            # Calculate grid parameters
            # Cell size decreases with higher resolution
            cell_size = 0.1 * (15 - resolution) / 2
            
            # Calculate grid dimensions
            min_lon, min_lat = extent.xMinimum(), extent.yMinimum()
            max_lon, max_lat = extent.xMaximum(), extent.yMaximum()
            
            cols = int((max_lon - min_lon) / cell_size) + 1
            rows = int((max_lat - min_lat) / cell_size) + 1
            
            # Limit grid size to prevent performance issues
            max_cells = 100
            if cols * rows > max_cells:
                factor = ((cols * rows) / max_cells) ** 0.5
                cell_size *= factor
                cols = int((max_lon - min_lon) / cell_size) + 1
                rows = int((max_lat - min_lat) / cell_size) + 1
            
            print(f"[DGGS Grid] Creating {rows}x{cols} = {rows*cols} cells")
            
            grid_features = []
            
            for row in range(rows):
                for col in range(cols):
                    # Calculate cell bounds
                    cell_min_lon = min_lon + col * cell_size
                    cell_max_lon = min_lon + (col + 1) * cell_size
                    cell_min_lat = min_lat + row * cell_size
                    cell_max_lat = min_lat + (row + 1) * cell_size
                    
                    # Calculate center
                    center_lon = (cell_min_lon + cell_max_lon) / 2
                    center_lat = (cell_min_lat + cell_max_lat) / 2
                    
                    # Generate zone ID for center
                    zone_id = self.calculate_dggs_zone(
                        center_lat, center_lon, dggs_type, resolution
                    )
                    
                    # Create cell polygon
                    cell_polygon = QgsGeometry.fromPolygonXY([[
                        QgsPointXY(cell_min_lon, cell_min_lat),
                        QgsPointXY(cell_max_lon, cell_min_lat),
                        QgsPointXY(cell_max_lon, cell_max_lat),
                        QgsPointXY(cell_min_lon, cell_max_lat),
                        QgsPointXY(cell_min_lon, cell_min_lat)
                    ]])
                    
                    grid_feature = QgsFeature(layer.fields())
                    grid_feature.setGeometry(cell_polygon)
                    grid_feature.setAttributes([
                        zone_id,
                        dggs_type,
                        resolution,
                        center_lat,
                        center_lon,
                        row,
                        col
                    ])
                    grid_features.append(grid_feature)
            
            # Add features
            provider.addFeatures(grid_features)
            layer.commitChanges()
            layer.updateExtents()
            
            print(f"[DGGS Grid] Created {len(grid_features)} grid cells")
            
            # Style the layer
            symbol = QgsFillSymbol.createSimple({
                'color': '107,179,255,50',  # Semi-transparent blue
                'outline_color': '#1976D2',
                'outline_width': '0.3'
            })
            renderer = QgsSingleSymbolRenderer(symbol)
            layer.setRenderer(renderer)
            
            # Add labels
            text_format = QgsTextFormat()
            text_format.setFont(QFont("Arial", 8))
            text_format.setSize(8)
            text_format.setColor(QColor(0, 0, 0))
            
            buffer_settings = QgsTextBufferSettings()
            buffer_settings.setEnabled(True)
            buffer_settings.setSize(0.5)
            buffer_settings.setColor(QColor(255, 255, 255))
            text_format.setBuffer(buffer_settings)
            
            label_settings = QgsPalLayerSettings()
            label_settings.setFormat(text_format)
            label_settings.fieldName = "zone_id"
            label_settings.enabled = True
            
            labeling = QgsVectorLayerSimpleLabeling(label_settings)
            layer.setLabeling(labeling)
            layer.setLabelsEnabled(True)
            
            # Add layer to project
            QgsProject.instance().addMapLayer(layer)
            
            # Zoom to layer
            self.canvas.setExtent(layer.extent())
            self.canvas.refresh()
            
            self.iface.messageBar().pushMessage(
                "Success",
                f"Created DGGS grid with {len(grid_features)} cells ({rows}×{cols})",
                level=Qgis.Success,
                duration=5
            )
            
        except Exception as e:
            self.iface.messageBar().pushMessage(
                "Error",
                f"Failed to create DGGS grid: {str(e)}",
                level=Qgis.Critical,
                duration=5
            )
            import traceback
            traceback.print_exc()
            self.lblZoneId.setText("Zone ID: (conversion failed)")
            QMessageBox.critical(self, "Error", f"DGGS conversion failed: {str(e)}")
    
    def create_dggs_layer(self, dggs_type, resolution, zone_id):
        """Create and display DGGS zone layer on map.
        
        Args:
            dggs_type: DGGS coordinate reference system type
            resolution: DGGS resolution level
            zone_id: Calculated zone ID
        """
        try:
            print(f"[DGGS Layer] Creating layer for zone: {zone_id}")
            print(f"[DGGS Layer] Location: {self.current_lat}, {self.current_lon}")
            
            # Check if DGGS layer already exists and remove it
            existing_layers = QgsProject.instance().mapLayersByName("DGGS Zones")
            for existing_layer in existing_layers:
                print(f"[DGGS Layer] Removing existing layer: {existing_layer.id()}")
                QgsProject.instance().removeMapLayer(existing_layer.id())
            
            # Create new point layer
            layer = QgsVectorLayer("Point?crs=EPSG:4326", "DGGS Zones", "memory")
            
            if not layer.isValid():
                raise Exception("Failed to create valid memory layer")
            
            print(f"[DGGS Layer] Layer created, valid: {layer.isValid()}")
            
            provider = layer.dataProvider()
            
            # Start editing
            layer.startEditing()
            
            # Add fields
            provider.addAttributes([
                QgsField("zone_id", QVariant.String),
                QgsField("dggs_type", QVariant.String),
                QgsField("resolution", QVariant.Int),
                QgsField("latitude", QVariant.Double),
                QgsField("longitude", QVariant.Double),
                QgsField("location", QVariant.String)
            ])
            layer.updateFields()
            
            print(f"[DGGS Layer] Fields added: {[f.name() for f in layer.fields()]}")
            
            # Create feature for center point
            center_feature = QgsFeature(layer.fields())
            point_geom = QgsGeometry.fromPointXY(QgsPointXY(self.current_lon, self.current_lat))
            center_feature.setGeometry(point_geom)
            center_feature.setAttributes([
                zone_id,
                dggs_type,
                resolution,
                self.current_lat,
                self.current_lon,
                self.txtLocationName.text() or "Center Point"
            ])
            
            print(f"[DGGS Layer] Center feature created with geometry: {center_feature.hasGeometry()}")
            
            features = [center_feature]
            
            # Calculate AOI and add corner zone IDs if available
            if self.current_aoi_bbox:
                print(f"[DGGS Layer] Adding AOI corners from bbox: {self.current_aoi_bbox}")
                west, south, east, north = self.current_aoi_bbox
                
                # Calculate corner zone IDs
                corners = {
                    "SW": (south, west),
                    "SE": (south, east),
                    "NW": (north, west),
                    "NE": (north, east)
                }
                
                for corner_name, (lat, lon) in corners.items():
                    corner_zone_id = self.calculate_dggs_zone(lat, lon, dggs_type, resolution)
                    
                    corner_feature = QgsFeature(layer.fields())
                    corner_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
                    corner_feature.setAttributes([
                        corner_zone_id,
                        dggs_type,
                        resolution,
                        lat,
                        lon,
                        f"AOI Corner {corner_name}"
                    ])
                    features.append(corner_feature)
            
            # Add features to layer
            success, added_features = provider.addFeatures(features)
            print(f"[DGGS Layer] Add features result: {success}, count: {len(added_features)}")
            
            # Commit changes
            layer.commitChanges()
            layer.updateExtents()
            
            print(f"[DGGS Layer] Feature count: {layer.featureCount()}")
            print(f"[DGGS Layer] Extent: {layer.extent().toString()}")
            
            # Style the layer with distinctive markers
            symbol = QgsMarkerSymbol.createSimple({
                'name': 'circle',
                'color': '#FF6B6B',
                'size': '4',
                'outline_color': '#C92A2A',
                'outline_width': '0.5'
            })
            renderer = QgsSingleSymbolRenderer(symbol)
            layer.setRenderer(renderer)
            
            # Add labels showing zone IDs
            text_format = QgsTextFormat()
            text_format.setFont(QFont("Arial", 10, QFont.Bold))
            text_format.setSize(10)
            text_format.setColor(QColor(0, 0, 0))
            
            # Add text buffer (halo) for better visibility
            buffer_settings = QgsTextBufferSettings()
            buffer_settings.setEnabled(True)
            buffer_settings.setSize(1)
            buffer_settings.setColor(QColor(255, 255, 255))
            text_format.setBuffer(buffer_settings)
            
            label_settings = QgsPalLayerSettings()
            label_settings.setFormat(text_format)
            label_settings.fieldName = "zone_id"
            label_settings.enabled = True
            label_settings.dist = 2
            
            # Try to set placement, but handle version incompatibility gracefully
            try:
                # Try different placement options based on QGIS version
                if hasattr(QgsPalLayerSettings, 'AroundPoint'):
                    label_settings.placement = QgsPalLayerSettings.AroundPoint
                elif hasattr(QgsPalLayerSettings, 'OverPoint'):
                    label_settings.placement = QgsPalLayerSettings.OverPoint
                # If neither exists, leave at default
            except Exception as e:
                print(f"[DGGS Layer] Could not set label placement: {e}")
                # Continue without placement setting
            
            labeling = QgsVectorLayerSimpleLabeling(label_settings)
            layer.setLabeling(labeling)
            layer.setLabelsEnabled(True)
            
            # Add layer to project
            QgsProject.instance().addMapLayer(layer)
            print(f"[DGGS Layer] Layer added to project")
            
            # Force refresh
            layer.triggerRepaint()
            self.canvas.refresh()
            
            # Zoom to layer extent if it has features
            if layer.featureCount() > 0:
                extent = layer.extent()
                buffered_extent = extent.buffered(extent.width() * 0.2 if extent.width() > 0 else 0.1)
                print(f"[DGGS Layer] Zooming to extent: {buffered_extent.toString()}")
                self.canvas.setExtent(buffered_extent)
                self.canvas.refresh()
            
            self.iface.messageBar().pushMessage(
                "Success",
                f"Created DGGS zone layer with {layer.featureCount()} point(s)",
                level=Qgis.Success,
                duration=5
            )
            
        except Exception as e:
            self.iface.messageBar().pushMessage(
                "Warning",
                f"Could not create DGGS layer: {str(e)}",
                level=Qgis.Warning,
                duration=5
            )
            import traceback
            traceback.print_exc()
    
    def zoom_to_location(self):
        """Zoom map to current location."""
        if self.current_lon is None or self.current_lat is None:
            return
        
        # Get scale from combo box
        scale_index = self.cmbZoomLevel.currentIndex()
        scale = self.zoom_scales.get(scale_index, 10000)
        
        # Transform point to map CRS
        point_4326 = QgsPointXY(self.current_lon, self.current_lat)
        
        transform = QgsCoordinateTransform(
            QgsCoordinateReferenceSystem('EPSG:4326'),
            self.canvas.mapSettings().destinationCrs(),
            QgsProject.instance()
        )
        
        try:
            point_map = transform.transform(point_4326)
            
            # Set center and scale
            self.canvas.setCenter(point_map)
            self.canvas.zoomScale(scale)
            self.canvas.refresh()
            
            self.iface.messageBar().pushMessage(
                "Success",
                f"Zoomed to location at 1:{scale:,}",
                level=Qgis.Success,
                duration=2
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to zoom: {str(e)}")
    
    def reverse_geocode(self):
        """Perform reverse geocoding using Nominatim."""
        if self.current_lon is None or self.current_lat is None:
            return
        
        try:
            # Nominatim API
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={self.current_lat}&lon={self.current_lon}"
            
            # Set user agent (required by Nominatim)
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'QGIS ShareCOP Plugin/1.0'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
                if 'display_name' in data:
                    self.current_address = data['display_name']
                    self.lblAddress.setText(f"Address: {self.current_address}")
                else:
                    self.lblAddress.setText("Address: (not found)")
        
        except Exception as e:
            self.lblAddress.setText(f"Address: (geocoding failed: {str(e)[:50]})")
    
    def browse_output_dir(self):
        """Browse for output directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly
        )
        
        if directory:
            self.txtOutputDir.setText(directory)
            self.check_export_ready()
    
    def check_export_ready(self):
        """Check if all requirements are met for export."""
        ready = (
            self.current_lon is not None and
            self.current_lat is not None and
            self.txtLocationName.text().strip() != "" and
            len(self.lstLayers.selectedItems()) > 0 and
            self.txtMission.text().strip() != "" and
            self.txtReleasability.text().strip() != "" and
            self.txtOutputDir.text().strip() != ""
        )
        
        self.btnExport.setEnabled(ready)
    
    def export_cop_package(self):
        """Export COP package as signed ZIP file."""
        try:
            # Get metadata
            location_name = self.txtLocationName.text().strip()
            mission = self.txtMission.text().strip()
            classification = self.cmbClassification.currentText()
            releasability = self.txtReleasability.text().strip()
            output_dir = self.txtOutputDir.text().strip()
            sign_package = self.chkSignPackage.isChecked()
            
            # Get selected layers
            selected_layers = []
            project = QgsProject.instance()
            for item in self.lstLayers.selectedItems():
                layer_id = item.data(Qt.UserRole)
                layer = project.mapLayer(layer_id)
                if layer:
                    selected_layers.append(layer)
            
            if not selected_layers:
                QMessageBox.warning(self, "Error", "No layers selected")
                return
            
            # Create exporter
            exporter = STACCOPExporter(output_dir, self.canvas)
            
            # Set clip extent to current view
            extent = self.canvas.extent()
            crs = self.canvas.mapSettings().destinationCrs()
            exporter.set_clip_extent(extent, crs)
            
            # Prepare COP metadata
            cop_metadata = {
                'mission': mission,
                'classification': classification,
                'releasability': releasability,
                'location_name': location_name,
                'location_lat': self.current_lat,
                'location_lon': self.current_lon
            }
            
            if self.current_address:
                cop_metadata['address'] = self.current_address
            
            if self.current_zone_id:
                cop_metadata['dggs_zone_id'] = self.current_zone_id
                cop_metadata['dggs_crs'] = self.cmbDggsCrs.currentText()
            
            # Calculate and add AOI
            aoi_info = self.calculate_aoi()
            if aoi_info:
                cop_metadata['aoi'] = aoi_info
            
            # Add SEAL Geo mission query results if available
            if self.mission_query_results:
                cop_metadata['sealgeo_query'] = {
                    'mission': mission,
                    'timestamp': self.mission_query_results.get('timestamp'),
                    'options_count': len(self.mission_options),
                    'options': self.mission_options[:5]  # Include top 5 options
                }
            
            # Export layers
            self.iface.messageBar().pushMessage(
                "Info",
                f"Exporting {len(selected_layers)} layers...",
                level=Qgis.Info,
                duration=5
            )
            
            exported_items = []
            for layer in selected_layers:
                try:
                    item_path = exporter.export_layer(layer, cop_metadata)
                    exported_items.append(item_path)
                except Exception as e:
                    self.iface.messageBar().pushMessage(
                        "Warning",
                        f"Failed to export layer '{layer.name()}': {str(e)[:100]}",
                        level=Qgis.Warning,
                        duration=5
                    )
            
            # Generate PDF for chatbot results if available
            chatbot_pdf_path = None
            if self.mission_query_results:
                # Check if it's conversation format (new) or options format (old)
                if 'conversation' in self.mission_query_results:
                    chatbot_pdf_path = self.generate_conversation_pdf(
                        exporter.assets_dir,
                        mission,
                        self.mission_query_results['conversation']
                    )
                elif 'options' in self.mission_query_results:
                    # Legacy format support
                    chatbot_pdf_path = self.generate_chatbot_pdf(
                        exporter.assets_dir,
                        mission,
                        self.mission_query_results['options']
                    )
            
            # Create collection
            collection = self.create_collection(exporter, cop_metadata, selected_layers, chatbot_pdf_path)
            collection_path = os.path.join(exporter.stac_dir, 'collection.json')
            with open(collection_path, 'w', encoding='utf-8') as f:
                json.dump(collection, f, indent=2)
            
            # Create ZIP package
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            zip_filename = f"COP_{location_name.replace(' ', '_')}_{timestamp}.zip"
            zip_path = os.path.join(output_dir, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all files from stac_dir
                for root, dirs, files in os.walk(exporter.stac_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, exporter.stac_dir)
                        zipf.write(file_path, arcname)
            
            # Sign package if requested
            if sign_package:
                signature = self.sign_package(zip_path)
                sig_path = zip_path + '.sig'
                with open(sig_path, 'w') as f:
                    f.write(signature)
            
            # Success message
            msg = f"COP package created successfully:\n{zip_path}"
            if sign_package:
                msg += f"\n\nSignature: {sig_path}"
            
            QMessageBox.information(self, "Success", msg)
            
            self.iface.messageBar().pushMessage(
                "Success",
                f"COP package exported: {zip_filename}",
                level=Qgis.Success,
                duration=5
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def create_collection(self, exporter, cop_metadata, layers, chatbot_pdf_path=None):
        """Create STAC collection for the COP.
        
        Args:
            exporter: STACCOPExporter instance
            cop_metadata: Dictionary of COP metadata
            layers: List of exported layers
            chatbot_pdf_path: Optional path to chatbot results PDF
            
        Returns:
            Dictionary representing STAC collection
        """
        # Calculate spatial extent
        extent_4326 = self.calculate_extent(layers)
        
        # Get temporal extent
        now = datetime.now(timezone.utc).isoformat()
        
        collection = {
            "type": "Collection",
            "stac_version": "1.0.0",
            "stac_extensions": [
                "https://stac-extensions.github.io/cop/v1.0.0/schema.json"
            ],
            "id": f"cop-{cop_metadata['location_name'].replace(' ', '-').lower()}",
            "title": f"Common Operating Picture: {cop_metadata['location_name']}",
            "description": f"COP for {cop_metadata['location_name']} - Mission: {cop_metadata['mission']}",
            "license": "proprietary",
            "extent": {
                "spatial": {
                    "bbox": [extent_4326]
                },
                "temporal": {
                    "interval": [[now, None]]
                }
            },
            "properties": {
                "cop:mission": cop_metadata['mission'],
                "cop:classification": cop_metadata['classification'],
                "cop:releasability": cop_metadata['releasability'],
                "location_name": cop_metadata['location_name'],
                "location": {
                    "type": "Point",
                    "coordinates": [cop_metadata['location_lon'], cop_metadata['location_lat']]
                }
            },
            "links": [
                {
                    "rel": "self",
                    "href": "./collection.json",
                    "type": "application/json"
                }
            ]
        }
        
        # Add address if available
        if 'address' in cop_metadata:
            collection['properties']['address'] = cop_metadata['address']
        
        # Add item links
        for item in exporter.exported_items:
            file_name = item.get('_file_name', item['id'])
            collection['links'].append({
                "rel": "item",
                "href": f"./{file_name}.json",
                "type": "application/json"
            })
        
        # Add AOI information if available
        if 'aoi' in cop_metadata:
            collection['properties']['aoi'] = cop_metadata['aoi']
            
            # Add DGGS zone IDs to collection level if available
            if 'dggs_zones' in cop_metadata['aoi']:
                dggs_info = cop_metadata['aoi']['dggs_zones']
                collection['properties']['cop:dggs_crs'] = dggs_info['crs']
                collection['properties']['cop:dggs_resolution'] = dggs_info['resolution']
                
                # Extract unique zone IDs from all corners
                zone_ids = list(set(dggs_info['corners'].values()))
                collection['properties']['cop:dggs_zone_ids'] = zone_ids
                
                # Add center zone ID
                if dggs_info.get('center'):
                    collection['properties']['cop:dggs_center_zone'] = dggs_info['center']
        
        # Add chatbot PDF as asset if available
        if chatbot_pdf_path:
            collection['assets'] = {
                "chatbot_report": {
                    "href": os.path.relpath(chatbot_pdf_path, exporter.stac_dir),
                    "title": "SEAL Geo Chatbot Mission Analysis",
                    "description": "AI-generated mission analysis and recommendations from SEAL Geo RAG Chatbot",
                    "type": "application/pdf",
                    "roles": ["metadata", "overview"]
                }
            }
        
        return collection
    
    def calculate_aoi(self):
        """Calculate 10x10 km Area of Interest around the current point.
        
        Returns:
            Dictionary with AOI bbox and DGGS zone IDs, or None if no location set
        """
        if self.current_lat is None or self.current_lon is None:
            return None
        
        try:
            # Calculate bounding box approximately 5 km in each direction
            # At the equator: 1 degree ≈ 111 km
            # Adjust longitude for latitude using cos(lat)
            km_per_deg_lat = 111.32  # roughly constant
            km_per_deg_lon = 111.32 * math.cos(math.radians(self.current_lat))
            
            # 5 km offset in degrees
            lat_offset = 5.0 / km_per_deg_lat
            lon_offset = 5.0 / km_per_deg_lon
            
            # Calculate bounding box (west, south, east, north)
            west = self.current_lon - lon_offset
            east = self.current_lon + lon_offset
            south = self.current_lat - lat_offset
            north = self.current_lat + lat_offset
            
            # Store bbox
            self.current_aoi_bbox = [west, south, east, north]
            
            aoi_info = {
                "bbox": [round(west, 6), round(south, 6), round(east, 6), round(north, 6)],
                "center": [round(self.current_lon, 6), round(self.current_lat, 6)],
                "size_km": [10, 10],
                "description": "10km x 10km area of interest centered on the selected location"
            }
            
            # Calculate DGGS zone IDs for the four corners if DGGS was converted
            if self.current_zone_id:
                dggs_crs = self.cmbDggsCrs.currentText()
                resolution = self.spinResolution.value()
                
                corners = {
                    "southwest": self.calculate_dggs_zone(south, west, dggs_crs, resolution),
                    "southeast": self.calculate_dggs_zone(south, east, dggs_crs, resolution),
                    "northwest": self.calculate_dggs_zone(north, west, dggs_crs, resolution),
                    "northeast": self.calculate_dggs_zone(north, east, dggs_crs, resolution)
                }
                
                aoi_info["dggs_zones"] = {
                    "crs": dggs_crs,
                    "resolution": resolution,
                    "corners": corners,
                    "center": self.current_zone_id
                }
                
                self.current_aoi_dggs_zones = corners
            
            return aoi_info
            
        except Exception as e:
            self.iface.messageBar().pushMessage(
                "Warning",
                f"Could not calculate AOI: {str(e)}",
                level=Qgis.Warning,
                duration=3
            )
            return None
    
    def calculate_dggs_zone(self, lat, lon, dggs_crs, resolution):
        """Calculate DGGS zone ID for a point.
        
        Args:
            lat: Latitude
            lon: Longitude
            dggs_crs: DGGS coordinate reference system
            resolution: DGGS resolution level
            
        Returns:
            String zone ID
        """
        try:
            # Try using dggal library
            import dggal
            
            # For now, use simplified zone ID format
            # Format: {DGGS_TYPE}-R{RESOLUTION}-{LAT}_{LON}
            zone_id = f"{dggs_crs}-R{resolution}-{lat:.4f}_{lon:.4f}"
            return zone_id
            
        except Exception:
            # Fallback to simplified format
            zone_id = f"{dggs_crs}-R{resolution}-{lat:.4f}_{lon:.4f}"
            return zone_id
    
    def calculate_extent(self, layers):
        """Calculate combined extent of layers in EPSG:4326.
        
        Args:
            layers: List of QgsMapLayer objects
            
        Returns:
            List [west, south, east, north]
        """
        if not layers:
            return [-180, -90, 180, 90]
        
        # Get canvas extent
        extent = self.canvas.extent()
        crs = self.canvas.mapSettings().destinationCrs()
        
        # Transform to EPSG:4326
        transform = QgsCoordinateTransform(
            crs,
            QgsCoordinateReferenceSystem('EPSG:4326'),
            QgsProject.instance()
        )
        
        try:
            extent_4326 = transform.transformBoundingBox(extent)
            return [
                extent_4326.xMinimum(),
                extent_4326.yMinimum(),
                extent_4326.xMaximum(),
                extent_4326.yMaximum()
            ]
        except:
            return [-180, -90, 180, 90]
    
    def sign_package(self, zip_path):
        """Create digital signature for ZIP package.
        
        Args:
            zip_path: Path to ZIP file
            
        Returns:
            String containing signature (SHA256 hash for now)
        """
        # Calculate SHA256 hash
        sha256_hash = hashlib.sha256()
        with open(zip_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        # Create signature metadata
        signature = {
            "version": "1.0",
            "algorithm": "SHA256",
            "hash": sha256_hash.hexdigest(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "signer": "QGIS ShareCOP Plugin",
            "file": os.path.basename(zip_path)
        }
        
        return json.dumps(signature, indent=2)
