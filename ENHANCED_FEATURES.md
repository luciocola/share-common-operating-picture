# Share Common Operating Picture - Enhanced Features

## 🎉 New Features Added

### 1. Location Naming
- Add a descriptive name to your location (e.g., "Berlin Operations Center")
- Location name is included in the COP package and used for file naming

### 2. Map Navigation
- **Zoom to Location**: Automatically zoom the map to your selected location
- **Configurable Zoom Levels**:
  - 1:1,000 (Building level)
  - 1:5,000 (Block level)
  - 1:10,000 (Neighborhood level)
  - 1:50,000 (City level)
  - 1:100,000 (Region level)

### 3. Layer Selection
- Select multiple layers from your QGIS project
- "Select All" / "Select None" buttons for convenience
- Only selected layers are included in the COP package

### 4. COP Metadata
- **Mission**: Operation or mission identifier
- **Classification**: Security classification level
- **Releasability**: Data sharing permissions

### 5. STAC-COP Package Creation
- Creates a complete STAC catalog following the COP extension specification
- Exports selected layers as GeoJSON/raster assets
- Packages everything into a ZIP file
- Includes STAC Collection and Items

### 6. Digital Signing
- Optional SHA256-based package signing
- Creates a `.sig` file with:
  - File hash (SHA256)
  - Timestamp
  - Signer information
- Ensures package integrity and authenticity

## 📋 Complete Workflow

### Step 1: Select Location
1. Click **"Pick Location from Map"**
2. Click anywhere on the map
3. Enter a **Location Name** (e.g., "Berlin HQ")
4. Coordinates are automatically filled

### Step 2: Zoom to Location (Optional)
1. Choose zoom level from dropdown
2. Click **"Zoom to Location"**
3. Map centers and scales to your location

### Step 3: Select Layers
1. In the **Layer Selection** section, choose layers to include
2. Use "Select All" to include all project layers
3. Or select specific layers by clicking them

### Step 4: Add COP Metadata
1. **Mission**: Enter mission/operation name
2. **Classification**: Choose security level
3. **Releasability**: Specify data sharing rules

### Step 5: Configure Export
1. Click **"Browse..."** to select output directory
2. Check **"Sign package"** if you want digital signature
3. Click **"Create COP Package"**

### Step 6: Result
- ZIP file created: `COP_LocationName_YYYYMMDD_HHMMSS.zip`
- Optional signature file: `COP_LocationName_YYYYMMDD_HHMMSS.zip.sig`

## 📦 Package Contents

The ZIP file contains:

```
COP_Berlin_HQ_20251211_100530.zip
├── collection.json          # STAC Collection
├── layer1.json              # STAC Item for layer 1
├── layer2.json              # STAC Item for layer 2
└── assets/
    ├── layer1.geojson       # Exported layer data
    └── layer2.geojson       # Exported layer data
```

### STAC Collection Format

```json
{
  "type": "Collection",
  "stac_version": "1.0.0",
  "stac_extensions": [
    "https://stac-extensions.github.io/cop/v1.0.0/schema.json"
  ],
  "id": "cop-berlin-hq",
  "title": "Common Operating Picture: Berlin HQ",
  "description": "COP for Berlin HQ - Mission: Emergency Response",
  "properties": {
    "cop:mission": "Emergency Response",
    "cop:classification": "public release",
    "cop:releasability": "Public",
    "location_name": "Berlin HQ",
    "location": {
      "type": "Point",
      "coordinates": [13.4050, 52.5200]
    },
    "address": "Berlin, 10178, Deutschland"
  },
  "extent": {...},
  "links": [...]
}
```

### STAC Item Format

Each layer becomes a STAC Item:

```json
{
  "type": "Feature",
  "stac_version": "1.0.0",
  "stac_extensions": [
    "https://stac-extensions.github.io/cop/v1.0.0/schema.json"
  ],
  "id": "uuid-here",
  "geometry": {...},
  "bbox": [...],
  "properties": {
    "datetime": "2025-12-11T10:05:30Z",
    "cop:mission": "Emergency Response",
    "cop:classification": "public release",
    "cop:releasability": "Public"
  },
  "assets": {
    "data": {
      "href": "./assets/layer1.geojson",
      "type": "application/geo+json",
      "roles": ["data"],
      "cop:asset_type": "feature"
    }
  }
}
```

### Signature File Format

```json
{
  "version": "1.0",
  "algorithm": "SHA256",
  "hash": "a1b2c3d4...",
  "timestamp": "2025-12-11T10:05:30+00:00",
  "signer": "QGIS ShareCOP Plugin",
  "file": "COP_Berlin_HQ_20251211_100530.zip"
}
```

## 🔐 Signature Verification

To verify package integrity:

```python
import json
import hashlib

# Load signature
with open('COP_package.zip.sig', 'r') as f:
    sig = json.load(f)

# Calculate hash
sha256_hash = hashlib.sha256()
with open('COP_package.zip', 'rb') as f:
    for chunk in iter(lambda: f.read(4096), b""):
        sha256_hash.update(chunk)

# Verify
if sha256_hash.hexdigest() == sig['hash']:
    print("✅ Package verified!")
else:
    print("❌ Package corrupted!")
```

## 🎯 Use Cases

### Emergency Response
```
Location: "Incident Command Post"
Mission: "Flood Response 2025"
Classification: "internal"
Releasability: "Emergency Services"
Layers: Affected areas, evacuation routes, shelters
```

### Military Operations
```
Location: "Forward Operating Base Alpha"
Mission: "Operation Shield"
Classification: "restricted"
Releasability: "NATO"
Layers: Unit positions, supply routes, threat areas
```

### Environmental Monitoring
```
Location: "Forest Fire Observation Point"
Mission: "Wildfire Containment"
Classification: "public release"
Releasability: "Public"
Layers: Fire perimeter, resources, access roads
```

## 🔧 Technical Details

### Coordinate Systems
- All locations stored in EPSG:4326 (WGS84)
- Layer data transformed to WGS84 for export
- Map extent used for clipping exported data

### File Formats
- Vector layers: GeoJSON
- Raster layers: GeoTIFF
- Metadata: JSON (STAC format)
- Package: ZIP (DEFLATE compression)

### STAC Compliance
- Follows STAC v1.0.0 specification
- Uses COP extension v1.0.0
- Valid JSON Schema
- Self-describing with links

### Required COP Fields
- `cop:mission` - Mission identifier (required)
- `cop:classification` - Security level (required)
- `cop:releasability` - Sharing specification (required)
- `cop:asset_type` - In assets, type of data

## 🚀 Quick Start

1. **Install dggal** (still needed for DGGS if enabled):
   ```python
   import subprocess, sys
   subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'dggal'])
   ```

2. **Restart QGIS**

3. **Enable plugin**: Plugins → Manage and Install Plugins → Installed

4. **Open plugin**: Click toolbar icon

5. **Create COP**:
   - Pick location + name it
   - Select layers
   - Add metadata
   - Export!

## 📝 Notes

- **Automatic Geocoding**: Location is automatically reverse-geocoded when picked
- **Map Extent**: Exported data is clipped to current map view
- **Layer Names**: Used for file naming (sanitized)
- **UUID Generation**: Each STAC item gets a unique UUID
- **Timestamp**: All exports timestamped in UTC

## ⚠️ Limitations

- Maximum ZIP size depends on available disk space
- Large raster layers may take time to export
- Nominatim geocoding requires internet
- SHA256 signing is basic (not cryptographic)

## 🆘 Troubleshooting

**"No layers selected"**: Select at least one layer from the list

**"Export failed"**: Check QGIS Python Console for detailed error

**"Package creation failed"**: Ensure output directory is writable

**Geocoding slow**: Normal for first request, subsequent faster

## 📚 References

- [STAC Specification](https://stacspec.org/)
- [COP Extension](https://github.com/stac-extensions/cop)
- [QGIS API](https://qgis.org/pyqgis/)
- [Nominatim API](https://nominatim.org/release-docs/develop/api/Reverse/)

---

**Version**: 2.0.0  
**Updated**: December 11, 2025  
**Status**: ✅ Production Ready with Enhanced Features
