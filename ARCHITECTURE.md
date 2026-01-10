# Share Common Operating Picture - Architecture Documentation

## Overview

**Share Common Operating Picture** is a QGIS 3.x plugin designed for emergency response and military operations. It enables users to create, package, and share geospatial Common Operating Pictures (COP) using the STAC (SpatioTemporal Asset Catalog) standard with the COP extension v1.0.0.

**Version:** 1.0.0  
**QGIS Compatibility:** 3.0+  
**Primary Use Case:** Emergency management, disaster response, military operations, geospatial intelligence sharing

---

## Architectural Layers

The plugin follows a clean three-layer architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    QGIS Plugin Shell                        │
│  (share_cop.py, __init__.py)                               │
│  • Plugin lifecycle management                              │
│  • Menu/toolbar registration                                │
│  • QGIS interface integration                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    UI & Dialog Layer                        │
│  (share_cop_dialog.py, chat_dialog.py, location_picker.py) │
│  • User interaction                                         │
│  • Form validation                                          │
│  • Map interaction tools                                    │
│  • Chat interface                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Core Business Logic                        │
│  (stac_cop_exporter.py, sealgeo_agent.py,                  │
│   ontology_parser.py)                                       │
│  • STAC/COP export generation                              │
│  • RAG chatbot integration                                  │
│  • Ontology processing                                      │
│  • DGGS zone calculations                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Plugin Entry Point

#### `__init__.py`
- **Purpose:** QGIS plugin loader entry point
- **Responsibility:** Instantiates the main plugin class
- **Key Function:** `classFactory(iface)` - Required by QGIS plugin system

#### `share_cop.py` (ShareCOP class)
- **Purpose:** Main plugin controller
- **Responsibilities:**
  - Plugin initialization and cleanup
  - Menu and toolbar creation
  - Action registration
  - Dialog lifecycle management
- **Key Methods:**
  - `initGui()` - Creates UI elements
  - `unload()` - Cleanup on plugin unload
  - `run()` - Opens main dialog
- **Integration Points:** QGIS interface (`iface`)

---

### 2. User Interface Layer

#### `share_cop_dialog.py` (ShareCOPDialog class)
**Primary Dialog - ~1400 lines**

**Responsibilities:**
- Location selection and geocoding
- Mission metadata collection
- Layer selection and filtering
- DGGS zone calculation
- COP package export orchestration
- PDF report generation

**Key Features:**
- **Location Management:**
  - Map click selection via `LocationPickerTool`
  - Manual coordinate entry
  - Reverse geocoding (Nominatim API)
  - Forward geocoding (address → coordinates)
  - Zoom to location functionality

- **DGGS Integration:**
  - Convert lat/lon to DGGS zone IDs
  - Support for multiple DGGS systems (rHEALPix, IGRS, etc.)
  - AOI (Area of Interest) calculation with corner zones
  - Resolution level selection (1-15)

- **Mission Metadata:**
  - Mission description field
  - Classification level (public/internal/confidential/restricted/classified)
  - Releasability specification
  - Ontology-based concept selection (Red River Flood Ontology)

- **RAG Chatbot Integration:**
  - Manual query button → opens interactive chat
  - Mission analysis and recommendations
  - Conversation history storage
  - PDF transcript generation

- **Export Workflow:**
  - Layer selection from QGIS project
  - STAC item generation per layer
  - Collection metadata assembly
  - ZIP package creation with SHA256 hash
  - Optional digital signature

**UI File:** `ui/share_cop_dialog.ui` (Qt Designer XML)

**Key Methods:**
```python
pick_location()              # Activates map picking tool
geocode_location_name()      # Forward geocoding
reverse_geocode()            # Lat/lon → address
convert_to_dggs()            # Lat/lon → DGGS zone
calculate_aoi()              # 10km×10km AOI with DGGS zones
query_chatbot_manual()       # Opens chat dialog
on_export_clicked()          # Main export orchestration
create_collection()          # STAC Collection assembly
generate_conversation_pdf()  # PDF from chat transcript
```

---

#### `chat_dialog.py` (ChatDialog class)
**Interactive Chat Window - ~350 lines**

**Purpose:** Real-time conversation interface with SEAL Geo RAG chatbot

**Features:**
- **Chat UI:**
  - Styled message bubbles (blue for user, green for bot)
  - Timestamps for each message
  - Auto-scrolling to latest messages
  - Error message display

- **Conversation Management:**
  - Send messages (button or Enter key)
  - Clear chat history
  - Save conversation (TXT or JSON format)
  - Conversation history tracking

- **Export Formats:**
  - **Text:** Human-readable transcript with timestamps
  - **JSON:** Structured data with session metadata

**Key Methods:**
```python
send_message(message)        # Query RAG API
append_user_message()        # Display user input
append_bot_message()         # Display bot response
save_conversation()          # Export to file
get_conversation_history()   # Return conversation data
```

---

#### `location_picker.py` (LocationPickerTool class)
**Map Interaction Tool**

**Purpose:** Custom QGIS map tool for point selection

**Responsibilities:**
- Capture map clicks
- Emit coordinates as signals
- Handle cursor changes
- Restore previous map tool on deactivation

**Key Signal:** `locationPicked(lat, lon)` - Emitted on click

**Integration:** Used by `ShareCOPDialog` to get coordinates from map

---

### 3. Business Logic Layer

#### `stac_cop_exporter.py` (STACCOPExporter class)
**STAC Export Engine - ~590 lines**

**Purpose:** Generate STAC-compliant COP packages

**Responsibilities:**
- Export QGIS layers (vector/raster) to portable formats
- Create STAC Items with COP extension metadata
- Generate STAC Collection with aggregated metadata
- Handle web service layers (XYZ, WMS, WMTS)
- Calculate spatial/temporal extents

**Export Workflow:**
```
1. Create output directory structure:
   output_dir/
   └── stac_cop_export/
       ├── collection.json
       ├── {layer_id}.json (STAC Items)
       └── assets/
           └── {layer_id}.geojson/.tif (Layer data)

2. For each layer:
   - Export to GeoJSON (vector) or GeoTIFF (raster)
   - Create STAC Item with COP metadata
   - Add asset reference with relative path

3. Create Collection:
   - Calculate overall spatial extent
   - Aggregate temporal extent
   - Add DGGS zone metadata (if available)
   - Link all items

4. Package:
   - ZIP all files
   - Generate SHA256 hash
   - Optional digital signature
```

**STAC Compliance:**
- **Version:** 1.0.0
- **Extensions:** 
  - COP v1.0.0 (required)
  - Raster v1.1.0 (for raster layers)

**COP Extension Fields:**
```json
{
  "cop:mission": "string",
  "cop:classification": "public release|internal|confidential|restricted|classified",
  "cop:releasability": "string",
  "cop:dggs_crs": "rHEALPix-R12",
  "cop:dggs_zone_id": "string",
  "cop:dggs_zone_ids": ["zone1", "zone2", ...],
  "cop:dggs_center_zone": "string",
  "cop:dggs_resolution": 12,
  "cop:service_provider": "string",
  "cop:asset_type": "feature|imagery|metadata"
}
```

**Key Methods:**
```python
export_layer(layer, cop_metadata)       # Export single layer
export_layer_data(layer, layer_id)     # Write to file
create_stac_item(layer, metadata)      # Generate STAC Item JSON
create_collection(id, title, desc)     # Generate Collection JSON
create_zip_archive()                   # Package for distribution
sanitize_id(name)                      # Layer name → STAC ID
```

**Special Handling:**
- **Vector Layers:** Export as GeoJSON with CRS transformation to EPSG:4326
- **Raster Layers:** Export as GeoTIFF with GDAL (fallback to QGIS writer)
- **Web Services:** Export metadata JSON instead of raster data
- **Extent Calculation:** Transform to WGS84, handle invalid extents with AOI fallback

---

#### `sealgeo_agent.py` (SEALGeoAgent class)
**RAG Chatbot Client - ~426 lines**

**Purpose:** Interface to SEAL Geo RAG API for mission intelligence

**API Details:**
- **Base URL:** `https://sealgeo.servequake.com`
- **Endpoint:** `/api/chat`
- **Method:** POST
- **Request Format:** `{"question": "query text"}`
- **Response Format:** `{"answer": "response text"}`

**Responsibilities:**
- Query RAG API with mission text
- Handle HTTP errors and timeouts
- Parse and return chatbot responses
- Support multiple query attempts

**Key Methods:**
```python
query_mission(text)          # Main query interface
_query_chatbot(query)        # POST to /api/chat
_query_search(query)         # Try search endpoints (fallback)
_query_stac_catalog(query)   # Try STAC endpoints (fallback)
```

**Error Handling:**
- HTTP 404/422 errors logged with details
- Network timeouts (30s default)
- Graceful degradation with mock data for testing

---

#### `ontology_parser.py`
**Red River Flood Ontology Parser - ~80 lines**

**Purpose:** Extract mission concepts from OWL ontology

**Ontology Source:** `red_river_flood_ontology/red_river_ontology.owl`

**Extracted Concepts (33 total):**
- Bridge, Building, Dam, Emergency Service
- Flood Hazard, Hospital, Infrastructure
- Road Network, School, Shelter, Water Body
- Emergency Vehicle, Evacuation Route, Power Station
- Communication Tower, Critical Infrastructure
- And 18 more...

**Key Functions:**
```python
parse_red_river_ontology()   # Parse OWL file
get_mission_concepts()       # Return concept list
```

**XML Parsing:**
- Namespace: `http://www.semanticweb.org/ontologies/2025/0/red-river-flood#`
- Target Elements: `<owl:Class>` with `<rdfs:label>`
- Format: Returns sorted list of concept names

**UI Integration:**
- Concepts displayed as checkboxes in 3-column grid
- Selected concepts concatenated into Mission field
- Used for mission planning and classification

---

## Data Flow Architecture

### Export Workflow
```
User Input (Dialog)
    ↓
Mission Metadata Collection
    ↓
Layer Selection (QGIS Project)
    ↓
Optional: RAG Chatbot Query
    ↓
STACCOPExporter.export_layer() ← for each layer
    ↓
Create STAC Items (JSON + Assets)
    ↓
ShareCOPDialog.create_collection()
    ↓
Aggregate Metadata (extent, DGGS zones)
    ↓
Create collection.json
    ↓
Optional: Generate PDF Reports
    ↓
ZIP Package Creation
    ↓
SHA256 Hash + Optional Signature
    ↓
Output: COP_{location}_{timestamp}.zip
```

### Chat Workflow
```
User clicks "Query Chatbot"
    ↓
ChatDialog opens with initial mission
    ↓
User types message → ChatDialog.send_message()
    ↓
SEALGeoAgent.query_mission()
    ↓
POST to https://sealgeo.servequake.com/api/chat
    ↓
Response displayed in chat UI
    ↓
Conversation stored in memory
    ↓
User closes dialog
    ↓
Conversation returned to main dialog
    ↓
Stored in mission_query_results
    ↓
PDF generated during export
    ↓
Included in COP package as asset
```

---

## File Structure

```
share_common_operating_picture/
├── __init__.py                    # Plugin entry point
├── share_cop.py                   # Main plugin class (144 lines)
├── share_cop_dialog.py            # Primary dialog (1431 lines)
├── chat_dialog.py                 # Interactive chat UI (350 lines)
├── location_picker.py             # Map click tool (60 lines)
├── stac_cop_exporter.py           # STAC export engine (590 lines)
├── sealgeo_agent.py               # RAG API client (426 lines)
├── ontology_parser.py             # OWL parser (80 lines)
├── metadata.txt                   # Plugin metadata
├── pb_tool.cfg                    # Deployment config
├── icon.png                       # Toolbar icon
├── ui/
│   └── share_cop_dialog.ui        # Qt Designer UI definition
├── test_*.py                      # API testing scripts
└── *.md                           # Documentation files
```

---

## Technology Stack

### Core Technologies
- **QGIS:** 3.0+ (PyQGIS API)
- **Python:** 3.x
- **PyQt5:** UI framework
- **Qt Designer:** UI layout

### Libraries & Dependencies
- **QGIS Core:**
  - `QgsProject` - Project/layer access
  - `QgsVectorLayer` / `QgsRasterLayer` - Layer handling
  - `QgsCoordinateTransform` - CRS transformations
  - `QgsVectorFileWriter` - Vector export
  - `QgsRasterFileWriter` - Raster export
  
- **Python Standard Library:**
  - `json` - STAC JSON generation
  - `zipfile` - Package creation
  - `hashlib` - SHA256 hashing
  - `urllib` - HTTP requests (no external deps)
  - `xml.etree.ElementTree` - OWL parsing
  - `datetime` - Timestamps

- **Optional:**
  - `reportlab` - PDF generation (install via pip)
  - `gdal` - Enhanced raster export

### External APIs
- **Nominatim (OpenStreetMap):** Geocoding
- **SEAL Geo RAG:** Mission intelligence chatbot
- **DGGS Libraries:** Zone calculation (rHEALPix, etc.)

---

## Key Design Patterns

### 1. **Separation of Concerns**
- **UI Layer:** Pure presentation and user interaction
- **Business Layer:** STAC generation, API queries, data processing
- **Plugin Shell:** QGIS integration and lifecycle

### 2. **Signal-Slot Pattern** (Qt/PyQt)
- `LocationPickerTool.locationPicked` → `ShareCOPDialog.on_location_picked()`
- Button clicks → handler methods
- Enables loose coupling between UI components

### 3. **Factory Pattern**
- `classFactory(iface)` - QGIS plugin instantiation

### 4. **Data Transfer Object (DTO)**
- `cop_metadata` dictionary - Passes metadata between layers
- Decouples dialog inputs from export logic

### 5. **Strategy Pattern** (Implicit)
- `export_layer_data()` - Different export strategies for vector/raster/web service

### 6. **Template Method** (Export Workflow)
- `on_export_clicked()` orchestrates steps
- Each step delegates to specialized methods

---

## Extension Points

### Adding New Metadata Fields
1. **UI:** Add widget to `ui/share_cop_dialog.ui`
2. **Dialog:** Read widget value in `on_export_clicked()`
3. **Metadata Dict:** Add to `cop_metadata` dictionary
4. **Exporter:** Add to STAC Item properties in `create_stac_item()`
5. **Collection:** Optionally add to Collection properties in `create_collection()`

### Adding New STAC Extensions
1. Update `stac_extensions` array in `create_stac_item()`
2. Add extension-specific properties to STAC Item
3. Document in comments/README

### Adding New Layer Types
1. Extend `export_layer_data()` with new `isinstance()` check
2. Implement export logic for new type
3. Set appropriate `cop:asset_type`

### Customizing Export Format
- Modify `create_zip_archive()` for different packaging
- Override `create_collection()` for custom metadata structure

---

## Security Considerations

### Digital Signatures
- SHA256 hash of ZIP package
- Optional cryptographic signature (`.sig` file)
- Verifies package integrity during distribution

### Classification Handling
- COP extension classification field (5 levels)
- Releasability specification
- No encryption implemented (transport security only)

### API Communication
- HTTPS required for SEAL Geo RAG API
- No authentication implemented (public endpoint)
- 30-second timeout prevents hanging

### Data Privacy
- Geocoding via public Nominatim API
- No PII collected by plugin
- User responsible for classified data handling

---

## Performance Characteristics

### Scalability
- **Layer Count:** Tested up to 50 layers
- **File Size:** Depends on raster resolution (GeoTIFF compression: LZW)
- **Export Time:** ~1-5 seconds per layer (vector), 10-30 seconds (large rasters)

### Bottlenecks
- **Raster Export:** Large rasters (>1GB) slow, consider clipping
- **Geocoding:** Rate-limited (1 req/sec for Nominatim)
- **RAG API:** Network latency (~2-5 seconds per query)

### Optimizations
- Vector layers export to GeoJSON (fast, portable)
- Raster compression (LZW) reduces ZIP size
- Relative paths in STAC Items (portability)
- Web services export metadata only (no data download)

---

## Testing & Quality Assurance

### Manual Testing Workflow
1. Install plugin: `pb_tool deploy`
2. Restart QGIS
3. Enable in Plugin Manager
4. Test location picker
5. Test geocoding (forward/reverse)
6. Test DGGS conversion
7. Test RAG chatbot
8. Test export with sample layers
9. Validate STAC JSON with `stac-validator`

### Test Scripts Included
- `test_chat_endpoint.py` - RAG API connectivity
- `test_rag_connection.py` - Full conversation test
- `check_api.py` - API endpoint validation

### Known Limitations
- No automated unit tests
- No CI/CD pipeline
- Manual deployment only
- DGGS requires `dggal` library (external dependency)

---

## Deployment

### Installation
1. **Manual:** Copy to QGIS plugins directory
   - macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - Windows: `%APPDATA%/QGIS/QGIS3/profiles/default/python/plugins/`

2. **pb_tool:** `pb_tool deploy` (development workflow)

3. **Dependencies:**
   ```bash
   # Optional: PDF generation
   pip install reportlab
   
   # Optional: Enhanced raster support
   # GDAL usually included with QGIS
   ```

### Configuration
- No external config files
- All settings in dialog UI
- Plugin metadata in `metadata.txt`

---

## Future Enhancements

### Planned Features
1. **Authentication:** API key support for SEAL Geo RAG
2. **Encryption:** AES encryption for classified packages
3. **Batch Export:** Export multiple AOIs in one operation
4. **STAC Browser:** Integrated catalog viewer
5. **Cloud Upload:** Direct upload to STAC API servers
6. **Template System:** Save/load COP metadata templates
7. **Multi-language:** Internationalization (i18n)

### Technical Debt
- Refactor `share_cop_dialog.py` (too large, split into modules)
- Add unit tests (pytest framework)
- Improve error handling (specific exceptions)
- Add logging framework (replace print statements)
- API client abstraction (support multiple RAG backends)

---

## References

### Standards & Specifications
- **STAC:** https://stacspec.org/
- **COP Extension:** https://github.com/stac-extensions/cop
- **GeoJSON:** https://geojson.org/
- **WGS84:** EPSG:4326

### APIs & Services
- **SEAL Geo RAG:** https://sealgeo.servequake.com/api
- **Nominatim:** https://nominatim.openstreetmap.org/
- **DGGS:** rHEALPix, IGRS specifications

### QGIS Resources
- **PyQGIS Cookbook:** https://docs.qgis.org/latest/en/docs/pyqgis_developer_cookbook/
- **Plugin Development:** https://docs.qgis.org/latest/en/docs/pyqgis_developer_cookbook/plugins/index.html

---

## Support & Contact

**Author:** Lucio Colaiacomo  
**Email:** luciocol@gmail.com  
**Repository:** https://github.com/luciocola/qgisplugin4cop  
**Issues:** https://github.com/luciocola/qgisplugin4cop/issues

---

**Document Version:** 1.0  
**Last Updated:** December 14, 2025  
**Plugin Version:** 1.0.0
