# Share Common Operating Picture

A QGIS plugin for selecting locations with reverse geocoding and converting them to DGGS (Discrete Global Grid System) zone IDs using the dggal library.

## Features

- **Interactive Location Picker**: Click on the map to select any location
- **Manual Coordinate Entry**: Enter longitude/latitude coordinates directly
- **Reverse Geocoding**: Get human-readable addresses from coordinates using OpenStreetMap Nominatim
- **DGGS Conversion**: Convert locations to various DGGS zone IDs:
  - rHEALPix (default)
  - ISEA3H
  - H3
  - S2
- **Configurable Resolution**: Select DGGS resolution level (0-20)
- **JSON Export**: Get structured JSON output with location and DGGS data

## Requirements

- QGIS 3.x
- Python 3.x
- **dggal library** (must be installed separately)

## Installation

### 1. Install the Plugin

Copy the `share_common_operating_picture` folder to your QGIS plugins directory:

**macOS:**
```bash
~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/
```

**Linux:**
```bash
~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
```

**Windows:**
```
%APPDATA%/QGIS/QGIS3/profiles/default/python/plugins/
```

Or use `pb_tool deploy` if you have pb_tool installed:
```bash
cd share_common_operating_picture
pb_tool deploy
```

### 2. Install dggal Library

The plugin requires the `dggal` library. Install it in QGIS's Python environment:

**Option A: Using QGIS Python Console (Recommended)**
```python
import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "dggal"])
```

**Option B: Using Terminal (macOS)**
```bash
# For QGIS LTR
/Applications/QGIS-LTR.app/Contents/MacOS/bin/python3 -m pip install dggal

# For QGIS regular version
/Applications/QGIS.app/Contents/MacOS/bin/python3 -m pip install dggal
```

**Note**: The dggal library API is complex. The plugin uses a simplified approach to generate DGGS zone IDs that may not reflect the full DGGS cell identification. For production use with precise DGGS cells, additional integration work may be needed.

### 3. Enable the Plugin

1. Restart QGIS
2. Go to: **Plugins → Manage and Install Plugins → Installed**
3. Enable **"Share Common Operating Picture"**
4. Look for the plugin icon in the toolbar

## Usage

### Pick a Location

1. Click the plugin icon in the toolbar
2. In the dialog, click **"Pick Location from Map"**
3. Click anywhere on the map
4. The coordinates will appear in the longitude/latitude fields

### Reverse Geocode

1. After selecting a location, click **"Reverse Geocode Location"**
2. The address will appear below the button
3. Uses OpenStreetMap Nominatim (free, no API key required)

### Convert to DGGS Zone ID

1. Select your preferred DGGS system from the dropdown (rHEALPix, ISEA3H, H3, or S2)
2. Set the resolution level (default: 12)
3. Click **"Convert to DGGS Zone ID"**
4. The zone ID will appear below the button
5. Full results with JSON output appear in the Results section

### Manual Coordinate Entry

You can also enter coordinates manually:
1. Type longitude in the first field (e.g., 13.4050)
2. Type latitude in the second field (e.g., 52.5200)
3. The geocoding and conversion buttons will enable automatically

## DGGS Systems Supported

- **rHEALPix**: Hierarchical equal area pixelization of a sphere
- **ISEA3H**: Icosahedral Snyder Equal Area Aperture 3 Hexagonal Grid
- **H3**: Uber's Hexagonal Hierarchical Spatial Index
- **S2**: Google's S2 Geometry Library

## Output Format

The plugin generates JSON output in the Results section:

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [13.4050, 52.5200]
  },
  "properties": {
    "dggs_crs": "rHEALPix",
    "dggs_zone_id": "N0123456789",
    "resolution": 12,
    "address": "Berlin, Germany"
  }
}
```

## Troubleshooting

### "dggal library not found" Error

Install dggal using QGIS's Python:
```python
import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "dggal"])
```

### Location Picker Not Working

- Make sure you clicked "Pick Location from Map" first
- The cursor should change to a crosshair
- Click anywhere on the map canvas

### Geocoding Fails

- Check your internet connection (uses OpenStreetMap API)
- Wait a moment and try again (rate limiting)
- The service is free and may have temporary outages

### DGGS Conversion Fails

- Verify dggal is installed correctly
- Check that coordinates are valid (-180 to 180 for longitude, -90 to 90 for latitude)
- Try a different DGGS system or resolution

## Development

The plugin consists of:
- `share_cop.py` - Main plugin class (QGIS lifecycle)
- `share_cop_dialog.py` - Dialog implementation with business logic
- `location_picker.py` - Map tool for picking locations
- `ui/share_cop_dialog.ui` - Qt Designer UI file

## License

This plugin is released under the GNU General Public License v2 or later.

## Credits

- Uses OpenStreetMap Nominatim for reverse geocoding
- Uses dggal library for DGGS conversions
- Developed for the Common Operating Picture (COP) project

## Support

For issues, questions, or contributions:
- Email: luciocol@gmail.com
- GitHub: https://github.com/luciocola/qgisplugin4cop
